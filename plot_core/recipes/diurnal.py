from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Sequence, Tuple, Union

import numpy as np
import xarray as xr
from matplotlib.figure import Figure

from ..adapter import DataAdapter
from ..plot_data import HorizontalFieldPlotData
from ..rendering import (
    FigureSpecification,
    RenderSpecification,
    SharedColorbarSpecification,
    SpecializedPlotter,
)
from ..requests import HorizontalFieldRequest
from .maps import (
    MapLayerInput,
    MapPanelInput,
    PreparedMapLayerInput,
    plot_map_panels,
)

BBox = Tuple[float, float, float, float]
MapLayerDefinition = Union[MapLayerInput, PreparedMapLayerInput]


@dataclass
class DiurnalAmplitudeSourceInput:
    """Describe one source field participating in a diurnal-amplitude row.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing the source field.
    variable_name:
        Canonical variable name resolved by the adapter.
    source_label:
        Human-readable label used in panel titles.
    bbox:
        Optional bounding box forwarded to the amplitude reduction request.
    vertical_selection:
        Optional vertical selection forwarded to the amplitude request.
    """

    adapter: DataAdapter
    variable_name: str
    source_label: str
    bbox: BBox | None = None
    vertical_selection: Any | None = None


@dataclass
class DiurnalAmplitudeRowInput:
    """Describe one diurnal-amplitude comparison row.

    Parameters
    ----------
    left_source:
        Source rendered in the first column.
    right_source:
        Source rendered in the second column.
    day_start:
        First instant of the daily window represented by the row.
    field_label:
        Human-readable variable label used in titles and colorbars.
    absolute_render_specification:
        Rendering specification used by both absolute-field panels. When
        `vmin` and `vmax` are not provided, one shared limit pair is
        computed from the two source fields.
    difference_render_specification:
        Rendering specification used by the difference panel. When `vmin`
        and `vmax` are not provided, symmetric limits centred on zero are
        derived from the difference field.
    day_duration:
        Temporal span used to compute the amplitude. The default is one day.
    left_panel_title:
        Optional title override for the first column.
    right_panel_title:
        Optional title override for the second column.
    difference_panel_title:
        Optional title override for the difference column.
    absolute_colorbar_label:
        Label applied to the shared absolute-field colorbar.
    difference_colorbar_label:
        Label applied to the difference colorbar.
    absolute_colorbar_kwargs:
        Extra kwargs forwarded to the shared absolute-field colorbar.
    difference_colorbar_kwargs:
        Extra kwargs forwarded to the difference colorbar.
    left_extra_layers:
        Optional extra horizontal-field layers added over the left panel.
    right_extra_layers:
        Optional extra horizontal-field layers added over the right panel.
    difference_extra_layers:
        Optional extra horizontal-field layers added over the difference
        panel.
    extent:
        Optional map extent in the order `(min_lon, max_lon, min_lat,
        max_lat)`.
    coastlines_kwargs:
        Optional kwargs forwarded to `GeoAxes.coastlines`.
    borders_kwargs:
        Optional kwargs forwarded to `GeoAxes.add_feature` for borders.
    gridlines_kwargs:
        Optional kwargs forwarded to `GeoAxes.gridlines`.
    gridliner_attrs:
        Optional base attributes applied to each `Gridliner`.
    """

    left_source: DiurnalAmplitudeSourceInput
    right_source: DiurnalAmplitudeSourceInput
    day_start: np.datetime64
    field_label: str
    absolute_render_specification: RenderSpecification
    difference_render_specification: RenderSpecification
    day_duration: np.timedelta64 = np.timedelta64(1, "D")
    left_panel_title: str | None = None
    right_panel_title: str | None = None
    difference_panel_title: str | None = None
    absolute_colorbar_label: str | None = None
    difference_colorbar_label: str | None = None
    absolute_colorbar_kwargs: dict[str, Any] = field(default_factory=dict)
    difference_colorbar_kwargs: dict[str, Any] = field(
        default_factory=dict
    )
    left_extra_layers: Sequence[MapLayerDefinition] = field(
        default_factory=tuple
    )
    right_extra_layers: Sequence[MapLayerDefinition] = field(
        default_factory=tuple
    )
    difference_extra_layers: Sequence[MapLayerDefinition] = field(
        default_factory=tuple
    )
    extent: BBox | None = None
    coastlines_kwargs: dict[str, Any] | None = field(
        default_factory=dict
    )
    borders_kwargs: dict[str, Any] | None = field(default_factory=dict)
    gridlines_kwargs: dict[str, Any] | None = None
    gridliner_attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiurnalPeakPhaseSourceInput:
    """Describe one source field participating in a diurnal peak-phase row.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing the source field.
    variable_name:
        Canonical variable name resolved by the adapter.
    source_label:
        Human-readable label used in panel titles.
    bbox:
        Optional bounding box forwarded to the daily selection.
    vertical_selection:
        Optional vertical selection forwarded to the phase request.
    """

    adapter: DataAdapter
    variable_name: str
    source_label: str
    bbox: BBox | None = None
    vertical_selection: Any | None = None


