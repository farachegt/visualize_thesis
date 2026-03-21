from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .plot_data import (
    HorizontalFieldPlotData,
    TimeSeriesPlotData,
    TimeVerticalSectionPlotData,
    VerticalCrossSectionPlotData,
    VerticalProfilePlotData,
)

ArtistMethod = Literal["plot", "contourf", "contour", "pcolormesh"]
PlotDataType = Union[
    VerticalProfilePlotData,
    HorizontalFieldPlotData,
    VerticalCrossSectionPlotData,
    TimeSeriesPlotData,
    TimeVerticalSectionPlotData,
]

ArtistResult = Any


@dataclass
class RenderSpecification:
    """Describe how a plot layer should be rendered."""

    artist_method: ArtistMethod
    artist_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class ColorbarSpecification:
    """Describe the colorbar associated with a plot panel."""

    source_layer_index: int
    label: str | None = None
    colorbar_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlotLayer:
    """Aggregate ready-to-plot data with its rendering instructions."""

    plot_data: PlotDataType
    render_specification: RenderSpecification


@dataclass
class PlotPanel:
    """Represent a single subplot and the layers drawn on it."""

    layers: list[PlotLayer]
    axes_set_kwargs: dict[str, Any] = field(default_factory=dict)
    grid_kwargs: dict[str, Any] | None = None
    legend_kwargs: dict[str, Any] | None = None
    colorbar_specification: ColorbarSpecification | None = None
    axes_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FigureSpecification:
    """Describe the layout and metadata of a full matplotlib figure."""

    nrows: int
    ncols: int
    suptitle: str | None = None
    figure_kwargs: dict[str, Any] = field(default_factory=dict)
    subplot_kwargs: dict[str, Any] = field(default_factory=dict)
    suptitle_kwargs: dict[str, Any] = field(default_factory=dict)


