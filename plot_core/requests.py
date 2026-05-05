from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Tuple

import numpy as np

VerticalAxis = Literal["pressure", "height"]
TimeReduce = Literal["mean", "sum", "min", "max"]
PointSamplePattern = Literal["nearest", "cross_5"]
BBox = Tuple[float, float, float, float]


@dataclass
class BaseRequest:
    """Base request shared by all plot-data preparation flows.

    Parameters
    ----------
    times:
        Time selector used by the request. Its semantics depend on the target
        product:

        - for products that do not keep time as an explicit axis, such as
          `VerticalProfileRequest`, `HorizontalFieldRequest` and
          `VerticalCrossSectionRequest`, `times` must contain a single instant
          when `time_reduce` is not defined;
        - for products that keep time as an explicit axis, such as
          `TimeSeriesRequest` and `TimeVerticalSectionRequest`, `times` may be
          provided as the bounds of a continuous interval, for example
          `[start_time, end_time]`.
    time_reduce:
        Optional temporal reducer applied through the xarray methods `mean`,
        `sum`, `min` or `max`.
    """

    times: np.ndarray
    time_reduce: TimeReduce | None = None


@dataclass
class VerticalProfileRequest(BaseRequest):
    vertical_axis: VerticalAxis = "pressure"
    point_lat: float | None = None
    point_lon: float | None = None
    point_sample_pattern: PointSamplePattern = "nearest"


@dataclass
class HorizontalFieldRequest(BaseRequest):
    bbox: BBox | None = None
    vertical_selection: Any | None = None


@dataclass
class VerticalCrossSectionRequest(BaseRequest):
    start_lat: float = 0.0
    start_lon: float = 0.0
    end_lat: float = 0.0
    end_lon: float = 0.0
    vertical_axis: VerticalAxis = "pressure"
    n_points: int | None = None
    spacing_km: float | None = None


@dataclass
class TimeSeriesRequest(BaseRequest):
    """Request used to build a `TimeSeriesPlotData`.

    Parameters
    ----------
    point_lat:
        Latitude used for point extraction in gridded sources.
    point_lon:
        Longitude used for point extraction in gridded sources.
    bbox:
        Optional bounding box used for regional averaging in gridded
        sources. Its order is `(min_lon, max_lon, min_lat, max_lat)`.
    vertical_selection:
        Optional single vertical level to be selected before building the
        series.
    time_frequency:
        Optional xarray-compatible resampling frequency.
    point_sample_pattern:
        Point sampling strategy for gridded point extraction. `nearest`
        returns the closest grid point. `cross_5` returns the closest grid
        point plus its north, south, east and west neighbours.

    Notes
    -----
    In the MVP, `times` is interpreted as a continuous temporal interval for
    time-series outputs. Passing only the first and last instants is enough to
    request the full series within that range.
    """

    point_lat: float | None = None
    point_lon: float | None = None
    bbox: BBox | None = None
    vertical_selection: Any | None = None
    time_frequency: str | None = None
    point_sample_pattern: PointSamplePattern = "nearest"


@dataclass
class TimeVerticalSectionRequest(BaseRequest):
    """Request used to build a `TimeVerticalSectionPlotData`.

    Notes
    -----
    In the MVP, `times` is interpreted as the temporal span of the section.
    Passing the first and last instants is enough to request the full section
    within that range.
    """

    vertical_axis: VerticalAxis = "pressure"
    bbox: BBox | None = None
    time_frequency: str | None = None