@dataclass
class DiurnalPeakPhaseRowInput:
    """Describe one diurnal peak-phase comparison row.

    Parameters
    ----------
    left_source:
        Source rendered in the first column.
    right_source:
        Source rendered in the second column.
    day_start:
        First instant of the daily window represented by the row.
    field_label:
        Human-readable variable label used in titles and colorbars.
    absolute_render_specification:
        Rendering specification used by both absolute-field panels. When
        `vmin` and `vmax` are not provided, one shared limit pair is
        computed from the two source fields.
    difference_render_specification:
        Rendering specification used by the difference panel. When `vmin`
        and `vmax` are not provided, symmetric limits centred on zero are
        derived from the difference field.
    day_duration:
        Temporal span used to compute the phase. The default is one day.
    left_panel_title:
        Optional title override for the first column.
    right_panel_title:
        Optional title override for the second column.
    difference_panel_title:
        Optional title override for the difference column.
    absolute_colorbar_label:
        Label applied to the shared absolute-field colorbar.
    difference_colorbar_label:
        Label applied to the difference colorbar.
    absolute_colorbar_kwargs:
        Extra kwargs forwarded to the shared absolute-field colorbar.
    difference_colorbar_kwargs:
        Extra kwargs forwarded to the difference colorbar.
    left_extra_layers:
        Optional extra horizontal-field layers added over the left panel.
    right_extra_layers:
        Optional extra horizontal-field layers added over the right panel.
    difference_extra_layers:
        Optional extra horizontal-field layers added over the difference
        panel.
    extent:
        Optional map extent in the order `(min_lon, max_lon, min_lat,
        max_lat)`.
    coastlines_kwargs:
        Optional kwargs forwarded to `GeoAxes.coastlines`.
    borders_kwargs:
        Optional kwargs forwarded to `GeoAxes.add_feature` for borders.
    gridlines_kwargs:
        Optional kwargs forwarded to `GeoAxes.gridlines`.
    gridliner_attrs:
        Optional base attributes applied to each `Gridliner`.
    """

    left_source: DiurnalPeakPhaseSourceInput
    right_source: DiurnalPeakPhaseSourceInput
    day_start: np.datetime64
    field_label: str
    absolute_render_specification: RenderSpecification
    difference_render_specification: RenderSpecification
    day_duration: np.timedelta64 = np.timedelta64(1, "D")
    left_panel_title: str | None = None
    right_panel_title: str | None = None
    difference_panel_title: str | None = None
    absolute_colorbar_label: str | None = None
    difference_colorbar_label: str | None = None
    absolute_colorbar_kwargs: dict[str, Any] = field(default_factory=dict)
    difference_colorbar_kwargs: dict[str, Any] = field(
        default_factory=dict
    )
    left_extra_layers: Sequence[MapLayerDefinition] = field(
        default_factory=tuple
    )
    right_extra_layers: Sequence[MapLayerDefinition] = field(
        default_factory=tuple
    )
    difference_extra_layers: Sequence[MapLayerDefinition] = field(
        default_factory=tuple
    )
    extent: BBox | None = None
    coastlines_kwargs: dict[str, Any] | None = field(
        default_factory=dict
    )
    borders_kwargs: dict[str, Any] | None = field(default_factory=dict)
    gridlines_kwargs: dict[str, Any] | None = None
    gridliner_attrs: dict[str, Any] = field(default_factory=dict)


