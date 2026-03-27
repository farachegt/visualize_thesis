from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import Optional, Sequence, Tuple

import numpy as np
import xarray as xr

from .requests import (
    BaseRequest,
    HorizontalFieldRequest,
    TimeSeriesRequest,
    TimeVerticalSectionRequest,
    VerticalCrossSectionRequest,
    VerticalProfileRequest,
)
from .specifications import SourceSpecification

BBox = Tuple[float, float, float, float]


class GeometryHandler(ABC):
    """Define the common interface for geometric dataset preparation."""

    @abstractmethod
    def assert_geometry_compatible(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> None:
        """Validate whether the dataset matches the handler geometry.

        Parameters
        ----------
        dataset:
            Raw dataset opened by a `FileFormatReader`.
        source_specification:
            Semantic source contract used to resolve coordinate names.

        Raises
        ------
        ValueError
            If the dataset geometry is incompatible with the handler.
        """

    @abstractmethod
    def supported_plot_data_kinds(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> tuple[str, ...]:
        """Return the plot data kinds supported by this geometry handler."""

    @abstractmethod
    def prepare_vertical_profile_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalProfileRequest,
    ) -> xr.Dataset:
        """Prepare an intermediate dataset for a vertical profile plot."""

    @abstractmethod
    def prepare_horizontal_field_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: HorizontalFieldRequest,
    ) -> xr.Dataset:
        """Prepare an intermediate dataset for a horizontal field plot."""

    @abstractmethod
    def prepare_vertical_cross_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalCrossSectionRequest,
    ) -> xr.Dataset:
        """Prepare an intermediate dataset for a vertical cross section."""

    @abstractmethod
    def prepare_time_series_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeSeriesRequest,
    ) -> xr.Dataset:
        """Prepare an intermediate dataset for a time series plot."""

    @abstractmethod
    def prepare_time_vertical_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeVerticalSectionRequest,
    ) -> xr.Dataset:
        """Prepare an intermediate dataset for a time-vertical section."""

    def _select_required_variables(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
    ) -> xr.Dataset:
        """Select only the variables required by the current call.

        Parameters
        ----------
        dataset:
            Input dataset before geometric preparation.
        source_specification:
            Source contract used to map canonical variables to source names.
        required_variable_names:
            Expanded set of canonical variables needed by the current call.

        Returns
        -------
        xr.Dataset
            Dataset containing only the required source variables.

        Raises
        ------
        ValueError
            If a canonical variable is missing from the source specification,
            if it lacks `source_name`, or if the source variable is absent in
            the dataset.
        """
        source_variable_names = []
        for canonical_name in required_variable_names:
            variable_specification = source_specification.variables.get(
                canonical_name
            )
            if variable_specification is None:
                raise ValueError(
                    "The canonical variable "
                    f"{canonical_name!r} is not defined in the "
                    "SourceSpecification."
                )

            if variable_specification.source_name is None:
                raise ValueError(
                    "Geometry preparation requires direct source variables. "
                    f"The canonical variable {canonical_name!r} does not "
                    "define `source_name`."
                )

            source_name = variable_specification.source_name
            if source_name not in dataset:
                raise ValueError(
                    "The source variable "
                    f"{source_name!r} required by {canonical_name!r} was "
                    "not found in the dataset."
                )

            source_variable_names.append(source_name)

        subset = dataset[source_variable_names]
        for axis_name in self._known_axis_names(source_specification, dataset):
            if axis_name in dataset and axis_name not in subset.coords:
                subset = subset.assign_coords({axis_name: dataset[axis_name]})

        return subset

    def _known_axis_names(
        self,
        source_specification: SourceSpecification,
        dataset: xr.Dataset,
    ) -> tuple[str, ...]:
        """Return all resolved axis names available for the dataset."""
        axis_names = []
        for role in ("latitude", "longitude", "time", "vertical"):
            resolved_name = self._resolve_axis_name(
                dataset,
                source_specification,
                role,
            )
            if resolved_name is not None:
                axis_names.append(resolved_name)

        return tuple(axis_names)

    def _resolve_axis_name(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        role: str,
    ) -> Optional[str]:
        """Resolve an axis name from the specification or conservative falls.

        Parameters
        ----------
        dataset:
            Dataset from which coordinates are being resolved.
        source_specification:
            Source contract that may define explicit coordinate names.
        role:
            Axis role to resolve. Supported values are `latitude`,
            `longitude`, `time` and `vertical`.

        Returns
        -------
        str | None
            Resolved axis name, or `None` when the role is not available.

        Raises
        ------
        ValueError
            If an explicit axis name is configured but not found in the
            dataset.
        """
        explicit_names = {
            "latitude": source_specification.latitude_name,
            "longitude": source_specification.longitude_name,
            "time": source_specification.time_name,
            "vertical": source_specification.vertical_name,
        }
        fallbacks = {
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

        for fallback_name in fallbacks[role]:
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

    def _ensure_coordinate(
        self,
        dataset: xr.Dataset,
        coordinate_name: str,
    ) -> xr.Dataset:
        """Promote a 1D variable to coordinate when necessary.

        Parameters
        ----------
        dataset:
            Dataset to normalize.
        coordinate_name:
            Name of the coordinate or 1D variable.

        Returns
        -------
        xr.Dataset
            Dataset with the coordinate promoted when possible.

        Raises
        ------
        ValueError
            If the requested coordinate does not exist or is not 1D.
        """
        if coordinate_name in dataset.coords:
            return dataset

        if coordinate_name not in dataset:
            raise ValueError(
                f"The coordinate {coordinate_name!r} does not exist."
            )

        coordinate_data = dataset[coordinate_name]
        if coordinate_data.ndim != 1:
            raise ValueError(
                f"The coordinate {coordinate_name!r} must be 1D."
            )

        return dataset.assign_coords({coordinate_name: coordinate_data})

    def _apply_single_time_selection(
        self,
        dataset: xr.Dataset,
        time_name: str,
        target_time: np.datetime64,
    ) -> xr.Dataset:
        """Select the nearest instant from a 1D time axis."""
        dataset = self._ensure_coordinate(dataset, time_name)
        time_values = np.asarray(dataset[time_name].values)
        coerced_target_time = self._coerce_time_target(
            time_values,
            target_time,
        )

        try:
            return dataset.sel(
                {time_name: coerced_target_time},
                method="nearest",
            )
        except Exception:
            nearest_index = self._nearest_index(
                time_values,
                coerced_target_time,
            )
            time_dimension = dataset[time_name].dims[0]
            return dataset.isel({time_dimension: nearest_index})

    def _apply_time_range_selection(
        self,
        dataset: xr.Dataset,
        time_name: str,
        times: np.ndarray,
    ) -> xr.Dataset:
        """Select all points within the requested temporal range."""
        dataset = self._ensure_coordinate(dataset, time_name)
        time_values = np.asarray(dataset[time_name].values)
        time_dimension = dataset[time_name].dims[0]
        start_time = self._coerce_time_target(
            time_values,
            np.min(times),
        )
        end_time = self._coerce_time_target(
            time_values,
            np.max(times),
        )

        selected_indices = np.nonzero(
            (time_values >= start_time) & (time_values <= end_time)
        )[0]
        return dataset.isel({time_dimension: selected_indices})

    def _apply_time_reduce(
        self,
        dataset: xr.Dataset,
        time_name: str,
        reduce_name: str,
    ) -> xr.Dataset:
        """Reduce a dataset along its time dimension."""
        dataset = self._ensure_coordinate(dataset, time_name)
        time_dimension = dataset[time_name].dims[0]
        reducer = getattr(dataset, reduce_name)
        return reducer(dim=time_dimension, keep_attrs=True)

    def _apply_time_resample(
        self,
        dataset: xr.Dataset,
        time_name: str,
        time_frequency: Optional[str],
        time_reduce: Optional[str],
    ) -> xr.Dataset:
        """Resample the time axis when both frequency and reduction exist.

        Raises
        ------
        ValueError
            If `time_frequency` is provided without `time_reduce`.
        """
        if time_frequency is None:
            return dataset

        if time_reduce is None:
            raise ValueError(
                "`time_frequency` requires `time_reduce` to be defined."
            )

        dataset = self._ensure_coordinate(dataset, time_name)
        resampler = dataset.resample({time_name: time_frequency})
        reducer = getattr(resampler, time_reduce)
        return reducer(keep_attrs=True)

    def _apply_vertical_selection(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        vertical_selection: object,
    ) -> xr.Dataset:
        """Select a single vertical level when requested."""
        if vertical_selection is None:
            return dataset

        vertical_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "vertical",
        )
        if vertical_name is None:
            raise ValueError(
                "Vertical selection was requested, but no vertical axis "
                "could be resolved."
            )

        dataset = self._ensure_coordinate(dataset, vertical_name)
        try:
            return dataset.sel({vertical_name: vertical_selection},
                               method="nearest")
        except Exception:
            vertical_values = np.asarray(dataset[vertical_name].values)
            nearest_index = self._nearest_index(
                vertical_values,
                vertical_selection,
            )
            vertical_dimension = dataset[vertical_name].dims[0]
            return dataset.isel({vertical_dimension: nearest_index})

    def _require_single_time_or_reduce(
        self,
        request: BaseRequest,
    ) -> None:
        """Validate requests that should not keep multiple times on output."""
        if request.time_reduce is None and len(request.times) != 1:
            raise ValueError(
                "This request expects a single time when `time_reduce` is "
                "not defined."
            )

    def _nearest_index(
        self,
        values: np.ndarray,
        target: object,
    ) -> int:
        """Return the index of the value closest to a target."""
        distances = np.abs(values - target)
        return int(np.argmin(distances))

    def _coerce_time_target(
        self,
        reference_values: np.ndarray,
        target_time: np.datetime64,
    ) -> object:
        """Convert a requested time to the dataset native time type.

        Parameters
        ----------
        reference_values:
            Native time values extracted from the dataset.
        target_time:
            Requested time expressed as `numpy.datetime64`.

        Returns
        -------
        object
            Time value converted to the same family used by the dataset.
        """
        reference_array = np.asarray(reference_values)
        if reference_array.size == 0:
            return target_time

        reference_value = reference_array.reshape(-1)[0]
        if isinstance(reference_value, np.datetime64):
            return np.datetime64(target_time, "ns")

        if self._is_cftime_value(reference_value):
            python_datetime = self._to_python_datetime(target_time)
            reference_type = type(reference_value)
            try:
                return reference_type(
                    python_datetime.year,
                    python_datetime.month,
                    python_datetime.day,
                    python_datetime.hour,
                    python_datetime.minute,
                    python_datetime.second,
                    python_datetime.microsecond,
                )
            except TypeError:
                return reference_type(
                    python_datetime.year,
                    python_datetime.month,
                    python_datetime.day,
                    python_datetime.hour,
                    python_datetime.minute,
                    python_datetime.second,
                )

        if isinstance(reference_value, datetime):
            return self._to_python_datetime(target_time)

        return target_time

    def _is_cftime_value(self, value: object) -> bool:
        """Return whether a value belongs to the `cftime` family."""
        module_name = type(value).__module__
        return module_name.startswith("cftime.")

    def _to_python_datetime(
        self,
        value: np.datetime64,
    ) -> datetime:
        """Convert `numpy.datetime64` values to Python `datetime`."""
        iso_value = np.datetime_as_string(
            np.datetime64(value, "us"),
            unit="us",
        )
        return datetime.fromisoformat(iso_value)

    def _ordered_slice(
        self,
        coordinate_values: np.ndarray,
        lower: float,
        upper: float,
    ) -> slice:
        """Build a slice compatible with ascending or descending axes."""
        if coordinate_values[0] <= coordinate_values[-1]:
            return slice(lower, upper)

        return slice(upper, lower)


