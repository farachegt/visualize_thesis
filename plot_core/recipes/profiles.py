from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from matplotlib.figure import Figure

from ..adapter import DataAdapter
from ..rendering import (
    PlotLayer,
    PlotPanel,
    FigureSpecification,
    RenderSpecification,
    SpecializedPlotter,
)
from ..requests import TimeReduce, VerticalProfileRequest


@dataclass
class VerticalProfileLayerInput:
    """Describe one vertical-profile layer requested by a recipe.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing the profile data.
    request:
        Vertical profile request for this source.
    variable_name:
        Canonical variable name to be resolved by the adapter.
    render_specification:
        Rendering instructions used to convert the profile into a matplotlib
        artist.
    legend_label:
        Optional legend label injected into the rendering kwargs when one is
        not already defined there.
    """

    adapter: DataAdapter
    request: VerticalProfileRequest
    variable_name: str
    render_specification: RenderSpecification
    legend_label: str | None = None


@dataclass
class VerticalProfileSourceInput:
    """Describe one source used by `plot_vertical_profiles_panel_at_point`.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing profile data for this source.
    variable_names:
        Canonical variables, one per output panel.
    legend_label:
        Optional source label injected into the line rendering.
    render_specification:
        Optional source-wide rendering. When omitted, the wrapper uses a
        default line style that varies by source index.
    """

    adapter: DataAdapter
    variable_names: Sequence[str]
    legend_label: str | None = None
    render_specification: RenderSpecification | None = None


@dataclass
class PanelInput:
    """Describe one vertical-profile subplot to be built by the recipe.

    Parameters
    ----------
    layers:
        Ordered vertical-profile layers that will be composed in the same
        subplot.
    axes_set_kwargs:
        Keyword arguments forwarded to `Axes.set`.
    grid_kwargs:
        Optional grid configuration forwarded to `Axes.grid`.
    legend_kwargs:
        Optional legend configuration forwarded to `Axes.legend`.
    axes_calls:
        Ordered list of extra `Axes` method calls applied after the layers
        are drawn.
    """

    layers: Sequence[VerticalProfileLayerInput]
    axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    grid_kwargs: dict[str, Any] | None = None
    legend_kwargs: dict[str, Any] | None = None
    axes_calls: list[dict[str, Any]] = field(default_factory=list)