def plot_diurnal_amplitude_rows(
    *,
    rows: Sequence[DiurnalAmplitudeRowInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build a comparison figure with left, right and delta amplitude maps.

    Parameters
    ----------
    rows:
        Ordered comparison rows. Each row produces three panels:
        left source, right source and left-minus-right difference.
    figure_specification:
        Global figure layout and metadata.
    plotter:
        Optional plotter instance. When omitted, a fresh
        `SpecializedPlotter` is created.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.

    Raises
    ------
    ValueError
        If no row is provided or if one row compares incompatible grids.
    """
    if not rows:
        raise ValueError(
            "At least one DiurnalAmplitudeRowInput is required."
        )

    comparison_panels: list[MapPanelInput] = []
    shared_colorbars: list[SharedColorbarSpecification] = list(
        figure_specification.shared_colorbar_specifications
    )
    for row_index, row_input in enumerate(rows):
        row_panels, row_colorbars = _build_diurnal_amplitude_row(
            row_input=row_input,
            row_index=row_index,
        )
        comparison_panels.extend(row_panels)
        shared_colorbars.extend(row_colorbars)

    comparison_figure_specification = replace(
        figure_specification,
        shared_colorbar_specifications=shared_colorbars,
    )
    return plot_map_panels(
        panels=comparison_panels,
        figure_specification=comparison_figure_specification,
        plotter=plotter,
    )


def plot_diurnal_cycle_amplitude_pblh(
    *,
    monan_adapter: DataAdapter,
    e3sm_adapter: DataAdapter,
    day_start: np.datetime64,
    monan_var: str = "hpbl",
    e3sm_var: str = "hpbl",
    cmap_abs: str = "turbo",
    cmap_diff: str = "RdBu_r",
    vmin: float = 0.0,
    vmax: float | None = 2500.0,
    diff_limit: float | None = 1500.0,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build the legacy daily amplitude figure using the new core.

    Parameters
    ----------
    monan_adapter:
        Adapter representing the MONAN source.
    e3sm_adapter:
        Adapter representing the E3SM source.
    day_start:
        First instant of the day represented by the figure.
    monan_var:
        Canonical variable name used by the MONAN source.
    e3sm_var:
        Canonical variable name used by the E3SM source.
    cmap_abs:
        Colormap used by the absolute fields.
    cmap_diff:
        Colormap used by the difference field.
    vmin:
        Minimum color value used by the absolute fields.
    vmax:
        Optional maximum color value used by the absolute fields. When
        omitted, one shared value is derived from the two source fields.
    diff_limit:
        Optional symmetric difference limit. When omitted, one value is
        derived from the difference field.
    plotter:
        Optional plotter instance. When omitted, a fresh
        `SpecializedPlotter` is created.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.
    """
    absolute_artist_kwargs: dict[str, Any] = {
        "cmap": cmap_abs,
        "vmin": float(vmin),
    }
    if vmax is not None:
        absolute_artist_kwargs["vmax"] = float(vmax)

    difference_artist_kwargs: dict[str, Any] = {"cmap": cmap_diff}
    if diff_limit is not None:
        difference_artist_kwargs["vmin"] = -float(diff_limit)
        difference_artist_kwargs["vmax"] = float(diff_limit)

    day_label = np.datetime_as_string(day_start, unit="D")
    return plot_diurnal_amplitude_rows(
        rows=[
            DiurnalAmplitudeRowInput(
                left_source=DiurnalAmplitudeSourceInput(
                    adapter=monan_adapter,
                    variable_name=monan_var,
                    source_label="MONAN",
                ),
                right_source=DiurnalAmplitudeSourceInput(
                    adapter=e3sm_adapter,
                    variable_name=e3sm_var,
                    source_label="E3SM",
                ),
                day_start=day_start,
                field_label="Amplitude PBLH",
                absolute_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=absolute_artist_kwargs,
                ),
                difference_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=difference_artist_kwargs,
                ),
                left_panel_title="MONAN - Diurnal Amplitude PBLH",
                right_panel_title="E3SM - Diurnal Amplitude PBLH",
                difference_panel_title=(
                    "Delta Amplitude (MONAN - E3SM)"
                ),
                absolute_colorbar_label="Amplitude PBLH",
                difference_colorbar_label="Delta Amplitude",
                absolute_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                difference_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                coastlines_kwargs={"linewidth": 0.8},
                borders_kwargs={"linewidth": 0.5},
                gridlines_kwargs={
                    "draw_labels": True,
                    "linewidth": 0.6,
                    "alpha": 0.3,
                    "x_inline": False,
                    "y_inline": False,
                },
            )
        ],
        figure_specification=FigureSpecification(
            nrows=1,
            ncols=3,
            suptitle=f"Diurnal-Cycle Amplitude of PBLH - {day_label}",
            figure_kwargs={"figsize": (18, 6), "constrained_layout": True},
        ),
        plotter=plotter,
    )


