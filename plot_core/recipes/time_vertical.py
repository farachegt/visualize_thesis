from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

import numpy as np
from matplotlib.figure import Figure

from ..adapter import DataAdapter
from ..derivations import derive_pressure_from_height_standard_atmosphere
from ..plot_data import TimeSeriesPlotData, TimeVerticalSectionPlotData
from ..rendering import (
    ColorbarSpecification,
    FigureSpecification,
    PlotLayer,
    PlotPanel,
    RenderSpecification,
    SpecializedPlotter,
)
from ..requests import TimeSeriesRequest, TimeVerticalSectionRequest

HourlyMeanDataKind = Literal["time_series", "time_vertical"]


@dataclass
class HourlyMeanLayerInput:
    """Describe one hourly-mean layer requested by a recipe.

    Parameters
    ----------
    adapter:
        Data adapter responsible for producing the layer data.
    request:
        Request used by the adapter. Its concrete type depends on
        `data_kind`.
    variable_name:
        Canonical variable name to be resolved by the adapter.
    data_kind:
        Whether the input should produce a `time_series` or a
        `time_vertical` hourly-mean product.
    render_specification:
        Rendering instructions used to convert the prepared data into a
        matplotlib artist.
    legend_label:
        Optional legend label injected into the rendering kwargs when one is
        not already defined there.
    convert_height_to_pressure:
        When `True`, a time-series input is converted from height in metres
        to pressure before plotting. This is useful for overlaying `hpbl`
        over a `time x pressure` panel.
    """

    adapter: DataAdapter
    request: TimeSeriesRequest | TimeVerticalSectionRequest
    variable_name: str
    data_kind: HourlyMeanDataKind
    render_specification: RenderSpecification
    legend_label: str | None = None
    convert_height_to_pressure: bool = False


@dataclass
class HourlyMeanPanelInput:
    """Describe one subplot to be built by the hourly-mean recipe.

    Parameters
    ----------
    layers:
        Ordered hourly-mean layers that will be composed in the same panel.
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
    """

    layers: Sequence[HourlyMeanLayerInput]
    axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    grid_kwargs: dict[str, Any] | None = None
    legend_kwargs: dict[str, Any] | None = None
    colorbar_specification: ColorbarSpecification | None = None
    axes_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HourlyMeanTkeColumnInput:
    """Describe one source column in the legacy TKE comparison figure.

    Parameters
    ----------
    tke_layer:
        Main `time x vertical` TKE layer.
    hfx_layer:
        Lower-panel sensible heat flux series.
    upper_panel_title:
        Title for the upper panel.
    lower_panel_title:
        Title for the lower panel.
    qc_layer:
        Optional cloud-water contour layer drawn over the TKE section.
    hpbl_layer:
        Optional boundary-layer-height series converted to pressure and drawn
        over the TKE section.
    upper_axes_set_kwargs:
        Extra keyword arguments merged into the upper panel `Axes.set` call.
    lower_axes_set_kwargs:
        Extra keyword arguments merged into the lower panel `Axes.set` call.
    upper_colorbar_specification:
        Optional colorbar definition attached to the upper panel.
    """

    tke_layer: HourlyMeanLayerInput
    hfx_layer: HourlyMeanLayerInput
    upper_panel_title: str
    lower_panel_title: str
    qc_layer: HourlyMeanLayerInput | None = None
    hpbl_layer: HourlyMeanLayerInput | None = None
    upper_axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    lower_axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    upper_colorbar_specification: ColorbarSpecification | None = None


@dataclass
class _ResolvedHourlyMeanTkeColumn:
    """Store prepared plot layers for one legacy TKE comparison column."""

    tke_layer: PlotLayer
    hfx_layer: PlotLayer
    upper_panel_title: str
    lower_panel_title: str
    qc_layer: PlotLayer | None = None
    hpbl_layer: PlotLayer | None = None
    upper_axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    lower_axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    upper_colorbar_specification: ColorbarSpecification | None = None


