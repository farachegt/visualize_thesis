from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Tuple

import numpy as np
import xarray as xr

from ...adapter import DataAdapter
from ...plot_data import HorizontalFieldPlotData
from ...requests import HorizontalFieldRequest
from .comparison_matrix import (
    resolve_difference_units,
    validate_horizontal_field_compatibility,
)

BBox = Tuple[float, float, float, float]
DiurnalTimeReduce = Literal["min", "max"]


@dataclass
class DiurnalSourceInput:
    """Describe one source field participating in a diurnal reduction."""

    adapter: DataAdapter
    variable_name: str
    source_label: str
    bbox: BBox | None = None
    vertical_selection: Any | None = None


def resolve_diurnal_reduced_plot_data(
    source_input: DiurnalSourceInput,
    day_start: np.datetime64,
    day_duration: np.timedelta64,
    *,
    time_reduce: DiurnalTimeReduce,
) -> HorizontalFieldPlotData:
    """Resolve one source into a reduced daily map field."""
    plot_data = source_input.adapter.to_horizontal_field_plot_data(
        variable_name=source_input.variable_name,
        request=_build_diurnal_horizontal_request(
            day_start=day_start,
            day_duration=day_duration,
            time_reduce=time_reduce,
            bbox=source_input.bbox,
            vertical_selection=source_input.vertical_selection,
        ),
    )
    plot_data.label = source_input.source_label
    plot_data.time_label = np.datetime_as_string(day_start, unit="D")
    return plot_data


def resolve_diurnal_amplitude_plot_data(
    source_input: DiurnalSourceInput,
    day_start: np.datetime64,
    day_duration: np.timedelta64,
) -> HorizontalFieldPlotData:
    """Resolve one source into a daily amplitude map field."""
    max_plot_data = resolve_diurnal_reduced_plot_data(
        source_input,
        day_start,
        day_duration,
        time_reduce="max",
    )
    min_plot_data = resolve_diurnal_reduced_plot_data(
        source_input,
        day_start,
        day_duration,
        time_reduce="min",
    )
    validate_horizontal_field_compatibility(
        max_plot_data,
        min_plot_data,
    )
    return HorizontalFieldPlotData(
        label=source_input.source_label,
        field=max_plot_data.field - min_plot_data.field,
        longitude=np.asarray(max_plot_data.longitude),
        latitude=np.asarray(max_plot_data.latitude),
        units=resolve_difference_units(
            max_plot_data.units,
            min_plot_data.units,
        ),
        time_label=np.datetime_as_string(day_start, unit="D"),
        vertical_label=(
            max_plot_data.vertical_label or min_plot_data.vertical_label
        ),
    )


def resolve_diurnal_peak_phase_plot_data(
    source_input: DiurnalSourceInput,
    day_start: np.datetime64,
    day_duration: np.timedelta64,
) -> HorizontalFieldPlotData:
    """Resolve one source into a daily peak-phase map field."""
    peak_phase_field = _resolve_diurnal_peak_phase_field(
        source_input,
        day_start,
        day_duration,
    )
    dataset = source_input.adapter.open_data()
    latitude_name = source_input.adapter._resolve_axis_name(
        dataset,
        "latitude",
    )
    longitude_name = source_input.adapter._resolve_axis_name(
        dataset,
        "longitude",
    )
    if latitude_name is None or longitude_name is None:
        raise ValueError(
            "Diurnal peak-phase rows require latitude and longitude axes."
        )

    if (
        latitude_name in peak_phase_field.dims
        and longitude_name in peak_phase_field.dims
    ):
        peak_phase_field = peak_phase_field.transpose(
            latitude_name,
            longitude_name,
        )

    return HorizontalFieldPlotData(
        label=source_input.source_label,
        field=np.asarray(peak_phase_field.values, dtype=float),
        longitude=np.asarray(peak_phase_field[longitude_name].values),
        latitude=np.asarray(peak_phase_field[latitude_name].values),
        units="hour",
        time_label=np.datetime_as_string(day_start, unit="D"),
        vertical_label=source_input.adapter._format_vertical_label(
            source_input.vertical_selection
        ),
    )