def plot_diurnal_peak_phase_rows(
    *,
    rows: Sequence[DiurnalPeakPhaseRowInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build a comparison figure with left, right and delta phase maps.

    Parameters
    ----------
    rows:
        Ordered comparison rows. Each row produces three panels:
        left source, right source and left-minus-right phase difference.
    figure_specification:
        Global figure layout and metadata.
    plotter:
        Optional plotter instance. When omitted, a fresh
        `SpecializedPlotter` is created.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.

    Raises
    ------
    ValueError
        If no row is provided or if one row compares incompatible grids.
    """
    if not rows:
        raise ValueError(
            "At least one DiurnalPeakPhaseRowInput is required."
        )

    comparison_panels: list[MapPanelInput] = []
    shared_colorbars: list[SharedColorbarSpecification] = list(
        figure_specification.shared_colorbar_specifications
    )
    for row_index, row_input in enumerate(rows):
        row_panels, row_colorbars = _build_diurnal_peak_phase_row(
            row_input=row_input,
            row_index=row_index,
        )
        comparison_panels.extend(row_panels)
        shared_colorbars.extend(row_colorbars)

    comparison_figure_specification = replace(
        figure_specification,
        shared_colorbar_specifications=shared_colorbars,
    )
    return plot_map_panels(
        panels=comparison_panels,
        figure_specification=comparison_figure_specification,
        plotter=plotter,
    )


def plot_diurnal_peak_phase_pblh(
    *,
    monan_adapter: DataAdapter,
    e3sm_adapter: DataAdapter,
    day_start: np.datetime64,
    monan_var: str = "hpbl",
    e3sm_var: str = "hpbl",
    cmap_phase: str = "twilight",
    cmap_diff: str = "RdBu_r",
    phase_vmin: float = 0.0,
    phase_vmax: float = 23.0,
    diff_limit: float = 12.0,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build the legacy daily peak-phase figure using the new core.

    Parameters
    ----------
    monan_adapter:
        Adapter representing the MONAN source.
    e3sm_adapter:
        Adapter representing the E3SM source.
    day_start:
        First instant of the day represented by the figure.
    monan_var:
        Canonical variable name used by the MONAN source.
    e3sm_var:
        Canonical variable name used by the E3SM source.
    cmap_phase:
        Colormap used by the absolute phase fields.
    cmap_diff:
        Colormap used by the difference field.
    phase_vmin:
        Minimum color value used by the absolute phase fields.
    phase_vmax:
        Maximum color value used by the absolute phase fields.
    diff_limit:
        Symmetric difference limit centred on zero.
    plotter:
        Optional plotter instance. When omitted, a fresh
        `SpecializedPlotter` is created.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.
    """
    day_label = np.datetime_as_string(day_start, unit="D")
    return plot_diurnal_peak_phase_rows(
        rows=[
            DiurnalPeakPhaseRowInput(
                left_source=DiurnalPeakPhaseSourceInput(
                    adapter=monan_adapter,
                    variable_name=monan_var,
                    source_label="MONAN",
                ),
                right_source=DiurnalPeakPhaseSourceInput(
                    adapter=e3sm_adapter,
                    variable_name=e3sm_var,
                    source_label="E3SM",
                ),
                day_start=day_start,
                field_label="Peak Hour PBLH",
                absolute_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs={
                        "cmap": cmap_phase,
                        "vmin": float(phase_vmin),
                        "vmax": float(phase_vmax),
                    },
                ),
                difference_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs={
                        "cmap": cmap_diff,
                        "vmin": -float(diff_limit),
                        "vmax": float(diff_limit),
                    },
                ),
                left_panel_title="Peak Hour MONAN",
                right_panel_title="Peak Hour E3SM",
                difference_panel_title="Phase Difference (MONAN - E3SM)",
                absolute_colorbar_label="Peak Hour (local model hour)",
                difference_colorbar_label="Phase Difference",
                absolute_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                    "ticks": np.arange(0, 24, 3),
                },
                difference_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                    "ticks": np.arange(-12, 13, 3),
                },
                coastlines_kwargs={"linewidth": 0.8},
                borders_kwargs={"linewidth": 0.5},
                gridlines_kwargs={
                    "draw_labels": True,
                    "linewidth": 0.6,
                    "alpha": 0.3,
                    "x_inline": False,
                    "y_inline": False,
                },
            )
        ],
        figure_specification=FigureSpecification(
            nrows=1,
            ncols=3,
            suptitle=f"Diurnal Peak Phase of PBLH - {day_label}",
            figure_kwargs={"figsize": (18, 6), "constrained_layout": True},
        ),
        plotter=plotter,
    )


