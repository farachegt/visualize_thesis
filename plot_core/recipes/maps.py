from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Sequence, Tuple

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from matplotlib.figure import Figure

from ..adapter import DataAdapter
from ..plot_data import HorizontalFieldPlotData
from ..rendering import (
    ColorbarSpecification,
    FigureSpecification,
    PlotLayer,
    PlotPanel,
    RenderSpecification,
    SpecializedPlotter,
)
from ..requests import HorizontalFieldRequest

BBox = Tuple[float, float, float, float]


@dataclass
class MapLayerInput:
    """Describe one horizontal-field layer requested by a map recipe.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing the map data.
    request:
        Horizontal field request for this source.
    variable_name:
        Canonical variable name to be resolved by the adapter.
    render_specification:
        Rendering instructions used to convert the field into a matplotlib
        artist.
    legend_label:
        Optional legend label injected into the rendering kwargs when one is
        not already defined there.
    """

    adapter: DataAdapter
    request: HorizontalFieldRequest
    variable_name: str
    render_specification: RenderSpecification
    legend_label: str | None = None


@dataclass
class MapPanelInput:
    """Describe one map subplot to be built by the recipe.

    Parameters
    ----------
    layers:
        Ordered map layers that will be composed in the same subplot.
    axes_set_kwargs:
        Keyword arguments forwarded to `Axes.set`.
    legend_kwargs:
        Optional legend configuration forwarded to `Axes.legend`.
    colorbar_specification:
        Optional colorbar definition attached to one layer in the panel.
    axes_calls:
        Ordered list of extra `Axes` method calls applied after the layers
        are drawn.
    extent:
        Optional map extent in the order `(min_lon, max_lon, min_lat,
        max_lat)`.
    coastlines_kwargs:
        Optional kwargs forwarded to `GeoAxes.coastlines`. Set to `None` to
        disable coastlines.
    borders_kwargs:
        Optional kwargs forwarded to `GeoAxes.add_feature` for political
        borders. Set to `None` to disable borders.
    gridlines_kwargs:
        Optional kwargs forwarded to `GeoAxes.gridlines`.
    gridliner_attrs:
        Optional attributes applied to the `Gridliner` returned by
        `GeoAxes.gridlines`.
    """

    layers: Sequence[MapLayerInput]
    axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    legend_kwargs: dict[str, Any] | None = None
    colorbar_specification: ColorbarSpecification | None = None
    axes_calls: list[dict[str, Any]] = field(default_factory=list)
    extent: BBox | None = None
    coastlines_kwargs: dict[str, Any] | None = field(
        default_factory=dict
    )
    borders_kwargs: dict[str, Any] | None = field(default_factory=dict)
    gridlines_kwargs: dict[str, Any] | None = None
    gridliner_attrs: dict[str, Any] = field(default_factory=dict)


