from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from matplotlib.figure import Figure

from ..adapter import DataAdapter
from ..rendering import (
    PlotLayer,
    PlotPanel,
    FigureSpecification,
    RenderSpecification,
    SpecializedPlotter,
)
from ..requests import VerticalProfileRequest


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