def _build_diurnal_amplitude_row(
    *,
    row_input: DiurnalAmplitudeRowInput,
    row_index: int,
) -> tuple[list[MapPanelInput], list[SharedColorbarSpecification]]:
    """Build the three panels and colorbars associated with one row."""
    left_plot_data = _resolve_diurnal_amplitude_plot_data(
        row_input.left_source,
        row_input.day_start,
        row_input.day_duration,
    )
    right_plot_data = _resolve_diurnal_amplitude_plot_data(
        row_input.right_source,
        row_input.day_start,
        row_input.day_duration,
    )
    _validate_horizontal_field_compatibility(
        left_plot_data,
        right_plot_data,
    )
    difference_plot_data = _build_difference_plot_data(
        left_plot_data,
        right_plot_data,
        label=(
            row_input.difference_panel_title
            or f"Delta {row_input.field_label}"
        ),
    )

    absolute_render_specification = (
        _build_absolute_render_specification(
            row_input.absolute_render_specification,
            left_plot_data.field,
            right_plot_data.field,
        )
    )
    difference_render_specification = _build_difference_render_specification(
        row_input.difference_render_specification,
        difference_plot_data.field,
    )

    absolute_units_label = _format_units_label(
        row_input.absolute_colorbar_label or row_input.field_label,
        left_plot_data.units or right_plot_data.units,
    )
    difference_units_label = _format_units_label(
        (
            row_input.difference_colorbar_label
            or f"Delta {row_input.field_label}"
        ),
        difference_plot_data.units,
    )

    base_panel_index = row_index * 3
    panels = [
        _build_diurnal_map_panel(
            base_plot_data=left_plot_data,
            base_render_specification=absolute_render_specification,
            title=(
                row_input.left_panel_title
                or f"{row_input.left_source.source_label} - "
                f"{row_input.field_label}"
            ),
            extra_layers=row_input.left_extra_layers,
            row_input=row_input,
            show_left_labels=True,
        ),
        _build_diurnal_map_panel(
            base_plot_data=right_plot_data,
            base_render_specification=absolute_render_specification,
            title=(
                row_input.right_panel_title
                or f"{row_input.right_source.source_label} - "
                f"{row_input.field_label}"
            ),
            extra_layers=row_input.right_extra_layers,
            row_input=row_input,
            show_left_labels=False,
        ),
        _build_diurnal_map_panel(
            base_plot_data=difference_plot_data,
            base_render_specification=difference_render_specification,
            title=(
                row_input.difference_panel_title
                or f"Delta {row_input.field_label} = "
                f"{row_input.left_source.source_label} - "
                f"{row_input.right_source.source_label}"
            ),
            extra_layers=row_input.difference_extra_layers,
            row_input=row_input,
            show_left_labels=False,
        ),
    ]

    colorbars = [
        SharedColorbarSpecification(
            source_panel_index=base_panel_index,
            source_layer_index=0,
            target_panel_indices=[base_panel_index, base_panel_index + 1],
            label=absolute_units_label,
            colorbar_kwargs=dict(row_input.absolute_colorbar_kwargs),
        ),
        SharedColorbarSpecification(
            source_panel_index=base_panel_index + 2,
            source_layer_index=0,
            target_panel_indices=[base_panel_index + 2],
            label=difference_units_label,
            colorbar_kwargs=dict(row_input.difference_colorbar_kwargs),
        ),
    ]
    return panels, colorbars


