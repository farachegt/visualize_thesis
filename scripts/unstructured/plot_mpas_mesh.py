from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np


DEFAULT_OUTPUT_PATH = Path("mpas_mesh.png")
DEFAULT_FIGSIZE = (12.0, 6.0)
DEFAULT_DPI = 150
DEFAULT_LAND_COLOR = "0.88"
DEFAULT_OCEAN_COLOR = "white"
DEFAULT_MESH_COLOR = "black"
DEFAULT_MESH_LINEWIDTH = 0.25
DEFAULT_GRIDLINE_LINEWIDTH = 0.4
DEFAULT_GRIDLINE_ALPHA = 0.5
DEFAULT_EXTENT_PADDING_FRACTION = 0.05
DEFAULT_MARKER_COLOR = "red"
DEFAULT_MARKER_SIZE = 45.0
GLOBAL_LONGITUDE_SPAN_DEGREES = 330.0


def plot_mpas_mesh(
    mesh_path: Path,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    extent: tuple[float, float, float, float] | None = None,
    projection_name: str = "robinson",
    central_longitude: float = 0.0,
    use_dual: bool = False,
    mesh_color: str = DEFAULT_MESH_COLOR,
    mesh_linewidth: float = DEFAULT_MESH_LINEWIDTH,
    land_color: str = DEFAULT_LAND_COLOR,
    ocean_color: str = DEFAULT_OCEAN_COLOR,
    coastline_linewidth: float = 0.7,
    borders_linewidth: float | None = None,
    draw_gridline_labels: bool = True,
    gridline_linewidth: float = DEFAULT_GRIDLINE_LINEWIDTH,
    gridline_alpha: float = DEFAULT_GRIDLINE_ALPHA,
    extent_padding_fraction: float = DEFAULT_EXTENT_PADDING_FRACTION,
    marker_coordinate: tuple[float, float] | None = None,
    marker_color: str = DEFAULT_MARKER_COLOR,
    marker_size: float = DEFAULT_MARKER_SIZE,
    marker_symbol: str = "o",
    marker_label: str | None = None,
    figsize: tuple[float, float] = DEFAULT_FIGSIZE,
    dpi: int = DEFAULT_DPI,
    title: str | None = None,
) -> Path:
    """Plot MPAS mesh edges over land/coastline features.

    This utility is intentionally standalone and does not use `plot_core`,
    because MPAS grids are unstructured while the project recipes currently
    target structured horizontal grids.
    """
    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh file not found: {mesh_path}")

    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        import matplotlib.pyplot as plt
        import uxarray as ux
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "plot_mpas_mesh.py requires uxarray, cartopy and matplotlib."
        ) from error

    output_path.parent.mkdir(parents=True, exist_ok=True)

    projection = _build_projection(
        projection_name=projection_name,
        central_longitude=central_longitude,
        ccrs=ccrs,
    )
    grid = ux.open_grid(mesh_path, use_dual=use_dual)
    mesh_edges = grid.to_linecollection(
        colors=mesh_color,
        linewidths=mesh_linewidth,
        periodic_elements="split",
    )
    mesh_edges.set_zorder(4)

    figure, axis = plt.subplots(
        figsize=figsize,
        constrained_layout=True,
        subplot_kw={"projection": projection},
    )
    axis.set_facecolor(ocean_color)
    if extent is None:
        inferred_extent = _infer_extent_from_grid(
            grid,
            padding_fraction=extent_padding_fraction,
        )
        if inferred_extent is None:
            axis.set_global()
        else:
            axis.set_extent(inferred_extent, crs=ccrs.PlateCarree())
    else:
        axis.set_extent(extent, crs=ccrs.PlateCarree())

    axis.add_feature(
        cfeature.LAND,
        facecolor=land_color,
        edgecolor="none",
        zorder=1,
    )
    axis.add_feature(
        cfeature.COASTLINE,
        linewidth=coastline_linewidth,
        zorder=3,
    )
    if borders_linewidth is not None:
        axis.add_feature(
            cfeature.BORDERS,
            linewidth=borders_linewidth,
            zorder=3,
        )

    if draw_gridline_labels:
        gridliner = axis.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=True,
            linewidth=gridline_linewidth,
            color="0.4",
            alpha=gridline_alpha,
            linestyle="--",
            x_inline=False,
            y_inline=False,
            zorder=2,
        )
        gridliner.top_labels = False
        gridliner.right_labels = False

    axis.add_collection(mesh_edges)
    if marker_coordinate is not None:
        marker_lat, marker_lon = marker_coordinate
        axis.scatter(
            [marker_lon],
            [marker_lat],
            s=marker_size,
            c=marker_color,
            marker=marker_symbol,
            edgecolors="black",
            linewidths=0.6,
            transform=ccrs.PlateCarree(),
            zorder=5,
            label=marker_label,
        )
        if marker_label is not None:
            axis.legend(loc="best")

    axis.set_title(title or f"MPAS {'Dual ' if use_dual else ''}Mesh")
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _build_projection(
    *,
    projection_name: str,
    central_longitude: float,
    ccrs: object,
) -> object:
    """Build a Cartopy projection from a small CLI-facing selector."""
    normalized_name = projection_name.lower()
    if normalized_name == "platecarree":
        return ccrs.PlateCarree(central_longitude=central_longitude)
    if normalized_name == "robinson":
        return ccrs.Robinson(central_longitude=central_longitude)
    if normalized_name == "mollweide":
        return ccrs.Mollweide(central_longitude=central_longitude)
    if normalized_name == "orthographic":
        return ccrs.Orthographic(
            central_longitude=central_longitude,
            central_latitude=0.0,
        )

    raise ValueError(
        "Unsupported projection. Choose one of: platecarree, robinson, "
        "mollweide, orthographic."
    )


