import gc
import os
from typing import List, Optional, Sequence, Tuple, Union

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.axes import Axes
from matplotlib.collections import QuadMesh
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


TimeSelector = Union[np.datetime64, Sequence[np.datetime64]]


def _spatial_select_in_bbox(
    ds: xr.Dataset,
    var_names: Sequence[str],
    start_date: np.datetime64,
    end_date: np.datetime64,
    lat_name: str,
    lon_name: str,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
) -> xr.Dataset:
    """Select a time window and subset data over a lat/lon bounding box."""
    lat_lo, lat_hi = sorted((lat_min, lat_max))
    lon_lo, lon_hi = sorted((lon_min, lon_max))
    subset = ds[var_names].sel(
        time=slice(start_date, end_date),
        **{
            lat_name: slice(lat_lo, lat_hi),
            lon_name: slice(lon_lo, lon_hi),
        },
    ).compute()
    if (
        subset.sizes.get(lat_name, 0) == 0
        or subset.sizes.get(lon_name, 0) == 0
    ):
        raise ValueError("No points found inside the selected bounding box.")

    return subset


def _solar_offset_hours(point_lon: float) -> int:
    """Approximate solar-time offset from longitude (15 deg ~= 1 hour)."""
    point_lon_norm = ((point_lon + 180.0) % 360.0) - 180.0
    return int(np.round(point_lon_norm / 15.0))


def _ensure_dim_order(
    data: xr.DataArray, first_dim: str, second_dim: str
) -> xr.DataArray:
    """Return data with dimensions ordered as (first_dim, second_dim)."""
    expected_dims = (first_dim, second_dim)
    if data.dims == expected_dims:
        return data
    return data.transpose(*expected_dims)


def _height_to_pressure_hpa(height_m: np.ndarray) -> np.ndarray:
    """Convert geometric height (m) to pressure (hPa) using ISA formula."""
    height = np.asarray(height_m, dtype=float)
    return 1013.25 * np.power(
        np.clip(1.0 - 2.25577e-5 * height, 1e-6, None), 5.25588
    )


def _build_contour_levels(
    field_2d: np.ndarray, n_levels: int = 5
) -> Optional[np.ndarray]:
    """Create evenly spaced contour levels, or ``None`` if field is flat."""
    field_min = float(np.nanmin(field_2d))
    field_max = float(np.nanmax(field_2d))
    if np.isnan(field_min) or np.isnan(field_max) or field_min == field_max:
        return None
    return np.linspace(field_min, field_max, n_levels)


def _compute_hfx_limits(
    monan_hfx: np.ndarray, e3sm_hfx: np.ndarray
) -> Tuple[float, float]:
    """Return shared y-axis limits for MONAN/E3SM HFX curves plus padding."""
    hfx_min = min(float(np.nanmin(monan_hfx)), float(np.nanmin(e3sm_hfx)))
    hfx_max = max(float(np.nanmax(monan_hfx)), float(np.nanmax(e3sm_hfx)))
    if np.isnan(hfx_min) or np.isnan(hfx_max) or hfx_min == hfx_max:
        return -1.0, 1.0
    hfx_pad = 0.05 * (hfx_max - hfx_min)
    return hfx_min - hfx_pad, hfx_max + hfx_pad


def _plot_vertical_panel(
    ax: Axes,
    x_coord: np.ndarray,
    y_pressure: np.ndarray,
    tke_2d: np.ndarray,
    qc_2d: np.ndarray,
    qc_levels: Optional[np.ndarray],
    pblh_pressure: np.ndarray,
    hours_arr: np.ndarray,
    p_max_common: float,
    p_top_plot: float,
    title: str,
    pblh_label: str,
    tke_norm: mcolors.Normalize,
) -> QuadMesh:
    """Plot one model panel with TKE shading, QC contours, and PBLH line."""
    im = ax.pcolormesh(
        x_coord,
        y_pressure,
        tke_2d,
        cmap="viridis",
        norm=tke_norm,
        shading="auto",
    )
    if qc_levels is not None:
        cs = ax.contour(
            x_coord,
            y_pressure,
            qc_2d,
            levels=qc_levels,
            colors="white",
            linewidths=0.8,
            alpha=0.8,
        )
        ax.clabel(cs, inline=True, fontsize=7, fmt="%.1e")
    ax.plot(
        hours_arr,
        pblh_pressure,
        color="black",
        linewidth=2,
        label=f"{pblh_label.upper()} (pressure-equivalent)",
    )
    ax.set_title(title)
    ax.set_xlabel("Local hour")
    ax.set_ylabel("pressure [hPa]")
    ax.invert_yaxis()
    ax.set_ylim(p_max_common, p_top_plot)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(np.arange(0, 24, 3))
    ax.set_xlim(0, 23)
    ax.legend(loc="upper right")
    return im