def _build_diurnal_peak_phase_row(
    *,
    row_input: DiurnalPeakPhaseRowInput,
    row_index: int,
) -> tuple[list[MapPanelInput], list[SharedColorbarSpecification]]:
    """Build the three panels and colorbars associated with one phase row."""
    left_plot_data = _resolve_diurnal_peak_phase_plot_data(
        row_input.left_source,
        row_input.day_start,
        row_input.day_duration,
    )
    right_plot_data = _resolve_diurnal_peak_phase_plot_data(
        row_input.right_source,
        row_input.day_start,
        row_input.day_duration,
    )
    _validate_horizontal_field_compatibility(
        left_plot_data,
        right_plot_data,
    )
    difference_plot_data = _build_phase_difference_plot_data(
        left_plot_data,
        right_plot_data,
        label=(
            row_input.difference_panel_title
            or f"Delta {row_input.field_label}"
        ),
    )

    absolute_render_specification = (
        _build_absolute_render_specification(
            row_input.absolute_render_specification,
            left_plot_data.field,
            right_plot_data.field,
        )
    )
    difference_render_specification = _build_difference_render_specification(
        row_input.difference_render_specification,
        difference_plot_data.field,
    )

    absolute_units_label = _format_units_label(
        row_input.absolute_colorbar_label or row_input.field_label,
        left_plot_data.units or right_plot_data.units,
    )
    difference_units_label = _format_units_label(
        (
            row_input.difference_colorbar_label
            or f"Delta {row_input.field_label}"
        ),
        difference_plot_data.units,
    )

    base_panel_index = row_index * 3
    panels = [
        _build_diurnal_map_panel(
            base_plot_data=left_plot_data,
            base_render_specification=absolute_render_specification,
            title=(
                row_input.left_panel_title
                or f"{row_input.left_source.source_label} - "
                f"{row_input.field_label}"
            ),
            extra_layers=row_input.left_extra_layers,
            row_input=row_input,
            show_left_labels=True,
        ),
        _build_diurnal_map_panel(
            base_plot_data=right_plot_data,
            base_render_specification=absolute_render_specification,
            title=(
                row_input.right_panel_title
                or f"{row_input.right_source.source_label} - "
                f"{row_input.field_label}"
            ),
            extra_layers=row_input.right_extra_layers,
            row_input=row_input,
            show_left_labels=False,
        ),
        _build_diurnal_map_panel(
            base_plot_data=difference_plot_data,
            base_render_specification=difference_render_specification,
            title=(
                row_input.difference_panel_title
                or f"Delta {row_input.field_label} = "
                f"{row_input.left_source.source_label} - "
                f"{row_input.right_source.source_label}"
            ),
            extra_layers=row_input.difference_extra_layers,
            row_input=row_input,
            show_left_labels=False,
        ),
    ]

    colorbars = [
        SharedColorbarSpecification(
            source_panel_index=base_panel_index,
            source_layer_index=0,
            target_panel_indices=[base_panel_index, base_panel_index + 1],
            label=absolute_units_label,
            colorbar_kwargs=dict(row_input.absolute_colorbar_kwargs),
        ),
        SharedColorbarSpecification(
            source_panel_index=base_panel_index + 2,
            source_layer_index=0,
            target_panel_indices=[base_panel_index + 2],
            label=difference_units_label,
            colorbar_kwargs=dict(row_input.difference_colorbar_kwargs),
        ),
    ]
    return panels, colorbars


