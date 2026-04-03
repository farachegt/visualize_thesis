from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Sequence, Tuple, Union

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
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
    SharedColorbarSpecification,
    SpecializedPlotter,
)
from ..requests import HorizontalFieldRequest
from ._shared.comparison_matrix import (
    apply_comparison_matrix_labels as _apply_paper_grade_matrix_labels,
    build_absolute_render_specification as _build_absolute_comparison_render_specification,
    build_difference_plot_data as _build_difference_plot_data,
    build_difference_render_specification as _build_difference_render_specification,
    compute_shared_field_limits as _compute_shared_field_limits,
    copy_artist_calls as _copy_artist_calls,
    resolve_difference_units as _resolve_difference_units,
    validate_horizontal_field_compatibility as _validate_horizontal_field_compatibility,
)

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
class PreparedMapLayerInput:
    """Describe one precomputed map layer requested by a recipe.

    Parameters
    ----------
    plot_data:
        Horizontal field that is already prepared and ready for rendering.
    render_specification:
        Rendering instructions used to convert the field into a matplotlib
        artist.
    legend_label:
        Optional legend label injected into the rendering kwargs when one is
        not already defined there.
    """

    plot_data: HorizontalFieldPlotData
    render_specification: RenderSpecification
    legend_label: str | None = None


MapLayerDefinition = Union[MapLayerInput, PreparedMapLayerInput]


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

    layers: Sequence[MapLayerDefinition]
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


@dataclass
class MapComparisonSourceInput:
    """Describe one source field participating in a map comparison row."""

    adapter: DataAdapter
    request: HorizontalFieldRequest
    variable_name: str
    source_label: str


