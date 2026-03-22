from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Literal, Sequence

import numpy as np
from matplotlib.figure import Figure

from ..adapter import DataAdapter
from ..plot_data import VerticalCrossSectionPlotData
from ..rendering import (
    ColorbarSpecification,
    FigureSpecification,
    PlotLayer,
    PlotPanel,
    RenderSpecification,
    SpecializedPlotter,
)
from ..requests import VerticalCrossSectionRequest

TransectAxisMode = Literal["index", "distance_km"]


@dataclass
class CrossSectionLayerInput:
    """Describe one cross-section layer requested by a recipe.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing the cross-section data.
    request:
        Vertical cross-section request for this source.
    variable_name:
        Canonical variable name to be resolved by the adapter.
    render_specification:
        Rendering instructions used to convert the cross section into a
        matplotlib artist.
    legend_label:
        Optional legend label injected into the rendering kwargs when one is
        not already defined there.
    minimum_contour_level:
        Optional lower bound used when automatically computing contour
        levels for `artist_method="contour"`. When the resolved field
        maximum does not exceed this threshold, the contour layer is skipped.
    convert_pressure_to_hpa:
        When `True`, pressure vertical coordinates are converted from Pa to
        hPa before plotting.
    """

    adapter: DataAdapter
    request: VerticalCrossSectionRequest
    variable_name: str
    render_specification: RenderSpecification
    legend_label: str | None = None
    minimum_contour_level: float | None = None
    convert_pressure_to_hpa: bool = False


@dataclass
class CrossSectionPanelInput:
    """Describe one cross-section subplot to be built by the recipe.

    Parameters
    ----------
    layers:
        Ordered cross-section layers that will be composed in the same
        subplot.
    axes_set_kwargs:
        Keyword arguments forwarded to `Axes.set`.
    grid_kwargs:
        Optional grid configuration forwarded to `Axes.grid`.
    legend_kwargs:
        Optional legend configuration forwarded to `Axes.legend`.
    colorbar_specification:
        Optional colorbar definition attached to one layer in the panel.
    axes_calls:
        Ordered list of extra `Axes` method calls applied after the layers
        are drawn.
    transect_axis_mode:
        Whether the x-axis should keep the raw transect index or be
        converted to cumulative distance in kilometres.
    use_coordinate_tick_labels:
        When `True`, the recipe derives x-axis tick labels from the sampled
        transect latitudes and longitudes.
    transect_tick_count:
        Number of coordinate ticks used when
        `use_coordinate_tick_labels=True`.
    """

    layers: Sequence[CrossSectionLayerInput]
    axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    grid_kwargs: dict[str, Any] | None = None
    legend_kwargs: dict[str, Any] | None = None
    colorbar_specification: ColorbarSpecification | None = None
    axes_calls: list[dict[str, Any]] = field(default_factory=list)
    transect_axis_mode: TransectAxisMode = "index"
    use_coordinate_tick_labels: bool = False
    transect_tick_count: int = 4