def _build_diurnal_map_panel(
    *,
    base_plot_data: HorizontalFieldPlotData,
    base_render_specification: RenderSpecification,
    title: str,
    extra_layers: Sequence[MapLayerDefinition],
    row_input: Union[DiurnalAmplitudeRowInput, DiurnalPeakPhaseRowInput],
    show_left_labels: bool,
) -> MapPanelInput:
    """Build one panel of a diurnal-amplitude comparison row."""
    gridliner_attrs = dict(row_input.gridliner_attrs)
    gridliner_attrs.setdefault("top_labels", False)
    gridliner_attrs.setdefault("right_labels", False)
    gridliner_attrs["left_labels"] = show_left_labels
    panel_layers: list[MapLayerDefinition] = [
        PreparedMapLayerInput(
            plot_data=base_plot_data,
            render_specification=base_render_specification,
        )
    ]
    panel_layers.extend(extra_layers)
    return MapPanelInput(
        layers=panel_layers,
        axes_set_kwargs={"title": title},
        extent=row_input.extent,
        coastlines_kwargs=_copy_optional_mapping(
            row_input.coastlines_kwargs
        ),
        borders_kwargs=_copy_optional_mapping(row_input.borders_kwargs),
        gridlines_kwargs=_copy_optional_mapping(
            row_input.gridlines_kwargs
        ),
        gridliner_attrs=gridliner_attrs,
    )


def _resolve_diurnal_amplitude_plot_data(
    source_input: DiurnalAmplitudeSourceInput,
    day_start: np.datetime64,
    day_duration: np.timedelta64,
) -> HorizontalFieldPlotData:
    """Resolve one source into a daily amplitude map field."""
    max_plot_data = source_input.adapter.to_horizontal_field_plot_data(
        variable_name=source_input.variable_name,
        request=_build_diurnal_horizontal_request(
            day_start=day_start,
            day_duration=day_duration,
            time_reduce="max",
            bbox=source_input.bbox,
            vertical_selection=source_input.vertical_selection,
        ),
    )
    min_plot_data = source_input.adapter.to_horizontal_field_plot_data(
        variable_name=source_input.variable_name,
        request=_build_diurnal_horizontal_request(
            day_start=day_start,
            day_duration=day_duration,
            time_reduce="min",
            bbox=source_input.bbox,
            vertical_selection=source_input.vertical_selection,
        ),
    )
    _validate_horizontal_field_compatibility(
        max_plot_data,
        min_plot_data,
    )
    return HorizontalFieldPlotData(
        label=source_input.source_label,
        field=max_plot_data.field - min_plot_data.field,
        longitude=np.asarray(max_plot_data.longitude),
        latitude=np.asarray(max_plot_data.latitude),
        units=_resolve_difference_units(
            max_plot_data.units,
            min_plot_data.units,
        ),
        time_label=np.datetime_as_string(day_start, unit="D"),
        vertical_label=(
            max_plot_data.vertical_label or min_plot_data.vertical_label
        ),
    )


