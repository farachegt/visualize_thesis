import os
from typing import List, Optional, Tuple

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


def plot_diurnal_cycle_amplitude_pblh(
    monan_data: xr.Dataset,
    e3sm_data: xr.Dataset,
    monan_var: str = "hpbl",
    e3sm_var: str = "hpbl",
    start_date: np.datetime64 = np.datetime64("2014-02-24"),
    n_days: int = 3,
    cmap_abs: str = "turbo",
    cmap_diff: str = "RdBu_r",
    vmin: float = 0.0,
    vmax: Optional[float] = None,
    diff_limit: Optional[float] = None,
    output_dir: str = "plots/diurnal_amplitude_pblh",
) -> None:
    """Plot daily PBLH diurnal-amplitude maps for MONAN, E3SM, and delta."""
    os.makedirs(output_dir, exist_ok=True)
    daily_amplitudes: List[
        Tuple[np.datetime64, xr.DataArray, xr.DataArray, xr.DataArray]
    ] = []
    for day_idx in range(n_days):
        day_start = start_date + np.timedelta64(day_idx, "D")
        day_str = np.datetime_as_string(day_start, unit="D")
        monan_day = monan_data[monan_var].where(
            monan_data["time"].dt.strftime("%Y-%m-%d") == day_str, drop=True
        )
        e3sm_day = e3sm_data[e3sm_var].where(
            e3sm_data["time"].dt.strftime("%Y-%m-%d") == day_str, drop=True
        )
        if (
            monan_day.sizes.get("time", 0) == 0
            or e3sm_day.sizes.get("time", 0) == 0
        ):
            print(f"Skipping day {day_str}: no time samples.")
            continue
        monan_amp = monan_day.max("time") - monan_day.min("time")
        e3sm_amp = e3sm_day.max("time") - e3sm_day.min("time")
        daily_amplitudes.append(
            (day_start, monan_amp, e3sm_amp, monan_amp - e3sm_amp)
        )
    if len(daily_amplitudes) == 0:
        print("No daily amplitudes computed; check time range and variables.")
        return

    if vmax is None:
        vmax = max(
            float(np.nanmax(a.values)) for _, a, _, _ in daily_amplitudes
        )
        vmax = max(
            vmax,
            max(float(np.nanmax(a.values)) for _, _, a, _ in daily_amplitudes),
        )
        if np.isnan(vmax) or vmax <= vmin:
            vmax = vmin + 1.0
    if diff_limit is None:
        diff_limit = max(
            float(np.nanmax(np.abs(d.values)))
            for _, _, _, d in daily_amplitudes
        )
        if np.isnan(diff_limit) or diff_limit == 0.0:
            diff_limit = 1.0
    abs_norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    diff_norm = mcolors.TwoSlopeNorm(
        vmin=-diff_limit, vcenter=0.0, vmax=diff_limit
    )

    for day_start, monan_amp, e3sm_amp, diff_amp in daily_amplitudes:
        fig, axes = plt.subplots(
            1,
            3,
            figsize=(18, 6),
            subplot_kw={"projection": ccrs.PlateCarree()},
            constrained_layout=True,
        )
        im_monan = axes[0].pcolormesh(
            monan_data["longitude"],
            monan_data["latitude"],
            monan_amp,
            transform=ccrs.PlateCarree(),
            cmap=cmap_abs,
            norm=abs_norm,
        )
        axes[0].set_title("MONAN - Diurnal Amplitude PBLH")
        im_e3sm = axes[1].pcolormesh(
            e3sm_data["longitude"],
            e3sm_data["latitude"],
            e3sm_amp,
            transform=ccrs.PlateCarree(),
            cmap=cmap_abs,
            norm=abs_norm,
        )
        axes[1].set_title("E3SM - Diurnal Amplitude PBLH")
        im_diff = axes[2].pcolormesh(
            monan_data["longitude"],
            monan_data["latitude"],
            diff_amp,
            transform=ccrs.PlateCarree(),
            cmap=cmap_diff,
            norm=diff_norm,
        )
        axes[2].set_title("Delta Amplitude = MONAN - E3SM")
        for idx, ax in enumerate(axes):
            ax.add_feature(cfeature.BORDERS)
            ax.add_feature(cfeature.COASTLINE)
            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            if idx != 0:
                gl.left_labels = False
        units = monan_data[monan_var].attrs.get("units", "")
        cbar_abs = fig.colorbar(
            im_monan,
            ax=[axes[0], axes[1]],
            orientation="horizontal",
            fraction=0.05,
            pad=0.08,
        )
        cbar_abs.set_label(f"Amplitude PBLH [{units}]".rstrip(" []"))
        cbar_diff = fig.colorbar(
            im_diff,
            ax=axes[2],
            orientation="horizontal",
            fraction=0.05,
            pad=0.08,
        )
        cbar_diff.set_label(f"Delta Amplitude [{units}]".rstrip(" []"))
        day_str = np.datetime_as_string(day_start, unit="D")
        fig.suptitle(
            f"Diurnal-Cycle Amplitude of PBLH - {day_str}", fontsize=14
        )
        plt.savefig(
            os.path.join(output_dir, f"diurnal_amplitude_pblh_{day_str}.png"),
            dpi=300,
        )
        plt.close(fig)


