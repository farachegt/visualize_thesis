from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

VerticalAxis = Literal["pressure", "height"]


@dataclass
class VerticalProfilePlotData:
    label: str
    values: np.ndarray
    vertical_values: np.ndarray
    vertical_axis: VerticalAxis
    units: str | None = None
    auxiliary_vertical_values: np.ndarray | None = None
    draw_mask: np.ndarray | None = None


@dataclass
class HorizontalFieldPlotData:
    label: str
    field: np.ndarray
    longitude: np.ndarray
    latitude: np.ndarray
    units: str | None = None
    time_label: str | None = None
    vertical_label: str | None = None
    draw_mask: np.ndarray | None = None


@dataclass
class VerticalCrossSectionPlotData:
    label: str
    field: np.ndarray
    transect_values: np.ndarray
    transect_label: str
    vertical_values: np.ndarray
    vertical_axis: VerticalAxis
    units: str | None = None
    auxiliary_vertical_values: np.ndarray | None = None
    draw_mask: np.ndarray | None = None
    transect_latitude: np.ndarray | None = None
    transect_longitude: np.ndarray | None = None
    start_label: str | None = None
    end_label: str | None = None


@dataclass
class TimeSeriesPlotData:
    label: str
    times: np.ndarray
    values: np.ndarray
    units: str | None = None
    site_label: str | None = None
    vertical_label: str | None = None
    draw_mask: np.ndarray | None = None


@dataclass
class TimeVerticalSectionPlotData:
    label: str
    field: np.ndarray
    times: np.ndarray
    vertical_values: np.ndarray
    vertical_axis: VerticalAxis
    units: str | None = None
    auxiliary_vertical_values: np.ndarray | None = None
    region_label: str | None = None
    draw_mask: np.ndarray | None = None
