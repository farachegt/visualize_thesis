from __future__ import annotations

import numpy as np

from plot_core.adapter import DataAdapter
from plot_core.requests import (
    HorizontalFieldRequest,
    TimeSeriesRequest,
    VerticalProfileRequest,
)


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