def _infer_extent_from_grid(
    grid: object,
    *,
    padding_fraction: float,
) -> tuple[float, float, float, float] | None:
    """Infer map extent from UXarray grid node coordinates."""
    if padding_fraction < 0.0:
        raise ValueError("--extent-padding must be non-negative.")

    longitude_info = _get_grid_coordinate(grid, ("node_lon", "lonVertex"))
    latitude_info = _get_grid_coordinate(grid, ("node_lat", "latVertex"))
    if longitude_info is None or latitude_info is None:
        return None

    longitude = _coordinate_to_degrees(*longitude_info)
    latitude = _coordinate_to_degrees(*latitude_info)
    finite_mask = np.isfinite(longitude) & np.isfinite(latitude)
    if not np.any(finite_mask):
        return None

    longitude = longitude[finite_mask]
    latitude = latitude[finite_mask]
    lon_min, lon_max, lon_span = _minimal_longitude_interval(longitude)
    if lon_span >= GLOBAL_LONGITUDE_SPAN_DEGREES:
        return None

    lat_min = float(np.nanmin(latitude))
    lat_max = float(np.nanmax(latitude))
    lon_pad = max(lon_span * padding_fraction, 0.1)
    lat_pad = max((lat_max - lat_min) * padding_fraction, 0.1)

    return (
        lon_min - lon_pad,
        lon_max + lon_pad,
        max(-90.0, lat_min - lat_pad),
        min(90.0, lat_max + lat_pad),
    )


def _get_grid_coordinate(
    grid: object,
    names: Sequence[str],
) -> tuple[np.ndarray, str, str | None] | None:
    """Return one grid coordinate array by trying common UXarray names."""
    for name in names:
        if not hasattr(grid, name):
            continue

        values = getattr(grid, name)
        units = None
        if hasattr(values, "attrs"):
            units = values.attrs.get("units")
        if hasattr(values, "values"):
            values = values.values
        return np.asarray(values, dtype=float).ravel(), name, units

    return None


