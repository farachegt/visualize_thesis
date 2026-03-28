from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from matplotlib.figure import Figure

from ...plot_data import HorizontalFieldPlotData
from ...rendering import RenderSpecification


def apply_comparison_matrix_labels(
    *,
    figure: Figure,
    row_labels: Sequence[str],
    column_headers: Sequence[str],
) -> None:
    """Replace per-panel titles with figure-level matrix headers and labels."""
    row_count = len(row_labels)
    panel_count = row_count * 3
    panel_axes = figure.axes[:panel_count]
    if len(panel_axes) < panel_count:
        return

    figure.canvas.draw()

    for axis in panel_axes:
        axis.set_title("")

    suptitle = getattr(figure, "_suptitle", None)
    suptitle_y = 0.99
    if suptitle is not None:
        suptitle.set_y(suptitle_y)
        suptitle_y = suptitle.get_position()[1]

    top_row_axes = panel_axes[:3]
    header_y = max(axis.get_position().y1 for axis in top_row_axes) + 0.003
    header_y = min(header_y, suptitle_y - 0.04)
    for header, axis in zip(column_headers, top_row_axes):
        position = axis.get_position()
        header_x = 0.5 * (position.x0 + position.x1)
        figure.text(
            header_x,
            header_y,
            header,
            ha="center",
            va="bottom",
            fontsize=14,
        )

    left_column_x0 = min(axis.get_position().x0 for axis in panel_axes[::3])
    for row_index, row_label in enumerate(row_labels):
        row_axis = panel_axes[row_index * 3]
        position = row_axis.get_position()
        label_y = 0.5 * (position.y0 + position.y1)
        label_x = max(left_column_x0 - 0.105, 0.005)
        figure.text(
            label_x,
            label_y,
            row_label,
            ha="right",
            va="center",
            rotation=90,
            fontsize=13,
        )


def build_absolute_render_specification(
    render_specification: RenderSpecification,
    left_field: np.ndarray,
    right_field: np.ndarray,
) -> RenderSpecification:
    """Return one absolute-field render specification shared by both sides."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    if "vmin" not in artist_kwargs or "vmax" not in artist_kwargs:
        shared_vmin, shared_vmax = compute_shared_field_limits(
            [left_field, right_field]
        )
        artist_kwargs.setdefault("vmin", shared_vmin)
        artist_kwargs.setdefault("vmax", shared_vmax)

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=copy_artist_calls(render_specification.artist_calls),
    )


def build_difference_render_specification(
    render_specification: RenderSpecification,
    difference_field: np.ndarray,
) -> RenderSpecification:
    """Return one render specification for the difference field."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    if "vmin" not in artist_kwargs and "vmax" not in artist_kwargs:
        diff_limit = compute_difference_limit(difference_field)
        artist_kwargs["vmin"] = -diff_limit
        artist_kwargs["vmax"] = diff_limit
    elif "vmin" not in artist_kwargs:
        artist_kwargs["vmin"] = -abs(float(artist_kwargs["vmax"]))
    elif "vmax" not in artist_kwargs:
        artist_kwargs["vmax"] = abs(float(artist_kwargs["vmin"]))

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=copy_artist_calls(render_specification.artist_calls),
    )


def compute_shared_field_limits(
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


def compute_difference_limit(
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


def build_difference_plot_data(
    left_plot_data: HorizontalFieldPlotData,
    right_plot_data: HorizontalFieldPlotData,
    *,
    label: str,
) -> HorizontalFieldPlotData:
    """Build the left-minus-right field used in comparison panels."""
    validate_horizontal_field_compatibility(
        left_plot_data,
        right_plot_data,
    )
    return HorizontalFieldPlotData(
        label=label,
        field=left_plot_data.field - right_plot_data.field,
        longitude=np.asarray(left_plot_data.longitude),
        latitude=np.asarray(left_plot_data.latitude),
        units=resolve_difference_units(
            left_plot_data.units,
            right_plot_data.units,
        ),
        time_label=left_plot_data.time_label or right_plot_data.time_label,
        vertical_label=(
            left_plot_data.vertical_label or right_plot_data.vertical_label
        ),
    )


def resolve_difference_units(
    left_units: str | None,
    right_units: str | None,
) -> str | None:
    """Return the units used by a difference field."""
    if left_units == right_units:
        return left_units

    return left_units or right_units


def format_units_label(
    label: str,
    units: str | None,
) -> str:
    """Return a label optionally enriched with physical units."""
    if units is None or units == "":
        return label

    return f"{label} [{units}]"


def validate_horizontal_field_compatibility(
    left_plot_data: HorizontalFieldPlotData,
    right_plot_data: HorizontalFieldPlotData,
) -> None:
    """Validate that two map fields share the same grid geometry."""
    if left_plot_data.field.shape != right_plot_data.field.shape:
        raise ValueError(
            "Map comparison requires both fields to share the same shape."
        )

    if not np.allclose(
        np.asarray(left_plot_data.latitude, dtype=float),
        np.asarray(right_plot_data.latitude, dtype=float),
        equal_nan=True,
    ):
        raise ValueError(
            "Map comparison requires matching latitude coordinates."
        )

    if not np.allclose(
        np.asarray(left_plot_data.longitude, dtype=float),
        np.asarray(right_plot_data.longitude, dtype=float),
        equal_nan=True,
    ):
        raise ValueError(
            "Map comparison requires matching longitude coordinates."
        )


def copy_artist_calls(
    artist_calls: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a defensive copy of artist method calls."""
    return [dict(call) for call in artist_calls]

