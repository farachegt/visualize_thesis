from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np
import xarray as xr
from pint import UnitRegistry

from .canonical_variables import CANONICAL_VARIABLE_NAMES
from .derivations import get_derivation_spec
from .geometry import (
    FixedPointGeometryHandler,
    GeometryHandler,
    GriddedGeometryHandler,
    MovingPointGeometryHandler,
)
from .plot_data import (
    HorizontalFieldPlotData,
    TimeSeriesBandPlotData,
    TimeSeriesPlotData,
    TimeVerticalSectionPlotData,
    VerticalCrossSectionPlotData,
    VerticalProfileBandPlotData,
    VerticalProfilePlotData,
)
from .readers import CSVFileFormatReader, FileFormatReader
from .readers import GRIBFileFormatReader
from .readers import NetCDFFileFormatReader
from .requests import (
    HorizontalFieldRequest,
    TimeSeriesRequest,
    TimeVerticalSectionRequest,
    VerticalCrossSectionRequest,
    VerticalProfileRequest,
)
from .specifications import SourceSpecification, VariableSpecification

FileFormat = Literal["netcdf", "csv", "grib"]
GeometryType = Literal["gridded", "fixed_point", "moving_point"]

UNIT_REGISTRY = UnitRegistry()


@dataclass
class DataAdapter:
    """Prepare semantic data products from a single source.

    Parameters
    ----------
    file_format:
        Source file format used to resolve the concrete reader.
    geometry_type:
        Source geometry used to resolve the concrete geometry handler.
    source_specification:
        Semantic description of variables, coordinates and site metadata.
    path:
        Path to a single source file.
    glob_pattern:
        Glob pattern used only for NetCDF multi-file opening.
    glob_patterns:
        Multiple glob patterns used only for NetCDF multi-file opening.
    reader_options:
        Backend-specific reader options forwarded to xarray or pandas.
    """

    file_format: FileFormat
    geometry_type: GeometryType
    source_specification: SourceSpecification
    path: str | Path | None = None
    glob_pattern: str | None = None
    glob_patterns: Sequence[str] | None = None
    reader_options: Mapping[str, Any] | None = None
    _reader: FileFormatReader | None = field(
        init=False,
        default=None,
        repr=False,
    )
    _geometry_handler: GeometryHandler | None = field(
        init=False,
        default=None,
        repr=False,
    )
    _dataset: xr.Dataset | None = field(
        init=False,
        default=None,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Validate and normalize the adapter configuration.

        Raises
        ------
        ValueError
            If the configured path/glob combination is invalid or if the
            selected file format and geometry type are incompatible.
        """
        if self.path is not None:
            self.path = Path(self.path)
        if self.glob_patterns is not None:
            if isinstance(self.glob_patterns, str):
                raise ValueError(
                    "`glob_patterns` must be a sequence of glob pattern "
                    "strings, not a single string."
                )
            self.glob_patterns = tuple(self.glob_patterns)

        self._validate_configuration()

    def open_data(self) -> xr.Dataset:
        """Open and cache the configured source dataset.

        Returns
        -------
        xr.Dataset
            Dataset opened from disk and validated against the configured
            geometry handler.

        Raises
        ------
        ValueError
            If the source configuration is invalid or the dataset geometry
            does not match the configured geometry handler.
        FileNotFoundError
            If the configured source cannot be found.
        """
        if self._dataset is None:
            reader = self._get_reader()
            dataset = reader.open_data()
            geometry_handler = self._get_geometry_handler()
            geometry_handler.assert_geometry_compatible(
                dataset,
                self.source_specification,
            )
            self._dataset = dataset

        return self._dataset

    def close(self) -> None:
        """Close the cached dataset and clear the adapter cache.

        This is mainly useful in scripts that generate many figures in a
        loop and want to reuse one adapter instance without relying on
        garbage collection to release NetCDF handles.
        """
        if self._dataset is None:
            return

        try:
            self._dataset.close()
        except RuntimeError:
            pass
        finally:
            self._dataset = None

    def to_vertical_profile_plot_data(
        self,
        *,
        variable_name: str,
        request: VerticalProfileRequest,
    ) -> VerticalProfilePlotData:
        """Build a vertical profile plot data object.

        Parameters
        ----------
        variable_name:
            Canonical variable name to be resolved.
        request:
            Vertical profile request describing time, point and vertical axis.

        Returns
        -------
        VerticalProfilePlotData
            Ready-to-plot profile with values on the x axis and vertical
            values on the y axis.

        Raises
        ------
        ValueError
            If the variable cannot be resolved or if the request is
            incompatible with the configured source.
        """
        self._validate_requested_variable(variable_name)
        required_variable_names = self._build_required_variable_names(
            variable_name,
            request.vertical_axis,
        )
        prepared = self._prepare_vertical_profile_dataset(
            required_variable_names,
            request,
        )
        resolved_variables: dict[str, xr.DataArray] = {}
        values = self._resolve_variable(
            prepared,
            variable_name,
            resolved_variables,
        )
        vertical_values = self._resolve_vertical_axis_values(
            prepared,
            request.vertical_axis,
            resolved_variables,
        )

        return VerticalProfilePlotData(
            label=self.source_specification.label,
            values=self._to_numpy_1d(values),
            vertical_values=self._to_numpy_1d(vertical_values),
            vertical_axis=request.vertical_axis,
            units=self._extract_units(values),
        )

    def to_vertical_profile_mean_std_plot_data(
        self,
        *,
        variable_name: str,
        request: VerticalProfileRequest,
    ) -> tuple[VerticalProfilePlotData, VerticalProfileBandPlotData]:
        """Build mean and std-band vertical-profile plot data.

        This supports profile requests that preserve a sample dimension, such
        as the gridded cross-5 point stencil. The mean and population standard
        deviation are computed across non-vertical dimensions at each vertical
        level.
        """
        self._validate_requested_variable(variable_name)
        required_variable_names = self._build_required_variable_names(
            variable_name,
            request.vertical_axis,
        )
        prepared = self._prepare_vertical_profile_dataset(
            required_variable_names,
            request,
        )
        resolved_variables: dict[str, xr.DataArray] = {}
        values = self._resolve_variable(
            prepared,
            variable_name,
            resolved_variables,
        )
        vertical_values = self._resolve_vertical_axis_values(
            prepared,
            request.vertical_axis,
            resolved_variables,
        )
        vertical_name = self._resolve_vertical_axis_name(
            prepared,
            request.vertical_axis,
            resolved_variables,
        )
        mean_values, std_values = self._profile_mean_and_std_over_samples(
            values,
            vertical_name,
        )
        vertical_axis_values = self._to_numpy_1d(vertical_values)
        units = self._extract_units(values)
        mean_plot_data = VerticalProfilePlotData(
            label=self.source_specification.label,
            values=mean_values,
            vertical_values=vertical_axis_values,
            vertical_axis=request.vertical_axis,
            units=units,
        )
        band_plot_data = VerticalProfileBandPlotData(
            label=self.source_specification.label,
            lower_values=mean_values - std_values,
            upper_values=mean_values + std_values,
            vertical_values=vertical_axis_values,
            vertical_axis=request.vertical_axis,
            units=units,
        )
        return mean_plot_data, band_plot_data

    def to_horizontal_field_plot_data(
        self,
        *,
        variable_name: str,
        request: HorizontalFieldRequest,
    ) -> HorizontalFieldPlotData:
        """Build a horizontal field plot data object.

        Parameters
        ----------
        variable_name:
            Canonical variable name to be resolved.
        request:
            Horizontal field request describing time, bbox and level.

        Returns
        -------
        HorizontalFieldPlotData
            Ready-to-plot horizontal field in `(y, x)` order.

        Raises
        ------
        ValueError
            If the variable cannot be resolved or if the request is
            incompatible with the configured source.
        """
        self._validate_requested_variable(variable_name)
        prepared = self._prepare_horizontal_field_dataset(
            self._build_required_variable_names(variable_name),
            request,
        )
        field = self._resolve_variable(prepared, variable_name, {})
        latitude_name = self._resolve_axis_name(prepared, "latitude")
        longitude_name = self._resolve_axis_name(prepared, "longitude")
        if latitude_name is None or longitude_name is None:
            raise ValueError(
                "HorizontalFieldPlotData requires latitude and longitude."
            )

        if latitude_name in field.dims and longitude_name in field.dims:
            field = field.transpose(latitude_name, longitude_name)

        return HorizontalFieldPlotData(
            label=self.source_specification.label,
            field=self._to_numpy_2d(field),
            longitude=np.asarray(prepared[longitude_name].values),
            latitude=np.asarray(prepared[latitude_name].values),
            units=self._extract_units(field),
            time_label=self._format_time_label(
                request.times,
                request.time_reduce,
            ),
            vertical_label=self._format_vertical_label(
                request.vertical_selection
            ),
        )

    def to_vertical_cross_section_plot_data(
        self,
        *,
        variable_name: str,
        request: VerticalCrossSectionRequest,
    ) -> VerticalCrossSectionPlotData:
        """Build a vertical cross-section plot data object.

        Parameters
        ----------
        variable_name:
            Canonical variable name to be resolved.
        request:
            Cross-section request describing transect and vertical axis.

        Returns
        -------
        VerticalCrossSectionPlotData
            Ready-to-plot vertical cross section with `(y, x)` field order.

        Raises
        ------
        ValueError
            If the variable cannot be resolved or if the request is
            incompatible with the configured source.
        """
        self._validate_requested_variable(variable_name)
        required_variable_names = self._build_required_variable_names(
            variable_name,
            request.vertical_axis,
        )
        prepared = self._prepare_vertical_cross_section_dataset(
            required_variable_names,
            request,
        )
        resolved_variables: dict[str, xr.DataArray] = {}
        field = self._resolve_variable(
            prepared,
            variable_name,
            resolved_variables,
        )
        vertical_values = self._resolve_vertical_axis_values(
            prepared,
            request.vertical_axis,
            resolved_variables,
        )
        vertical_name = self._resolve_vertical_axis_name(
            prepared,
            request.vertical_axis,
            resolved_variables,
        )
        if vertical_name in field.dims and "transect" in field.dims:
            field = field.transpose(vertical_name, "transect")

        return VerticalCrossSectionPlotData(
            label=self.source_specification.label,
            field=self._to_numpy_2d(field),
            transect_values=np.asarray(prepared["transect"].values),
            transect_label="Transect index",
            vertical_values=self._to_numpy_1d(vertical_values),
            vertical_axis=request.vertical_axis,
            units=self._extract_units(field),
            transect_latitude=self._optional_coordinate(
                prepared,
                "transect_latitude",
            ),
            transect_longitude=self._optional_coordinate(
                prepared,
                "transect_longitude",
            ),
            start_label=self._format_point_label(
                request.start_lat,
                request.start_lon,
            ),
            end_label=self._format_point_label(
                request.end_lat,
                request.end_lon,
            ),
        )

    def to_time_series_plot_data(
        self,
        *,
        variable_name: str,
        request: TimeSeriesRequest,
    ) -> TimeSeriesPlotData:
        """Build a time-series plot data object.

        Parameters
        ----------
        variable_name:
            Canonical variable name to be resolved.
        request:
            Time-series request describing temporal selection and optional
            point or level selection.

        Returns
        -------
        TimeSeriesPlotData
            Ready-to-plot time series.

        Raises
        ------
        ValueError
            If the variable cannot be resolved or if the request is
            incompatible with the configured source.
        """
        self._validate_requested_variable(variable_name)
        prepared = self._prepare_time_series_dataset(
            self._build_required_variable_names(variable_name),
            request,
        )
        values = self._resolve_variable(prepared, variable_name, {})
        time_name = self._resolve_axis_name(prepared, "time")
        if time_name is None:
            raise ValueError(
                "TimeSeriesPlotData requires a resolved time axis."
            )

        values, times = self._prepare_time_series_values_and_times(
            prepared,
            values,
            time_name,
            request,
        )

        return TimeSeriesPlotData(
            label=self.source_specification.label,
            times=times,
            values=self._to_numpy_1d(values),
            units=self._extract_units(values),
            site_label=self.source_specification.site_label,
            vertical_label=self._format_vertical_label(
                request.vertical_selection
            ),
        )

    def to_time_series_mean_std_plot_data(
        self,
        *,
        variable_name: str,
        request: TimeSeriesRequest,
    ) -> tuple[TimeSeriesPlotData, TimeSeriesBandPlotData]:
        """Build mean and mean-plus/minus-std time-series plot data.

        The requested source may keep one or more sample dimensions after the
        time axis, for example a small grid-point stencil. The returned line is
        the mean across those sample dimensions at each timestamp, and the band
        is mean +/- one population standard deviation.
        """
        self._validate_requested_variable(variable_name)
        prepared = self._prepare_time_series_dataset(
            self._build_required_variable_names(variable_name),
            request,
        )
        values = self._resolve_variable(prepared, variable_name, {})
        time_name = self._resolve_axis_name(prepared, "time")
        if time_name is None:
            raise ValueError(
                "TimeSeriesPlotData requires a resolved time axis."
            )

        values, times = self._prepare_time_series_values_and_times(
            prepared,
            values,
            time_name,
            request,
            preserve_sample_dimensions=True,
        )
        mean_values, std_values = self._mean_and_std_over_samples(values)
        units = self._extract_units(values)
        vertical_label = self._format_vertical_label(
            request.vertical_selection
        )
        mean_plot_data = TimeSeriesPlotData(
            label=self.source_specification.label,
            times=times,
            values=mean_values,
            units=units,
            site_label=self.source_specification.site_label,
            vertical_label=vertical_label,
        )
        band_plot_data = TimeSeriesBandPlotData(
            label=self.source_specification.label,
            times=times,
            lower_values=mean_values - std_values,
            upper_values=mean_values + std_values,
            units=units,
            site_label=self.source_specification.site_label,
            vertical_label=vertical_label,
        )
        return mean_plot_data, band_plot_data

    def to_time_vertical_section_plot_data(
        self,
        *,
        variable_name: str,
        request: TimeVerticalSectionRequest,
    ) -> TimeVerticalSectionPlotData:
        """Build a time-vertical-section plot data object.

        Parameters
        ----------
        variable_name:
            Canonical variable name to be resolved.
        request:
            Time-vertical request describing the temporal range, region and
            vertical axis.

        Returns
        -------
        TimeVerticalSectionPlotData
            Ready-to-plot time-vertical section with `(y, x)` field order.

        Raises
        ------
        ValueError
            If the variable cannot be resolved or if the request is
            incompatible with the configured source.
        """
        self._validate_requested_variable(variable_name)
        required_variable_names = self._build_required_variable_names(
            variable_name,
            request.vertical_axis,
        )
        prepared = self._prepare_time_vertical_section_dataset(
            required_variable_names,
            request,
        )
        resolved_variables: dict[str, xr.DataArray] = {}
        field = self._resolve_variable(
            prepared,
            variable_name,
            resolved_variables,
        )
        time_name = self._resolve_axis_name(prepared, "time")
        if time_name is None:
            raise ValueError(
                "TimeVerticalSectionPlotData requires a resolved time axis."
            )

        vertical_values = self._resolve_vertical_axis_values(
            prepared,
            request.vertical_axis,
            resolved_variables,
        )
        vertical_name = self._resolve_vertical_axis_name(
            prepared,
            request.vertical_axis,
            resolved_variables,
        )
        if vertical_name in field.dims and time_name in field.dims:
            field = field.transpose(vertical_name, time_name)

        return TimeVerticalSectionPlotData(
            label=self.source_specification.label,
            field=self._to_numpy_2d(field),
            times=self._to_datetime64_array(prepared[time_name].values),
            vertical_values=self._to_numpy_1d(vertical_values),
            vertical_axis=request.vertical_axis,
            units=self._extract_units(field),
            region_label=self._format_region_label(request.bbox),
        )

    def _prepare_vertical_profile_dataset(
        self,
        required_variable_names: Sequence[str],
        request: VerticalProfileRequest,
    ) -> xr.Dataset:
        """Dispatch a vertical profile request to the geometry handler."""
        return self._get_geometry_handler().prepare_vertical_profile_dataset(
            self.open_data(),
            self.source_specification,
            required_variable_names,
            request,
        )

    def _prepare_horizontal_field_dataset(
        self,
        required_variable_names: Sequence[str],
        request: HorizontalFieldRequest,
    ) -> xr.Dataset:
        """Dispatch a horizontal field request to the geometry handler."""
        return self._get_geometry_handler().prepare_horizontal_field_dataset(
            self.open_data(),
            self.source_specification,
            required_variable_names,
            request,
        )

    def _prepare_vertical_cross_section_dataset(
        self,
        required_variable_names: Sequence[str],
        request: VerticalCrossSectionRequest,
    ) -> xr.Dataset:
        """Dispatch a cross-section request to the geometry handler."""
        return (
            self._get_geometry_handler()
            .prepare_vertical_cross_section_dataset(
                self.open_data(),
                self.source_specification,
                required_variable_names,
                request,
            )
        )

    def _prepare_time_series_dataset(
        self,
        required_variable_names: Sequence[str],
        request: TimeSeriesRequest,
    ) -> xr.Dataset:
        """Dispatch a time-series request to the geometry handler."""
        return self._get_geometry_handler().prepare_time_series_dataset(
            self.open_data(),
            self.source_specification,
            required_variable_names,
            request,
        )

    def _prepare_time_vertical_section_dataset(
        self,
        required_variable_names: Sequence[str],
        request: TimeVerticalSectionRequest,
    ) -> xr.Dataset:
        """Dispatch a time-vertical request to the geometry handler."""
        return (
            self._get_geometry_handler()
            .prepare_time_vertical_section_dataset(
                self.open_data(),
                self.source_specification,
                required_variable_names,
                request,
            )
        )

    def _build_required_variable_names(
        self,
        variable_name: str,
        vertical_axis_name: str | None = None,
    ) -> tuple[str, ...]:
        """Expand requested variables into direct source dependencies.

        Parameters
        ----------
        variable_name:
            Canonical variable requested by the public adapter method.
        vertical_axis_name:
            Optional canonical vertical-axis variable, such as `pressure` or
            `height`.

        Returns
        -------
        tuple[str, ...]
            Canonical names that map directly to source variables and should
            be passed to the geometry layer.

        Raises
        ------
        ValueError
            If a required variable cannot be resolved to a direct source
            dependency.
        """
        required_names: list[str] = []
        self._collect_source_dependencies(variable_name, required_names)
        if (
            vertical_axis_name is not None
            and self._can_resolve_variable(vertical_axis_name)
        ):
            self._collect_source_dependencies(
                vertical_axis_name,
                required_names,
            )

        return tuple(dict.fromkeys(required_names))

    def _collect_source_dependencies(
        self,
        variable_name: str,
        required_names: list[str],
    ) -> None:
        """Collect direct source dependencies for a canonical variable.

        Parameters
        ----------
        variable_name:
            Canonical variable being expanded.
        required_names:
            Mutable list that accumulates canonical names backed by direct
            source variables.

        Raises
        ------
        ValueError
            If the variable is not declared or cannot be expanded to direct
            source dependencies.
        """
        variable_specification = self.source_specification.variables.get(
            variable_name
        )
        if variable_specification is None:
            raise ValueError(
                "The canonical variable "
                f"{variable_name!r} is not declared in the "
                "SourceSpecification."
            )

        if variable_specification.source_name is not None:
            required_names.append(variable_name)
            return

        if variable_specification.derivation_kind is None:
            raise ValueError(
                "The canonical variable "
                f"{variable_name!r} does not define `source_name` or "
                "`derivation_kind`."
            )

        derivation_spec = get_derivation_spec(
            variable_specification.derivation_kind
        )
        for dependency_name in derivation_spec["dependencies"]:
            self._collect_source_dependencies(dependency_name, required_names)

    def _resolve_variable(
        self,
        dataset: xr.Dataset,
        variable_name: str,
        resolved_variables: dict[str, xr.DataArray],
    ) -> xr.DataArray:
        """Resolve a canonical variable from direct data or derivation.

        Parameters
        ----------
        dataset:
            Prepared dataset returned by the geometry layer.
        variable_name:
            Canonical variable requested for the current output.
        resolved_variables:
            Cache used to avoid repeated conversions and derivations.

        Returns
        -------
        xr.DataArray
            Resolved variable in the units requested by the source
            specification when configured.

        Raises
        ------
        ValueError
            If the variable cannot be resolved from the prepared dataset.
        """
        if variable_name in resolved_variables:
            return resolved_variables[variable_name]

        variable_specification = self.source_specification.variables.get(
            variable_name
        )
        if variable_specification is None:
            raise ValueError(
                "The canonical variable "
                f"{variable_name!r} is not declared in the "
                "SourceSpecification."
            )

        if variable_specification.source_name is not None:
            resolved_variable = self._resolve_direct_variable(
                dataset,
                variable_name,
                variable_specification,
            )
            resolved_variables[variable_name] = resolved_variable
            return resolved_variable

        if variable_specification.derivation_kind is None:
            raise ValueError(
                "The canonical variable "
                f"{variable_name!r} is neither direct nor derivable."
            )

        derivation_spec = get_derivation_spec(
            variable_specification.derivation_kind
        )
        dependency_arrays = [
            self._resolve_variable(
                dataset,
                dependency_name,
                resolved_variables,
            )
            for dependency_name in derivation_spec["dependencies"]
        ]
        derivation_options = self._filter_derivation_options(
            variable_specification,
            derivation_spec["accepted_options"],
        )
        derived_variable = derivation_spec["function"](
            *dependency_arrays,
            **derivation_options,
        )
        if not isinstance(derived_variable, xr.DataArray):
            derived_variable = xr.DataArray(derived_variable)

        target_units = variable_specification.target_units
        if target_units is not None:
            current_units = self._extract_units(derived_variable)
            if current_units is None:
                raise ValueError(
                    "The derived variable "
                    f"{variable_name!r} does not expose units needed for "
                    "conversion."
                )
            derived_variable = self._convert_data_array_units(
                derived_variable,
                current_units,
                target_units,
            )

        resolved_variables[variable_name] = derived_variable
        return derived_variable

    def _resolve_direct_variable(
        self,
        dataset: xr.Dataset,
        variable_name: str,
        variable_specification: VariableSpecification,
    ) -> xr.DataArray:
        """Resolve a direct variable from the prepared dataset."""
        source_name = variable_specification.source_name
        if source_name is None:
            raise ValueError(
                f"The direct variable {variable_name!r} lacks `source_name`."
            )

        if source_name not in dataset and source_name not in dataset.coords:
            raise ValueError(
                "The source variable "
                f"{source_name!r} for {variable_name!r} is not available in "
                "the prepared dataset."
            )

        direct_variable = dataset[source_name]
        known_units = (
            variable_specification.input_units
            or self._extract_units(direct_variable)
        )
        if known_units is not None:
            direct_variable = direct_variable.copy()
            direct_variable.attrs["units"] = known_units

        target_units = variable_specification.target_units
        if target_units is not None:
            if known_units is None:
                raise ValueError(
                    "The variable "
                    f"{variable_name!r} requires unit conversion but no "
                    "input units are available."
                )
            direct_variable = self._convert_data_array_units(
                direct_variable,
                known_units,
                target_units,
            )

        return direct_variable

    def _prepare_time_series_values_and_times(
        self,
        dataset: xr.Dataset,
        values: xr.DataArray,
        time_name: str,
        request: TimeSeriesRequest,
        *,
        preserve_sample_dimensions: bool = False,
    ) -> tuple[xr.DataArray, np.ndarray]:
        """Return time-series values and a matching 1D datetime axis.

        Most sources expose a single time dimension. Some GRIB sources expose
        forecast reference time plus lead time as `(time, step)` and carry the
        actual timestamps in `valid_time`. Those are flattened into a regular
        1D valid-time series here, after the geometry handler has selected the
        point or region.
        """
        if preserve_sample_dimensions and time_name in values.dims:
            ordered_dimensions = (time_name,) + tuple(
                dimension
                for dimension in values.dims
                if dimension != time_name
            )
            return (
                values.transpose(*ordered_dimensions),
                self._to_datetime64_array(dataset[time_name].values),
            )

        if time_name in values.dims:
            extra_dimensions = tuple(
                dimension
                for dimension in values.dims
                if dimension != time_name
            )
            if all(
                values.sizes[dimension] == 1
                for dimension in extra_dimensions
            ):
                one_dimensional_values = values.squeeze(
                    dim=extra_dimensions,
                    drop=True,
                )
                return (
                    one_dimensional_values.transpose(time_name),
                    self._to_datetime64_array(dataset[time_name].values),
                )

        squeezed_values = values.squeeze(drop=True)
        if (
            time_name in squeezed_values.dims
            and len(squeezed_values.dims) == 1
        ):
            return (
                squeezed_values.transpose(time_name),
                self._to_datetime64_array(dataset[time_name].values),
            )

        valid_time = self._resolve_valid_time_coordinate(
            dataset,
            squeezed_values,
        )
        if valid_time is not None:
            return self._stack_valid_time_series(
                squeezed_values,
                valid_time,
                request,
            )

        if time_name in squeezed_values.dims:
            raise ValueError(
                "TimeSeriesPlotData requires values with only the resolved "
                f"time dimension {time_name!r}; got dimensions "
                f"{squeezed_values.dims!r}."
            )

        raise ValueError(
            "TimeSeriesPlotData requires values to expose the resolved time "
            f"dimension {time_name!r} or a compatible `valid_time` "
            f"coordinate; got dimensions {squeezed_values.dims!r}."
        )

    def _resolve_valid_time_coordinate(
        self,
        dataset: xr.Dataset,
        values: xr.DataArray,
    ) -> xr.DataArray | None:
        """Return a `valid_time` coordinate compatible with `values`."""
        valid_time: xr.DataArray | None = None
        if "valid_time" in values.coords:
            valid_time = values.coords["valid_time"]
        elif "valid_time" in dataset.coords:
            valid_time = dataset.coords["valid_time"]
        elif "valid_time" in dataset:
            valid_time = dataset["valid_time"]

        if valid_time is None:
            return None

        valid_time = valid_time.squeeze(drop=True)
        if not valid_time.dims:
            return None

        if any(dimension not in values.dims for dimension in valid_time.dims):
            return None

        return valid_time

    def _stack_valid_time_series(
        self,
        values: xr.DataArray,
        valid_time: xr.DataArray,
        request: TimeSeriesRequest,
    ) -> tuple[xr.DataArray, np.ndarray]:
        """Flatten values that are indexed by a multi-dimensional valid time."""
        stack_dimensions = tuple(valid_time.dims)
        extra_dimensions = tuple(
            dimension
            for dimension in values.dims
            if dimension not in stack_dimensions
        )
        if extra_dimensions:
            values = values.squeeze(dim=extra_dimensions, drop=True)

        if set(values.dims) != set(stack_dimensions):
            raise ValueError(
                "The resolved time-series values are not compatible with "
                "`valid_time`; got value dimensions "
                f"{values.dims!r} and valid_time dimensions "
                f"{valid_time.dims!r}."
            )

        sample_dimension = "__time_series_sample"
        stacked_values = values.stack(
            {sample_dimension: stack_dimensions}
        )
        stacked_times = valid_time.stack(
            {sample_dimension: stack_dimensions}
        )
        time_values = self._to_datetime64_array(stacked_times.values)
        value_array = np.asarray(stacked_values.values)
        finite_time_mask = ~np.isnat(time_values)
        request_times = self._to_datetime64_array(request.times)
        start_time = np.min(request_times)
        end_time = np.max(request_times)
        in_window = (
            finite_time_mask
            & (time_values >= start_time)
            & (time_values <= end_time)
        )
        if not np.any(in_window):
            raise ValueError(
                "TimeSeriesPlotData has no valid-time samples within the "
                "requested interval."
            )

        selected_times = time_values[in_window]
        selected_values = value_array[in_window]
        sort_indices = np.argsort(selected_times)
        selected_times = selected_times[sort_indices]
        selected_values = selected_values[sort_indices]
        result = xr.DataArray(
            selected_values,
            dims=(sample_dimension,),
            coords={sample_dimension: selected_times},
            attrs=dict(values.attrs),
            name=values.name,
        )
        return result, selected_times

    def _mean_and_std_over_samples(
        self,
        values: xr.DataArray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return mean and population std across non-time dimensions."""
        value_array = np.asarray(values.values, dtype=float)
        if value_array.ndim == 0:
            raise ValueError(
                "Time-series statistics require at least a time dimension."
            )
        if value_array.ndim == 1:
            return value_array, np.zeros_like(value_array, dtype=float)

        sample_axes = tuple(range(1, value_array.ndim))
        valid_mask = np.isfinite(value_array)
        valid_counts = np.sum(valid_mask, axis=sample_axes)
        sample_sums = np.nansum(value_array, axis=sample_axes)
        mean_values = np.divide(
            sample_sums,
            valid_counts,
            out=np.full(sample_sums.shape, np.nan, dtype=float),
            where=valid_counts > 0,
        )

        mean_for_samples = mean_values.reshape(
            mean_values.shape + (1,) * (value_array.ndim - 1)
        )
        squared_differences = np.where(
            valid_mask,
            (value_array - mean_for_samples) ** 2,
            0.0,
        )
        variance_values = np.divide(
            np.sum(squared_differences, axis=sample_axes),
            valid_counts,
            out=np.full(mean_values.shape, np.nan, dtype=float),
            where=valid_counts > 0,
        )
        return mean_values, np.sqrt(variance_values)

    def _profile_mean_and_std_over_samples(
        self,
        values: xr.DataArray,
        vertical_dimension: str,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return profile mean/std across non-vertical dimensions."""
        if vertical_dimension not in values.dims:
            raise ValueError(
                "The requested vertical dimension "
                f"{vertical_dimension!r} is not present in the profile "
                "values."
            )

        ordered_dimensions = (vertical_dimension,) + tuple(
            dimension
            for dimension in values.dims
            if dimension != vertical_dimension
        )
        ordered_values = values.transpose(*ordered_dimensions)
        value_array = np.asarray(ordered_values.values, dtype=float)
        if value_array.ndim == 1:
            return value_array, np.zeros_like(value_array, dtype=float)

        sample_axes = tuple(range(1, value_array.ndim))
        valid_mask = np.isfinite(value_array)
        valid_counts = np.sum(valid_mask, axis=sample_axes)
        sample_sums = np.nansum(value_array, axis=sample_axes)
        mean_values = np.divide(
            sample_sums,
            valid_counts,
            out=np.full(sample_sums.shape, np.nan, dtype=float),
            where=valid_counts > 0,
        )
        mean_for_samples = mean_values.reshape(
            mean_values.shape + (1,) * (value_array.ndim - 1)
        )
        squared_differences = np.where(
            valid_mask,
            (value_array - mean_for_samples) ** 2,
            0.0,
        )
        variance_values = np.divide(
            np.sum(squared_differences, axis=sample_axes),
            valid_counts,
            out=np.full(mean_values.shape, np.nan, dtype=float),
            where=valid_counts > 0,
        )
        return mean_values, np.sqrt(variance_values)

    def _resolve_vertical_axis_values(
        self,
        dataset: xr.Dataset,
        vertical_axis: str,
        resolved_variables: dict[str, xr.DataArray],
    ) -> xr.DataArray:
        """Resolve the vertical values used by a vertical plot."""
        if self._can_resolve_variable(vertical_axis):
            vertical_variable = self._resolve_variable(
                dataset,
                vertical_axis,
                resolved_variables,
            )
            vertical_dimension = self._resolve_vertical_axis_name(
                dataset,
                vertical_axis,
                resolved_variables,
            )
            return self._collapse_to_vertical_axis(
                vertical_variable,
                vertical_dimension,
            )

        vertical_name = self._resolve_axis_name(dataset, "vertical")
        if vertical_name is None:
            raise ValueError(
                "The requested vertical axis could not be resolved."
            )

        vertical_coordinate = dataset[vertical_name]
        if not isinstance(vertical_coordinate, xr.DataArray):
            vertical_coordinate = xr.DataArray(vertical_coordinate)
        return self._collapse_to_vertical_axis(
            vertical_coordinate,
            vertical_name,
        )

    def _resolve_vertical_axis_name(
        self,
        dataset: xr.Dataset,
        vertical_axis: str,
        resolved_variables: dict[str, xr.DataArray],
    ) -> str:
        """Resolve the dimension name that should act as vertical axis."""
        vertical_variable = resolved_variables.get(vertical_axis)
        if (
            vertical_variable is None
            and self._can_resolve_variable(vertical_axis)
        ):
            vertical_variable = self._resolve_variable(
                dataset,
                vertical_axis,
                resolved_variables,
            )

        if vertical_variable is not None:
            candidate_name = self._resolve_axis_name(dataset, "vertical")
            if (
                candidate_name is not None
                and candidate_name in vertical_variable.dims
            ):
                return candidate_name

            if vertical_variable.ndim == 1:
                return vertical_variable.dims[0]

            raise ValueError(
                "The resolved vertical variable does not expose a clear "
                "vertical dimension."
            )

        vertical_name = self._resolve_axis_name(dataset, "vertical")
        if vertical_name is None:
            raise ValueError("No vertical axis could be resolved.")

        return vertical_name

    def _collapse_to_vertical_axis(
        self,
        values: xr.DataArray,
        vertical_dimension: str,
    ) -> xr.DataArray:
        """Collapse a vertical coordinate to a single 1D axis.

        This is mainly needed when pressure or height are stored as 2D arrays
        over `(time, vertical)` or `(vertical, transect)`. The MVP keeps the
        vertical axis 1D by averaging across non-vertical dimensions.
        """
        if vertical_dimension not in values.dims:
            raise ValueError(
                "The requested vertical dimension "
                f"{vertical_dimension!r} is not present in the values."
            )

        if values.ndim == 1:
            return values

        reduce_dimensions = [
            dimension
            for dimension in values.dims
            if dimension != vertical_dimension
        ]
        return values.mean(dim=reduce_dimensions, keep_attrs=True)

    def _get_reader(self) -> FileFormatReader:
        """Return the lazily built concrete reader instance."""
        if self._reader is None:
            reader_options = dict(self.reader_options or {})
            if self.file_format == "netcdf":
                self._reader = NetCDFFileFormatReader(
                    path=self.path,
                    glob_pattern=self.glob_pattern,
                    glob_patterns=self.glob_patterns,
                    reader_options=reader_options,
                )
            elif self.file_format == "csv":
                self._reader = CSVFileFormatReader(
                    path=self.path,
                    glob_pattern=self.glob_pattern,
                    glob_patterns=self.glob_patterns,
                    reader_options=reader_options,
                )
            elif self.file_format == "grib":
                self._reader = GRIBFileFormatReader(
                    path=self.path,
                    glob_pattern=self.glob_pattern,
                    glob_patterns=self.glob_patterns,
                    reader_options=reader_options,
                )
            else:
                raise ValueError(
                    f"Unsupported file_format: {self.file_format!r}."
                )

        return self._reader

    def _get_geometry_handler(self) -> GeometryHandler:
        """Return the lazily built concrete geometry handler instance."""
        if self._geometry_handler is None:
            if self.geometry_type == "gridded":
                self._geometry_handler = GriddedGeometryHandler()
            elif self.geometry_type == "fixed_point":
                self._geometry_handler = FixedPointGeometryHandler()
            elif self.geometry_type == "moving_point":
                self._geometry_handler = MovingPointGeometryHandler()
            else:
                raise ValueError(
                    f"Unsupported geometry_type: {self.geometry_type!r}."
                )

        return self._geometry_handler

    def _validate_configuration(self) -> None:
        """Validate whether the adapter configuration is coherent."""
        has_path = self.path is not None
        has_glob = self.glob_pattern is not None
        has_globs = self.glob_patterns is not None
        if sum([has_path, has_glob, has_globs]) != 1:
            raise ValueError(
                "DataAdapter requires exactly one of `path`, "
                "`glob_pattern`, or `glob_patterns`."
            )

        if self.glob_patterns is not None and len(self.glob_patterns) == 0:
            raise ValueError(
                "DataAdapter requires at least one glob pattern when "
                "`glob_patterns` is provided."
            )

        if self.file_format == "csv" and (
            self.glob_pattern is not None
            or self.glob_patterns is not None
        ):
            raise ValueError(
                "CSV sources do not support glob patterns in the MVP."
            )

        if self.file_format == "grib" and self.glob_patterns is not None:
            raise ValueError(
                "GRIB sources do not support `glob_patterns`."
            )

        if self.file_format == "csv" and self.geometry_type != "fixed_point":
            raise ValueError(
                "CSV sources are restricted to `fixed_point` geometry in the "
                "MVP."
            )

    def _validate_requested_variable(self, variable_name: str) -> None:
        """Validate whether a requested variable is canonical and declared."""
        if variable_name not in CANONICAL_VARIABLE_NAMES:
            raise ValueError(
                f"Unknown canonical variable name: {variable_name!r}."
            )

        if variable_name not in self.source_specification.variables:
            raise ValueError(
                "The requested canonical variable "
                f"{variable_name!r} is not declared in the "
                "SourceSpecification."
            )

    def _can_resolve_variable(self, variable_name: str) -> bool:
        """Return whether a variable can be resolved from the source spec."""
        variable_specification = self.source_specification.variables.get(
            variable_name
        )
        if variable_specification is None:
            return False

        if variable_specification.source_name is not None:
            return True

        return variable_specification.derivation_kind is not None

    def _filter_derivation_options(
        self,
        variable_specification: VariableSpecification,
        accepted_options: Sequence[str],
    ) -> dict[str, Any]:
        """Filter derivation options accepted by the selected function."""
        return {
            option_name: option_value
            for option_name, option_value
            in variable_specification.derivation_options.items()
            if option_name in accepted_options
        }

    def _resolve_axis_name(
        self,
        dataset: xr.Dataset,
        role: str,
    ) -> str | None:
        """Resolve an axis name from the source specification or fallbacks."""
        explicit_names = {
            "latitude": self.source_specification.latitude_name,
            "longitude": self.source_specification.longitude_name,
            "time": self.source_specification.time_name,
            "vertical": self.source_specification.vertical_name,
        }
        fallback_names = {
            "latitude": ("latitude", "lat"),
            "longitude": ("longitude", "lon"),
            "time": ("time", "Time"),
            "vertical": ("level", "pres"),
        }
        explicit_name = explicit_names[role]
        if explicit_name is not None:
            if self._name_exists(dataset, explicit_name):
                return explicit_name
            raise ValueError(
                f"The configured {role} name {explicit_name!r} was not "
                "found in the dataset."
            )

        for fallback_name in fallback_names[role]:
            if self._name_exists(dataset, fallback_name):
                return fallback_name

        return None

    def _name_exists(self, dataset: xr.Dataset, name: str) -> bool:
        """Return whether a name exists as variable, coordinate or dim."""
        return (
            name in dataset
            or name in dataset.coords
            or name in dataset.dims
        )

    def _convert_data_array_units(
        self,
        data_array: xr.DataArray,
        from_units: str,
        to_units: str,
    ) -> xr.DataArray:
        """Convert a data array between two explicit unit strings.

        Parameters
        ----------
        data_array:
            Data array to be converted.
        from_units:
            Source units known for the current data array.
        to_units:
            Target units desired by the source specification.

        Returns
        -------
        xr.DataArray
            Converted data array with updated `units` attribute.
        """
        normalized_from = self._normalize_unit_string(from_units)
        normalized_to = self._normalize_unit_string(to_units)
        if normalized_from == normalized_to:
            converted = data_array.copy()
            converted.attrs["units"] = to_units
            return converted

        quantity = (
            np.asarray(data_array.values) * UNIT_REGISTRY(normalized_from)
        )
        converted_values = quantity.to(normalized_to).magnitude
        converted = data_array.copy(data=converted_values)
        converted.attrs["units"] = to_units
        return converted

    def _normalize_unit_string(self, units_text: str) -> str:
        """Normalize loose unit strings into something pint can parse."""
        normalized = units_text.strip()
        normalized = normalized.replace("unitless", "dimensionless")
        normalized = normalized.replace("^", "**")
        normalized = re.sub(r"\{([^{}]+)\}", r"\1", normalized)
        normalized = re.sub(
            r"(?<=[A-Za-z\)])-(\d+)",
            r"**-\1",
            normalized,
        )
        if normalized == "1":
            return "dimensionless"

        return normalized

    def _extract_units(self, values: xr.DataArray) -> str | None:
        """Extract units from a data array when available."""
        units_value = values.attrs.get("units")
        if units_value is None:
            return None

        return str(units_value)

    def _to_numpy_1d(self, values: xr.DataArray) -> np.ndarray:
        """Convert a data array into a squeezed 1D numpy array."""
        return np.asarray(values.values).squeeze()

    def _to_numpy_2d(self, values: xr.DataArray) -> np.ndarray:
        """Convert a data array into a 2D numpy array.

        Raises
        ------
        ValueError
            If the resulting array is not 2D after squeezing.
        """
        array = np.asarray(values.values).squeeze()
        if array.ndim != 2:
            raise ValueError(
                "Expected a 2D field after dataset preparation, but got "
                f"{array.ndim} dimensions."
            )
        return array

    def _to_datetime64_array(self, values: Any) -> np.ndarray:
        """Convert time-like values into `datetime64[ns]` numpy arrays."""
        return np.asarray(values, dtype="datetime64[ns]")

    def _format_time_label(
        self,
        times: np.ndarray,
        time_reduce: str | None,
    ) -> str | None:
        """Build a concise label describing the temporal selection."""
        if times.size == 0:
            return None

        if time_reduce is None:
            return np.datetime_as_string(times[0], unit="s")

        start_time = np.datetime_as_string(np.min(times), unit="s")
        end_time = np.datetime_as_string(np.max(times), unit="s")
        return f"{time_reduce} from {start_time} to {end_time}"

    def _format_vertical_label(self, vertical_selection: Any) -> str | None:
        """Build a compact label for a fixed vertical selection."""
        if vertical_selection is None:
            return None

        return str(vertical_selection)

    def _format_region_label(
        self,
        bbox: tuple[float, float, float, float] | None,
    ) -> str | None:
        """Build a compact label for a selected bounding box."""
        if bbox is None:
            return None

        min_lon, max_lon, min_lat, max_lat = bbox
        return (
            f"lon=({min_lon}, {max_lon}), lat=({min_lat}, {max_lat})"
        )

    def _format_point_label(self, latitude: float, longitude: float) -> str:
        """Build a compact label for a transect endpoint."""
        return f"({latitude}, {longitude})"

    def _optional_coordinate(
        self,
        dataset: xr.Dataset,
        coordinate_name: str,
    ) -> np.ndarray | None:
        """Return an optional coordinate as numpy array when available."""
        if (
            coordinate_name not in dataset
            and coordinate_name not in dataset.coords
        ):
            return None

        return np.asarray(dataset[coordinate_name].values)