def build_phase_difference_plot_data(
    left_plot_data: HorizontalFieldPlotData,
    right_plot_data: HorizontalFieldPlotData,
    *,
    label: str,
) -> HorizontalFieldPlotData:
    """Build the wrapped phase difference field used in comparison panels."""
    validate_horizontal_field_compatibility(
        left_plot_data,
        right_plot_data,
    )
    difference_field = (
        ((left_plot_data.field - right_plot_data.field + 12.0) % 24.0)
        - 12.0
    )
    return HorizontalFieldPlotData(
        label=label,
        field=difference_field,
        longitude=np.asarray(left_plot_data.longitude),
        latitude=np.asarray(left_plot_data.latitude),
        units="hour",
        time_label=left_plot_data.time_label or right_plot_data.time_label,
        vertical_label=(
            left_plot_data.vertical_label or right_plot_data.vertical_label
        ),
    )


def _resolve_diurnal_peak_phase_field(
    source_input: DiurnalSourceInput,
    day_start: np.datetime64,
    day_duration: np.timedelta64,
) -> xr.DataArray:
    """Resolve one source into a daily peak-hour `DataArray`."""
    dataset = source_input.adapter.open_data()
    resolved_variables: dict[str, xr.DataArray] = {}
    field = source_input.adapter._resolve_variable(
        dataset,
        source_input.variable_name,
        resolved_variables,
    )
    field = _apply_optional_bbox_to_data_array(
        field,
        source_input.adapter,
        source_input.bbox,
    )
    field = _apply_optional_vertical_selection_to_data_array(
        field,
        source_input.adapter,
        source_input.vertical_selection,
    )
    time_name = source_input.adapter._resolve_axis_name(dataset, "time")
    if time_name is None or time_name not in field.dims:
        raise ValueError(
            "Diurnal peak-phase rows require a time axis in the resolved "
            "field."
        )

    daily_field = _select_day_samples(
        field,
        time_name,
        day_start,
        day_duration,
        source_input.adapter,
    )
    if daily_field.sizes.get(time_name, 0) == 0:
        raise ValueError(
            "The requested day produced no time samples for "
            f"{source_input.variable_name!r}."
        )

    valid_mask = daily_field.notnull().any(time_name)
    peak_time = daily_field.fillna(-np.inf).idxmax(time_name)
    peak_hour = peak_time.dt.hour.astype(float)
    return peak_hour.where(valid_mask)


def _build_diurnal_horizontal_request(
    *,
    day_start: np.datetime64,
    day_duration: np.timedelta64,
    time_reduce: str,
    bbox: BBox | None,
    vertical_selection: Any | None,
) -> HorizontalFieldRequest:
    """Build one reduced horizontal-field request for a diurnal product."""
    day_end = day_start + day_duration
    return HorizontalFieldRequest(
        times=np.asarray([day_start, day_end], dtype="datetime64[ns]"),
        time_reduce=time_reduce,  # type: ignore[arg-type]
        bbox=bbox,
        vertical_selection=vertical_selection,
    )


def _select_day_samples(
    field: xr.DataArray,
    time_name: str,
    day_start: np.datetime64,
    day_duration: np.timedelta64,
    adapter: DataAdapter,
) -> xr.DataArray:
    """Select only the samples that belong to one daily window."""
    day_label = np.datetime_as_string(day_start, unit="D")
    selected = field.where(
        field[time_name].dt.strftime("%Y-%m-%d") == day_label,
        drop=True,
    )
    if selected.sizes.get(time_name, 0) > 0:
        return selected

    geometry_handler = adapter._get_geometry_handler()
    start_target = geometry_handler._coerce_time_target(
        np.asarray(field[time_name].values),
        np.datetime64(day_start, "ns"),
    )
    end_target = geometry_handler._coerce_time_target(
        np.asarray(field[time_name].values),
        np.datetime64(day_start + day_duration, "ns"),
    )
    return field.sel({time_name: slice(start_target, end_target)})


def _apply_optional_bbox_to_data_array(
    field: xr.DataArray,
    adapter: DataAdapter,
    bbox: BBox | None,
) -> xr.DataArray:
    """Apply optional bbox selection to a resolved data array."""
    if bbox is None:
        return field

    dataset = field.to_dataset(name="__value__")
    prepared = adapter._get_geometry_handler()._select_bbox(
        dataset,
        adapter.source_specification,
        bbox,
    )
    return prepared["__value__"]


def _apply_optional_vertical_selection_to_data_array(
    field: xr.DataArray,
    adapter: DataAdapter,
    vertical_selection: Any | None,
) -> xr.DataArray:
    """Apply optional vertical selection to a resolved data array."""
    if vertical_selection is None:
        return field

    dataset = field.to_dataset(name="__value__")
    prepared = adapter._get_geometry_handler()._apply_vertical_selection(
        dataset,
        adapter.source_specification,
        vertical_selection,
    )
    return prepared["__value__"]