class GriddedGeometryHandler(GeometryHandler):
    """Handle datasets organised on a structured horizontal grid."""

    def assert_geometry_compatible(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> None:
        """Validate whether the dataset behaves as a structured grid."""
        latitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "latitude",
        )
        longitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "longitude",
        )
        if latitude_name is None or longitude_name is None:
            raise ValueError(
                "GriddedGeometryHandler requires latitude and longitude."
            )

        latitude_data = dataset[latitude_name]
        longitude_data = dataset[longitude_name]
        if latitude_data.size <= 1 or longitude_data.size <= 1:
            raise ValueError(
                "GriddedGeometryHandler requires more than one horizontal "
                "point in latitude and longitude."
            )

    def supported_plot_data_kinds(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> tuple[str, ...]:
        """Return the plot data kinds supported by gridded geometry."""
        self.assert_geometry_compatible(dataset, source_specification)
        return (
            "VerticalProfilePlotData",
            "HorizontalFieldPlotData",
            "VerticalCrossSectionPlotData",
            "TimeSeriesPlotData",
            "TimeVerticalSectionPlotData",
        )

    def prepare_vertical_profile_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalProfileRequest,
    ) -> xr.Dataset:
        """Prepare a vertical profile dataset from a gridded source."""
        self.assert_geometry_compatible(dataset, source_specification)
        self._require_single_time_or_reduce(request)

        if request.point_lat is None or request.point_lon is None:
            raise ValueError(
                "Gridded vertical profiles require `point_lat` and "
                "`point_lon`."
            )

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )
        prepared = self._apply_gridded_time_logic(
            prepared,
            source_specification,
            request,
        )
        return self._select_nearest_grid_point(
            prepared,
            source_specification,
            request.point_lat,
            request.point_lon,
        )

    def prepare_horizontal_field_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: HorizontalFieldRequest,
    ) -> xr.Dataset:
        """Prepare a horizontal field dataset from a gridded source."""
        self.assert_geometry_compatible(dataset, source_specification)
        self._require_single_time_or_reduce(request)

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )
        prepared = self._apply_gridded_time_logic(
            prepared,
            source_specification,
            request,
        )
        if request.bbox is not None:
            prepared = self._select_bbox(
                prepared,
                source_specification,
                request.bbox,
            )

        return self._apply_vertical_selection(
            prepared,
            source_specification,
            request.vertical_selection,
        )

    def prepare_vertical_cross_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalCrossSectionRequest,
    ) -> xr.Dataset:
        """Prepare a vertical cross section from a gridded source."""
        self.assert_geometry_compatible(dataset, source_specification)
        self._require_single_time_or_reduce(request)
        self._validate_transect_sampling_request(request)

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )
        prepared = self._apply_gridded_time_logic(
            prepared,
            source_specification,
            request,
        )
        return self._sample_transect(
            prepared,
            source_specification,
            request,
        )

    def prepare_time_series_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeSeriesRequest,
    ) -> xr.Dataset:
        """Prepare a time series dataset from a gridded source."""
        self.assert_geometry_compatible(dataset, source_specification)

        if request.bbox is not None and (
            request.point_lat is not None or request.point_lon is not None
        ):
            raise ValueError(
                "Gridded time series must use either `bbox` or point "
                "selection, not both."
            )

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )

        if request.bbox is not None:
            prepared = self._select_bbox(
                prepared,
                source_specification,
                request.bbox,
            )
            prepared = self._average_horizontal_domain(
                prepared,
                source_specification,
            )
        elif request.point_lat is None or request.point_lon is None:
            raise ValueError(
                "Gridded time series require either `bbox` or both "
                "`point_lat` and `point_lon`."
            )
        else:
            prepared = self._select_nearest_grid_point(
                prepared,
                source_specification,
                request.point_lat,
                request.point_lon,
            )
        prepared = self._apply_time_axis_logic(
            prepared,
            source_specification,
            request,
        )
        return self._apply_vertical_selection(
            prepared,
            source_specification,
            request.vertical_selection,
        )

    def prepare_time_vertical_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeVerticalSectionRequest,
    ) -> xr.Dataset:
        """Prepare a time-vertical section dataset from a gridded source."""
        self.assert_geometry_compatible(dataset, source_specification)

        if request.bbox is None:
            raise ValueError(
                "Gridded time-vertical sections require `bbox` in the MVP."
            )

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )
        prepared = self._select_bbox(
            prepared,
            source_specification,
            request.bbox,
        )
        prepared = self._average_horizontal_domain(
            prepared,
            source_specification,
        )
        return self._apply_time_axis_logic(
            prepared,
            source_specification,
            request,
        )

    def _apply_gridded_time_logic(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        request: BaseRequest,
    ) -> xr.Dataset:
        """Apply selection and optional reduction for non-time-axis outputs."""
        time_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "time",
        )
        if time_name is None:
            return dataset

        prepared = self._apply_single_time_selection(
            dataset,
            time_name,
            request.times[0],
        )
        if request.time_reduce is not None:
            prepared = self._apply_time_range_selection(
                dataset,
                time_name,
                request.times,
            )
            prepared = self._apply_time_reduce(
                prepared,
                time_name,
                request.time_reduce,
            )

        return prepared

    def _apply_time_axis_logic(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        request: BaseRequest,
    ) -> xr.Dataset:
        """Apply time-range selection and optional resampling."""
        time_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "time",
        )
        if time_name is None:
            return dataset

        prepared = self._apply_time_range_selection(
            dataset,
            time_name,
            request.times,
        )
        return self._apply_time_resample(
            prepared,
            time_name,
            getattr(request, "time_frequency", None),
            request.time_reduce,
        )

    def _select_nearest_grid_point(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        point_lat: float,
        point_lon: float,
    ) -> xr.Dataset:
        """Select the nearest grid point from a structured grid."""
        latitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "latitude",
        )
        longitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "longitude",
        )
        if latitude_name is None or longitude_name is None:
            raise ValueError(
                "Latitude and longitude are required for point selection."
            )

        dataset = self._ensure_coordinate(dataset, latitude_name)
        dataset = self._ensure_coordinate(dataset, longitude_name)
        latitude_data = dataset[latitude_name]
        longitude_data = dataset[longitude_name]

        if latitude_data.ndim != 1 or longitude_data.ndim != 1:
            raise NotImplementedError(
                "The MVP supports nearest-point selection only for 1D "
                "latitude and longitude coordinates."
            )

        normalized_point_lon = self._normalize_longitude_to_dataset(
            point_lon,
            longitude_data.values,
            source_specification,
        )

        return dataset.sel(
            {
                latitude_name: point_lat,
                longitude_name: normalized_point_lon,
            },
            method="nearest",
        )

    def _select_bbox(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        bbox: BBox,
    ) -> xr.Dataset:
        """Select a horizontal bounding box on a structured grid."""
        latitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "latitude",
        )
        longitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "longitude",
        )
        if latitude_name is None or longitude_name is None:
            raise ValueError(
                "Latitude and longitude are required for bbox selection."
            )

        dataset = self._ensure_coordinate(dataset, latitude_name)
        dataset = self._ensure_coordinate(dataset, longitude_name)
        latitude_values = np.asarray(dataset[latitude_name].values)
        longitude_values = np.asarray(dataset[longitude_name].values)

        if latitude_values.ndim != 1 or longitude_values.ndim != 1:
            raise NotImplementedError(
                "The MVP supports bbox selection only for 1D latitude and "
                "longitude coordinates."
            )

        min_lon, max_lon, min_lat, max_lat = bbox
        min_lon = self._normalize_longitude_to_dataset(
            min_lon,
            longitude_values,
            source_specification,
        )
        max_lon = self._normalize_longitude_to_dataset(
            max_lon,
            longitude_values,
            source_specification,
        )
        latitude_slice = self._ordered_slice(
            latitude_values,
            min_lat,
            max_lat,
        )
        longitude_slice = self._ordered_slice(
            longitude_values,
            min_lon,
            max_lon,
        )
        return dataset.sel(
            {latitude_name: latitude_slice, longitude_name: longitude_slice}
        )

    def _normalize_longitude_to_dataset(
        self,
        longitude: float,
        longitude_values: np.ndarray,
        source_specification: SourceSpecification,
    ) -> float:
        """Normalize one longitude to the convention used by the dataset."""
        convention = self._resolve_longitude_convention(
            longitude_values,
            source_specification,
        )
        if convention == "0_360":
            return float(longitude % 360.0)
        if convention == "-180_180":
            normalized = ((float(longitude) + 180.0) % 360.0) - 180.0
            if normalized == -180.0 and float(longitude) > 0.0:
                return 180.0

            return float(normalized)

        return float(longitude)

    def _resolve_longitude_convention(
        self,
        longitude_values: np.ndarray,
        source_specification: SourceSpecification,
    ) -> str | None:
        """Return the longitude convention declared or implied by a grid."""
        if source_specification.longitude_convention is not None:
            return source_specification.longitude_convention

        finite_values = np.asarray(longitude_values, dtype=float)
        finite_values = finite_values[np.isfinite(finite_values)]
        if finite_values.size == 0:
            return None
        if np.nanmax(finite_values) > 180.0:
            return "0_360"
        if np.nanmin(finite_values) < 0.0:
            return "-180_180"

        return None

    def _average_horizontal_domain(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> xr.Dataset:
        """Average the dataset over its horizontal dimensions."""
        latitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "latitude",
        )
        longitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "longitude",
        )
        if latitude_name is None or longitude_name is None:
            raise ValueError(
                "Latitude and longitude are required for horizontal averaging."
            )

        mean_dimensions = []
        for axis_name in (latitude_name, longitude_name):
            if axis_name in dataset.dims:
                mean_dimensions.append(axis_name)

        if not mean_dimensions:
            raise ValueError(
                "The dataset does not expose horizontal dimensions that can "
                "be averaged."
            )

        return dataset.mean(dim=mean_dimensions, keep_attrs=True)

    def _validate_transect_sampling_request(
        self,
        request: VerticalCrossSectionRequest,
    ) -> None:
        """Validate transect sampling configuration.

        Raises
        ------
        ValueError
            If both or neither `n_points` and `spacing_km` are defined.
        """
        has_n_points = request.n_points is not None
        has_spacing = request.spacing_km is not None
        if has_n_points == has_spacing:
            raise ValueError(
                "Exactly one of `n_points` or `spacing_km` must be defined."
            )

    def _sample_transect(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        request: VerticalCrossSectionRequest,
    ) -> xr.Dataset:
        """Sample a nearest-neighbour transect across the grid."""
        longitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "longitude",
        )
        if longitude_name is None:
            raise ValueError(
                "Longitude is required for transect sampling."
            )

        dataset = self._ensure_coordinate(dataset, longitude_name)
        longitude_values = np.asarray(dataset[longitude_name].values)
        start_lon = self._normalize_longitude_to_dataset(
            request.start_lon,
            longitude_values,
            source_specification,
        )
        end_lon = self._normalize_longitude_to_dataset(
            request.end_lon,
            longitude_values,
            source_specification,
        )

        sample_count = request.n_points
        if sample_count is None:
            total_distance = self._haversine_distance_km(
                request.start_lat,
                start_lon,
                request.end_lat,
                end_lon,
            )
            sample_count = int(total_distance / request.spacing_km) + 1

        sample_count = max(int(sample_count), 2)
        transect_latitudes = np.linspace(
            request.start_lat,
            request.end_lat,
            sample_count,
        )
        transect_longitudes = np.linspace(
            start_lon,
            end_lon,
            sample_count,
        )

        sampled_datasets = []
        for sample_latitude, sample_longitude in zip(
            transect_latitudes,
            transect_longitudes,
        ):
            sampled_dataset = self._select_nearest_grid_point(
                dataset,
                source_specification,
                float(sample_latitude),
                float(sample_longitude),
            )
            sampled_datasets.append(sampled_dataset)

        transect_dataset = xr.concat(sampled_datasets, dim="transect")
        return transect_dataset.assign_coords(
            transect=np.arange(sample_count),
            transect_latitude=("transect", transect_latitudes),
            transect_longitude=("transect", transect_longitudes),
        )

    def _haversine_distance_km(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
    ) -> float:
        """Return the approximate great-circle distance in kilometres."""
        earth_radius_km = 6371.0
        delta_lat = radians(end_lat - start_lat)
        delta_lon = radians(end_lon - start_lon)
        start_lat_rad = radians(start_lat)
        end_lat_rad = radians(end_lat)

        haversine = (
            sin(delta_lat / 2.0) ** 2
            + cos(start_lat_rad)
            * cos(end_lat_rad)
            * sin(delta_lon / 2.0) ** 2
        )
        return 2.0 * earth_radius_km * asin(sqrt(haversine))


