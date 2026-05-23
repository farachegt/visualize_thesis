from __future__ import annotations

from dataclasses import replace
from typing import Literal

import numpy as np

from plot_core.plot_data import TimeSeriesPlotData
from plot_core.requests import TimeSeriesRequest


def build_cross_5_time_series_request(
    request: TimeSeriesRequest,
) -> TimeSeriesRequest:
    """Return a copy of a request that samples a cross-5 stencil."""
    return replace(request, point_sample_pattern="cross_5")


def build_hourly_nearest_station_plot_data(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> TimeSeriesPlotData:
    """Reduce a station series to one nearest sample per hour."""
    source_times = np.asarray(plot_data.times, dtype="datetime64[ns]")
    source_values = np.asarray(plot_data.values, dtype=float)
    if source_times.size != source_values.size:
        raise ValueError(
            "Station hourly sampling requires matching time and value sizes."
        )
    if source_times.size == 0:
        raise ValueError("Station time series is empty for this request.")

    in_window = (
        (source_times >= start_time)
        & (source_times < end_time_exclusive)
    )
    if not np.any(in_window):
        raise ValueError(
            "Station time series has no samples within the requested "
            "comparison interval."
        )

    window_times = source_times[in_window]
    window_values = source_values[in_window]
    sort_indices = np.argsort(window_times)
    window_times = window_times[sort_indices]
    window_values = window_values[sort_indices]

    hourly_times = _build_hourly_times(start_time, end_time_exclusive)
    nearest_indices = _select_nearest_time_indices(
        source_times=window_times,
        target_times=hourly_times,
    )
    hourly_values = window_values[nearest_indices]

    hourly_draw_mask = None
    if plot_data.draw_mask is not None:
        source_draw_mask = np.asarray(plot_data.draw_mask, dtype=bool)[in_window]
        source_draw_mask = source_draw_mask[sort_indices]
        hourly_draw_mask = source_draw_mask[nearest_indices]

    return TimeSeriesPlotData(
        label=plot_data.label,
        times=hourly_times,
        values=np.asarray(hourly_values, dtype=float),
        units=plot_data.units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=hourly_draw_mask,
    )


def build_hourly_last_plot_data(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> TimeSeriesPlotData:
    """Reduce a series to one last sample per hour over the window."""
    hourly_times, hourly_values, hourly_draw_mask = build_hourly_binned_time_series(
        plot_data,
        start_time=start_time,
        end_time_exclusive=end_time_exclusive,
        aggregation="last",
    )
    return TimeSeriesPlotData(
        label=plot_data.label,
        times=hourly_times,
        values=hourly_values,
        units=plot_data.units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=hourly_draw_mask,
    )


def build_monan_hourly_precipitation_rate_plot_data(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> TimeSeriesPlotData:
    """Convert MONAN accumulated precipitation to hourly `mm h^-1`."""
    hourly_times, hourly_accumulated_values, hourly_draw_mask = (
        build_hourly_binned_time_series(
            plot_data,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
            aggregation="last",
        )
    )
    hourly_rates = np.full(hourly_accumulated_values.shape, np.nan, dtype=float)
    for index in range(1, hourly_accumulated_values.size):
        current_value = hourly_accumulated_values[index]
        previous_value = hourly_accumulated_values[index - 1]
        if not np.isfinite(current_value) or not np.isfinite(previous_value):
            continue
        increment = current_value - previous_value
        if increment >= 0.0:
            hourly_rates[index] = increment

    rate_draw_mask = None
    if hourly_draw_mask is not None:
        rate_draw_mask = hourly_draw_mask.copy()
        rate_draw_mask[0] = False
        rate_draw_mask[~np.isfinite(hourly_rates)] = False

    return TimeSeriesPlotData(
        label=plot_data.label,
        times=hourly_times,
        values=hourly_rates,
        units="mm h^-1",
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=rate_draw_mask,
    )


def build_era5_hourly_precipitation_rate_plot_data(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> TimeSeriesPlotData:
    """Convert ERA5 precipitation from `m h^-1` to `mm h^-1`."""
    hourly_times, hourly_values, hourly_draw_mask = build_hourly_binned_time_series(
        plot_data,
        start_time=start_time,
        end_time_exclusive=end_time_exclusive,
        aggregation="last",
    )
    return TimeSeriesPlotData(
        label=plot_data.label,
        times=hourly_times,
        values=hourly_values * 1000.0,
        units="mm h^-1",
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=hourly_draw_mask,
    )


def build_hourly_binned_time_series(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
    aggregation: Literal["last", "mean"],
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Return one hourly value per hour over the comparison window."""
    source_times = np.asarray(plot_data.times, dtype="datetime64[ns]")
    source_values = np.asarray(plot_data.values, dtype=float)
    if source_times.size != source_values.size:
        raise ValueError(
            "Hourly binning requires matching time and value sizes."
        )
    if source_times.size == 0:
        raise ValueError("Time series is empty for hourly processing.")

    in_window = (
        (source_times >= start_time)
        & (source_times < end_time_exclusive)
    )
    if not np.any(in_window):
        raise ValueError(
            "Time series has no samples within the requested comparison "
            "interval."
        )

    window_times = source_times[in_window]
    window_values = source_values[in_window]
    sort_indices = np.argsort(window_times)
    window_times = window_times[sort_indices]
    window_values = window_values[sort_indices]
    window_hours = (
        window_times.astype("datetime64[h]").astype("datetime64[ns]")
    )

    hourly_times = _build_hourly_times(start_time, end_time_exclusive)
    hourly_values = np.full(hourly_times.shape, np.nan, dtype=float)
    for hourly_index, hourly_time in enumerate(hourly_times):
        hour_mask = window_hours == hourly_time
        if not np.any(hour_mask):
            continue
        hour_values = window_values[hour_mask]
        valid_mask = np.isfinite(hour_values)
        if not np.any(valid_mask):
            continue

        if aggregation == "last":
            hourly_values[hourly_index] = float(hour_values[valid_mask][-1])
        else:
            hourly_values[hourly_index] = float(np.nanmean(hour_values))

    hourly_draw_mask = None
    if plot_data.draw_mask is not None:
        source_draw_mask = np.asarray(plot_data.draw_mask, dtype=bool)[in_window]
        source_draw_mask = source_draw_mask[sort_indices]
        hourly_draw_mask = np.zeros(hourly_times.size, dtype=bool)
        for hourly_index, hourly_time in enumerate(hourly_times):
            hour_mask = window_hours == hourly_time
            if np.any(hour_mask):
                hourly_draw_mask[hourly_index] = bool(
                    np.any(source_draw_mask[hour_mask])
                )

    return hourly_times, hourly_values, hourly_draw_mask


def _build_hourly_times(
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> np.ndarray:
    return np.arange(
        start_time,
        end_time_exclusive,
        np.timedelta64(1, "h"),
    ).astype("datetime64[ns]")


def _select_nearest_time_indices(
    *,
    source_times: np.ndarray,
    target_times: np.ndarray,
) -> np.ndarray:
    """Return source indices nearest to each target timestamp."""
    source_int = source_times.astype("datetime64[ns]").astype(np.int64)
    target_int = target_times.astype("datetime64[ns]").astype(np.int64)
    insertion_points = np.searchsorted(source_int, target_int, side="left")
    right_indices = np.clip(insertion_points, 0, source_int.size - 1)
    left_indices = np.clip(right_indices - 1, 0, source_int.size - 1)
    left_distance = np.abs(target_int - source_int[left_indices])
    right_distance = np.abs(source_int[right_indices] - target_int)
    choose_left = left_distance <= right_distance
    return np.where(choose_left, left_indices, right_indices)