def _plot_hfx_panel(
    ax: Axes,
    hours_arr: np.ndarray,
    hfx_1d: np.ndarray,
    title: str,
    ylabel: str,
    y_min: float,
    y_max: float,
) -> None:
    """Plot hourly sensible heat flux line for one model."""
    ax.plot(hours_arr, hfx_1d, color="tab:red", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel("Local hour")
    ax.set_ylabel(ylabel)
    ax.set_ylim(y_min, y_max)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(np.arange(0, 24, 3))
    ax.set_xlim(0, 23)


def plot_vertical_profile_tke_hourly_mean(
    monan_data: xr.Dataset,
    e3sm_data: xr.Dataset,
    point_lat: float,
    point_lon: float,
    region_name: str,
    monan_var: str = "tke_pbl",
    e3sm_var: str = "tke",
    monan_pblh_var: str = "hpbl",
    e3sm_pblh_var: str = "hpbl",
    monan_qc_var: str = "qc",
    e3sm_qc_var: str = "qc",
    monan_hfx_var: str = "hfx",
    e3sm_hfx_var: str = "hfx",
    start_date: np.datetime64 = np.datetime64("2014-02-24T00:00"),
    n_days: int = 3,
    half_box_deg: float = 0.5,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    output_dir: str = "plots/tke_vertical_profile_hourly_mean",
) -> None:
    """Plot hourly-mean TKE profile panels and HFX series for MONAN vs E3SM."""
    os.makedirs(output_dir, exist_ok=True)
    end_date = start_date + np.timedelta64(n_days, "D")
    lat_min = max(-90.0, point_lat - half_box_deg)
    lat_max = min(90.0, point_lat + half_box_deg)
    lon_min = max(-180.0, point_lon - half_box_deg)
    lon_max = min(180.0, point_lon + half_box_deg)

    monan_lon_name = "longitude" if "longitude" in monan_data else "lon"
    monan_lat_name = "latitude" if "latitude" in monan_data else "lat"
    e3sm_lon_name = "longitude" if "longitude" in e3sm_data else "lon"
    e3sm_lat_name = "latitude" if "latitude" in e3sm_data else "lat"

    monan_vars = [
        monan_var,
        "pressure",
        monan_pblh_var,
        monan_qc_var,
        monan_hfx_var,
    ]
    e3sm_vars = [e3sm_var, e3sm_pblh_var, e3sm_qc_var, e3sm_hfx_var]

    monan_sel_data = _spatial_select_in_bbox(
        monan_data,
        monan_vars,
        start_date,
        end_date,
        monan_lat_name,
        monan_lon_name,
        lat_min,
        lat_max,
        lon_min,
        lon_max,
    )
    e3sm_sel_data = _spatial_select_in_bbox(
        e3sm_data,
        e3sm_vars,
        start_date,
        end_date,
        e3sm_lat_name,
        e3sm_lon_name,
        lat_min,
        lat_max,
        lon_min,
        lon_max,
    )
    if (
        monan_sel_data.sizes.get("time", 0) == 0
        or e3sm_sel_data.sizes.get("time", 0) == 0
    ):
        print("No data in selected time range for vertical TKE profile.")
        return
    monan_sel_data = monan_sel_data.mean(
        dim=[monan_lat_name, monan_lon_name], skipna=True
    )
    e3sm_sel_data = e3sm_sel_data.mean(
        dim=[e3sm_lat_name, e3sm_lon_name], skipna=True
    )

    solar_offset_hours = _solar_offset_hours(point_lon)
    solar_offset = np.timedelta64(solar_offset_hours, "h")
    monan_sel_data = monan_sel_data.assign_coords(
        time=monan_sel_data["time"] + solar_offset
    )
    e3sm_sel_data = e3sm_sel_data.assign_coords(
        time=e3sm_sel_data["time"] + solar_offset
    )

    monan_hourly_data = monan_sel_data.groupby("time.hour").mean("time")
    e3sm_hourly_data = e3sm_sel_data.groupby("time.hour").mean("time")
    monan_hourly = monan_hourly_data[monan_var]
    e3sm_hourly = e3sm_hourly_data[e3sm_var]
    monan_zdim = (
        "level"
        if "level" in monan_hourly.dims
        else next(dim for dim in monan_hourly.dims if dim != "hour")
    )
    e3sm_zdim = (
        "lev"
        if "lev" in e3sm_hourly.dims
        else next(dim for dim in e3sm_hourly.dims if dim != "hour")
    )

    hours = sorted(
        set(monan_hourly["hour"].values.tolist())
        & set(e3sm_hourly["hour"].values.tolist())
    )
    if not hours:
        print("No overlapping hourly bins found between MONAN and E3SM.")
        return

    monan_hourly_ds = (
        xr.Dataset(
            {
                "tke": monan_hourly,
                "pressure_hpa": monan_hourly_data["pressure"] / 100.0,
                "pblh": monan_hourly_data[monan_pblh_var],
                "qc": monan_hourly_data[monan_qc_var],
                "hfx": monan_hourly_data[monan_hfx_var],
            }
        )
        .sel(hour=hours)
        .compute()
    )
    e3sm_hourly_ds = (
        xr.Dataset(
            {
                "tke": e3sm_hourly,
                "pblh": e3sm_hourly_data[e3sm_pblh_var],
                "qc": e3sm_hourly_data[e3sm_qc_var],
                "hfx": e3sm_hourly_data[e3sm_hfx_var],
            }
        )
        .sel(hour=hours)
        .compute()
    )

    hours_arr = np.asarray(hours)
    monan_tke_2d = _ensure_dim_order(
        monan_hourly_ds["tke"], monan_zdim, "hour"
    ).to_numpy()
    monan_pressure_2d = _ensure_dim_order(
        monan_hourly_ds["pressure_hpa"], monan_zdim, "hour"
    ).to_numpy()
    monan_hours_2d = np.broadcast_to(hours_arr, monan_tke_2d.shape)
    monan_qc_2d = _ensure_dim_order(
        monan_hourly_ds["qc"], monan_zdim, "hour"
    ).to_numpy()
    monan_pblh_pressure = _height_to_pressure_hpa(
        monan_hourly_ds["pblh"].to_numpy()
    )
    monan_hfx_1d = monan_hourly_ds["hfx"].to_numpy()

    e3sm_tke_2d = _ensure_dim_order(
        e3sm_hourly_ds["tke"], e3sm_zdim, "hour"
    ).to_numpy()
    e3sm_pressure = e3sm_hourly_ds["tke"][e3sm_zdim].to_numpy()
    e3sm_qc_2d = _ensure_dim_order(
        e3sm_hourly_ds["qc"], e3sm_zdim, "hour"
    ).to_numpy()
    e3sm_pblh_pressure = _height_to_pressure_hpa(
        e3sm_hourly_ds["pblh"].to_numpy()
    )
    e3sm_hfx_1d = e3sm_hourly_ds["hfx"].to_numpy()

    monan_p_min = float(np.nanmin(monan_pressure_2d))
    monan_p_max = float(np.nanmax(monan_pressure_2d))
    e3sm_p_min = float(np.nanmin(e3sm_pressure))
    e3sm_p_max = float(np.nanmax(e3sm_pressure))
    p_min_common = max(monan_p_min, e3sm_p_min)
    p_max_common = min(monan_p_max, e3sm_p_max)
    if p_min_common >= p_max_common:
        raise ValueError(
            "No overlapping pressure interval between MONAN and E3SM at the "
            "selected point."
        )
    p_top_plot = (
        max(p_min_common, 400.0) if p_max_common > 400.0 else p_min_common
    )

    if not vmin:
        tke_min = min(
            float(np.nanmin(monan_tke_2d)), float(np.nanmin(e3sm_tke_2d))
        )
    else:
        tke_min = vmin
    if not vmax:
        tke_max = max(
            float(np.nanmax(monan_tke_2d)), float(np.nanmax(e3sm_tke_2d))
        )
    else:
        tke_max = vmax
    if np.isnan(tke_min) or np.isnan(tke_max) or tke_min == tke_max:
        tke_min, tke_max = 0.0, 1.0
    tke_norm = mcolors.Normalize(vmin=tke_min, vmax=tke_max)

    monan_qc_levels = _build_contour_levels(monan_qc_2d, n_levels=5)
    e3sm_qc_levels = _build_contour_levels(e3sm_qc_2d, n_levels=5)
    hfx_min, hfx_max = _compute_hfx_limits(monan_hfx_1d, e3sm_hfx_1d)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12), constrained_layout=True)
    _plot_vertical_panel(
        axes[0, 0],
        monan_hours_2d,
        monan_pressure_2d,
        monan_tke_2d,
        monan_qc_2d,
        monan_qc_levels,
        monan_pblh_pressure,
        hours_arr,
        p_max_common,
        p_top_plot,
        "MONAN - TKE Hourly Mean",
        monan_pblh_var,
        tke_norm,
    )
    im_e3sm = _plot_vertical_panel(
        axes[0, 1],
        hours_arr,
        e3sm_pressure,
        e3sm_tke_2d,
        e3sm_qc_2d,
        e3sm_qc_levels,
        e3sm_pblh_pressure,
        hours_arr,
        p_max_common,
        p_top_plot,
        "E3SM - TKE Hourly Mean",
        e3sm_pblh_var,
        tke_norm,
    )

    _plot_hfx_panel(
        axes[1, 0],
        hours_arr,
        monan_hfx_1d,
        "MONAN - Sensible Heat Flux Hourly Mean",
        "Sensible Heat Flux [W/m²]",
        hfx_min,
        hfx_max,
    )
    _plot_hfx_panel(
        axes[1, 1],
        hours_arr,
        e3sm_hfx_1d,
        "E3SM - Sensible Heat Flux Hourly Mean",
        "Sensible Heat Flux [W/m²]",
        hfx_min,
        hfx_max,
    )
    cbar = fig.colorbar(
        im_e3sm,
        ax=[axes[0, 0], axes[0, 1]],
        orientation="horizontal",
        fraction=0.05,
        pad=0.08,
    )
    cbar.set_label("TKE")
    lat_str = f"{abs(point_lat):.2f}°{'N' if point_lat >= 0 else 'S'}"
    lon_str = f"{abs(point_lon):.2f}°{'E' if point_lon >= 0 else 'W'}"
    plt.suptitle(
        (
            f"TKE Vertical Profile Hourly Mean - "
            f"{region_name} ({lat_str}, {lon_str}), "
            f"UTC{solar_offset_hours:+d}"
        ),
        fontsize=12,
    )
    out_file = os.path.join(
        output_dir,
        (
            "tke_vertical_profile_hourly_mean_"
            f"lat{point_lat:.2f}_lon{point_lon:.2f}_"
            f"box{half_box_deg:.2f}_"
            f"{np.datetime_as_string(start_date, unit='D')}_{n_days}d.png"
        ),
    )
    plt.savefig(out_file, dpi=300)
    plt.close(fig)
    del monan_sel_data
    del e3sm_sel_data
    del monan_hourly_data
    del e3sm_hourly_data
    del monan_hourly_ds
    del e3sm_hourly_ds
    del monan_tke_2d
    del monan_pressure_2d
    del monan_hours_2d
    del monan_qc_2d
    del monan_pblh_pressure
    del monan_hfx_1d
    del e3sm_tke_2d
    del e3sm_pressure
    del e3sm_qc_2d
    del e3sm_pblh_pressure
    del e3sm_hfx_1d
    del fig
    del axes
    gc.collect()


