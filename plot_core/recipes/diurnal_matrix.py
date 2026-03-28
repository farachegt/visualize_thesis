from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Sequence, Tuple, Union

import numpy as np
from matplotlib.figure import Figure

from ..plot_data import HorizontalFieldPlotData
from ..rendering import (
    FigureSpecification,
    RenderSpecification,
    SharedColorbarSpecification,
    SpecializedPlotter,
)
from ._shared.comparison_matrix import (
    apply_comparison_matrix_labels,
    build_absolute_render_specification,
    build_difference_plot_data,
    build_difference_render_specification,
    format_units_label,
    validate_horizontal_field_compatibility,
)
from ._shared.diurnal_reductions import (
    DiurnalSourceInput,
    resolve_diurnal_amplitude_plot_data,
)
from .maps import (
    MapLayerInput,
    MapPanelInput,
    PreparedMapLayerInput,
    plot_map_panels,
)

BBox = Tuple[float, float, float, float]
MapLayerDefinition = Union[MapLayerInput, PreparedMapLayerInput]
DEFAULT_COLUMN_HEADERS = (
    "MONAN",
    "E3SM",
    "Delta (MONAN - E3SM)",
)


@dataclass
class DiurnalAmplitudeMatrixSourceInput(DiurnalSourceInput):
    """Describe one source field participating in a matrix-amplitude row."""

    pass


@dataclass
class DiurnalAmplitudeMatrixRowInput:
    """Describe one diurnal-amplitude comparison row in a matrix figure."""

    left_source: DiurnalAmplitudeMatrixSourceInput
    right_source: DiurnalAmplitudeMatrixSourceInput
    day_start: np.datetime64
    field_label: str
    absolute_render_specification: RenderSpecification
    difference_render_specification: RenderSpecification
    day_duration: np.timedelta64 = np.timedelta64(1, "D")
    row_label: str | None = None
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


def plot_diurnal_amplitude_matrix_rows(
    *,
    rows: Sequence[DiurnalAmplitudeMatrixRowInput],
    figure_specification: FigureSpecification,
    column_headers: Sequence[str] = DEFAULT_COLUMN_HEADERS,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build a matrix figure with left, right and delta amplitude maps."""
    if not rows:
        raise ValueError(
            "At least one DiurnalAmplitudeMatrixRowInput is required."
        )

    if len(column_headers) != 3:
        raise ValueError(
            "Diurnal amplitude matrix requires exactly three "
            "column headers."
        )

    comparison_panels: list[MapPanelInput] = []
    shared_colorbars: list[SharedColorbarSpecification] = list(
        figure_specification.shared_colorbar_specifications
    )
    row_labels: list[str] = []
    for row_index, row_input in enumerate(rows):
        row_panels, row_colorbars = _build_diurnal_amplitude_matrix_row(
            row_input=row_input,
            row_index=row_index,
        )
        comparison_panels.extend(row_panels)
        shared_colorbars.extend(row_colorbars)
        row_labels.append(row_input.row_label or row_input.field_label)

    comparison_figure_specification = replace(
        figure_specification,
        shared_colorbar_specifications=shared_colorbars,
    )
    figure = plot_map_panels(
        panels=comparison_panels,
        figure_specification=comparison_figure_specification,
        plotter=plotter,
    )
    apply_comparison_matrix_labels(
        figure=figure,
        row_labels=row_labels,
        column_headers=column_headers,
    )
    return figure


def _build_diurnal_amplitude_matrix_row(
    *,
    row_input: DiurnalAmplitudeMatrixRowInput,
    row_index: int,
) -> tuple[list[MapPanelInput], list[SharedColorbarSpecification]]:
    """Build the three panels and colorbars associated with one row."""
    left_plot_data = resolve_diurnal_amplitude_plot_data(
        row_input.left_source,
        row_input.day_start,
        row_input.day_duration,
    )
    right_plot_data = resolve_diurnal_amplitude_plot_data(
        row_input.right_source,
        row_input.day_start,
        row_input.day_duration,
    )
    validate_horizontal_field_compatibility(
        left_plot_data,
        right_plot_data,
    )
    difference_plot_data = build_difference_plot_data(
        left_plot_data,
        right_plot_data,
        label=(
            row_input.difference_panel_title
            or f"Delta {row_input.field_label}"
        ),
    )

    absolute_render_specification = build_absolute_render_specification(
        row_input.absolute_render_specification,
        left_plot_data.field,
        right_plot_data.field,
    )
    difference_render_specification = (
        build_difference_render_specification(
            row_input.difference_render_specification,
            difference_plot_data.field,
        )
    )

    absolute_units_label = format_units_label(
        row_input.absolute_colorbar_label or row_input.field_label,
        left_plot_data.units or right_plot_data.units,
    )
    difference_units_label = format_units_label(
        (
            row_input.difference_colorbar_label
            or f"Delta {row_input.field_label}"
        ),
        difference_plot_data.units,
    )

    base_panel_index = row_index * 3
    panels = [
        _build_diurnal_amplitude_matrix_panel(
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
        _build_diurnal_amplitude_matrix_panel(
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
        _build_diurnal_amplitude_matrix_panel(
            base_plot_data=difference_plot_data,
            base_render_specification=difference_render_specification,
            title=(
                row_input.difference_panel_title
                or f"Delta {row_input.field_label} ("
                f"{row_input.left_source.source_label} - "
                f"{row_input.right_source.source_label})"
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


def _build_diurnal_amplitude_matrix_panel(
    *,
    base_plot_data: HorizontalFieldPlotData,
    base_render_specification: RenderSpecification,
    title: str,
    extra_layers: Sequence[MapLayerDefinition],
    row_input: DiurnalAmplitudeMatrixRowInput,
    show_left_labels: bool,
) -> MapPanelInput:
    """Build one panel of a diurnal-amplitude matrix row."""
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


def _copy_optional_mapping(
    mapping: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Copy optional dictionaries used by panel configuration."""
    if mapping is None:
        return None

    return dict(mapping)