def _resolve_diurnal_peak_phase_plot_data(
    source_input: DiurnalPeakPhaseSourceInput,
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


def _resolve_diurnal_peak_phase_field(
    source_input: DiurnalPeakPhaseSourceInput,
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


def _build_phase_difference_plot_data(
    left_plot_data: HorizontalFieldPlotData,
    right_plot_data: HorizontalFieldPlotData,
    *,
    label: str,
) -> HorizontalFieldPlotData:
    """Build the wrapped phase difference field used in comparison panels."""
    _validate_horizontal_field_compatibility(
        left_plot_data,
        right_plot_data,
    )
    difference_field = (
        (
            left_plot_data.field
            - right_plot_data.field
            + 12.0
        )
        % 24.0
    ) - 12.0
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


def _build_absolute_render_specification(
    render_specification: RenderSpecification,
    left_field: np.ndarray,
    right_field: np.ndarray,
) -> RenderSpecification:
    """Return one absolute-field render specification shared by both sides."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    if "vmin" not in artist_kwargs or "vmax" not in artist_kwargs:
        shared_vmin, shared_vmax = _compute_shared_field_limits(
            [left_field, right_field]
        )
        artist_kwargs.setdefault("vmin", shared_vmin)
        artist_kwargs.setdefault("vmax", shared_vmax)

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=_copy_artist_calls(render_specification.artist_calls),
    )


def _build_difference_render_specification(
    render_specification: RenderSpecification,
    difference_field: np.ndarray,
) -> RenderSpecification:
    """Return one render specification for the difference field."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    if "vmin" not in artist_kwargs and "vmax" not in artist_kwargs:
        diff_limit = _compute_difference_limit(difference_field)
        artist_kwargs["vmin"] = -diff_limit
        artist_kwargs["vmax"] = diff_limit
    elif "vmin" not in artist_kwargs:
        artist_kwargs["vmin"] = -abs(float(artist_kwargs["vmax"]))
    elif "vmax" not in artist_kwargs:
        artist_kwargs["vmax"] = abs(float(artist_kwargs["vmin"]))

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=_copy_artist_calls(render_specification.artist_calls),
    )


def _compute_shared_field_limits(
    fields: Sequence[np.ndarray],
) -> tuple[float, float]:
    """Return shared finite limits for absolute fields."""
    valid_values = [
        np.asarray(field, dtype=float)[np.isfinite(field)]
        for field in fields
    ]
    valid_values = [values for values in valid_values if values.size > 0]
    if not valid_values:
        return 0.0, 1.0

    shared_vmin = min(float(np.nanmin(values)) for values in valid_values)
    shared_vmax = max(float(np.nanmax(values)) for values in valid_values)
    if shared_vmin == shared_vmax:
        shared_vmax = shared_vmin + 1.0

    return shared_vmin, shared_vmax


def _compute_difference_limit(
    difference_field: np.ndarray,
) -> float:
    """Return one finite symmetric limit for a difference field."""
    values = np.asarray(difference_field, dtype=float)
    valid_values = values[np.isfinite(values)]
    if valid_values.size == 0:
        return 1.0

    diff_limit = float(np.nanmax(np.abs(valid_values)))
    if diff_limit == 0.0:
        return 1.0

    return diff_limit


def _build_difference_plot_data(
    left_plot_data: HorizontalFieldPlotData,
    right_plot_data: HorizontalFieldPlotData,
    *,
    label: str,
) -> HorizontalFieldPlotData:
    """Build the left-minus-right field used in comparison panels."""
    _validate_horizontal_field_compatibility(
        left_plot_data,
        right_plot_data,
    )
    return HorizontalFieldPlotData(
        label=label,
        field=left_plot_data.field - right_plot_data.field,
        longitude=np.asarray(left_plot_data.longitude),
        latitude=np.asarray(left_plot_data.latitude),
        units=_resolve_difference_units(
            left_plot_data.units,
            right_plot_data.units,
        ),
        time_label=left_plot_data.time_label or right_plot_data.time_label,
        vertical_label=(
            left_plot_data.vertical_label or right_plot_data.vertical_label
        ),
    )


def _resolve_difference_units(
    left_units: str | None,
    right_units: str | None,
) -> str | None:
    """Return the units used by a difference field."""
    if left_units == right_units:
        return left_units
    return left_units or right_units


def _format_units_label(
    label: str,
    units: str | None,
) -> str:
    """Return a label optionally enriched with physical units."""
    if units is None or units == "":
        return label

    return f"{label} [{units}]"


def _validate_horizontal_field_compatibility(
    left_plot_data: HorizontalFieldPlotData,
    right_plot_data: HorizontalFieldPlotData,
) -> None:
    """Validate that two map fields share the same grid geometry."""
    if left_plot_data.field.shape != right_plot_data.field.shape:
        raise ValueError(
            "Diurnal map comparison requires both fields to share the same "
            "shape."
        )

    if not np.allclose(
        np.asarray(left_plot_data.latitude, dtype=float),
        np.asarray(right_plot_data.latitude, dtype=float),
        equal_nan=True,
    ):
        raise ValueError(
            "Diurnal map comparison requires matching latitude values."
        )

    if not np.allclose(
        np.asarray(left_plot_data.longitude, dtype=float),
        np.asarray(right_plot_data.longitude, dtype=float),
        equal_nan=True,
    ):
        raise ValueError(
            "Diurnal map comparison requires matching longitude values."
        )


def _copy_artist_calls(
    artist_calls: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a defensive copy of artist method calls."""
    return [dict(call) for call in artist_calls]


def _copy_optional_mapping(
    mapping: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Copy optional dictionaries used by panel configuration."""
    if mapping is None:
        return None

    return dict(mapping)
