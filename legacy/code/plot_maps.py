import os
from typing import List, Optional, Sequence, Tuple

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr


def plot_side_by_side(
    e3sm_data: xr.Dataset,
    monan_data: xr.Dataset,
    variable_e3sm: str,
    variable_monan: str,
    vmin: float,
    vmax: float,
    cmap: str,
    date: np.datetime64,
    central_value: Optional[float] = None,
    cmap_diff: str = "RdBu_r",
    diff_limit: Optional[float] = None,
) -> None:
    """Plot MONAN/E3SM side-by-side fields and a MONAN-E3SM difference map."""
    print(f"Plotting side by side {variable_monan} for date:", date)
    if not os.path.exists("plots"):
        os.makedirs("plots")
    out_dir = f"plots/monan-vs-e3sm_{variable_monan}"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if central_value is not None:
        norm = mcolors.TwoSlopeNorm(
            vmin=vmin, vcenter=central_value, vmax=vmax
        )
    else:
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    monan_field = monan_data[variable_monan].sel(time=date).squeeze()
    e3sm_field = e3sm_data[variable_e3sm].sel(time=date).squeeze()
    diff_field = monan_field - e3sm_field

    if diff_limit is None:
        diff_limit = float(np.nanmax(np.abs(diff_field.values)))
        if np.isnan(diff_limit) or diff_limit == 0.0:
            diff_limit = 1.0
    diff_norm = mcolors.TwoSlopeNorm(
        vmin=-diff_limit, vcenter=0.0, vmax=diff_limit
    )

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(24, 6),
        subplot_kw={"projection": ccrs.PlateCarree()},
        constrained_layout=True,
    )

    im1 = axes[0].pcolormesh(
        monan_data["longitude"],
        monan_data["latitude"],
        monan_field,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        norm=norm,
    )
    axes[0].set_title(
        (
            f"MONAN - {variable_monan.upper()} "
            f"{np.datetime_as_string(date, unit='m')}"
        )
    )

    e3sm_lon = (
        e3sm_data["longitude"]
        if "longitude" in e3sm_data
        else e3sm_data["lon"]
    )
    e3sm_lat = (
        e3sm_data["latitude"] if "latitude" in e3sm_data else e3sm_data["lat"]
    )
    im2 = axes[1].pcolormesh(
        e3sm_lon,
        e3sm_lat,
        e3sm_field,
        transform=ccrs.PlateCarree(),
        cmap=cmap,
        norm=norm,
    )
    axes[1].set_title(
        (
            f"E3SM - {variable_e3sm.upper()} "
            f"{np.datetime_as_string(date, unit='m')}"
        )
    )

    im3 = axes[2].pcolormesh(
        monan_data["longitude"],
        monan_data["latitude"],
        diff_field,
        transform=ccrs.PlateCarree(),
        cmap=cmap_diff,
        norm=diff_norm,
    )
    axes[2].set_title(f"Delta {variable_monan.upper()} = MONAN - E3SM")

    cbar_abs = fig.colorbar(
        im1,
        ax=[axes[0], axes[1]],
        orientation="horizontal",
        fraction=0.05,
        pad=0.05,
    )
    cbar_abs.set_label(
        f"{monan_data[variable_monan].attrs.get('long_name', variable_monan)} "
        f"[{monan_data[variable_monan].attrs.get('units', '')}]"
    )

    cbar_diff = fig.colorbar(
        im3,
        ax=axes[2],
        orientation="horizontal",
        fraction=0.05,
        pad=0.05,
    )
    cbar_diff.set_label(
        "Delta "
        f"{monan_data[variable_monan].attrs.get('long_name', variable_monan)} "
        f"[{monan_data[variable_monan].attrs.get('units', '')}]"
    )

    for idx, ax in enumerate(axes):
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(cfeature.COASTLINE)
        gl = ax.gridlines(draw_labels=True)
        gl.top_labels = False
        gl.right_labels = False
        if idx != 0:
            gl.left_labels = False

    plt.savefig(
        (
            f"{out_dir}/{variable_monan}_"
            f"{np.datetime_as_string(date, unit='h')}.png"
        ),
        dpi=300,
    )
    plt.close(fig)