@dataclass
class MapComparisonRowInput:
    """Describe one comparison row in a publication-style map figure.

    Parameters
    ----------
    left_source:
        Source rendered in the first column.
    right_source:
        Source rendered in the second column.
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

    left_source: MapComparisonSourceInput
    right_source: MapComparisonSourceInput
    field_label: str
    absolute_render_specification: RenderSpecification
    difference_render_specification: RenderSpecification
    left_panel_title: str | None = None
    right_panel_title: str | None = None
    difference_panel_title: str | None = None
    absolute_colorbar_label: str | None = None
    difference_colorbar_label: str | None = None
    absolute_colorbar_kwargs: dict[str, Any] = field(default_factory=dict)
    difference_colorbar_kwargs: dict[str, Any] = field(
        default_factory=dict
    )
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


def plot_map_comparison_rows(
    *,
    rows: Sequence[MapComparisonRowInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build a comparison figure with left, right and delta map columns.

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
    """
    if not rows:
        raise ValueError("At least one MapComparisonRowInput is required.")

    comparison_panels: list[MapPanelInput] = []
    shared_colorbars: list[SharedColorbarSpecification] = list(
        figure_specification.shared_colorbar_specifications
    )
    for row_index, row_input in enumerate(rows):
        row_panels, row_colorbars = _build_map_comparison_row(
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


def plot_paper_grade_panel(
    *,
    monan_adapter: DataAdapter,
    e3sm_adapter: DataAdapter,
    date: np.datetime64,
    variable_pairs: Sequence[tuple[str, str]] = (
        ("hpbl", "hpbl"),
        ("sensible_heat_flux", "sensible_heat_flux"),
    ),
    labels: Sequence[str] = ("PBL Height", "Sensible Heat Flux"),
    vmins: Sequence[float] = (0.0, -200.0),
    vmaxs: Sequence[float] = (3000.0, 500.0),
    cmaps_abs: Sequence[str] = ("turbo", "Spectral_r"),
    cmap_diff: str = "RdBu_r",
    diff_limits: Sequence[float | None] = (1500.0, 200.0),
    absolute_colorbar_labels: Sequence[str] = (
        "PBL Height [m]",
        "SHF [W/m^2]",
    ),
    difference_colorbar_labels: Sequence[str] = (
        "Delta PBLH [m]",
        "Delta SHF [W/m^2]",
    ),
    column_headers: Sequence[str] = (
        "MONAN",
        "E3SM",
        "Delta (MONAN - E3SM)",
    ),
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build the legacy publication-style MONAN/E3SM comparison panel.

    Parameters
    ----------
    monan_adapter:
        Adapter representing the MONAN source.
    e3sm_adapter:
        Adapter representing the E3SM source.
    date:
        UTC instant represented by the panel.
    variable_pairs:
        Canonical variable pairs in `(monan_variable, e3sm_variable)` order,
        one pair per row.
    labels:
        Human-readable row labels.
    vmins:
        Minimum absolute-field limits, one per row.
    vmaxs:
        Maximum absolute-field limits, one per row.
    cmaps_abs:
        Colormaps used by the absolute fields, one per row.
    cmap_diff:
        Colormap used by every difference panel.
    diff_limits:
        Optional symmetric limits used by each difference panel. When one
        entry is `None`, that row derives its limit from the data.
    absolute_colorbar_labels:
        Labels used by the absolute-field colorbars, one per row.
    difference_colorbar_labels:
        Labels used by the difference colorbars, one per row.
    column_headers:
        Figure-level headers applied above the three columns.
    plotter:
        Optional plotter instance. When omitted, a fresh
        `SpecializedPlotter` is created.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.
    """
    row_count = len(variable_pairs)
    parameter_lengths = [
        len(labels),
        len(vmins),
        len(vmaxs),
        len(cmaps_abs),
        len(diff_limits),
        len(absolute_colorbar_labels),
        len(difference_colorbar_labels),
    ]
    if any(length != row_count for length in parameter_lengths):
        raise ValueError(
            "All row-wise parameters must match variable_pairs length."
        )
    if len(column_headers) != 3:
        raise ValueError(
            "column_headers must contain exactly three entries."
        )

    request = HorizontalFieldRequest(
        times=np.asarray([date], dtype="datetime64[ns]"),
    )
    row_inputs: list[MapComparisonRowInput] = []
    for (
        variable_pair,
        field_label,
        vmin,
        vmax,
        cmap_abs,
        diff_limit,
        absolute_colorbar_label,
        difference_colorbar_label,
    ) in zip(
        variable_pairs,
        labels,
        vmins,
        vmaxs,
        cmaps_abs,
        diff_limits,
        absolute_colorbar_labels,
        difference_colorbar_labels,
    ):
        monan_variable, e3sm_variable = variable_pair
        difference_artist_kwargs = {"cmap": cmap_diff}
        if diff_limit is not None:
            difference_artist_kwargs["vmin"] = -float(diff_limit)
            difference_artist_kwargs["vmax"] = float(diff_limit)

        row_inputs.append(
            MapComparisonRowInput(
                left_source=MapComparisonSourceInput(
                    adapter=monan_adapter,
                    request=request,
                    variable_name=monan_variable,
                    source_label="MONAN",
                ),
                right_source=MapComparisonSourceInput(
                    adapter=e3sm_adapter,
                    request=request,
                    variable_name=e3sm_variable,
                    source_label="E3SM",
                ),
                field_label=field_label,
                absolute_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs={
                        "cmap": cmap_abs,
                        "vmin": float(vmin),
                        "vmax": float(vmax),
                    },
                ),
                difference_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=difference_artist_kwargs,
                ),
                absolute_colorbar_label=absolute_colorbar_label,
                difference_colorbar_label=difference_colorbar_label,
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
        )

    time_label = np.datetime_as_string(date, unit="m")
    figure = plot_map_comparison_rows(
        rows=row_inputs,
        figure_specification=FigureSpecification(
            nrows=row_count,
            ncols=3,
            suptitle=(
                f"Initialization 2014-02-24T00:00 - Forecast {time_label}"
            ),
            figure_kwargs={
                "figsize": (22, max(5.0 * row_count, 9.0)),
                "constrained_layout": True,
            },
        ),
        plotter=plotter,
    )
    _apply_paper_grade_matrix_labels(
        figure=figure,
        row_labels=labels,
        column_headers=column_headers,
    )
    return figure


def plot_precipitation_monan(
    *,
    monan_adapter: DataAdapter,
    date: np.datetime64,
    precipitation_var: str = "precipitation",
    levels: Sequence[float] | None = None,
    extra_layers: Sequence[MapLayerDefinition] | None = None,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build one legacy MONAN hourly-precipitation map.

    Parameters
    ----------
    monan_adapter:
        Adapter representing the MONAN source.
    date:
        UTC instant represented by the precipitation map. This should not be
        the first cumulative instant because the hourly field is computed as
        a difference against the previous hour.
    precipitation_var:
        Canonical name of the accumulated precipitation field. In the legacy
        MONAN fixture, this is derived semantically from `rainc + rainnc`.
    levels:
        Optional precipitation bins in millimetres. When omitted, the legacy
        level list is used.
    extra_layers:
        Optional additional map layers appended on top of the precipitation
        shading. This is the main extension point for adding compatible
        overlays without changing the recipe signature.
    plotter:
        Optional plotter instance. When omitted, a fresh
        `SpecializedPlotter` is created.

    Returns
    -------
    Figure
        Rendered matplotlib figure ready for `savefig` or `show`.
    """
    date = np.datetime64(date, "ns")
    previous_date = date - np.timedelta64(1, "h")
    current_request = HorizontalFieldRequest(
        times=np.asarray([date], dtype="datetime64[ns]"),
    )
    previous_request = HorizontalFieldRequest(
        times=np.asarray([previous_date], dtype="datetime64[ns]"),
    )

    current_precipitation = monan_adapter.to_horizontal_field_plot_data(
        variable_name=precipitation_var,
        request=current_request,
    )
    previous_precipitation = monan_adapter.to_horizontal_field_plot_data(
        variable_name=precipitation_var,
        request=previous_request,
    )
    precipitation_plot_data = _build_precipitation_plot_data(
        current_precipitation=current_precipitation,
        previous_precipitation=previous_precipitation,
        label="MONAN",
        time_label=np.datetime_as_string(date, unit="m"),
    )
    precipitation_levels, precipitation_cmap, precipitation_norm = (
        _build_precipitation_color_mapping(levels)
    )
    panel_layers: list[MapLayerDefinition] = [
        PreparedMapLayerInput(
            plot_data=precipitation_plot_data,
            render_specification=RenderSpecification(
                artist_method="pcolormesh",
                artist_kwargs={
                    "cmap": precipitation_cmap,
                    "norm": precipitation_norm,
                },
            ),
        )
    ]
    if extra_layers is not None:
        panel_layers.extend(extra_layers)

    return plot_map_panels(
        panels=[
            MapPanelInput(
                layers=panel_layers,
                axes_set_kwargs={
                    "title": (
                        "MONAN - Precipitation "
                        f"{np.datetime_as_string(date, unit='m')}"
                    )
                },
                colorbar_specification=ColorbarSpecification(
                    source_layer_index=0,
                    label="Precipitation [mm]",
                    colorbar_kwargs={
                        "boundaries": precipitation_levels,
                        "ticks": precipitation_levels,
                    },
                ),
                coastlines_kwargs={},
                borders_kwargs={},
                gridlines_kwargs={"draw_labels": True},
                gridliner_attrs={"top_labels": False},
            )
        ],
        figure_specification=FigureSpecification(
            nrows=1,
            ncols=1,
            figure_kwargs={"figsize": (12, 6), "constrained_layout": True},
        ),
        plotter=plotter,
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
    layer_input: MapLayerDefinition,
) -> PlotLayer:
    """Convert one recipe layer input into a renderable `PlotLayer`."""
    if isinstance(layer_input, MapLayerInput):
        plot_data = layer_input.adapter.to_horizontal_field_plot_data(
            variable_name=layer_input.variable_name,
            request=layer_input.request,
        )
        legend_label = layer_input.legend_label
    else:
        plot_data = layer_input.plot_data
        legend_label = layer_input.legend_label

    render_specification = _build_map_render_specification(
        layer_input.render_specification,
        legend_label,
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


def _build_map_comparison_row(
    *,
    row_input: MapComparisonRowInput,
    row_index: int,
) -> tuple[list[MapPanelInput], list[SharedColorbarSpecification]]:
    """Build the three panels and colorbars associated with one row."""
    left_plot_data = _resolve_map_comparison_source_plot_data(
        row_input.left_source
    )
    right_plot_data = _resolve_map_comparison_source_plot_data(
        row_input.right_source
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
        _build_absolute_comparison_render_specification(
            row_input.absolute_render_specification,
            left_plot_data.field,
            right_plot_data.field,
        )
    )
    difference_render_specification = (
        _build_difference_render_specification(
            row_input.difference_render_specification,
            difference_plot_data.field,
        )
    )

    base_panel_index = row_index * 3
    panels = [
        _build_map_comparison_panel(
            plot_data=left_plot_data,
            render_specification=absolute_render_specification,
            title=(
                row_input.left_panel_title
                or f"{row_input.left_source.source_label} - "
                f"{row_input.field_label}"
            ),
            row_input=row_input,
            show_left_labels=True,
        ),
        _build_map_comparison_panel(
            plot_data=right_plot_data,
            render_specification=absolute_render_specification,
            title=(
                row_input.right_panel_title
                or f"{row_input.right_source.source_label} - "
                f"{row_input.field_label}"
            ),
            row_input=row_input,
            show_left_labels=False,
        ),
        _build_map_comparison_panel(
            plot_data=difference_plot_data,
            render_specification=difference_render_specification,
            title=(
                row_input.difference_panel_title
                or f"Delta {row_input.field_label} = "
                f"{row_input.left_source.source_label} - "
                f"{row_input.right_source.source_label}"
            ),
            row_input=row_input,
            show_left_labels=False,
        ),
    ]

    colorbars = [
        SharedColorbarSpecification(
            source_panel_index=base_panel_index,
            source_layer_index=0,
            target_panel_indices=[base_panel_index, base_panel_index + 1],
            label=row_input.absolute_colorbar_label,
            colorbar_kwargs=dict(row_input.absolute_colorbar_kwargs),
        ),
        SharedColorbarSpecification(
            source_panel_index=base_panel_index + 2,
            source_layer_index=0,
            target_panel_indices=[base_panel_index + 2],
            label=row_input.difference_colorbar_label,
            colorbar_kwargs=dict(row_input.difference_colorbar_kwargs),
        ),
    ]
    return panels, colorbars


def _build_map_comparison_panel(
    *,
    plot_data: HorizontalFieldPlotData,
    render_specification: RenderSpecification,
    title: str,
    row_input: MapComparisonRowInput,
    show_left_labels: bool,
) -> MapPanelInput:
    """Build one panel of a map-comparison row."""
    gridliner_attrs = dict(row_input.gridliner_attrs)
    gridliner_attrs.setdefault("top_labels", False)
    gridliner_attrs.setdefault("right_labels", False)
    gridliner_attrs["left_labels"] = show_left_labels
    return MapPanelInput(
        layers=[
            PreparedMapLayerInput(
                plot_data=plot_data,
                render_specification=render_specification,
            )
        ],
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


def _resolve_map_comparison_source_plot_data(
    source_input: MapComparisonSourceInput,
) -> HorizontalFieldPlotData:
    """Resolve one comparison source into `HorizontalFieldPlotData`."""
    plot_data = source_input.adapter.to_horizontal_field_plot_data(
        variable_name=source_input.variable_name,
        request=source_input.request,
    )
    plot_data.label = source_input.source_label
    return plot_data


def _build_precipitation_plot_data(
    *,
    current_precipitation: HorizontalFieldPlotData,
    previous_precipitation: HorizontalFieldPlotData,
    label: str,
    time_label: str,
) -> HorizontalFieldPlotData:
    """Build one hourly precipitation field from accumulated precipitation."""
    _validate_horizontal_field_compatibility(
        current_precipitation,
        previous_precipitation,
    )
    precipitation_field = (
        current_precipitation.field
        - previous_precipitation.field
    )
    return HorizontalFieldPlotData(
        label=label,
        field=precipitation_field,
        longitude=np.asarray(current_precipitation.longitude),
        latitude=np.asarray(current_precipitation.latitude),
        units=current_precipitation.units or "mm",
        time_label=time_label,
    )


def _build_precipitation_color_mapping(
    levels: Sequence[float] | None,
) -> tuple[list[float], mcolors.ListedColormap, mcolors.BoundaryNorm]:
    """Return the legacy precipitation color mapping."""
    if levels is None:
        levels = [
            0,
            0.05,
            0.1,
            0.25,
            0.5,
            0.75,
            1,
            1.25,
            1.5,
            1.75,
            2,
            2.5,
            3,
            4,
            5,
            7.5,
            10,
            15,
            20,
            30,
            45,
        ]

    base_cmap = mcolors.LinearSegmentedColormap.from_list(
        "BlueDarkGreenYellowRed",
        [
            (0.70, 0.85, 1.00),
            (0.00, 0.20, 0.80),
            (0.00, 0.70, 0.20),
            (1.00, 0.95, 0.00),
            (0.90, 0.00, 0.00),
        ],
        N=256,
    )
    level_list = list(levels)
    bin_count = len(level_list) - 1
    viridis_like_colors = base_cmap(np.linspace(0, 1, bin_count - 1))
    colors = np.vstack(([1, 1, 1, 1], viridis_like_colors))
    discrete_cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(
        level_list,
        ncolors=bin_count,
        clip=True,
    )
    return level_list, discrete_cmap, norm


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


def _copy_optional_mapping(
    values: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Return a shallow copy of an optional dictionary."""
    if values is None:
        return None
    return dict(values)
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