def plot_hourly_mean_panels(
    *,
    panels: Sequence[HourlyMeanPanelInput],
    figure_specification: FigureSpecification,
    reference_longitude: float,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build and render a figure composed of generic hourly-mean panels.

    Parameters
    ----------
    panels:
        Ordered panel inputs. Each panel is converted into a `PlotPanel`
        after its layers are resolved through the configured adapters.
    figure_specification:
        Global figure layout and metadata.
    reference_longitude:
        Longitude used to convert UTC timestamps into local-hour bins.
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
        raise ValueError("At least one HourlyMeanPanelInput is required.")

    resolved_panels = [
        _build_hourly_mean_plot_panel(
            panel_input,
            reference_longitude,
        )
        for panel_input in panels
    ]
    recipe_plotter = plotter or SpecializedPlotter()
    return recipe_plotter.plot(
        panels=resolved_panels,
        figure_specification=figure_specification,
    )


def plot_vertical_profile_tke_hourly_mean(
    *,
    columns: Sequence[HourlyMeanTkeColumnInput],
    figure_specification: FigureSpecification | None = None,
    region_name: str | None = None,
    reference_longitude: float | None = None,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    """Build the legacy hourly-mean TKE comparison using the new core.

    Parameters
    ----------
    columns:
        Ordered source columns. Each column becomes one upper
        `time x pressure` panel plus one lower sensible-heat-flux panel.
    figure_specification:
        Optional global figure configuration. When omitted, a `2 x N` layout
        with constrained layout is created automatically.
    region_name:
        Optional region label used to build the figure suptitle.
    reference_longitude:
        Longitude used to convert UTC timestamps into local-hour bins. When
        omitted, the value is inferred from the first column bbox.
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
        If no column is provided, if the time axes do not overlap in local
        hour, or if the recipe cannot infer the local-hour longitude.
    """
    if not columns:
        raise ValueError(
            "At least one HourlyMeanTkeColumnInput is required."
        )

    local_longitude = _resolve_reference_longitude(
        columns,
        reference_longitude,
    )
    resolved_columns = [
        _resolve_tke_column(column, local_longitude)
        for column in columns
    ]
    common_hours = _build_common_hours(resolved_columns)
    resolved_columns = [
        _select_common_hours(column, common_hours)
        for column in resolved_columns
    ]

    tke_vmin, tke_vmax = _compute_shared_field_limits(
        [
            _as_time_vertical_plot_data(column.tke_layer.plot_data).field
            for column in resolved_columns
        ]
    )
    hfx_ymin, hfx_ymax = _compute_shared_series_limits(
        [
            _as_time_series_plot_data(column.hfx_layer.plot_data).values
            for column in resolved_columns
        ]
    )
    pressure_ymin, pressure_ymax = _compute_shared_pressure_limits(
        [
            _as_time_vertical_plot_data(
                column.tke_layer.plot_data
            ).vertical_values
            for column in resolved_columns
        ]
    )

    panels = _build_tke_legacy_panels(
        resolved_columns,
        tke_vmin,
        tke_vmax,
        hfx_ymin,
        hfx_ymax,
        pressure_ymin,
        pressure_ymax,
    )
    recipe_plotter = plotter or SpecializedPlotter()
    final_figure_specification = figure_specification or (
        _build_default_figure_specification(
            n_columns=len(columns),
            region_name=region_name,
            reference_longitude=local_longitude,
        )
    )
    return recipe_plotter.plot(
        panels=panels,
        figure_specification=final_figure_specification,
    )


def _build_hourly_mean_plot_panel(
    panel_input: HourlyMeanPanelInput,
    reference_longitude: float,
) -> PlotPanel:
    """Convert a recipe panel input into a renderable `PlotPanel`.

    Parameters
    ----------
    panel_input:
        Recipe panel definition.
    reference_longitude:
        Longitude used to convert UTC timestamps into local-hour bins.

    Returns
    -------
    PlotPanel
        Panel ready for the `SpecializedPlotter`.

    Raises
    ------
    ValueError
        If the panel has no layers.
    """
    if not panel_input.layers:
        raise ValueError(
            "Each HourlyMeanPanelInput must contain at least one layer."
        )

    plot_layers = [
        _build_hourly_mean_plot_layer(
            layer_input,
            reference_longitude,
        )
        for layer_input in panel_input.layers
    ]
    return PlotPanel(
        layers=plot_layers,
        axes_set_kwargs=dict(panel_input.axes_set_kwargs),
        grid_kwargs=panel_input.grid_kwargs,
        legend_kwargs=panel_input.legend_kwargs,
        colorbar_specification=panel_input.colorbar_specification,
        axes_calls=[dict(axis_call) for axis_call in panel_input.axes_calls],
    )


def _build_hourly_mean_plot_layer(
    layer_input: HourlyMeanLayerInput,
    reference_longitude: float,
) -> PlotLayer:
    """Resolve one hourly-mean layer input into a `PlotLayer`.

    Parameters
    ----------
    layer_input:
        Layer definition for one hourly-mean product.
    reference_longitude:
        Longitude used to convert UTC timestamps into local-hour bins.

    Returns
    -------
    PlotLayer
        Plot layer containing prepared `PlotData` and rendering
        instructions.
    """
    plot_data = _resolve_hourly_mean_plot_data(
        layer_input,
        reference_longitude,
    )
    render_specification = _build_render_specification(
        layer_input.render_specification,
        layer_input.legend_label,
    )
    return PlotLayer(
        plot_data=plot_data,
        render_specification=render_specification,
    )


def _resolve_hourly_mean_plot_data(
    layer_input: HourlyMeanLayerInput,
    reference_longitude: float,
) -> TimeSeriesPlotData | TimeVerticalSectionPlotData:
    """Resolve one hourly-mean layer input into ready-to-plot data.

    Parameters
    ----------
    layer_input:
        Layer definition for one hourly-mean product.
    reference_longitude:
        Longitude used to convert UTC timestamps into local-hour bins.

    Returns
    -------
    TimeSeriesPlotData | TimeVerticalSectionPlotData
        Plot data prepared in local-hour bins.

    Raises
    ------
    ValueError
        If `data_kind` and request type are incompatible.
    """
    if layer_input.data_kind == "time_vertical":
        if not isinstance(layer_input.request, TimeVerticalSectionRequest):
            raise ValueError(
                "`data_kind='time_vertical'` requires "
                "`TimeVerticalSectionRequest`."
            )
        return _build_hourly_mean_time_vertical_plot_data(
            layer_input,
            reference_longitude,
        )

    if layer_input.data_kind == "time_series":
        if not isinstance(layer_input.request, TimeSeriesRequest):
            raise ValueError(
                "`data_kind='time_series'` requires `TimeSeriesRequest`."
            )
        return _build_hourly_mean_time_series_plot_data(
            layer_input,
            reference_longitude,
        )

    raise ValueError(f"Unsupported hourly-mean data kind: {layer_input!r}.")


def _resolve_tke_column(
    column: HourlyMeanTkeColumnInput,
    reference_longitude: float,
) -> _ResolvedHourlyMeanTkeColumn:
    """Resolve one legacy TKE comparison column into plot layers."""
    return _ResolvedHourlyMeanTkeColumn(
        tke_layer=_build_hourly_mean_plot_layer(
            column.tke_layer,
            reference_longitude,
        ),
        hfx_layer=_build_hourly_mean_plot_layer(
            column.hfx_layer,
            reference_longitude,
        ),
        qc_layer=(
            None
            if column.qc_layer is None
            else _build_hourly_mean_plot_layer(
                column.qc_layer,
                reference_longitude,
            )
        ),
        hpbl_layer=(
            None
            if column.hpbl_layer is None
            else _build_hourly_mean_plot_layer(
                column.hpbl_layer,
                reference_longitude,
            )
        ),
        upper_panel_title=column.upper_panel_title,
        lower_panel_title=column.lower_panel_title,
        upper_axes_set_kwargs=dict(column.upper_axes_set_kwargs),
        lower_axes_set_kwargs=dict(column.lower_axes_set_kwargs),
        upper_colorbar_specification=column.upper_colorbar_specification,
    )


def _build_hourly_mean_time_vertical_plot_data(
    layer_input: HourlyMeanLayerInput,
    reference_longitude: float,
) -> TimeVerticalSectionPlotData:
    """Resolve a section and reduce it to local-hour means."""
    request = layer_input.request
    if not isinstance(request, TimeVerticalSectionRequest):
        raise ValueError(
            "Time-vertical hourly means require `TimeVerticalSectionRequest`."
        )

    plot_data = layer_input.adapter.to_time_vertical_section_plot_data(
        variable_name=layer_input.variable_name,
        request=request,
    )
    _validate_non_empty_hourly_mean_source(
        times=plot_data.times,
        variable_name=layer_input.variable_name,
        data_kind=layer_input.data_kind,
    )
    local_hours = _compute_local_hours(
        plot_data.times,
        reference_longitude,
    )
    unique_hours = np.unique(local_hours)
    if unique_hours.size == 0:
        raise ValueError(
            "The hourly-mean time-vertical selection produced no local-hour "
            f"bins for variable {layer_input.variable_name!r}."
        )
    hourly_field = np.column_stack(
        [
            np.nanmean(plot_data.field[:, local_hours == hour], axis=1)
            for hour in unique_hours
        ]
    )
    vertical_values = np.asarray(plot_data.vertical_values, dtype=float)
    if plot_data.vertical_axis == "pressure":
        vertical_values = _convert_pressure_values_to_hpa(vertical_values)

    return TimeVerticalSectionPlotData(
        label=plot_data.label,
        field=hourly_field,
        times=np.asarray(unique_hours, dtype=float),
        vertical_values=vertical_values,
        vertical_axis=plot_data.vertical_axis,
        units=plot_data.units,
        auxiliary_vertical_values=plot_data.auxiliary_vertical_values,
        region_label=plot_data.region_label,
        draw_mask=plot_data.draw_mask,
    )


def _build_hourly_mean_time_series_plot_data(
    layer_input: HourlyMeanLayerInput,
    reference_longitude: float,
) -> TimeSeriesPlotData:
    """Resolve a time series and reduce it to local-hour means."""
    request = layer_input.request
    if not isinstance(request, TimeSeriesRequest):
        raise ValueError(
            "Time-series hourly means require `TimeSeriesRequest`."
        )

    plot_data = layer_input.adapter.to_time_series_plot_data(
        variable_name=layer_input.variable_name,
        request=request,
    )
    _validate_non_empty_hourly_mean_source(
        times=plot_data.times,
        variable_name=layer_input.variable_name,
        data_kind=layer_input.data_kind,
    )
    local_hours = _compute_local_hours(
        plot_data.times,
        reference_longitude,
    )
    unique_hours = np.unique(local_hours)
    if unique_hours.size == 0:
        raise ValueError(
            "The hourly-mean time-series selection produced no local-hour "
            f"bins for variable {layer_input.variable_name!r}."
        )
    hourly_values = np.asarray(
        [
            np.nanmean(plot_data.values[local_hours == hour])
            for hour in unique_hours
        ],
        dtype=float,
    )
    units = plot_data.units
    value_axis = plot_data.value_axis

    if layer_input.convert_height_to_pressure:
        converted_values = derive_pressure_from_height_standard_atmosphere(
            hourly_values
        )
        hourly_values = _convert_pressure_values_to_hpa(
            np.asarray(converted_values, dtype=float)
        )
        units = "hPa"
        value_axis = "pressure"

    return TimeSeriesPlotData(
        label=plot_data.label,
        times=np.asarray(unique_hours, dtype=float),
        values=hourly_values,
        units=units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=value_axis,
        draw_mask=plot_data.draw_mask,
    )


def _validate_non_empty_hourly_mean_source(
    *,
    times: np.ndarray,
    variable_name: str,
    data_kind: HourlyMeanDataKind,
) -> None:
    """Validate that an hourly-mean source contains at least one time step.

    Parameters
    ----------
    times:
        Time axis returned by the adapter before hourly reduction.
    variable_name:
        Canonical variable used to build the plot data.
    data_kind:
        Kind of hourly-mean product being prepared.

    Raises
    ------
    ValueError
        If the upstream selection returned no time samples.
    """
    if np.asarray(times).size == 0:
        raise ValueError(
            "The hourly-mean "
            f"{data_kind.replace('_', '-')} selection returned no time "
            f"samples for variable {variable_name!r}. Check the requested "
            "time interval and source path."
        )


def _build_tke_legacy_panels(
    columns: Sequence[_ResolvedHourlyMeanTkeColumn],
    tke_vmin: float,
    tke_vmax: float,
    hfx_ymin: float,
    hfx_ymax: float,
    pressure_ymin: float,
    pressure_ymax: float,
) -> list[PlotPanel]:
    """Build the row-major panel list consumed by the legacy wrapper."""
    upper_panels = [
        _build_tke_upper_panel(
            column,
            tke_vmin,
            tke_vmax,
            pressure_ymin,
            pressure_ymax,
            column_index,
        )
        for column_index, column in enumerate(columns)
    ]
    lower_panels = [
        _build_tke_lower_panel(
            column,
            hfx_ymin,
            hfx_ymax,
        )
        for column in columns
    ]
    return upper_panels + lower_panels


def _build_tke_upper_panel(
    column: _ResolvedHourlyMeanTkeColumn,
    tke_vmin: float,
    tke_vmax: float,
    pressure_ymin: float,
    pressure_ymax: float,
    column_index: int,
) -> PlotPanel:
    """Build one upper `time x pressure` panel for the legacy wrapper."""
    upper_layers = [
        PlotLayer(
            plot_data=column.tke_layer.plot_data,
            render_specification=_build_tke_render_specification(
                column.tke_layer.render_specification,
                tke_vmin,
                tke_vmax,
            ),
        )
    ]

    if column.qc_layer is not None:
        qc_plot_data = _as_time_vertical_plot_data(column.qc_layer.plot_data)
        contour_levels = _build_contour_levels(qc_plot_data.field)
        if contour_levels is not None:
            upper_layers.append(
                PlotLayer(
                    plot_data=qc_plot_data,
                    render_specification=_build_qc_render_specification(
                        column.qc_layer.render_specification,
                        contour_levels,
                    ),
                )
            )

    if column.hpbl_layer is not None:
        upper_layers.append(column.hpbl_layer)

    axes_set_kwargs = {
        "title": column.upper_panel_title,
        "xlabel": "Local hour",
        "ylabel": "Pressure (hPa)",
        "ylim": (pressure_ymin, pressure_ymax),
    }
    axes_set_kwargs.update(column.upper_axes_set_kwargs)

    colorbar_specification = column.upper_colorbar_specification
    if colorbar_specification is None and column_index == 0:
        colorbar_specification = ColorbarSpecification(
            source_layer_index=0,
            label="TKE",
            colorbar_kwargs={
                "orientation": "horizontal",
                "fraction": 0.05,
                "pad": 0.08,
            },
        )

    return PlotPanel(
        layers=upper_layers,
        axes_set_kwargs=axes_set_kwargs,
        grid_kwargs={"visible": True, "alpha": 0.3},
        legend_kwargs=(
            {"loc": "upper right"}
            if column.hpbl_layer is not None
            else None
        ),
        colorbar_specification=colorbar_specification,
        axes_calls=_build_hour_axis_calls(invert_yaxis=True),
    )


def _build_tke_lower_panel(
    column: _ResolvedHourlyMeanTkeColumn,
    hfx_ymin: float,
    hfx_ymax: float,
) -> PlotPanel:
    """Build one lower sensible-heat-flux panel for the legacy wrapper."""
    axes_set_kwargs = {
        "title": column.lower_panel_title,
        "xlabel": "Local hour",
        "ylabel": "Sensible Heat Flux [W/m²]",
        "ylim": (hfx_ymin, hfx_ymax),
    }
    axes_set_kwargs.update(column.lower_axes_set_kwargs)

    return PlotPanel(
        layers=[column.hfx_layer],
        axes_set_kwargs=axes_set_kwargs,
        grid_kwargs={"visible": True, "alpha": 0.3},
        axes_calls=_build_hour_axis_calls(invert_yaxis=False),
    )


def _build_render_specification(
    render_specification: RenderSpecification,
    legend_label: str | None,
) -> RenderSpecification:
    """Return a render specification with an optional legend label."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    if legend_label is not None and "label" not in artist_kwargs:
        artist_kwargs["label"] = legend_label

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
    )


def _build_tke_render_specification(
    render_specification: RenderSpecification,
    tke_vmin: float,
    tke_vmax: float,
) -> RenderSpecification:
    """Return the TKE render specification with shared color limits."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    if "norm" not in artist_kwargs:
        artist_kwargs.setdefault("vmin", tke_vmin)
        artist_kwargs.setdefault("vmax", tke_vmax)

    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
    )


def _build_qc_render_specification(
    render_specification: RenderSpecification,
    contour_levels: np.ndarray,
) -> RenderSpecification:
    """Return the QC contour specification with computed contour levels."""
    artist_kwargs = dict(render_specification.artist_kwargs)
    artist_kwargs.setdefault("levels", contour_levels)
    return RenderSpecification(
        artist_method=render_specification.artist_method,
        artist_kwargs=artist_kwargs,
    )


def _build_hour_axis_calls(
    *,
    invert_yaxis: bool,
) -> list[dict[str, Any]]:
    """Return the axis calls shared by hourly panels."""
    axis_calls: list[dict[str, Any]] = [
        {
            "method": "set_xticks",
            "args": (np.arange(0, 24, 3),),
        },
        {
            "method": "set_xlim",
            "args": (0.0, 23.0),
        },
    ]
    if invert_yaxis:
        axis_calls.append({"method": "invert_yaxis"})

    return axis_calls


def _build_default_figure_specification(
    *,
    n_columns: int,
    region_name: str | None,
    reference_longitude: float,
) -> FigureSpecification:
    """Build the default figure specification for the legacy wrapper."""
    suptitle = None
    if region_name is not None:
        utc_offset = _solar_offset_hours(reference_longitude)
        suptitle = (
            "TKE Vertical Profile Hourly Mean - "
            f"{region_name}, UTC{utc_offset:+d}"
        )

    return FigureSpecification(
        nrows=2,
        ncols=n_columns,
        suptitle=suptitle,
        figure_kwargs={
            "figsize": (8 * n_columns, 12),
            "constrained_layout": True,
        },
    )


def _resolve_reference_longitude(
    columns: Sequence[HourlyMeanTkeColumnInput],
    reference_longitude: float | None,
) -> float:
    """Resolve the longitude used to compute local-hour bins."""
    if reference_longitude is not None:
        return float(reference_longitude)

    first_bbox = _infer_bbox_from_column(columns[0])
    if first_bbox is None:
        raise ValueError(
            "`reference_longitude` is required when the recipe cannot infer "
            "it from the first column requests."
        )

    min_lon, max_lon, _, _ = first_bbox
    return 0.5 * (min_lon + max_lon)


def _infer_bbox_from_column(
    column: HourlyMeanTkeColumnInput,
) -> tuple[float, float, float, float] | None:
    """Infer a bbox from the first request in a legacy TKE column."""
    for layer_input in (
        column.tke_layer,
        column.qc_layer,
        column.hpbl_layer,
        column.hfx_layer,
    ):
        if layer_input is None:
            continue
        request = layer_input.request
        if isinstance(request, TimeVerticalSectionRequest):
            if request.bbox is not None:
                return request.bbox
        elif isinstance(request, TimeSeriesRequest):
            if request.bbox is not None:
                return request.bbox

    return None


def _build_common_hours(
    columns: Sequence[_ResolvedHourlyMeanTkeColumn],
) -> np.ndarray:
    """Return the sorted local-hour intersection across all prepared data."""
    common_hours: set[int] | None = None
    for column in columns:
        hour_arrays = [
            np.asarray(
                _as_time_vertical_plot_data(column.tke_layer.plot_data).times,
                dtype=int,
            ),
            np.asarray(
                _as_time_series_plot_data(column.hfx_layer.plot_data).times,
                dtype=int,
            ),
        ]
        if column.qc_layer is not None:
            hour_arrays.append(
                np.asarray(
                    _as_time_vertical_plot_data(
                        column.qc_layer.plot_data
                    ).times,
                    dtype=int,
                )
            )
        if column.hpbl_layer is not None:
            hour_arrays.append(
                np.asarray(
                    _as_time_series_plot_data(
                        column.hpbl_layer.plot_data
                    ).times,
                    dtype=int,
                )
            )

        column_hours = set(hour_arrays[0].tolist())
        for hour_array in hour_arrays[1:]:
            column_hours &= set(hour_array.tolist())

        if common_hours is None:
            common_hours = column_hours
        else:
            common_hours &= column_hours

    sorted_hours = np.asarray(sorted(common_hours or set()), dtype=float)
    if sorted_hours.size == 0:
        raise ValueError(
            "The provided sources do not share any local-hour bins."
        )

    return sorted_hours


def _select_common_hours(
    column: _ResolvedHourlyMeanTkeColumn,
    common_hours: np.ndarray,
) -> _ResolvedHourlyMeanTkeColumn:
    """Restrict all prepared plot data in a column to the shared hours."""
    return _ResolvedHourlyMeanTkeColumn(
        tke_layer=_replace_layer_plot_data(
            column.tke_layer,
            _select_hours_from_section(
                _as_time_vertical_plot_data(column.tke_layer.plot_data),
                common_hours,
            ),
        ),
        hfx_layer=_replace_layer_plot_data(
            column.hfx_layer,
            _select_hours_from_series(
                _as_time_series_plot_data(column.hfx_layer.plot_data),
                common_hours,
            ),
        ),
        qc_layer=(
            None
            if column.qc_layer is None
            else _replace_layer_plot_data(
                column.qc_layer,
                _select_hours_from_section(
                    _as_time_vertical_plot_data(column.qc_layer.plot_data),
                    common_hours,
                ),
            )
        ),
        hpbl_layer=(
            None
            if column.hpbl_layer is None
            else _replace_layer_plot_data(
                column.hpbl_layer,
                _select_hours_from_series(
                    _as_time_series_plot_data(column.hpbl_layer.plot_data),
                    common_hours,
                ),
            )
        ),
        upper_panel_title=column.upper_panel_title,
        lower_panel_title=column.lower_panel_title,
        upper_axes_set_kwargs=dict(column.upper_axes_set_kwargs),
        lower_axes_set_kwargs=dict(column.lower_axes_set_kwargs),
        upper_colorbar_specification=column.upper_colorbar_specification,
    )


def _replace_layer_plot_data(
    layer: PlotLayer,
    plot_data: TimeSeriesPlotData | TimeVerticalSectionPlotData,
) -> PlotLayer:
    """Return a new plot layer with updated plot data."""
    return PlotLayer(
        plot_data=plot_data,
        render_specification=layer.render_specification,
    )


def _select_hours_from_section(
    plot_data: TimeVerticalSectionPlotData,
    common_hours: np.ndarray,
) -> TimeVerticalSectionPlotData:
    """Restrict a time-vertical section to a shared hour axis."""
    mask = np.isin(np.asarray(plot_data.times, dtype=float), common_hours)
    return TimeVerticalSectionPlotData(
        label=plot_data.label,
        field=plot_data.field[:, mask],
        times=np.asarray(plot_data.times, dtype=float)[mask],
        vertical_values=plot_data.vertical_values,
        vertical_axis=plot_data.vertical_axis,
        units=plot_data.units,
        auxiliary_vertical_values=plot_data.auxiliary_vertical_values,
        region_label=plot_data.region_label,
        draw_mask=plot_data.draw_mask,
    )


def _select_hours_from_series(
    plot_data: TimeSeriesPlotData,
    common_hours: np.ndarray,
) -> TimeSeriesPlotData:
    """Restrict a time series to a shared hour axis."""
    mask = np.isin(np.asarray(plot_data.times, dtype=float), common_hours)
    return TimeSeriesPlotData(
        label=plot_data.label,
        times=np.asarray(plot_data.times, dtype=float)[mask],
        values=np.asarray(plot_data.values, dtype=float)[mask],
        units=plot_data.units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=plot_data.draw_mask,
    )


def _compute_local_hours(
    times: np.ndarray,
    reference_longitude: float,
) -> np.ndarray:
    """Return integer local-hour bins derived from UTC datetimes."""
    offset_hours = _solar_offset_hours(reference_longitude)
    shifted_times = np.asarray(times).astype("datetime64[ns]")
    shifted_times = shifted_times + np.timedelta64(offset_hours, "h")
    shifted_hours = shifted_times.astype("datetime64[h]")
    shifted_days = shifted_times.astype("datetime64[D]")
    return (
        (shifted_hours - shifted_days) / np.timedelta64(1, "h")
    ).astype(int)


def _solar_offset_hours(reference_longitude: float) -> int:
    """Approximate solar-time offset from longitude."""
    normalized_longitude = ((reference_longitude + 180.0) % 360.0) - 180.0
    return int(np.round(normalized_longitude / 15.0))


def _compute_shared_field_limits(
    fields: Sequence[np.ndarray],
) -> tuple[float, float]:
    """Return shared color limits across several 2D fields."""
    field_min = min(float(np.nanmin(field)) for field in fields)
    field_max = max(float(np.nanmax(field)) for field in fields)
    if np.isnan(field_min) or np.isnan(field_max) or field_min == field_max:
        return 0.0, 1.0

    return field_min, field_max


def _compute_shared_series_limits(
    series_values: Sequence[np.ndarray],
) -> tuple[float, float]:
    """Return shared y limits across several 1D series with padding."""
    value_min = min(float(np.nanmin(values)) for values in series_values)
    value_max = max(float(np.nanmax(values)) for values in series_values)
    if np.isnan(value_min) or np.isnan(value_max) or value_min == value_max:
        return -1.0, 1.0

    value_padding = 0.05 * (value_max - value_min)
    return value_min - value_padding, value_max + value_padding


def _compute_shared_pressure_limits(
    pressure_axes: Sequence[np.ndarray],
) -> tuple[float, float]:
    """Return shared pressure limits in hPa across all top panels."""
    pressure_mins = [
        float(np.nanmin(pressure_axis))
        for pressure_axis in pressure_axes
    ]
    pressure_maxs = [
        float(np.nanmax(pressure_axis))
        for pressure_axis in pressure_axes
    ]
    pressure_min_common = max(pressure_mins)
    pressure_max_common = min(pressure_maxs)
    if pressure_min_common >= pressure_max_common:
        raise ValueError(
            "No overlapping pressure interval exists between the columns."
        )

    pressure_top = (
        max(pressure_min_common, 400.0)
        if pressure_max_common > 400.0
        else pressure_min_common
    )
    return pressure_top, pressure_max_common


def _convert_pressure_values_to_hpa(values: np.ndarray) -> np.ndarray:
    """Convert pressure values to hPa when they appear to be in Pa."""
    values = np.asarray(values, dtype=float)
    if np.nanmax(np.abs(values)) > 2000.0:
        return values / 100.0

    return values


def _build_contour_levels(field: np.ndarray) -> np.ndarray | None:
    """Build contour levels for a non-flat 2D field."""
    field_min = float(np.nanmin(field))
    field_max = float(np.nanmax(field))
    if np.isnan(field_min) or np.isnan(field_max) or field_min == field_max:
        return None

    return np.linspace(field_min, field_max, 5)


def _as_time_vertical_plot_data(
    plot_data: Any,
) -> TimeVerticalSectionPlotData:
    """Return plot data typed as `TimeVerticalSectionPlotData`."""
    if not isinstance(plot_data, TimeVerticalSectionPlotData):
        raise TypeError(
            "Expected `TimeVerticalSectionPlotData` in this recipe path."
        )

    return plot_data


def _as_time_series_plot_data(
    plot_data: Any,
) -> TimeSeriesPlotData:
    """Return plot data typed as `TimeSeriesPlotData`."""
    if not isinstance(plot_data, TimeSeriesPlotData):
        raise TypeError(
            "Expected `TimeSeriesPlotData` in this recipe path."
        )

    return plot_data