def _haversine_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Return great-circle distance between two points in km."""
    dlon = ((lon2 - lon1 + 180.0) % 360.0) - 180.0
    lat1_rad = np.deg2rad(lat1)
    lat2_rad = np.deg2rad(lat2)
    dlat_rad = np.deg2rad(lat2 - lat1)
    dlon_rad = np.deg2rad(dlon)
    a = (
        np.sin(dlat_rad / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon_rad / 2.0) ** 2
    )
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(6371.0 * c)


def _nearest_lon_index(lon_values: np.ndarray, lon_target: float) -> int:
    """Return index of nearest longitude accounting for wrap-around."""
    lon_delta = ((lon_values - lon_target + 180.0) % 360.0) - 180.0
    return int(np.argmin(np.abs(lon_delta)))


def _pressure_to_hpa(pressure_values: np.ndarray) -> np.ndarray:
    """Convert pressure array to hPa if values look like Pa."""
    if float(np.nanmax(pressure_values)) > 2000.0:
        return pressure_values / 100.0
    return pressure_values


def _format_latlon(lat: float, lon: float) -> str:
    """Format latitude/longitude with hemisphere suffixes."""
    lat_hemi = "N" if lat >= 0.0 else "S"
    lon_hemi = "E" if lon >= 0.0 else "W"
    return f"{abs(lat):.2f}°{lat_hemi}, {abs(lon):.2f}°{lon_hemi}"


def _detect_coord_names(ds: xr.Dataset) -> Tuple[str, str]:
    """Return latitude/longitude coordinate names present in dataset."""
    lat_name = "latitude" if "latitude" in ds.coords else "lat"
    lon_name = "longitude" if "longitude" in ds.coords else "lon"
    if lat_name not in ds.coords or lon_name not in ds.coords:
        raise ValueError(
            "Dataset must provide latitude/longitude or lat/lon coordinates."
        )
    return lat_name, lon_name


def _extract_profile_at_point(
    ds: xr.Dataset,
    var_name: str,
    time: TimeSelector,
    lat_name: str,
    lon_name: str,
    lat_idx: int,
    lon_idx: int,
) -> xr.DataArray:
    """Extract a single-time, single-point profile and squeeze singleton dims."""
    if var_name not in ds:
        raise KeyError(f"Variable '{var_name}' not found in dataset.")
    data = ds[var_name]
    if "time" in data.dims or "time" in data.coords:
        if isinstance(time, np.datetime64):
            data = data.sel(time=time)
        else:
            time_array = np.asarray(time, dtype="datetime64[ns]")
            if time_array.ndim != 1 or time_array.size == 0:
                raise ValueError(
                    "When time is a sequence, it must be a non-empty 1D list."
                )
            data = data.sel(time=time_array).mean("time", skipna=True)
    if lat_name in data.dims:
        data = data.isel(**{lat_name: lat_idx})
    if lon_name in data.dims:
        data = data.isel(**{lon_name: lon_idx})
    profile = data.squeeze(drop=True)
    if profile.ndim != 1:
        raise ValueError(
            f"Variable '{var_name}' at point/time must be 1D, got {profile.dims}."
        )
    return profile


def _build_cloud_mask(
    ds: xr.Dataset,
    cloud_liquid_var: str,
    time: TimeSelector,
    lat_name: str,
    lon_name: str,
    lat_idx: int,
    lon_idx: int,
    zdim: str,
) -> np.ndarray:
    """Build cloud mask (ql > 1e-5) aligned to vertical dimension."""
    ql_profile = _extract_profile_at_point(
        ds=ds,
        var_name=cloud_liquid_var,
        time=time,
        lat_name=lat_name,
        lon_name=lon_name,
        lat_idx=lat_idx,
        lon_idx=lon_idx,
    )
    if zdim not in ql_profile.dims:
        raise ValueError(
            f"Cloud variable '{cloud_liquid_var}' does not use '{zdim}' dimension."
        )
    return (ql_profile.transpose(zdim).to_numpy() > 1e-5).astype(bool)


def plot_vertical_profiles_panel_at_point(
    dataset_1: xr.Dataset,
    point_lat: float,
    point_lon: float,
    time: TimeSelector,
    var_names_1: Sequence[str],
    panel_labels: Sequence[str],
    x_units: Sequence[str],
    vertical_axis: str = "pressure",
    dataset_2: Optional[xr.Dataset] = None,
    var_names_2: Optional[Sequence[str]] = None,
    pressure_var_1: str = "pressure",
    pressure_var_2: str = "pressure",
    height_var_1: Optional[str] = None,
    height_var_2: Optional[str] = None,
    shade_cloud_layer: bool = False,
    cloud_liquid_var_1: Optional[str] = None,
    cloud_liquid_var_2: Optional[str] = None,
    cloud_hatch_target: str = "dataset_1",
    dataset_1_label: str = "Dataset 1",
    dataset_2_label: str = "Dataset 2",
    output_dir: str = "plots/vertical_profiles_panel",
    output_name_prefix: str = "vertical_profiles_panel",
) -> None:
    """Plot 3-4 vertical-profile panels at nearest grid point for one/many times."""
    n_panels = len(var_names_1)
    if n_panels not in (3, 4):
        raise ValueError("var_names_1 must contain exactly 3 or 4 variables.")
    if len(panel_labels) != n_panels or len(x_units) != n_panels:
        raise ValueError(
            "panel_labels and x_units must have same length as var_names_1."
        )
    if dataset_2 is not None:
        if var_names_2 is None:
            var_names_2 = var_names_1
        if len(var_names_2) != n_panels:
            raise ValueError(
                "var_names_2 must match var_names_1 length when dataset_2 is used."
            )
    if vertical_axis not in ("pressure", "height"):
        raise ValueError("vertical_axis must be 'pressure' or 'height'.")
    if shade_cloud_layer:
        valid_targets = {"dataset_1", "dataset_2", "both"}
        if cloud_hatch_target not in valid_targets:
            raise ValueError(
                "cloud_hatch_target must be one of: dataset_1, dataset_2, both."
            )
        if cloud_hatch_target in {"dataset_1", "both"} and not cloud_liquid_var_1:
            raise ValueError(
                "cloud_liquid_var_1 is required for cloud hatching in dataset_1."
            )
        if (
            cloud_hatch_target in {"dataset_2", "both"}
            and dataset_2 is None
        ):
            raise ValueError(
                "dataset_2 is required when cloud_hatch_target uses dataset_2."
            )
        if cloud_hatch_target in {"dataset_2", "both"} and not cloud_liquid_var_2:
            raise ValueError(
                "cloud_liquid_var_2 is required for cloud hatching in dataset_2."
            )

    os.makedirs(output_dir, exist_ok=True)

    lat_name_1, lon_name_1 = _detect_coord_names(dataset_1)
    lat_values_1 = np.asarray(dataset_1[lat_name_1].to_numpy(), dtype=float)
    lon_values_1 = np.asarray(dataset_1[lon_name_1].to_numpy(), dtype=float)
    lat_idx_1 = int(np.argmin(np.abs(lat_values_1 - point_lat)))
    lon_idx_1 = _nearest_lon_index(lon_values_1, point_lon)
    grid_lat_1 = float(lat_values_1[lat_idx_1])
    grid_lon_1 = float((((lon_values_1[lon_idx_1] + 180.0) % 360.0) - 180.0))

    y_var_1 = pressure_var_1 if vertical_axis == "pressure" else height_var_1
    if y_var_1 is None:
        raise ValueError(
            "height_var_1 must be provided when vertical_axis='height'."
        )
    y_profile_1 = _extract_profile_at_point(
        ds=dataset_1,
        var_name=y_var_1,
        time=time,
        lat_name=lat_name_1,
        lon_name=lon_name_1,
        lat_idx=lat_idx_1,
        lon_idx=lon_idx_1,
    )
    zdim_1 = y_profile_1.dims[0]
    y_values_1 = y_profile_1.transpose(zdim_1).to_numpy()
    if vertical_axis == "pressure":
        y_values_1 = _pressure_to_hpa(y_values_1)

    profiles_1: List[np.ndarray] = []
    for var_name in var_names_1:
        profile = _extract_profile_at_point(
            ds=dataset_1,
            var_name=var_name,
            time=time,
            lat_name=lat_name_1,
            lon_name=lon_name_1,
            lat_idx=lat_idx_1,
            lon_idx=lon_idx_1,
        )
        if zdim_1 not in profile.dims:
            raise ValueError(
                f"Variable '{var_name}' does not share vertical dim '{zdim_1}'."
            )
        profiles_1.append(profile.transpose(zdim_1).to_numpy())

    y_values_2 = None
    profiles_2: Optional[List[np.ndarray]] = None
    grid_lat_2 = None
    grid_lon_2 = None
    zdim_2 = None
    lat_name_2 = ""
    lon_name_2 = ""
    lat_idx_2 = -1
    lon_idx_2 = -1

    if dataset_2 is not None and var_names_2 is not None:
        lat_name_2, lon_name_2 = _detect_coord_names(dataset_2)
        lat_values_2 = np.asarray(dataset_2[lat_name_2].to_numpy(), dtype=float)
        lon_values_2 = np.asarray(dataset_2[lon_name_2].to_numpy(), dtype=float)
        lat_idx_2 = int(np.argmin(np.abs(lat_values_2 - point_lat)))
        lon_idx_2 = _nearest_lon_index(lon_values_2, point_lon)
        grid_lat_2 = float(lat_values_2[lat_idx_2])
        grid_lon_2 = float(
            (((lon_values_2[lon_idx_2] + 180.0) % 360.0) - 180.0)
        )

        y_var_2 = pressure_var_2 if vertical_axis == "pressure" else height_var_2
        if y_var_2 is None:
            raise ValueError(
                "height_var_2 must be provided when vertical_axis='height'."
            )
        y_profile_2 = _extract_profile_at_point(
            ds=dataset_2,
            var_name=y_var_2,
            time=time,
            lat_name=lat_name_2,
            lon_name=lon_name_2,
            lat_idx=lat_idx_2,
            lon_idx=lon_idx_2,
        )
        zdim_2 = y_profile_2.dims[0]
        y_values_2 = y_profile_2.transpose(zdim_2).to_numpy()
        if vertical_axis == "pressure":
            y_values_2 = _pressure_to_hpa(y_values_2)

        profiles_2 = []
        for var_name in var_names_2:
            profile = _extract_profile_at_point(
                ds=dataset_2,
                var_name=var_name,
                time=time,
                lat_name=lat_name_2,
                lon_name=lon_name_2,
                lat_idx=lat_idx_2,
                lon_idx=lon_idx_2,
            )
            if zdim_2 not in profile.dims:
                raise ValueError(
                    f"Variable '{var_name}' does not share vertical dim '{zdim_2}'."
                )
            profiles_2.append(profile.transpose(zdim_2).to_numpy())

    cloud_mask_1 = None
    cloud_mask_2 = None
    if shade_cloud_layer and cloud_hatch_target in {"dataset_1", "both"}:
        cloud_mask_1 = _build_cloud_mask(
            ds=dataset_1,
            cloud_liquid_var=cloud_liquid_var_1,  # type: ignore[arg-type]
            time=time,
            lat_name=lat_name_1,
            lon_name=lon_name_1,
            lat_idx=lat_idx_1,
            lon_idx=lon_idx_1,
            zdim=zdim_1,
        )
    if shade_cloud_layer and cloud_hatch_target in {"dataset_2", "both"}:
        if dataset_2 is None or zdim_2 is None:
            raise ValueError("dataset_2 must be set for dataset_2 cloud hatching.")
        cloud_mask_2 = _build_cloud_mask(
            ds=dataset_2,
            cloud_liquid_var=cloud_liquid_var_2,  # type: ignore[arg-type]
            time=time,
            lat_name=lat_name_2,
            lon_name=lon_name_2,
            lat_idx=lat_idx_2,
            lon_idx=lon_idx_2,
            zdim=zdim_2,
        )

    if n_panels == 4:
        fig, axes_grid = plt.subplots(2, 2, figsize=(10.8, 10))
        axes = list(np.ravel(axes_grid))
    else:
        fig, axes = plt.subplots(1, n_panels, figsize=(4.5 * n_panels, 8))
        if n_panels == 1:
            axes = [axes]

    y_label = "Pressure [hPa]" if vertical_axis == "pressure" else "Height [m]"
    pressure_surface_hpa = None
    pressure_top_hpa = 700.0
    if vertical_axis == "pressure":
        pressure_surface_hpa = float(np.nanmax(y_values_1))
        if y_values_2 is not None:
            pressure_surface_hpa = max(
                pressure_surface_hpa, float(np.nanmax(y_values_2))
            )

    for idx, ax in enumerate(axes):
        if vertical_axis == "pressure":
            if pressure_surface_hpa is None:
                raise ValueError("Unable to infer surface pressure for y-axis.")
            mask_1 = (
                (y_values_1 >= pressure_top_hpa)
                & (y_values_1 <= pressure_surface_hpa)
                & np.isfinite(y_values_1)
                & np.isfinite(profiles_1[idx])
            )
            series_minmax = [profiles_1[idx][mask_1]]
            if profiles_2 is not None and y_values_2 is not None:
                mask_2 = (
                    (y_values_2 >= pressure_top_hpa)
                    & (y_values_2 <= pressure_surface_hpa)
                    & np.isfinite(y_values_2)
                    & np.isfinite(profiles_2[idx])
                )
                series_minmax.append(profiles_2[idx][mask_2])
            series_minmax = [arr for arr in series_minmax if arr.size > 0]
            if not series_minmax:
                series_minmax = [profiles_1[idx][np.isfinite(profiles_1[idx])]]
                if profiles_2 is not None:
                    series_minmax.append(
                        profiles_2[idx][np.isfinite(profiles_2[idx])]
                    )
        else:
            series_minmax = [profiles_1[idx]]
            if profiles_2 is not None:
                series_minmax.append(profiles_2[idx])
        xmin = min(float(np.nanmin(arr)) for arr in series_minmax)
        xmax = max(float(np.nanmax(arr)) for arr in series_minmax)
        if not np.isfinite(xmin) or not np.isfinite(xmax):
            xmin, xmax = -1.0, 1.0
        if xmin == xmax:
            xmin -= 0.5
            xmax += 0.5
        xpad = 0.05 * (xmax - xmin)
        xmin -= xpad
        xmax += xpad

        if shade_cloud_layer and cloud_mask_1 is not None:
            ax.fill_betweenx(
                y_values_1,
                xmin,
                xmax,
                where=cloud_mask_1,
                facecolor="none",
                hatch="///",
                edgecolor="0.5",
                linewidth=0.0,
                alpha=0.8,
            )
        if shade_cloud_layer and cloud_mask_2 is not None and y_values_2 is not None:
            ax.fill_betweenx(
                y_values_2,
                xmin,
                xmax,
                where=cloud_mask_2,
                facecolor="none",
                hatch="\\\\\\",
                edgecolor="0.3",
                linewidth=0.0,
                alpha=0.8,
            )

        ax.plot(
            profiles_1[idx],
            y_values_1,
            color="tab:blue",
            linewidth=2.0,
            label=dataset_1_label,
        )
        if profiles_2 is not None and y_values_2 is not None:
            ax.plot(
                profiles_2[idx],
                y_values_2,
                color="tab:orange",
                linewidth=2.0,
                label=dataset_2_label,
            )

        if x_units[idx]:
            ax.set_xlabel(f"{panel_labels[idx]} [{x_units[idx]}]")
        else:
            ax.set_xlabel(panel_labels[idx])
        if (n_panels == 4 and idx in (0, 2)) or (n_panels != 4 and idx == 0):
            ax.set_ylabel(y_label)
        ax.grid(alpha=0.3)
        ax.set_xlim(xmin, xmax)
        if vertical_axis == "pressure":
            if pressure_surface_hpa is None:
                raise ValueError("Unable to infer surface pressure for y-axis.")
            ax.set_ylim(pressure_surface_hpa, pressure_top_hpa)

    legend_handles: List[object] = [
        Line2D([0], [0], color="tab:blue", lw=2, label=dataset_1_label)
    ]
    if dataset_2 is not None:
        legend_handles.append(
            Line2D([0], [0], color="tab:orange", lw=2, label=dataset_2_label)
        )
    if shade_cloud_layer and cloud_mask_1 is not None:
        legend_handles.append(
            Patch(
                facecolor="none",
                hatch="///",
                edgecolor="0.5",
                label=f"Cloud layer ({dataset_1_label}, ql > 1e-5)",
            )
        )
    if shade_cloud_layer and cloud_mask_2 is not None:
        legend_handles.append(
            Patch(
                facecolor="none",
                hatch="\\\\\\",
                edgecolor="0.3",
                label=f"Cloud layer ({dataset_2_label}, ql > 1e-5)",
            )
        )
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        ncol=2,
    )

    ds1_coord = _format_latlon(grid_lat_1, grid_lon_1)
    if isinstance(time, np.datetime64):
        time_str = np.datetime_as_string(np.datetime64(time, "m"), unit="m")
    else:
        time_array = np.asarray(time, dtype="datetime64[ns]")
        if time_array.ndim != 1 or time_array.size == 0:
            raise ValueError(
                "When time is a sequence, it must be a non-empty 1D list."
            )
        tmin = np.datetime_as_string(np.datetime64(time_array.min(), "m"), unit="m")
        tmax = np.datetime_as_string(np.datetime64(time_array.max(), "m"), unit="m")
        time_str = f"mean {tmin} to {tmax} (n={time_array.size})"
    fig.suptitle(
        f"Vertical Profiles at {time_str} ({ds1_coord})",
        fontsize=11,
        y=0.97,
    )
    plt.tight_layout(rect=[0.0, 0.06, 1.0, 0.95])

    time_tag = (
        time_str.replace(":", "-")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
    )
    out_file = os.path.join(
        output_dir,
        (
            f"{output_name_prefix}_"
            f"lat{point_lat:+06.2f}_lon{point_lon:+07.2f}_"
            f"{vertical_axis}_{time_tag}.png"
        ),
    )
    plt.savefig(out_file, dpi=300)
    plt.close(fig)


def plot_cross_section_transect(
    monan_data: xr.Dataset,
    e3sm_data: xr.Dataset,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    start_date: np.datetime64,
    end_date: np.datetime64,
    monan_var: str = "tke_pbl",
    e3sm_var: str = "tke_pbl",
    monan_qc_var: str = "qc",
    e3sm_qc_var: str = "qc",
    monan_pressure_var: str = "pressure",
    grid_resolution_km: float = 30.0,
    qc_contour_min: float = 1e-5,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    output_dir: str = "plots/cross_section_transect",
) -> None:
    """Plot MONAN/E3SM vertical transect for each hour in a time range."""
    os.makedirs(output_dir, exist_ok=True)

    if grid_resolution_km <= 0.0:
        raise ValueError("grid_resolution_km must be greater than zero.")
    if end_date < start_date:
        raise ValueError(
            "end_date must be greater than or equal to start_date."
        )

    monan_lon_name = "longitude" if "longitude" in monan_data else "lon"
    monan_lat_name = "latitude" if "latitude" in monan_data else "lat"
    e3sm_lon_name = "longitude" if "longitude" in e3sm_data else "lon"
    e3sm_lat_name = "latitude" if "latitude" in e3sm_data else "lat"

    monan_lat_vals = np.asarray(
        monan_data[monan_lat_name].to_numpy(), dtype=float
    )
    monan_lon_vals = np.asarray(
        monan_data[monan_lon_name].to_numpy(), dtype=float
    )
    e3sm_lat_vals = np.asarray(
        e3sm_data[e3sm_lat_name].to_numpy(), dtype=float
    )
    e3sm_lon_vals = np.asarray(
        e3sm_data[e3sm_lon_name].to_numpy(), dtype=float
    )

    transect_length_km = _haversine_distance_km(
        start_lat, start_lon, end_lat, end_lon
    )
    n_points_req = max(
        2, int(np.ceil(transect_length_km / grid_resolution_km)) + 1
    )

    dlon = ((end_lon - start_lon + 180.0) % 360.0) - 180.0
    line_frac = np.linspace(0.0, 1.0, n_points_req)
    line_lat = start_lat + (end_lat - start_lat) * line_frac
    line_lon = start_lon + dlon * line_frac

    selected_keys: List[Tuple[int, int, int, int]] = []
    selected_points: List[Tuple[float, float]] = []
    last_key: Optional[Tuple[int, int, int, int]] = None

    for lat_i, lon_i in zip(line_lat, line_lon):
        monan_lat_idx = int(np.argmin(np.abs(monan_lat_vals - lat_i)))
        monan_lon_idx = _nearest_lon_index(monan_lon_vals, lon_i)
        e3sm_lat_idx = int(np.argmin(np.abs(e3sm_lat_vals - lat_i)))
        e3sm_lon_idx = _nearest_lon_index(e3sm_lon_vals, lon_i)

        key = (monan_lat_idx, monan_lon_idx, e3sm_lat_idx, e3sm_lon_idx)
        if key != last_key:
            selected_keys.append(key)
            selected_points.append((float(lat_i), float(lon_i)))
            last_key = key

    n_points_eff = len(selected_keys)
    if n_points_eff < 2:
        raise ValueError(
            "Transect collapsed to fewer than 2 unique nearest points. "
            "Increase path length or grid_resolution_km."
        )

    dist_km = np.zeros(n_points_eff, dtype=float)
    for idx in range(1, n_points_eff):
        lat_a, lon_a = selected_points[idx - 1]
        lat_b, lon_b = selected_points[idx]
        dist_km[idx] = dist_km[idx - 1] + _haversine_distance_km(
            lat_a, lon_a, lat_b, lon_b
        )
    tick_fracs = np.linspace(0.0, 1.0, 4)
    tick_positions = tick_fracs * dist_km[-1]
    tick_lats = start_lat + (end_lat - start_lat) * tick_fracs
    tick_lons = start_lon + dlon * tick_fracs
    tick_lons = ((tick_lons + 180.0) % 360.0) - 180.0
    tick_labels = []
    for lat_i, lon_i in zip(tick_lats, tick_lons):
        lat_hemi = "N" if lat_i >= 0.0 else "S"
        lon_hemi = "E" if lon_i >= 0.0 else "W"
        tick_labels.append(
            f"{abs(lat_i):.2f}°{lat_hemi}\n{abs(lon_i):.2f}°{lon_hemi}"
        )

    current_time = np.datetime64(start_date, "h")
    end_time = np.datetime64(end_date, "h")
    while current_time <= end_time:
        try:
            monan_field_t = monan_data[monan_var].sel(
                time=current_time
            ).squeeze()
            monan_qc_t = monan_data[monan_qc_var].sel(
                time=current_time
            ).squeeze()
            monan_pressure_t = monan_data[monan_pressure_var].sel(
                time=current_time
            ).squeeze()
            e3sm_field_t = e3sm_data[e3sm_var].sel(time=current_time).squeeze()
            e3sm_qc_t = e3sm_data[e3sm_qc_var].sel(time=current_time).squeeze()
        except KeyError:
            current_time += np.timedelta64(1, "h")
            continue

        monan_zdim = next(
            dim
            for dim in monan_field_t.dims
            if dim not in (monan_lat_name, monan_lon_name)
        )
        e3sm_zdim = next(
            dim
            for dim in e3sm_field_t.dims
            if dim not in (e3sm_lat_name, e3sm_lon_name)
        )

        monan_field_3d = monan_field_t.transpose(
            monan_zdim, monan_lat_name, monan_lon_name
        ).to_numpy()
        monan_qc_3d = monan_qc_t.transpose(
            monan_zdim, monan_lat_name, monan_lon_name
        ).to_numpy()
        monan_pressure_3d = _pressure_to_hpa(
            monan_pressure_t.transpose(
                monan_zdim, monan_lat_name, monan_lon_name
            ).to_numpy()
        )
        e3sm_field_3d = e3sm_field_t.transpose(
            e3sm_zdim, e3sm_lat_name, e3sm_lon_name
        ).to_numpy()
        e3sm_qc_3d = e3sm_qc_t.transpose(
            e3sm_zdim, e3sm_lat_name, e3sm_lon_name
        ).to_numpy()
        e3sm_pressure_1d = _pressure_to_hpa(
            np.asarray(e3sm_field_t[e3sm_zdim].to_numpy(), dtype=float)
        )
        e3sm_pressure_3d = np.broadcast_to(
            e3sm_pressure_1d[:, np.newaxis, np.newaxis], e3sm_field_3d.shape
        )

        monan_profiles = np.full(
            (monan_field_3d.shape[0], n_points_eff), np.nan
        )
        monan_qc_profiles = np.full(
            (monan_field_3d.shape[0], n_points_eff), np.nan
        )
        monan_pressure = np.full(
            (monan_field_3d.shape[0], n_points_eff), np.nan
        )
        e3sm_profiles = np.full((e3sm_field_3d.shape[0], n_points_eff), np.nan)
        e3sm_qc_profiles = np.full(
            (e3sm_field_3d.shape[0], n_points_eff), np.nan
        )
        e3sm_pressure = np.full((e3sm_field_3d.shape[0], n_points_eff), np.nan)

        for idx, key in enumerate(selected_keys):
            monan_lat_idx, monan_lon_idx, e3sm_lat_idx, e3sm_lon_idx = key
            monan_profiles[:, idx] = monan_field_3d[
                :, monan_lat_idx, monan_lon_idx
            ]
            monan_qc_profiles[:, idx] = monan_qc_3d[
                :, monan_lat_idx, monan_lon_idx
            ]
            monan_pressure[:, idx] = monan_pressure_3d[
                :, monan_lat_idx, monan_lon_idx
            ]
            e3sm_profiles[:, idx] = e3sm_field_3d[
                :, e3sm_lat_idx, e3sm_lon_idx
            ]
            e3sm_qc_profiles[:, idx] = e3sm_qc_3d[
                :, e3sm_lat_idx, e3sm_lon_idx
            ]
            e3sm_pressure[:, idx] = e3sm_pressure_3d[
                :, e3sm_lat_idx, e3sm_lon_idx
            ]

        if vmin is None:
            vmin_plot = min(
                float(np.nanmin(monan_profiles)),
                float(np.nanmin(e3sm_profiles)),
            )
        else:
            vmin_plot = vmin
        if vmax is None:
            vmax_plot = max(
                float(np.nanmax(monan_profiles)),
                float(np.nanmax(e3sm_profiles)),
            )
        else:
            vmax_plot = vmax
        if not np.isfinite(vmin_plot) or not np.isfinite(vmax_plot):
            vmin_plot, vmax_plot = 0.0, 1.0
        if vmin_plot == vmax_plot:
            vmax_plot = vmin_plot + 1.0

        abs_norm = mcolors.Normalize(vmin=vmin_plot, vmax=vmax_plot)
        monan_dist_2d = np.broadcast_to(dist_km, monan_profiles.shape)
        e3sm_dist_2d = np.broadcast_to(dist_km, e3sm_profiles.shape)
        fig, axes = plt.subplots(
            1, 2, figsize=(14, 6), constrained_layout=True
        )
        im_monan = axes[0].pcolormesh(
            monan_dist_2d,
            monan_pressure,
            monan_profiles,
            shading="auto",
            norm=abs_norm,
        )
        monan_qc_valid = monan_qc_profiles[np.isfinite(monan_qc_profiles)]
        monan_qc_levels = None
        if monan_qc_valid.size > 0:
            monan_qc_max = float(np.nanmax(monan_qc_valid))
            if monan_qc_max > qc_contour_min:
                monan_qc_levels = np.linspace(qc_contour_min, monan_qc_max, 5)
        if monan_qc_levels is not None:
            cs_monan = axes[0].contour(
                monan_dist_2d,
                monan_pressure,
                monan_qc_profiles,
                levels=monan_qc_levels,
                colors="white",
                linewidths=0.8,
                alpha=0.8,
            )
            axes[0].clabel(cs_monan, inline=True, fontsize=7, fmt="%.1e")
        axes[0].set_title("MONAN")
        im_e3sm = axes[1].pcolormesh(
            e3sm_dist_2d,
            e3sm_pressure,
            e3sm_profiles,
            shading="auto",
            norm=abs_norm,
        )
        e3sm_qc_valid = e3sm_qc_profiles[np.isfinite(e3sm_qc_profiles)]
        e3sm_qc_levels = None
        if e3sm_qc_valid.size > 0:
            e3sm_qc_max = float(np.nanmax(e3sm_qc_valid))
            if e3sm_qc_max > qc_contour_min:
                e3sm_qc_levels = np.linspace(qc_contour_min, e3sm_qc_max, 5)
        if e3sm_qc_levels is not None:
            cs_e3sm = axes[1].contour(
                e3sm_dist_2d,
                e3sm_pressure,
                e3sm_qc_profiles,
                levels=e3sm_qc_levels,
                colors="white",
                linewidths=0.8,
                alpha=0.8,
            )
            axes[1].clabel(cs_e3sm, inline=True, fontsize=7, fmt="%.1e")
        axes[1].set_title("E3SM")

        for ax in axes:
            ax.invert_yaxis()
            ax.set_xlabel("Coordinates along transect")
            ax.set_ylabel("Pressure [hPa]")
            ax.set_ylim(
                1000,
                700.0,
            )
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels)
            ax.grid(alpha=0.25)

        cbar_abs = fig.colorbar(
            im_e3sm, ax=axes, orientation="horizontal", pad=0.14
        )
        cbar_abs.set_label(monan_var)

        date_str = np.datetime_as_string(current_time, unit="m")
        start_lat_hemi = "N" if start_lat >= 0 else "S"
        start_lon_hemi = "E" if start_lon >= 0 else "W"
        end_lat_hemi = "N" if end_lat >= 0 else "S"
        end_lon_hemi = "E" if end_lon >= 0 else "W"
        start_lat_str = f"{abs(start_lat):.2f}°{start_lat_hemi}"
        start_lon_str = f"{abs(start_lon):.2f}°{start_lon_hemi}"
        end_lat_str = f"{abs(end_lat):.2f}°{end_lat_hemi}"
        end_lon_str = f"{abs(end_lon):.2f}°{end_lon_hemi}"
        fig.suptitle(
            (
                f"Transect {monan_var} | {date_str} | "
                f"({start_lat_str}, {start_lon_str}) -> "
                f"({end_lat_str}, {end_lon_str})"
            ),
            fontsize=11,
        )
        out_file = os.path.join(
            output_dir,
            (
                f"transect_{monan_var}_"
                f"{np.datetime_as_string(current_time, unit='h')}.png"
            ),
        )
        plt.savefig(out_file, dpi=300)
        plt.close(fig)
        current_time += np.timedelta64(1, "h")