class FixedPointGeometryHandler(GeometryHandler):
    """Handle datasets sampled at a fixed horizontal position."""

    def assert_geometry_compatible(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> None:
        """Validate whether the dataset behaves as a fixed-point source."""
        latitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "latitude",
        )
        longitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "longitude",
        )

        if latitude_name is None or longitude_name is None:
            if (
                source_specification.site_latitude is None
                or source_specification.site_longitude is None
            ):
                raise ValueError(
                    "FixedPointGeometryHandler requires either latitude and "
                    "longitude in the dataset or fixed site metadata in "
                    "SourceSpecification."
                )
            return

        if dataset[latitude_name].size > 1 or dataset[longitude_name].size > 1:
            raise ValueError(
                "FixedPointGeometryHandler expects a single horizontal "
                "position."
            )

    def supported_plot_data_kinds(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> tuple[str, ...]:
        """Return the plot data kinds supported by fixed-point geometry."""
        self.assert_geometry_compatible(dataset, source_specification)
        return (
            "VerticalProfilePlotData",
            "TimeSeriesPlotData",
            "TimeVerticalSectionPlotData",
        )

    def prepare_vertical_profile_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalProfileRequest,
    ) -> xr.Dataset:
        """Prepare a vertical profile dataset from a fixed-point source."""
        self.assert_geometry_compatible(dataset, source_specification)
        self._require_single_time_or_reduce(request)

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )
        return self._apply_non_axis_time_logic(
            prepared,
            source_specification,
            request,
        )

    def prepare_horizontal_field_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: HorizontalFieldRequest,
    ) -> xr.Dataset:
        """Fixed-point geometry cannot produce horizontal fields."""
        raise NotImplementedError(
            "FixedPointGeometryHandler does not support "
            "HorizontalFieldPlotData."
        )

    def prepare_vertical_cross_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalCrossSectionRequest,
    ) -> xr.Dataset:
        """Fixed-point geometry cannot produce vertical cross sections."""
        raise NotImplementedError(
            "FixedPointGeometryHandler does not support "
            "VerticalCrossSectionPlotData."
        )

    def prepare_time_series_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeSeriesRequest,
    ) -> xr.Dataset:
        """Prepare a time series dataset from a fixed-point source."""
        self.assert_geometry_compatible(dataset, source_specification)

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )
        prepared = self._apply_time_axis_logic(
            prepared,
            source_specification,
            request,
        )
        return self._apply_vertical_selection(
            prepared,
            source_specification,
            request.vertical_selection,
        )

    def prepare_time_vertical_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeVerticalSectionRequest,
    ) -> xr.Dataset:
        """Prepare a time-vertical section from a fixed-point source."""
        self.assert_geometry_compatible(dataset, source_specification)

        prepared = self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )
        return self._apply_time_axis_logic(
            prepared,
            source_specification,
            request,
        )

    def _apply_non_axis_time_logic(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        request: BaseRequest,
    ) -> xr.Dataset:
        """Apply time selection for outputs that do not keep time as axis."""
        time_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "time",
        )
        if time_name is None:
            return dataset

        prepared = self._apply_single_time_selection(
            dataset,
            time_name,
            request.times[0],
        )
        if request.time_reduce is not None:
            prepared = self._apply_time_range_selection(
                dataset,
                time_name,
                request.times,
            )
            prepared = self._apply_time_reduce(
                prepared,
                time_name,
                request.time_reduce,
            )

        return prepared

    def _apply_time_axis_logic(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        request: BaseRequest,
    ) -> xr.Dataset:
        """Apply time-range selection and optional resampling."""
        time_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "time",
        )
        if time_name is None:
            return dataset

        prepared = self._apply_time_range_selection(
            dataset,
            time_name,
            request.times,
        )
        return self._apply_time_resample(
            prepared,
            time_name,
            getattr(request, "time_frequency", None),
            request.time_reduce,
        )