def plot_vertical_profiles_panel(
    *,
    panels: Sequence[PanelInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build and render a figure composed of vertical-profile subplots.

    Parameters
    ----------
    panels:
        Ordered panel inputs. Each panel is converted into a `PlotPanel`
        after its layer inputs are resolved by the corresponding adapters.
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
        If no panel is provided, if a panel has no layers, or if the layers
        in the same panel do not share the same vertical axis semantics.
    """
    if not panels:
        raise ValueError("At least one PanelInput is required.")

    resolved_panels = [
        _build_plot_panel(panel_input)
        for panel_input in panels
    ]
    recipe_plotter = plotter or SpecializedPlotter()
    return recipe_plotter.plot(
        panels=resolved_panels,
        figure_specification=figure_specification,
    )


def plot_vertical_profiles_panel_at_point(
    *,
    sources: Sequence[VerticalProfileSourceInput],
    point_lat: float,
    point_lon: float,
    time: np.datetime64 | Sequence[np.datetime64],
    panel_labels: Sequence[str],
    x_units: Sequence[str],
    vertical_axis: str = "pressure",
    vertical_axis_label: str | None = None,
    time_reduce: TimeReduce | None = None,
    panel_extra_layers: Sequence[
        Sequence[VerticalProfileLayerInput]
    ] | None = None,
    figure_specification: FigureSpecification | None = None,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build the legacy point-profile panel using the new core.

    Parameters
    ----------
    sources:
        Ordered list of sources. Each source contributes one layer to every
        panel, and may define its own source-wide line style.
    point_lat:
        Latitude of the requested point.
    point_lon:
        Longitude of the requested point.
    time:
        One instant or a non-empty sequence of instants. When a sequence with
        more than one instant is provided and `time_reduce` is omitted, the
        wrapper uses `mean` to preserve the common legacy intent.
    panel_labels:
        Human-readable labels, one per panel.
    x_units:
        X-axis units, one per panel. Empty strings are allowed.
    vertical_axis:
        Semantic vertical axis used by the request.
    vertical_axis_label:
        Optional y-axis label used by the generated profile panels. When
        omitted, the wrapper uses a generic label derived from
        `vertical_axis`.
    time_reduce:
        Optional temporal reducer applied when `time` contains multiple
        instants.
    panel_extra_layers:
        Optional additional profile layers appended panel by panel after the
        source layers. This is the main extension point for adding compatible
        extra curves without changing the recipe signature.
    figure_specification:
        Optional global figure specification. When omitted, a legacy-like
        layout is created automatically.
    plotter:
        Optional plotter instance. When omitted, a fresh
        `SpecializedPlotter` is created.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.
    """
    if not sources:
        raise ValueError(
            "At least one VerticalProfileSourceInput is required."
        )

    panel_count = len(panel_labels)
    if panel_count == 0 or len(x_units) != panel_count:
        raise ValueError(
            "panel_labels and x_units must have the same non-zero length."
        )

    for source in sources:
        if len(source.variable_names) != panel_count:
            raise ValueError(
                "Each source must provide one variable per output panel."
            )

    normalized_times = _normalize_profile_times(time)
    effective_time_reduce = _resolve_profile_time_reduce(
        normalized_times,
        time_reduce,
    )
    shared_request = VerticalProfileRequest(
        times=normalized_times,
        time_reduce=effective_time_reduce,
        vertical_axis=vertical_axis,
        point_lat=float(point_lat),
        point_lon=float(point_lon),
    )
    resolved_panel_extra_layers = _normalize_panel_extra_layers(
        panel_extra_layers,
        panel_count,
    )
    final_figure_specification = figure_specification or (
        _build_default_profile_point_figure_specification(
            panel_count=panel_count,
            point_lat=point_lat,
            point_lon=point_lon,
            times=normalized_times,
            time_reduce=effective_time_reduce,
        )
    )
    panels: list[PanelInput] = []
    for panel_index, panel_label in enumerate(panel_labels):
        panel_layers = [
            VerticalProfileLayerInput(
                adapter=source.adapter,
                request=shared_request,
                variable_name=source.variable_names[panel_index],
                render_specification=(
                    source.render_specification
                    or _build_default_source_render_specification(
                        source_index
                    )
                ),
                legend_label=(
                    source.legend_label
                    or source.adapter.source_specification.label
                ),
            )
            for source_index, source in enumerate(sources)
        ]
        panel_layers.extend(resolved_panel_extra_layers[panel_index])
        axes_set_kwargs: dict[str, Any] = {
            "title": panel_label,
            "xlabel": _build_profile_xlabel(
                panel_label,
                x_units[panel_index],
            ),
        }
        if _panel_uses_ylabel(
            panel_index,
            panel_count,
            final_figure_specification.ncols,
        ):
            axes_set_kwargs["ylabel"] = (
                vertical_axis_label
                or _build_profile_ylabel(vertical_axis)
            )

        panels.append(
            PanelInput(
                layers=panel_layers,
                axes_set_kwargs=axes_set_kwargs,
                grid_kwargs={"visible": True, "alpha": 0.3},
                legend_kwargs=(
                    {"loc": "best"} if panel_index == 0 else None
                ),
            )
        )

    return plot_vertical_profiles_panel(
        panels=panels,
        figure_specification=final_figure_specification,
        plotter=plotter,
    )


def _build_plot_panel(panel_input: PanelInput) -> PlotPanel:
    """Convert one recipe panel input into a renderable `PlotPanel`.

    Parameters
    ----------
    panel_input:
        Recipe panel definition.

    Returns
    -------
    PlotPanel
        Panel ready for the `SpecializedPlotter`.

    Raises
    ------
    ValueError
        If the panel has no layers or if the layers disagree on the vertical
        axis semantics.
    """
    if not panel_input.layers:
        raise ValueError("Each PanelInput must contain at least one layer.")

    vertical_axis_names = {
        layer_input.request.vertical_axis
        for layer_input in panel_input.layers
    }
    if len(vertical_axis_names) != 1:
        raise ValueError(
            "All layers in the same PanelInput must use the same "
            "vertical_axis."
        )

    plot_layers = [
        _build_plot_layer(layer_input)
        for layer_input in panel_input.layers
    ]
    return PlotPanel(
        layers=plot_layers,
        axes_set_kwargs=dict(panel_input.axes_set_kwargs),
        grid_kwargs=panel_input.grid_kwargs,
        legend_kwargs=panel_input.legend_kwargs,
        axes_calls=_build_axes_calls(panel_input),
    )


def _build_plot_layer(layer_input: VerticalProfileLayerInput) -> PlotLayer:
    """Resolve one recipe layer input into a `PlotLayer`.

    Parameters
    ----------
    layer_input:
        Vertical-profile layer definition.

    Returns
    -------
    PlotLayer
        Layer containing resolved `VerticalProfilePlotData` and rendering
        instructions.
    """
    plot_data = layer_input.adapter.to_vertical_profile_plot_data(
        variable_name=layer_input.variable_name,
        request=layer_input.request,
    )
    render_specification = _build_render_specification(layer_input)
    return PlotLayer(
        plot_data=plot_data,
        render_specification=render_specification,
    )


def _build_render_specification(
    layer_input: VerticalProfileLayerInput,
) -> RenderSpecification:
    """Return the layer render specification with optional legend label."""
    artist_kwargs = dict(layer_input.render_specification.artist_kwargs)
    if (
        layer_input.legend_label is not None
        and "label" not in artist_kwargs
    ):
        artist_kwargs["label"] = layer_input.legend_label

    return RenderSpecification(
        artist_method=layer_input.render_specification.artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=list(layer_input.render_specification.artist_calls),
    )


def _build_axes_calls(panel_input: PanelInput) -> list[dict[str, Any]]:
    """Return panel axis calls with automatic pressure-axis inversion.

    Parameters
    ----------
    panel_input:
        Recipe panel definition.

    Returns
    -------
    list[dict[str, Any]]
        Axis calls to be stored in the final `PlotPanel`.
    """
    axes_calls = [dict(axis_call) for axis_call in panel_input.axes_calls]
    vertical_axis = panel_input.layers[0].request.vertical_axis
    if vertical_axis == "pressure" and not _has_invert_yaxis_call(axes_calls):
        axes_calls.append({"method": "invert_yaxis"})

    return axes_calls


def _has_invert_yaxis_call(axes_calls: Sequence[dict[str, Any]]) -> bool:
    """Return whether `invert_yaxis` is already configured for the panel."""
    return any(
        axis_call.get("method") == "invert_yaxis"
        for axis_call in axes_calls
    )


def _normalize_profile_times(
    time: np.datetime64 | Sequence[np.datetime64],
) -> np.ndarray:
    """Return a non-empty `datetime64[ns]` array for the profile wrapper."""
    normalized_times = np.atleast_1d(
        np.asarray(time, dtype="datetime64[ns]")
    )
    if normalized_times.size == 0:
        raise ValueError("time must contain at least one instant.")

    return normalized_times


def _resolve_profile_time_reduce(
    times: np.ndarray,
    time_reduce: TimeReduce | None,
) -> TimeReduce | None:
    """Infer the reducer for multi-time profile requests when omitted."""
    if times.size > 1 and time_reduce is None:
        return "mean"

    return time_reduce


def _normalize_panel_extra_layers(
    panel_extra_layers: Sequence[
        Sequence[VerticalProfileLayerInput]
    ] | None,
    panel_count: int,
) -> list[list[VerticalProfileLayerInput]]:
    """Return one mutable extra-layer list per panel."""
    if panel_extra_layers is None:
        return [[] for _ in range(panel_count)]

    if len(panel_extra_layers) != panel_count:
        raise ValueError(
            "panel_extra_layers must match the number of output panels."
        )

    return [
        list(extra_layers)
        for extra_layers in panel_extra_layers
    ]


def _build_default_profile_point_figure_specification(
    *,
    panel_count: int,
    point_lat: float,
    point_lon: float,
    times: np.ndarray,
    time_reduce: TimeReduce | None,
) -> FigureSpecification:
    """Build the default figure layout for the point-profile wrapper."""
    if panel_count == 4:
        nrows = 2
        ncols = 2
        figsize = (10.8, 10.0)
    else:
        nrows = 1
        ncols = max(panel_count, 1)
        figsize = (4.5 * ncols, 8.0)

    return FigureSpecification(
        nrows=nrows,
        ncols=ncols,
        suptitle=(
            "Vertical Profiles at "
            f"{_format_profile_time_label(times, time_reduce)} "
            f"({_format_profile_latlon_label(point_lat, point_lon)})"
        ),
        figure_kwargs={"figsize": figsize, "constrained_layout": True},
    )


def _build_default_source_render_specification(
    source_index: int,
) -> RenderSpecification:
    """Return the default line style used by the point-profile wrapper."""
    color_cycle = (
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
    )
    return RenderSpecification(
        artist_method="plot",
        artist_kwargs={
            "color": color_cycle[source_index % len(color_cycle)],
            "linewidth": 2.0,
        },
    )


def _build_profile_xlabel(panel_label: str, x_unit: str) -> str:
    """Return the x-axis label for one profile panel."""
    if x_unit:
        return f"{panel_label} [{x_unit}]"

    return panel_label


def _build_profile_ylabel(vertical_axis: str) -> str:
    """Return the default y-axis label used by the wrapper."""
    if vertical_axis == "pressure":
        return "Pressure"
    if vertical_axis == "height":
        return "Height"

    return vertical_axis


def _panel_uses_ylabel(
    panel_index: int,
    panel_count: int,
    ncols: int,
) -> bool:
    """Return whether the panel should display the shared y-axis label."""
    if panel_count == 1:
        return True

    safe_ncols = max(int(ncols), 1)
    return panel_index % safe_ncols == 0


def _format_profile_time_label(
    times: np.ndarray,
    time_reduce: TimeReduce | None,
) -> str:
    """Format the wrapper time label using the legacy profile semantics."""
    if times.size == 1:
        return np.datetime_as_string(
            np.datetime64(times[0], "m"),
            unit="m",
        )

    tmin = np.datetime_as_string(np.datetime64(times.min(), "m"), unit="m")
    tmax = np.datetime_as_string(np.datetime64(times.max(), "m"), unit="m")
    reduce_label = time_reduce or "mean"
    return f"{reduce_label} {tmin} to {tmax} (n={times.size})"


def _format_profile_latlon_label(lat: float, lon: float) -> str:
    """Format latitude and longitude with hemisphere suffixes."""
    normalized_lon = ((lon + 180.0) % 360.0) - 180.0
    lat_hemi = "N" if lat >= 0.0 else "S"
    lon_hemi = "E" if normalized_lon >= 0.0 else "W"
    return (
        f"{abs(lat):.2f} deg {lat_hemi}, "
        f"{abs(normalized_lon):.2f} deg {lon_hemi}"
    )
