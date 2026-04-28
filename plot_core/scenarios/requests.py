from __future__ import annotations

import numpy as np

from plot_core.adapter import DataAdapter
from plot_core.requests import (
    HorizontalFieldRequest,
    TimeSeriesRequest,
    VerticalProfileRequest,
)

LEGACY_CHILE_COAST_LATITUDE = -26.0
LEGACY_CHILE_COAST_LONGITUDE = -73.0
LEGACY_CHILE_COAST_TIME = np.datetime64("2014-09-03T00:00:00")
TIME_SERIES_COMPARISON_INIT_DATE = np.datetime64("2014-10-02T00:00:00")
TIME_SERIES_COMPARISON_DURATION_DAYS = 5
TIME_SERIES_COMPARISON_POINT_LAT = -3.21297
TIME_SERIES_COMPARISON_POINT_LON = -60.5981


def build_model_single_time_request(adapter: DataAdapter) -> np.ndarray:
    """Return the first model time as a one-item datetime64 array.

    Parameters
    ----------
    adapter:
        Model adapter already configured for the gridded test file.

    Returns
    -------
    np.ndarray
        One-item `datetime64[ns]` array with the first time in the file.
    """
    dataset = adapter.open_data()
    return np.asarray([dataset["Time"].values[0]], dtype="datetime64[ns]")


def build_ceilometro_time_series_request(
    adapter: DataAdapter,
) -> TimeSeriesRequest:
    """Build a full-range time-series request for the ceilometer fixture.

    Parameters
    ----------
    adapter:
        Fixed-point adapter configured for the ceilometer CSV fixture.

    Returns
    -------
    TimeSeriesRequest
        Request spanning the entire time coverage of the fixture.
    """
    dataset = adapter.open_data()
    times = np.asarray(
        [
            dataset["datetime"].values.min(),
            dataset["datetime"].values.max(),
        ],
        dtype="datetime64[ns]",
    )
    return TimeSeriesRequest(times=times)


def build_model_horizontal_field_request(
    adapter: DataAdapter,
) -> HorizontalFieldRequest:
    """Build a simple horizontal-field request for the model fixture.

    Parameters
    ----------
    adapter:
        Gridded adapter configured for the model NetCDF fixture.

    Returns
    -------
    HorizontalFieldRequest
        Request for the first available time and first model level.
    """
    dataset = adapter.open_data()
    return HorizontalFieldRequest(
        times=build_model_single_time_request(adapter),
        vertical_selection=float(dataset["level"].values[0]),
    )


def build_model_vertical_profile_request(
    adapter: DataAdapter,
) -> VerticalProfileRequest:
    """Build a central-point vertical-profile request for the model fixture.

    Parameters
    ----------
    adapter:
        Gridded adapter configured for the model NetCDF fixture.

    Returns
    -------
    VerticalProfileRequest
        Request using the central horizontal point and the first model time.
    """
    dataset = adapter.open_data()
    latitudes = dataset["latitude"].values
    longitudes = dataset["longitude"].values
    center_latitude = float(latitudes[len(latitudes) // 2])
    center_longitude = float(longitudes[len(longitudes) // 2])
    return VerticalProfileRequest(
        times=build_model_single_time_request(adapter),
        vertical_axis="pressure",
        point_lat=center_latitude,
        point_lon=center_longitude,
    )


def build_radiosonde_vertical_profile_request() -> VerticalProfileRequest:
    """Build the default radiosonde vertical-profile request.

    Returns
    -------
    VerticalProfileRequest
        Request aligned with the test radiosonde file semantics.
    """
    return VerticalProfileRequest(
        times=np.asarray(["2014-02-24T00:00:00"], dtype="datetime64[ns]"),
        vertical_axis="pressure",
    )


def build_legacy_chile_coast_vertical_profile_request(
    *,
    time_value: np.datetime64 = LEGACY_CHILE_COAST_TIME,
) -> VerticalProfileRequest:
    """Build the legacy MONAN profile request over the Chilean coast.

    The selected point is approximately offshore from northern Chile at
    `26°S, 73°W`. The longitude is expressed as `-73.0`, matching the
    `-180..180` convention used by the legacy MONAN and E3SM subsets.

    Parameters
    ----------
    time_value:
        Requested time for the vertical profile. The default mirrors the
        first time used by the legacy main loop.

    Returns
    -------
    VerticalProfileRequest
        Request compatible with the old SHOC vs MYNN profile comparison.
    """
    return VerticalProfileRequest(
        times=np.asarray([time_value], dtype="datetime64[ns]"),
        vertical_axis="pressure",
        point_lat=LEGACY_CHILE_COAST_LATITUDE,
        point_lon=LEGACY_CHILE_COAST_LONGITUDE,
    )


def build_time_series_comparison_gridded_request(
    *,
    init_date: np.datetime64 = TIME_SERIES_COMPARISON_INIT_DATE,
) -> TimeSeriesRequest:
    """Build the 5-day gridded request at the canonical station point."""
    return TimeSeriesRequest(
        times=_build_time_series_comparison_times(init_date),
        point_lat=TIME_SERIES_COMPARISON_POINT_LAT,
        point_lon=TIME_SERIES_COMPARISON_POINT_LON,
    )


def build_time_series_comparison_station_request(
    *,
    init_date: np.datetime64 = TIME_SERIES_COMPARISON_INIT_DATE,
) -> TimeSeriesRequest:
    """Build the 5-day fixed-point station request."""
    return TimeSeriesRequest(
        times=_build_time_series_comparison_times(init_date),
    )


def _build_time_series_comparison_times(
    init_date: np.datetime64,
) -> np.ndarray:
    """Return the standard 5-day comparison interval as `datetime64[ns]`."""
    start_time = np.datetime64(init_date, "ns")
    end_time_exclusive = start_time + np.timedelta64(
        TIME_SERIES_COMPARISON_DURATION_DAYS,
        "D",
    )
    end_time_inclusive = end_time_exclusive - np.timedelta64(1, "ns")
    return np.asarray(
        [start_time, end_time_inclusive],
        dtype="datetime64[ns]",
    )
