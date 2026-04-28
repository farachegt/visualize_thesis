from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence, Union

from matplotlib.figure import Figure

from ..adapter import DataAdapter
from ..plot_data import TimeSeriesPlotData
from ..rendering import (
    FigureSpecification,
    PlotLayer,
    PlotPanel,
    RenderSpecification,
    SpecializedPlotter,
)
from ..requests import TimeSeriesRequest


@dataclass
class TimeSeriesLayerInput:
    """Describe one time-series layer requested by a recipe.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing the time-series data.
    request:
        Time-series request for this source.
    variable_name:
        Canonical variable name to be resolved by the adapter.
    render_specification:
        Rendering instructions used to convert the time series into a
        matplotlib artist.
    legend_label:
        Optional legend label injected into the rendering kwargs when one is
        not already defined there.
    """

    adapter: DataAdapter
    request: TimeSeriesRequest
    variable_name: str
    render_specification: RenderSpecification
    legend_label: str | None = None


@dataclass
class PreparedTimeSeriesLayerInput:
    """Describe one precomputed time-series layer requested by a recipe.

    Parameters
    ----------
    plot_data:
        Time series that is already prepared and ready for rendering.
    render_specification:
        Rendering instructions used to convert the time series into a
        matplotlib artist.
    legend_label:
        Optional legend label injected into the rendering kwargs when one is
        not already defined there.
    """

    plot_data: TimeSeriesPlotData
    render_specification: RenderSpecification
    legend_label: str | None = None


TimeSeriesLayerDefinition = Union[
    TimeSeriesLayerInput,
    PreparedTimeSeriesLayerInput,
]


@dataclass
class TimeSeriesPanelInput:
    """Describe one time-series subplot to be built by the recipe.

    Parameters
    ----------
    layers:
        Ordered time-series layers that will be composed in the same subplot.
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

    layers: Sequence[TimeSeriesLayerDefinition]
    axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    grid_kwargs: dict[str, Any] | None = None
    legend_kwargs: dict[str, Any] | None = None
    axes_calls: list[dict[str, Any]] = field(default_factory=list)


def plot_time_series_panels(
    *,
    panels: Sequence[TimeSeriesPanelInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build and render a figure composed of time-series subplots.

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
        If no panel is provided or if one panel has no layers.
    """
    if not panels:
        raise ValueError("At least one TimeSeriesPanelInput is required.")

    resolved_panels = [
        _build_time_series_plot_panel(panel_input)
        for panel_input in panels
    ]
    recipe_plotter = plotter or SpecializedPlotter()
    return recipe_plotter.plot(
        panels=resolved_panels,
        figure_specification=figure_specification,
    )


def _build_time_series_plot_panel(
    panel_input: TimeSeriesPanelInput,
) -> PlotPanel:
    """Convert one recipe panel input into a renderable `PlotPanel`."""
    if not panel_input.layers:
        raise ValueError(
            "Each TimeSeriesPanelInput must contain at least one layer."
        )

    plot_layers = [
        _build_time_series_plot_layer(layer_input)
        for layer_input in panel_input.layers
    ]
    return PlotPanel(
        layers=plot_layers,
        axes_set_kwargs=dict(panel_input.axes_set_kwargs),
        grid_kwargs=_copy_optional_mapping(panel_input.grid_kwargs),
        legend_kwargs=_copy_optional_mapping(panel_input.legend_kwargs),
        axes_calls=_copy_artist_calls(panel_input.axes_calls),
    )


def _build_time_series_plot_layer(
    layer_input: TimeSeriesLayerDefinition,
) -> PlotLayer:
    """Resolve one recipe layer input into a `PlotLayer`."""
    if isinstance(layer_input, TimeSeriesLayerInput):
        plot_data = layer_input.adapter.to_time_series_plot_data(
            variable_name=layer_input.variable_name,
            request=layer_input.request,
        )
        legend_label = layer_input.legend_label
    else:
        plot_data = layer_input.plot_data
        legend_label = layer_input.legend_label

    render_specification = _build_time_series_render_specification(
        layer_input.render_specification,
        legend_label,
    )
    return PlotLayer(
        plot_data=plot_data,
        render_specification=render_specification,
    )


def _build_time_series_render_specification(
    render_specification: RenderSpecification,
    legend_label: str | None,
) -> RenderSpecification:
    """Copy and enrich a render specification for a time-series layer."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    if legend_label is not None and "label" not in artist_kwargs:
        artist_kwargs["label"] = legend_label

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=_copy_artist_calls(render_specification.artist_calls),
    )


def _copy_optional_mapping(
    values: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Return a shallow copy of an optional dictionary."""
    if values is None:
        return None
    return dict(values)


def _copy_artist_calls(
    artist_calls: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return shallow copies of artist or axis call dictionaries."""
    return [dict(call) for call in artist_calls]