def plot_paper_grade_panel(
    monan_data: xr.Dataset,
    e3sm_data: xr.Dataset,
    date: np.datetime64,
    variable_pairs: Tuple[Tuple[str, str], ...] = (
        ("hpbl", "hpbl"),
        ("hfx", "hfx"),
    ),
    labels: Tuple[str, ...] = ("PBLH", "SHF/HFX"),
    vmins: Tuple[float, ...] = (0.0, -200.0),
    vmaxs: Tuple[float, ...] = (3000.0, 500.0),
    cmaps_abs: Tuple[str, ...] = ("turbo", "Spectral_r"),
    cmap_diff: str = "RdBu_r",
    diff_limits: Tuple[Optional[float], ...] = (1500, 200),
    output_dir: str = "plots/monan-vs-e3sm_panel",
) -> None:
    """Create a publication-style panel with MONAN, E3SM, and delta columns."""
    os.makedirs(output_dir, exist_ok=True)
    n_rows = len(variable_pairs)
    param_lengths = [
        len(labels),
        len(vmins),
        len(vmaxs),
        len(cmaps_abs),
        len(diff_limits),
    ]
    if any(length != n_rows for length in param_lengths):
        raise ValueError(
            "All row-wise parameters must match variable_pairs length: "
            "labels, vmins, vmaxs, cmaps_abs, diff_limits."
        )

    fig, axes = plt.subplots(
        n_rows,
        3,
        figsize=(18, max(4 * n_rows, 6)),
        subplot_kw={"projection": ccrs.PlateCarree()},
        constrained_layout=True,
    )
    if n_rows == 1:
        axes = np.array([axes])

    for row, (var_monan, var_e3sm) in enumerate(variable_pairs):
        label = labels[row]
        vmin = vmins[row]
        vmax = vmaxs[row]
        cmap_abs = cmaps_abs[row]
        diff_limit_param = diff_limits[row]

        monan_field = monan_data[var_monan].sel(time=date).squeeze()
        e3sm_field = e3sm_data[var_e3sm].sel(time=date).squeeze()
        diff_field = monan_field - e3sm_field

        abs_norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        if diff_limit_param is None:
            diff_limit = float(np.nanmax(np.abs(diff_field.values)))
            if diff_limit == 0.0 or np.isnan(diff_limit):
                diff_limit = 1.0
        else:
            diff_limit = float(diff_limit_param)
        diff_norm = mcolors.TwoSlopeNorm(
            vmin=-diff_limit, vcenter=0.0, vmax=diff_limit
        )

        im_monan = axes[row, 0].pcolormesh(
            monan_data["longitude"],
            monan_data["latitude"],
            monan_field,
            transform=ccrs.PlateCarree(),
            cmap=cmap_abs,
            norm=abs_norm,
        )
        axes[row, 0].set_title(f"MONAN - {label}")
        im_e3sm = axes[row, 1].pcolormesh(
            e3sm_data["longitude"],
            e3sm_data["latitude"],
            e3sm_field,
            transform=ccrs.PlateCarree(),
            cmap=cmap_abs,
            norm=abs_norm,
        )
        axes[row, 1].set_title(f"E3SM - {label}")
        im_diff = axes[row, 2].pcolormesh(
            monan_data["longitude"],
            monan_data["latitude"],
            diff_field,
            transform=ccrs.PlateCarree(),
            cmap=cmap_diff,
            norm=diff_norm,
        )
        axes[row, 2].set_title(f"Delta {label} = MONAN - E3SM")

        for col in range(3):
            axes[row, col].add_feature(cfeature.BORDERS)
            axes[row, col].add_feature(cfeature.COASTLINE)
            gl = axes[row, col].gridlines(draw_labels=True)
            gl.top_labels = False
            if col != 0:
                gl.left_labels = False
            gl.right_labels = False

        cbar_abs = fig.colorbar(
            im_e3sm,
            ax=[axes[row, 0], axes[row, 1]],
            orientation="horizontal",
            fraction=0.045,
            pad=0.04,
        )
        units = monan_data[var_monan].attrs.get("units", "")
        cbar_abs.set_label(f"{label} [{units}]".rstrip(" []"))
        cbar_diff = fig.colorbar(
            im_diff,
            ax=axes[row, 2],
            orientation="horizontal",
            fraction=0.045,
            pad=0.04,
        )
        cbar_diff.set_label(f"Delta {label} [{units}]".rstrip(" []"))

    date_str = np.datetime_as_string(date, unit="m")
    fig.suptitle(f"MONAN vs E3SM - {date_str}", fontsize=14)
    out_file = os.path.join(
        output_dir,
        f"monan_e3sm_panel_{variable_pairs[0][0]}-"
        f"{variable_pairs[1][0]}_{np.datetime_as_string(date, unit='h')}.png",
    )
    plt.savefig(out_file, dpi=300)
    plt.close(fig)