class MovingPointGeometryHandler(GeometryHandler):
    """Handle datasets sampled along moving-point profiles."""

    def assert_geometry_compatible(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> None:
        """Validate whether the dataset can be treated as moving-point."""
        time_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "time",
        )
        if time_name is None:
            raise ValueError(
                "MovingPointGeometryHandler requires a time-like axis."
            )

        latitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "latitude",
        )
        longitude_name = self._resolve_axis_name(
            dataset,
            source_specification,
            "longitude",
        )
        if latitude_name is not None and dataset[latitude_name].size > 1:
            return

        if longitude_name is not None and dataset[longitude_name].size > 1:
            return

    def supported_plot_data_kinds(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
    ) -> tuple[str, ...]:
        """Return the plot data kinds supported by moving-point geometry."""
        self.assert_geometry_compatible(dataset, source_specification)
        return ("VerticalProfilePlotData",)

    def prepare_vertical_profile_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalProfileRequest,
    ) -> xr.Dataset:
        """Prepare a vertical profile dataset from a moving-point source."""
        self.assert_geometry_compatible(dataset, source_specification)
        if request.time_reduce is not None:
            raise ValueError(
                "Moving-point vertical profiles do not support "
                "`time_reduce` in the MVP."
            )

        return self._select_required_variables(
            dataset,
            source_specification,
            required_variable_names,
        )

    def prepare_horizontal_field_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: HorizontalFieldRequest,
    ) -> xr.Dataset:
        """Moving-point geometry cannot produce horizontal fields."""
        raise NotImplementedError(
            "MovingPointGeometryHandler does not support "
            "HorizontalFieldPlotData."
        )

    def prepare_vertical_cross_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: VerticalCrossSectionRequest,
    ) -> xr.Dataset:
        """Moving-point geometry cannot produce cross sections."""
        raise NotImplementedError(
            "MovingPointGeometryHandler does not support "
            "VerticalCrossSectionPlotData."
        )

    def prepare_time_series_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeSeriesRequest,
    ) -> xr.Dataset:
        """Moving-point geometry cannot produce time series in the MVP."""
        raise NotImplementedError(
            "MovingPointGeometryHandler does not support TimeSeriesPlotData "
            "in the MVP."
        )

    def prepare_time_vertical_section_dataset(
        self,
        dataset: xr.Dataset,
        source_specification: SourceSpecification,
        required_variable_names: Sequence[str],
        request: TimeVerticalSectionRequest,
    ) -> xr.Dataset:
        """Moving-point geometry cannot produce time-vertical sections."""
        raise NotImplementedError(
            "MovingPointGeometryHandler does not support "
            "TimeVerticalSectionPlotData."
        )