def _coordinate_to_degrees(
    values: np.ndarray,
    source_name: str,
    units: str | None,
) -> np.ndarray:
    """Convert probable radian coordinates to degrees."""
    if units is not None:
        normalized_units = units.lower()
        if "degree" in normalized_units:
            return values
        if "radian" in normalized_units or normalized_units == "rad":
            return np.rad2deg(values)

    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return values

    max_abs_value = float(np.nanmax(np.abs(finite_values)))
    if (
        source_name in {"lonVertex", "latVertex"}
        and max_abs_value <= (2.0 * np.pi + 1e-6)
    ):
        return np.rad2deg(values)
    return values


def _minimal_longitude_interval(
    longitude: np.ndarray,
) -> tuple[float, float, float]:
    """Return the smallest lon interval covering all points."""
    normalized = np.mod(longitude, 360.0)
    sorted_lon = np.sort(normalized)
    if sorted_lon.size == 1:
        lon_value = _normalize_longitude(float(sorted_lon[0]))
        return lon_value, lon_value, 0.0

    gaps = np.diff(sorted_lon)
    wrap_gap = sorted_lon[0] + 360.0 - sorted_lon[-1]
    all_gaps = np.concatenate([gaps, np.asarray([wrap_gap])])
    largest_gap_index = int(np.argmax(all_gaps))

    if largest_gap_index == sorted_lon.size - 1:
        interval_start = float(sorted_lon[0])
        interval_end = float(sorted_lon[-1])
    else:
        interval_start = float(sorted_lon[largest_gap_index + 1])
        interval_end = float(sorted_lon[largest_gap_index] + 360.0)

    lon_span = interval_end - interval_start
    return (
        _normalize_longitude(interval_start),
        _normalize_longitude(interval_start) + lon_span,
        lon_span,
    )


def _normalize_longitude(longitude: float) -> float:
    """Normalize longitude to the [-180, 180) interval."""
    return ((longitude + 180.0) % 360.0) - 180.0


def _parse_extent(values: Sequence[float] | None) -> (
    tuple[float, float, float, float] | None
):
    """Return an extent tuple in min_lon max_lon min_lat max_lat order."""
    if values is None:
        return None
    if len(values) != 4:
        raise ValueError("--extent requires exactly four values.")

    min_lon, max_lon, min_lat, max_lat = values
    if min_lon >= max_lon:
        raise ValueError("--extent min_lon must be smaller than max_lon.")
    if min_lat >= max_lat:
        raise ValueError("--extent min_lat must be smaller than max_lat.")
    return (min_lon, max_lon, min_lat, max_lat)


def _parse_figsize(values: Sequence[float] | None) -> tuple[float, float]:
    """Return a `(width, height)` figure size tuple."""
    if values is None:
        return DEFAULT_FIGSIZE
    if len(values) != 2:
        raise ValueError("--figsize requires exactly two values.")

    width, height = values
    if width <= 0.0 or height <= 0.0:
        raise ValueError("--figsize values must be positive.")
    return (width, height)