def plot_cross_section_panels(
    *,
    panels: Sequence[CrossSectionPanelInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
    share_main_field_limits: bool = False,
    main_field_layer_index: int = 0,
    synchronize_y_limits: bool = False,
) -> Figure:
    """Build and render a figure composed of cross-section subplots.

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
    synchronize_y_limits:
        When `True`, the rendered panels receive one shared y-axis range.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.

    Raises
    ------
    ValueError
        If no panel is provided, if one panel has no layers, or if a shared
        limit request points to an invalid layer.
    """
    if not panels:
        raise ValueError("At least one CrossSectionPanelInput is required.")

    resolved_panels = [
        _build_cross_section_plot_panel(panel_input)
        for panel_input in panels
    ]
    if share_main_field_limits:
        _apply_shared_field_limits(
            resolved_panels,
            main_field_layer_index,
        )

    recipe_plotter = plotter or SpecializedPlotter()
    figure = recipe_plotter.plot(
        panels=resolved_panels,
        figure_specification=figure_specification,
    )
    if synchronize_y_limits:
        _synchronize_panel_y_limits(
            figure=figure,
            panel_count=len(resolved_panels),
        )

    return figure


def _build_cross_section_plot_panel(
    panel_input: CrossSectionPanelInput,
) -> PlotPanel:
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
        If the panel has no layers or if all configured contour layers are
        skipped after applying the contour threshold.
    """
    if not panel_input.layers:
        raise ValueError(
            "Each CrossSectionPanelInput must contain at least one layer."
        )

    plot_layers: list[PlotLayer] = []
    representative_plot_data: VerticalCrossSectionPlotData | None = None
    for layer_input in panel_input.layers:
        plot_layer = _build_cross_section_plot_layer(
            layer_input,
            panel_input.transect_axis_mode,
        )
        if plot_layer is None:
            continue

        plot_layers.append(plot_layer)
        if representative_plot_data is None:
            representative_plot_data = plot_layer.plot_data

    if not plot_layers or representative_plot_data is None:
        raise ValueError(
            "The cross-section panel produced no drawable layers."
        )

    axes_calls = list(panel_input.axes_calls)
    if panel_input.use_coordinate_tick_labels:
        axes_calls.extend(
            _build_transect_coordinate_axes_calls(
                representative_plot_data,
                panel_input.transect_tick_count,
            )
        )

    return PlotPanel(
        layers=plot_layers,
        axes_set_kwargs=dict(panel_input.axes_set_kwargs),
        grid_kwargs=_copy_optional_mapping(panel_input.grid_kwargs),
        legend_kwargs=_copy_optional_mapping(panel_input.legend_kwargs),
        colorbar_specification=panel_input.colorbar_specification,
        axes_calls=axes_calls,
    )


def _build_cross_section_plot_layer(
    layer_input: CrossSectionLayerInput,
    transect_axis_mode: TransectAxisMode,
) -> PlotLayer | None:
    """Convert one recipe layer input into a renderable `PlotLayer`.

    Parameters
    ----------
    layer_input:
        Recipe layer definition.
    transect_axis_mode:
        Requested x-axis mode for the panel that owns the layer.

    Returns
    -------
    PlotLayer | None
        Plot layer ready for the `SpecializedPlotter`. `None` is returned
        when a contour layer is intentionally skipped because the field does
        not exceed the configured minimum contour level.
    """
    plot_data = _resolve_cross_section_plot_data(
        layer_input,
        transect_axis_mode,
    )
    render_specification = _build_cross_section_render_specification(
        layer_input,
        plot_data,
    )
    if render_specification is None:
        return None

    return PlotLayer(
        plot_data=plot_data,
        render_specification=render_specification,
    )


def _resolve_cross_section_plot_data(
    layer_input: CrossSectionLayerInput,
    transect_axis_mode: TransectAxisMode,
) -> VerticalCrossSectionPlotData:
    """Resolve a layer input into a `VerticalCrossSectionPlotData`."""
    plot_data = layer_input.adapter.to_vertical_cross_section_plot_data(
        variable_name=layer_input.variable_name,
        request=layer_input.request,
    )
    if layer_input.convert_pressure_to_hpa:
        plot_data = _convert_pressure_axis_to_hpa(plot_data)
    if transect_axis_mode == "distance_km":
        plot_data = _convert_transect_axis_to_distance(plot_data)

    return plot_data


def _build_cross_section_render_specification(
    layer_input: CrossSectionLayerInput,
    plot_data: VerticalCrossSectionPlotData,
) -> RenderSpecification | None:
    """Copy and enrich the rendering specification for one layer."""
    artist_kwargs = dict(layer_input.render_specification.artist_kwargs)
    if layer_input.legend_label is not None and "label" not in artist_kwargs:
        artist_kwargs["label"] = layer_input.legend_label

    artist_method = layer_input.render_specification.artist_method
    if artist_method == "contour" and "levels" not in artist_kwargs:
        levels = _build_contour_levels(
            plot_data.field,
            minimum_level=layer_input.minimum_contour_level,
        )
        if levels is None:
            return None
        artist_kwargs["levels"] = levels

    return RenderSpecification(
        artist_method=artist_method,
        artist_kwargs=artist_kwargs,
        artist_calls=_copy_artist_calls(
            layer_input.render_specification.artist_calls
        ),
    )


def _convert_pressure_axis_to_hpa(
    plot_data: VerticalCrossSectionPlotData,
) -> VerticalCrossSectionPlotData:
    """Return a copy of the plot data with pressure values in hPa."""
    if plot_data.vertical_axis != "pressure":
        return plot_data

    vertical_values = np.asarray(plot_data.vertical_values, dtype=float)
    converted_values = _pressure_values_to_hpa(vertical_values)
    auxiliary_values = plot_data.auxiliary_vertical_values
    if auxiliary_values is not None:
        auxiliary_values = _pressure_values_to_hpa(
            np.asarray(auxiliary_values, dtype=float)
        )

    return replace(
        plot_data,
        vertical_values=converted_values,
        auxiliary_vertical_values=auxiliary_values,
    )


def _convert_transect_axis_to_distance(
    plot_data: VerticalCrossSectionPlotData,
) -> VerticalCrossSectionPlotData:
    """Return a copy of the plot data with distance-based x coordinates."""
    latitudes = plot_data.transect_latitude
    longitudes = plot_data.transect_longitude
    if latitudes is None or longitudes is None:
        raise ValueError(
            "Transect distance mode requires transect latitude and "
            "longitude coordinates."
        )

    distances = np.zeros(len(latitudes), dtype=float)
    for index in range(1, len(latitudes)):
        distances[index] = distances[index - 1] + _haversine_distance_km(
            float(latitudes[index - 1]),
            float(longitudes[index - 1]),
            float(latitudes[index]),
            float(longitudes[index]),
        )

    return replace(
        plot_data,
        transect_values=distances,
        transect_label="Distance along transect [km]",
    )


def _build_transect_coordinate_axes_calls(
    plot_data: VerticalCrossSectionPlotData,
    tick_count: int,
) -> list[dict[str, Any]]:
    """Build axis calls that show coordinate labels along the transect."""
    latitudes = plot_data.transect_latitude
    longitudes = plot_data.transect_longitude
    if latitudes is None or longitudes is None:
        return []

    point_count = len(plot_data.transect_values)
    if point_count == 0:
        return []

    safe_tick_count = max(int(tick_count), 2)
    raw_indices = np.linspace(
        0,
        point_count - 1,
        safe_tick_count,
    ).round().astype(int)
    tick_indices = _deduplicate_indices(raw_indices)
    tick_positions = plot_data.transect_values[tick_indices]
    tick_labels = [
        _format_latlon_label(
            float(latitudes[index]),
            float(longitudes[index]),
        )
        for index in tick_indices
    ]

    return [
        {
            "method": "set_xticks",
            "args": [tick_positions],
        },
        {
            "method": "set_xticklabels",
            "args": [tick_labels],
        },
    ]


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

        field_arrays.append(layer.plot_data.field)
        target_layers.append(layer)

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


def _build_contour_levels(
    field: np.ndarray,
    minimum_level: float | None = None,
    n_levels: int = 5,
) -> np.ndarray | None:
    """Build contour levels, or return `None` for a flat/empty field."""
    valid_values = np.asarray(field, dtype=float)
    valid_values = valid_values[np.isfinite(valid_values)]
    if valid_values.size == 0:
        return None

    field_min = float(np.nanmin(valid_values))
    field_max = float(np.nanmax(valid_values))
    if minimum_level is not None:
        if field_max <= minimum_level:
            return None
        return np.linspace(minimum_level, field_max, n_levels)

    if field_min == field_max:
        return None
    return np.linspace(field_min, field_max, n_levels)


def _synchronize_panel_y_limits(
    *,
    figure: Figure,
    panel_count: int,
) -> None:
    """Apply one shared y-axis range to the rendered subplot panels."""
    main_axes = figure.axes[:panel_count]
    if len(main_axes) < 2:
        return

    y_limits = [axis.get_ylim() for axis in main_axes]
    shared_ymin = min(limit[0] for limit in y_limits)
    shared_ymax = max(limit[1] for limit in y_limits)
    for axis in main_axes:
        axis.set_ylim(shared_ymin, shared_ymax)


def _pressure_values_to_hpa(pressure_values: np.ndarray) -> np.ndarray:
    """Convert pressure values to hPa when the input looks like Pa."""
    if pressure_values.size == 0:
        return pressure_values
    if float(np.nanmax(pressure_values)) > 2000.0:
        return pressure_values / 100.0
    return pressure_values


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


def _deduplicate_indices(indices: np.ndarray) -> np.ndarray:
    """Return unique integer indices while preserving order."""
    unique_indices: list[int] = []
    for index in indices.tolist():
        if index not in unique_indices:
            unique_indices.append(index)
    return np.asarray(unique_indices, dtype=int)


def _format_latlon_label(lat: float, lon: float) -> str:
    """Format a latitude/longitude pair using hemisphere suffixes."""
    normalized_lon = ((lon + 180.0) % 360.0) - 180.0
    lat_hemi = "N" if lat >= 0.0 else "S"
    lon_hemi = "E" if normalized_lon >= 0.0 else "W"
    return (
        f"{abs(lat):.2f}°{lat_hemi}\n"
        f"{abs(normalized_lon):.2f}°{lon_hemi}"
    )


def _haversine_distance_km(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> float:
    """Return the approximate great-circle distance in kilometres."""
    earth_radius_km = 6371.0
    delta_lat = np.deg2rad(end_lat - start_lat)
    delta_lon = np.deg2rad(
        ((end_lon - start_lon + 180.0) % 360.0) - 180.0
    )
    start_lat_rad = np.deg2rad(start_lat)
    end_lat_rad = np.deg2rad(end_lat)

    haversine = (
        np.sin(delta_lat / 2.0) ** 2
        + np.cos(start_lat_rad)
        * np.cos(end_lat_rad)
        * np.sin(delta_lon / 2.0) ** 2
    )
    return float(
        2.0
        * earth_radius_km
        * np.arctan2(np.sqrt(haversine), np.sqrt(1.0 - haversine))
    )
