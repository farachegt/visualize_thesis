from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from glob import glob
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import xarray as xr


@dataclass
class FileFormatReader(ABC):
    """Define the common interface for file readers.

    Readers are responsible only for opening data from disk and converting it
    to an `xarray.Dataset`. They must not apply semantic normalization from
    `SourceSpecification`.
    """

    path: Optional[Path] = None
    glob_pattern: Optional[str] = None
    reader_options: Dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def open_data(self) -> xr.Dataset:
        """Open the source and return it as an `xarray.Dataset`.

        Returns
        -------
        xr.Dataset
            Dataset opened from the configured source.

        Raises
        ------
        ValueError
            If the source configuration is invalid.
        FileNotFoundError
            If the configured file or file set does not exist.
        """


@dataclass
class NetCDFFileFormatReader(FileFormatReader):
    """Read NetCDF data from a single file or a glob pattern."""

    def open_data(self) -> xr.Dataset:
        """Open NetCDF data with xarray.

        Returns
        -------
        xr.Dataset
            Dataset opened from the configured NetCDF source.

        Raises
        ------
        ValueError
            If neither `path` nor `glob_pattern` is defined, or if both are
            provided at the same time.
        FileNotFoundError
            If the configured path does not exist or no file matches the
            glob pattern.
        """
        self._validate_source_configuration()

        if self.path is not None:
            if not self.path.exists():
                raise FileNotFoundError(
                    f"NetCDF path does not exist: {self.path}"
                )

            return xr.open_dataset(self.path, **self.reader_options)

        matching_paths = sorted(glob(self.glob_pattern or ""))
        if not matching_paths:
            raise FileNotFoundError(
                "No NetCDF files matched the configured glob pattern: "
                f"{self.glob_pattern}"
            )

        reader_options = dict(self.reader_options)
        reader_options.setdefault("data_vars", "all")
        return xr.open_mfdataset(self.glob_pattern, **reader_options)

    def _validate_source_configuration(self) -> None:
        """Validate whether the reader source configuration is coherent.

        Raises
        ------
        ValueError
            If `path` and `glob_pattern` are both missing or both defined.
        """
        has_path = self.path is not None
        has_glob = self.glob_pattern is not None

        if has_path == has_glob:
            raise ValueError(
                "NetCDFFileFormatReader requires exactly one of `path` or "
                "`glob_pattern`."
            )


@dataclass
class CSVFileFormatReader(FileFormatReader):
    """Read a simple tabular CSV file and convert it to `xarray.Dataset`."""

    def open_data(self) -> xr.Dataset:
        """Open CSV data with pandas and convert it to a dataset.

        Returns
        -------
        xr.Dataset
            Dataset containing the CSV columns as 1D variables on the
            `row` dimension.

        Raises
        ------
        ValueError
            If `path` is missing or if `glob_pattern` is also provided.
        FileNotFoundError
            If the configured CSV path does not exist.
        """
        if self.path is None:
            raise ValueError(
                "CSVFileFormatReader requires a single `path`."
            )

        if self.glob_pattern is not None:
            raise ValueError(
                "CSVFileFormatReader does not support `glob_pattern` in "
                "the MVP."
            )

        if not self.path.exists():
            raise FileNotFoundError(
                f"CSV path does not exist: {self.path}"
            )

        dataframe = pd.read_csv(self.path, **self.reader_options)
        data_vars = {
            column_name: ("row", dataframe[column_name].to_numpy())
            for column_name in dataframe.columns
        }
        return xr.Dataset(data_vars=data_vars)