def _parse_marker_coordinate(
    values: Sequence[float] | None,
) -> tuple[float, float] | None:
    """Return a marker coordinate tuple in `(lat, lon)` order."""
    if values is None:
        return None
    if len(values) != 2:
        raise ValueError("--marker requires exactly two values.")

    latitude, longitude = values
    if latitude < -90.0 or latitude > 90.0:
        raise ValueError("--marker latitude must be between -90 and 90.")
    return (latitude, longitude)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Plot an MPAS unstructured mesh over Cartopy land and coastline "
            "features."
        )
    )
    parser.add_argument(
        "mesh_path",
        type=Path,
        help="Path to the MPAS mesh NetCDF file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output image path. Default: mpas_mesh.png.",
    )
    parser.add_argument(
        "--extent",
        type=float,
        nargs=4,
        metavar=("MIN_LON", "MAX_LON", "MIN_LAT", "MAX_LAT"),
        default=None,
        help="Optional map extent in degrees.",
    )
    parser.add_argument(
        "--projection",
        choices=("platecarree", "robinson", "mollweide", "orthographic"),
        default="robinson",
        help="Cartopy projection used for the output map.",
    )
    parser.add_argument(
        "--central-longitude",
        type=float,
        default=0.0,
        help="Central longitude passed to the selected projection.",
    )
    parser.add_argument(
        "--dual",
        action="store_true",
        help="Plot the MPAS dual grid instead of the primal grid.",
    )
    parser.add_argument(
        "--mesh-color",
        default=DEFAULT_MESH_COLOR,
        help="Matplotlib color for mesh edges.",
    )
    parser.add_argument(
        "--mesh-linewidth",
        type=float,
        default=DEFAULT_MESH_LINEWIDTH,
        help="Line width for mesh edges.",
    )
    parser.add_argument(
        "--land-color",
        default=DEFAULT_LAND_COLOR,
        help="Cartopy land face color.",
    )
    parser.add_argument(
        "--ocean-color",
        default=DEFAULT_OCEAN_COLOR,
        help="Axes background color used for ocean.",
    )
    parser.add_argument(
        "--coastline-linewidth",
        type=float,
        default=0.7,
        help="Line width for Cartopy coastlines.",
    )
    parser.add_argument(
        "--borders-linewidth",
        type=float,
        default=None,
        help="Optional line width for country borders.",
    )
    parser.add_argument(
        "--no-gridline-labels",
        action="store_true",
        help="Disable longitude and latitude labels on map gridlines.",
    )
    parser.add_argument(
        "--gridline-linewidth",
        type=float,
        default=DEFAULT_GRIDLINE_LINEWIDTH,
        help="Line width for longitude/latitude gridlines.",
    )
    parser.add_argument(
        "--gridline-alpha",
        type=float,
        default=DEFAULT_GRIDLINE_ALPHA,
        help="Alpha value for longitude/latitude gridlines.",
    )
    parser.add_argument(
        "--extent-padding",
        type=float,
        default=DEFAULT_EXTENT_PADDING_FRACTION,
        help=(
            "Fractional padding added around the inferred mesh extent when "
            "--extent is not provided."
        ),
    )
    parser.add_argument(
        "--marker",
        type=float,
        nargs=2,
        metavar=("LAT", "LON"),
        default=None,
        help="Optional marker coordinate in latitude longitude order.",
    )
    parser.add_argument(
        "--marker-color",
        default=DEFAULT_MARKER_COLOR,
        help="Marker face color.",
    )
    parser.add_argument(
        "--marker-size",
        type=float,
        default=DEFAULT_MARKER_SIZE,
        help="Marker size passed to matplotlib scatter.",
    )
    parser.add_argument(
        "--marker-symbol",
        default="o",
        help="Marker symbol passed to matplotlib scatter.",
    )
    parser.add_argument(
        "--marker-label",
        default=None,
        help="Optional marker legend label.",
    )
    parser.add_argument(
        "--figsize",
        type=float,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        default=None,
        help="Matplotlib figure size in inches.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help="Output figure DPI.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional plot title.",
    )
    return parser


def main() -> None:
    """Parse CLI arguments, generate the figure and print its path."""
    parser = build_parser()
    args = parser.parse_args()

    output_path = plot_mpas_mesh(
        mesh_path=args.mesh_path,
        output_path=args.output,
        extent=_parse_extent(args.extent),
        projection_name=args.projection,
        central_longitude=args.central_longitude,
        use_dual=args.dual,
        mesh_color=args.mesh_color,
        mesh_linewidth=args.mesh_linewidth,
        land_color=args.land_color,
        ocean_color=args.ocean_color,
        coastline_linewidth=args.coastline_linewidth,
        borders_linewidth=args.borders_linewidth,
        draw_gridline_labels=not args.no_gridline_labels,
        gridline_linewidth=args.gridline_linewidth,
        gridline_alpha=args.gridline_alpha,
        extent_padding_fraction=args.extent_padding,
        marker_coordinate=_parse_marker_coordinate(args.marker),
        marker_color=args.marker_color,
        marker_size=args.marker_size,
        marker_symbol=args.marker_symbol,
        marker_label=args.marker_label,
        figsize=_parse_figsize(args.figsize),
        dpi=args.dpi,
        title=args.title,
    )
    print(f"saved: {output_path}")


if __name__ == "__main__":
    main()