def plot_diurnal_peak_phase_pblh(
    monan_data: xr.Dataset,
    e3sm_data: xr.Dataset,
    monan_var: str = "hpbl",
    e3sm_var: str = "hpbl",
    start_date: np.datetime64 = np.datetime64("2014-02-24"),
    n_days: int = 3,
    cmap_phase: str = "twilight",
    cmap_diff: str = "RdBu_r",
    phase_vmin: float = 0.0,
    phase_vmax: float = 23.0,
    diff_limit: float = 12.0,
    output_dir: str = "plots/diurnal_peak_phase_pblh",
) -> None:
    """Plot daily maps of local-hour PBLH peak phase and phase difference."""
    os.makedirs(output_dir, exist_ok=True)
    phase_norm = mcolors.Normalize(vmin=phase_vmin, vmax=phase_vmax)
    diff_norm = mcolors.TwoSlopeNorm(
        vmin=-diff_limit, vcenter=0.0, vmax=diff_limit
    )
    for day_idx in range(n_days):
        day_start = start_date + np.timedelta64(day_idx, "D")
        day_str = np.datetime_as_string(day_start, unit="D")
        monan_day = monan_data[monan_var].where(
            monan_data["time"].dt.strftime("%Y-%m-%d") == day_str, drop=True
        )
        e3sm_day = e3sm_data[e3sm_var].where(
            e3sm_data["time"].dt.strftime("%Y-%m-%d") == day_str, drop=True
        )
        if (
            monan_day.sizes.get("time", 0) == 0
            or e3sm_day.sizes.get("time", 0) == 0
        ):
            print(f"Skipping day {day_str}: no time samples.")
            continue
        monan_peak_hour = monan_day.idxmax("time").dt.hour
        e3sm_peak_hour = e3sm_day.idxmax("time").dt.hour
        diff_phase = ((monan_peak_hour - e3sm_peak_hour + 12) % 24) - 12
        fig, axes = plt.subplots(
            1,
            3,
            figsize=(18, 6),
            subplot_kw={"projection": ccrs.PlateCarree()},
            constrained_layout=True,
        )
        im_monan = axes[0].pcolormesh(
            monan_data["longitude"],
            monan_data["latitude"],
            monan_peak_hour,
            transform=ccrs.PlateCarree(),
            cmap=cmap_phase,
            norm=phase_norm,
        )
        axes[0].set_title("Peak Hour MONAN")
        im_e3sm = axes[1].pcolormesh(
            e3sm_data["longitude"],
            e3sm_data["latitude"],
            e3sm_peak_hour,
            transform=ccrs.PlateCarree(),
            cmap=cmap_phase,
            norm=phase_norm,
        )
        axes[1].set_title("Peak Hour E3SM")
        im_diff = axes[2].pcolormesh(
            monan_data["longitude"],
            monan_data["latitude"],
            diff_phase,
            transform=ccrs.PlateCarree(),
            cmap=cmap_diff,
            norm=diff_norm,
        )
        axes[2].set_title("Phase Difference (MONAN - E3SM)")
        for idx, ax in enumerate(axes):
            ax.add_feature(cfeature.BORDERS)
            ax.add_feature(cfeature.COASTLINE)
            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            if idx != 0:
                gl.left_labels = False
        cbar_phase = fig.colorbar(
            im_monan,
            ax=[axes[0], axes[1]],
            orientation="horizontal",
            fraction=0.05,
            pad=0.08,
            ticks=np.arange(0, 24, 3),
        )
        cbar_phase.set_label("Peak Hour (local model hour)")
        cbar_diff = fig.colorbar(
            im_diff,
            ax=axes[2],
            orientation="horizontal",
            fraction=0.05,
            pad=0.08,
            ticks=np.arange(-12, 13, 3),
        )
        cbar_diff.set_label("Phase Difference [hour]")
        fig.suptitle(f"Diurnal Peak Phase of PBLH - {day_str}", fontsize=14)
        plt.savefig(
            os.path.join(output_dir, f"diurnal_peak_phase_pblh_{day_str}.png"),
            dpi=300,
        )
        plt.close(fig)