def plot_precipitation_monan(data: xr.Dataset) -> None:
    """Compute hourly precipitation from cumulative fields and save maps."""

    def blue_darkgreen_yellow_red(
        n: int = 256, name: str = "BlueDarkGreenYellowRed"
    ) -> mcolors.LinearSegmentedColormap:
        """Build a custom continuous colormap for precipitation rates."""
        colors = [
            (0.70, 0.85, 1.00),
            (0.00, 0.20, 0.80),
            (0.00, 0.70, 0.20),
            (1.00, 0.95, 0.00),
            (0.90, 0.00, 0.00),
        ]
        return mcolors.LinearSegmentedColormap.from_list(name, colors, N=n)

    def get_colormap_precipitation_properties(
        levels: Optional[Sequence[float]] = None,
    ) -> Tuple[List[float], mcolors.ListedColormap, mcolors.BoundaryNorm]:
        """Return levels, discrete colormap, and norm for precipitation."""
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
        levels_list = list(levels)
        n_bins = len(levels_list) - 1
        n_vir = n_bins - 1
        cmap = blue_darkgreen_yellow_red()
        vir_colors = cmap(np.linspace(0, 1, n_vir))
        colors = np.vstack(([1, 1, 1, 1], vir_colors))
        disc_cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(levels_list, ncolors=n_bins, clip=True)
        return levels_list, disc_cmap, norm

    for var in ["rainnc", "rainc"]:
        data[var] = data[var].diff("time")
    data["precipitation"] = data["rainnc"] + data["rainc"]

    if not os.path.exists("plots"):
        os.makedirs("plots")
    if not os.path.exists("plots/precipitation_monan"):
        os.makedirs("plots/precipitation_monan")

    levels, prec_cmap, prec_norm = get_colormap_precipitation_properties()
    for date in pd.date_range(
        "2014-02-24T01:00", "2014-02-27T00:00", freq="1H"
    ):
        date_numpy = np.datetime64(date)
        print("Plotting precipitation for date:", date)
        fig, ax = plt.subplots(
            figsize=(12, 6),
            subplot_kw={"projection": ccrs.PlateCarree()},
            constrained_layout=True,
        )
        im = ax.pcolormesh(
            data["longitude"],
            data["latitude"],
            data["precipitation"].sel(time=date),
            transform=ccrs.PlateCarree(),
            cmap=prec_cmap,
            norm=prec_norm,
        )
        ax.set_title(
            "MONAN - Precipitation "
            f"{np.datetime_as_string(date_numpy, unit='m')}"
        )
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(cfeature.COASTLINE)
        gl = ax.gridlines(draw_labels=True)
        gl.top_labels = False
        cbar = fig.colorbar(im, ax=ax, boundaries=levels, ticks=levels)
        cbar.set_label("Precipitation [mm]")
        plt.savefig(
            "plots/precipitation_monan/"
            f"precipitation_{np.datetime_as_string(date_numpy, unit='m')}.png",
            dpi=300,
        )
        plt.close(fig)