def plot_map_panels(
    *,
    panels: Sequence[MapPanelInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
    share_main_field_limits: bool = False,
    main_field_layer_index: int = 0,
) -> Figure:
    """Build and render a figure composed of map subplots.

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
    share_main_field_limits:
        When `True`, the layer selected by `main_field_layer_index` uses one
        shared `vmin`/`vmax` pair across all panels.
    main_field_layer_index:
        Layer index used when `share_main_field_limits=True`.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.
    """
    if not panels:
        raise ValueError("At least one MapPanelInput is required.")

    resolved_panels = [
        _build_map_plot_panel(panel_input)
        for panel_input in panels
    ]
    if share_main_field_limits:
        _apply_shared_field_limits(
            resolved_panels,
            main_field_layer_index,
        )

    recipe_plotter = plotter or SpecializedPlotter()
    return recipe_plotter.plot(
        panels=resolved_panels,
        figure_specification=_build_map_figure_specification(
            figure_specification
        ),
    )


def _build_map_plot_panel(
    panel_input: MapPanelInput,
) -> PlotPanel:
    """Convert one recipe panel input into a renderable `PlotPanel`."""
    if not panel_input.layers:
        raise ValueError("Each MapPanelInput must contain at least one layer.")

    plot_layers = [
        _build_map_plot_layer(layer_input)
        for layer_input in panel_input.layers
    ]
    return PlotPanel(
        layers=plot_layers,
        axes_set_kwargs=dict(panel_input.axes_set_kwargs),
        legend_kwargs=_copy_optional_mapping(panel_input.legend_kwargs),
        colorbar_specification=panel_input.colorbar_specification,
        axes_calls=_build_map_axes_calls(panel_input),
    )


def _build_map_plot_layer(
    layer_input: MapLayerInput,
) -> PlotLayer:
    """Convert one recipe layer input into a renderable `PlotLayer`."""
    plot_data = layer_input.adapter.to_horizontal_field_plot_data(
        variable_name=layer_input.variable_name,
        request=layer_input.request,
    )
    render_specification = _build_map_render_specification(
        layer_input.render_specification,
        layer_input.legend_label,
    )
    return PlotLayer(
        plot_data=plot_data,
        render_specification=render_specification,
    )


def _build_map_render_specification(
    render_specification: RenderSpecification,
    legend_label: str | None,
) -> RenderSpecification:
    """Copy and enrich a render specification for a map layer."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    artist_kwargs.setdefault("transform", ccrs.PlateCarree())
    if render_specification.artist_method == "pcolormesh":
        artist_kwargs.setdefault("shading", "auto")
    if legend_label is not None and "label" not in artist_kwargs:
        artist_kwargs["label"] = legend_label

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=_copy_artist_calls(render_specification.artist_calls),
    )


def _build_map_figure_specification(
    figure_specification: FigureSpecification,
) -> FigureSpecification:
    """Ensure the figure specification uses a cartopy projection."""
    subplot_kwargs = dict(figure_specification.subplot_kwargs)
    subplot_kwargs.setdefault("projection", ccrs.PlateCarree())
    return replace(
        figure_specification,
        subplot_kwargs=subplot_kwargs,
    )


def _build_map_axes_calls(
    panel_input: MapPanelInput,
) -> list[dict[str, Any]]:
    """Build cartopy-specific axis calls for one map panel."""
    axes_calls = [dict(axis_call) for axis_call in panel_input.axes_calls]
    if panel_input.extent is not None:
        axes_calls.append(
            {
                "method": "set_extent",
                "args": [panel_input.extent],
                "kwargs": {"crs": ccrs.PlateCarree()},
            }
        )

    if panel_input.coastlines_kwargs is not None:
        axes_calls.append(
            {
                "method": "coastlines",
                "kwargs": dict(panel_input.coastlines_kwargs),
            }
        )

    if panel_input.borders_kwargs is not None:
        axes_calls.append(
            {
                "method": "add_feature",
                "args": [cfeature.BORDERS],
                "kwargs": dict(panel_input.borders_kwargs),
            }
        )

    if panel_input.gridlines_kwargs is not None:
        gridlines_kwargs = dict(panel_input.gridlines_kwargs)
        gridlines_kwargs.setdefault("crs", ccrs.PlateCarree())
        axes_calls.append(
            {
                "method": "gridlines",
                "kwargs": gridlines_kwargs,
                "result_setattrs": dict(panel_input.gridliner_attrs),
            }
        )

    return axes_calls


def _apply_shared_field_limits(
    plot_panels: Sequence[PlotPanel],
    layer_index: int,
) -> None:
    """Apply one shared `vmin`/`vmax` pair to the selected panel layer."""
    field_arrays: list[np.ndarray] = []
    target_layers: list[PlotLayer] = []
    for panel in plot_panels:
        if layer_index >= len(panel.layers):
            raise ValueError(
                "Shared field limits require the selected layer index to "
                "exist in every panel."
            )

        layer = panel.layers[layer_index]
        artist_method = layer.render_specification.artist_method
        if artist_method not in {"contourf", "pcolormesh"}:
            raise ValueError(
                "Shared field limits require contourf or pcolormesh on the "
                "selected layer."
            )

        target_layers.append(layer)
        field_arrays.append(_as_horizontal_field_plot_data(layer).field)

    vmin, vmax = _compute_shared_field_limits(field_arrays)
    for layer in target_layers:
        artist_kwargs = dict(layer.render_specification.artist_kwargs)
        artist_kwargs["vmin"] = vmin
        artist_kwargs["vmax"] = vmax
        layer.render_specification = RenderSpecification(
            artist_method=layer.render_specification.artist_method,
            artist_kwargs=artist_kwargs,
            artist_calls=_copy_artist_calls(
                layer.render_specification.artist_calls
            ),
        )


def _compute_shared_field_limits(
    fields: Sequence[np.ndarray],
) -> tuple[float, float]:
    """Return one finite `vmin`/`vmax` pair for a collection of fields."""
    valid_values = [
        np.asarray(field, dtype=float)[np.isfinite(field)]
        for field in fields
    ]
    valid_values = [values for values in valid_values if values.size > 0]
    if not valid_values:
        return 0.0, 1.0

    vmin = min(float(np.nanmin(values)) for values in valid_values)
    vmax = max(float(np.nanmax(values)) for values in valid_values)
    if vmin == vmax:
        vmax = vmin + 1.0
    return vmin, vmax


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
    """Return deep-enough copies of artist-call dictionaries."""
    copied_calls: list[dict[str, Any]] = []
    for artist_call in artist_calls:
        copied_calls.append(
            {
                "method": artist_call["method"],
                "args": tuple(artist_call.get("args", ())),
                "kwargs": dict(artist_call.get("kwargs", {})),
            }
        )
    return copied_calls


def _as_horizontal_field_plot_data(
    layer: PlotLayer,
) -> HorizontalFieldPlotData:
    """Return the layer data as `HorizontalFieldPlotData`."""
    plot_data = layer.plot_data
    if not isinstance(plot_data, HorizontalFieldPlotData):
        raise TypeError(
            "Expected HorizontalFieldPlotData for map recipe layer."
        )
    return plot_data