class SpecializedPlotter:
    """Render `PlotPanel` objects into a matplotlib figure.

    The plotter is intentionally thin. It does not read files, resolve
    variables or derive data. It only translates `PlotData` plus
    `RenderSpecification` into matplotlib artists.
    """

    _SUPPORTED_METHODS = {
        VerticalProfilePlotData: {"plot"},
        TimeSeriesPlotData: {"plot"},
        HorizontalFieldPlotData: {"contourf", "contour", "pcolormesh"},
        VerticalCrossSectionPlotData: {"contourf", "contour", "pcolormesh"},
        TimeVerticalSectionPlotData: {"contourf", "contour", "pcolormesh"},
    }

    def plot(
        self,
        panels: list[PlotPanel],
        figure_specification: FigureSpecification,
    ) -> Figure:
        """Render panels into a matplotlib figure.

        Parameters
        ----------
        panels:
            Ordered list of plot panels to be rendered.
        figure_specification:
            Global figure configuration, including layout and suptitle.

        Returns
        -------
        Figure
            The rendered matplotlib figure.

        Raises
        ------
        ValueError
            If the number of panels exceeds the figure capacity, if a panel
            is empty, if layers in the same panel use incompatible axis
            semantics, or if the requested colorbar configuration is invalid.
        NotImplementedError
            If a `PlotData` type or `artist_method` combination is not
            supported by the MVP implementation.
        AttributeError
            If an `axes_call` refers to an unknown `Axes` method.
        """
        max_panels = (
            figure_specification.nrows * figure_specification.ncols
        )
        if len(panels) > max_panels:
            raise ValueError(
                "The number of panels exceeds the available subplot slots "
                "defined by FigureSpecification."
            )

        figure, axes = plt.subplots(
            figure_specification.nrows,
            figure_specification.ncols,
            **figure_specification.figure_kwargs,
            **figure_specification.subplot_kwargs,
        )
        flat_axes = self._flatten_axes(axes)

        for axis_index, panel in enumerate(panels):
            axis = flat_axes[axis_index]
            self._plot_panel(axis, panel, figure)

        for axis in flat_axes[len(panels):]:
            axis.set_visible(False)

        if figure_specification.suptitle is not None:
            figure.suptitle(
                figure_specification.suptitle,
                **figure_specification.suptitle_kwargs,
            )

        return figure

    def _plot_panel(
        self,
        axis: Axes,
        panel: PlotPanel,
        figure: Figure,
    ) -> None:
        """Render a single panel on a matplotlib axis.

        Parameters
        ----------
        axis:
            Axis that receives the panel.
        panel:
            Panel definition with ordered layers and axis options.
        figure:
            Parent matplotlib figure, used for colorbar creation.

        Raises
        ------
        ValueError
            If the panel has no layers, if axis semantics are incompatible,
            or if the colorbar specification points to an invalid layer.
        """
        if not panel.layers:
            raise ValueError(
                "A PlotPanel must contain at least one PlotLayer."
            )

        self._validate_panel_axis_compatibility(panel)

        artists: list[ArtistResult] = []
        for layer in panel.layers:
            artist = self._plot_layer(axis, layer)
            artists.append(artist)

        self._apply_panel_configuration(axis, panel)
        self._apply_colorbar_configuration(figure, axis, panel, artists)

    def _plot_layer(
        self,
        axis: Axes,
        layer: PlotLayer,
    ) -> ArtistResult:
        """Render a single plot layer on the provided axis.

        Parameters
        ----------
        axis:
            Axis where the layer will be drawn.
        layer:
            Layer containing data and rendering options.

        Returns
        -------
        Any
            The artist returned by the matplotlib method.

        Raises
        ------
        NotImplementedError
            If the layer uses an unsupported `PlotData` type or
            `artist_method`.
        """
        plot_data = layer.plot_data
        render_specification = layer.render_specification

        self._validate_layer_support(
            plot_data,
            render_specification.artist_method,
        )

        artist_method = getattr(axis, render_specification.artist_method)
        artist_args = self._build_artist_args(plot_data)
        return artist_method(
            *artist_args,
            **render_specification.artist_kwargs,
        )

    def _build_artist_args(
        self,
        plot_data: PlotDataType,
    ) -> Tuple[np.ndarray, ...]:
        """Build positional matplotlib arguments from a `PlotData`.

        Parameters
        ----------
        plot_data:
            Ready-to-plot data structure.

        Returns
        -------
        tuple[np.ndarray, ...]
            Positional arguments that should be passed to the matplotlib
            artist method.

        Raises
        ------
        NotImplementedError
            If the `PlotData` type is not supported by the MVP.
        """
        if isinstance(plot_data, VerticalProfilePlotData):
            return (plot_data.values, plot_data.vertical_values)

        if isinstance(plot_data, TimeSeriesPlotData):
            return (plot_data.times, plot_data.values)

        if isinstance(plot_data, HorizontalFieldPlotData):
            return (
                plot_data.longitude,
                plot_data.latitude,
                plot_data.field,
            )

        if isinstance(plot_data, VerticalCrossSectionPlotData):
            return (
                plot_data.transect_values,
                plot_data.vertical_values,
                plot_data.field,
            )

        if isinstance(plot_data, TimeVerticalSectionPlotData):
            return (
                plot_data.times,
                plot_data.vertical_values,
                plot_data.field,
            )

        raise NotImplementedError(
            "Unsupported PlotData type for SpecializedPlotter."
        )

    def _validate_layer_support(
        self,
        plot_data: PlotDataType,
        artist_method: ArtistMethod,
    ) -> None:
        """Validate whether a layer uses a supported data/method pair.

        Parameters
        ----------
        plot_data:
            Plot data used by the layer.
        artist_method:
            Matplotlib method requested by the layer.

        Raises
        ------
        NotImplementedError
            If the plot data type is unknown or the method is not supported
            for that type.
        """
        data_type = type(plot_data)
        supported_methods = self._SUPPORTED_METHODS.get(data_type)

        if supported_methods is None:
            raise NotImplementedError(
                f"Unsupported PlotData type: {data_type.__name__}."
            )

        if artist_method not in supported_methods:
            raise NotImplementedError(
                "Unsupported combination between PlotData type "
                f"{data_type.__name__} and artist_method "
                f"{artist_method!r}."
            )

    def _validate_panel_axis_compatibility(
        self,
        panel: PlotPanel,
    ) -> None:
        """Ensure all layers in a panel share the same axis semantics.

        Parameters
        ----------
        panel:
            Panel whose layers will be checked.

        Raises
        ------
        ValueError
            If the panel mixes incompatible axis semantics.
        """
        axis_semantics = [
            self._infer_axis_semantics(layer.plot_data)
            for layer in panel.layers
        ]
        first_semantics = axis_semantics[0]

        for semantics in axis_semantics[1:]:
            if semantics != first_semantics:
                raise ValueError(
                    "All PlotLayers in the same PlotPanel must share the "
                    "same axis semantics."
                )

    def _infer_axis_semantics(
        self,
        plot_data: PlotDataType,
    ) -> tuple[str, str]:
        """Infer logical axis semantics from a `PlotData` instance.

        Parameters
        ----------
        plot_data:
            Plot data whose axis semantics will be inferred.

        Returns
        -------
        tuple[str, str]
            Semantic labels for the x and y axes.
        """
        if isinstance(plot_data, VerticalProfilePlotData):
            return ("value", plot_data.vertical_axis)

        if isinstance(plot_data, HorizontalFieldPlotData):
            return ("longitude", "latitude")

        if isinstance(plot_data, VerticalCrossSectionPlotData):
            return ("transect", plot_data.vertical_axis)

        if isinstance(plot_data, TimeSeriesPlotData):
            return ("time", plot_data.value_axis)

        if isinstance(plot_data, TimeVerticalSectionPlotData):
            return ("time", plot_data.vertical_axis)

        raise NotImplementedError(
            "Unsupported PlotData type for axis semantic inference."
        )

    def _apply_panel_configuration(
        self,
        axis: Axes,
        panel: PlotPanel,
    ) -> None:
        """Apply axis configuration defined at panel level.

        Parameters
        ----------
        axis:
            Axis being configured.
        panel:
            Panel configuration to apply.

        Raises
        ------
        AttributeError
            If an item in `axes_calls` refers to a missing `Axes` method.
        """
        if panel.axes_set_kwargs:
            axis.set(**panel.axes_set_kwargs)

        if panel.grid_kwargs is not None:
            grid_kwargs = dict(panel.grid_kwargs)
            visible = grid_kwargs.pop("visible", None)
            if visible is None:
                axis.grid(**grid_kwargs)
            else:
                axis.grid(visible, **grid_kwargs)

        if panel.legend_kwargs is not None:
            axis.legend(**panel.legend_kwargs)

        for axis_call in panel.axes_calls:
            method_name = axis_call["method"]
            method_args = axis_call.get("args", ())
            method_kwargs = axis_call.get("kwargs", {})

            if not hasattr(axis, method_name):
                raise AttributeError(
                    f"Axes has no method named {method_name!r}."
                )

            axis_method = getattr(axis, method_name)
            axis_method(*method_args, **method_kwargs)

    def _apply_colorbar_configuration(
        self,
        figure: Figure,
        axis: Axes,
        panel: PlotPanel,
        artists: list[ArtistResult],
    ) -> None:
        """Create the panel colorbar when requested.

        Parameters
        ----------
        figure:
            Figure that will host the colorbar.
        axis:
            Axis associated with the panel.
        panel:
            Panel configuration containing the optional colorbar definition.
        artists:
            Artists created from the panel layers, in the same order.

        Raises
        ------
        ValueError
            If `source_layer_index` is outside the layer range.
        """
        colorbar_specification = panel.colorbar_specification
        if colorbar_specification is None:
            return

        layer_index = colorbar_specification.source_layer_index
        if layer_index < 0 or layer_index >= len(artists):
            raise ValueError(
                "ColorbarSpecification.source_layer_index points to an "
                "invalid PlotLayer."
            )

        colorbar = figure.colorbar(
            artists[layer_index],
            ax=axis,
            **colorbar_specification.colorbar_kwargs,
        )
        if colorbar_specification.label is not None:
            colorbar.set_label(colorbar_specification.label)

    def _flatten_axes(
        self,
        axes: Any,
    ) -> list[Axes]:
        """Normalize the output of `plt.subplots` to a flat axes list.

        Parameters
        ----------
        axes:
            Object returned by `plt.subplots`.

        Returns
        -------
        list[Axes]
            Flat list of axes in subplot order.
        """
        if isinstance(axes, Axes):
            return [axes]

        return list(axes.ravel())
