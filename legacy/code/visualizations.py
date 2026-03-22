import numpy as np
import pandas as pd

from io_utils import open_e3sm_data, open_monan_data
from plot_diurnal import (
    plot_diurnal_cycle_amplitude_pblh,
    plot_diurnal_peak_phase_pblh,
)
from plot_maps import (
    plot_paper_grade_panel,
    plot_precipitation_monan,
    plot_side_by_side,
)
from plot_profiles import (
    plot_cross_section_transect,
    plot_vertical_profile_tke_hourly_mean,
    plot_vertical_profiles_panel_at_point,
)


def main() -> None:
    """Load MONAN/E3SM subsets and execute the configured comparisons."""
    #e3sm_data = open_e3sm_data("/mnt/beegfs/guilherme.farache/peter_data/E3SM_in_MONAN*.nc")
    shoc_monan_data = open_monan_data(
        "/mnt/beegfs/guilherme.farache/runs/MONAN/model/"
        "GLOBAL_GFdef_ERA5_x1.655362_shoc_transition_dry/"
        "2014090300/diag/posprocess/diag.*"
    )
    mynn_monan_data = open_monan_data(
        "/mnt/beegfs/guilherme.farache/runs/MONAN/model/"
        "GLOBAL_GFdef_ERA5_x1.655362_mynn_transition_dry/"
        "2014090300/diag/posprocess/diag.*"
    )

    # e3sm_data_subset = e3sm_data[["qc", "qv", "tke", "PotentialTemperature", "U", "V"]]
    # #e3sm_data_subset = e3sm_data[["qc", "PotentialTemperature"]]
    # e3sm_data.close()
    # e3sm_data_subset = e3sm_data_subset.rename(
    #     {
    #         #"pbl_height": "hpbl",
    #         "tke": "tke_pbl",
    #         #"surf_sens_flux": "hfx",
    #         "PotentialTemperature": "theta",
    #     }
    # )
    # e3sm_data_subset['qt'] = e3sm_data_subset['qc'] + e3sm_data_subset['qv']
    # e3sm_data_subset['wind_speed'] = np.sqrt(
    #     e3sm_data_subset['U']**2 + e3sm_data_subset['V']**2
    # )

    shoc_monan_data_subset = shoc_monan_data[["qc", "theta", "tke_pbl", "hfx", "pressure", "qv", "u", "v"]]
    #shoc_monan_data_subset = shoc_monan_data[["qc", "theta", "pressure"]]
    shoc_monan_data_subset['qt'] = shoc_monan_data_subset['qc'] + shoc_monan_data_subset['qv']
    shoc_monan_data_subset['wind_speed'] = np.sqrt(
        shoc_monan_data_subset['u']**2 + shoc_monan_data_subset['v']**2
    )
    shoc_monan_data.close()

    mynn_monan_data_subset = mynn_monan_data[["qc", "theta", "tke_pbl", "hfx", "pressure", "qv", "u", "v"]]
    #mynn_monan_data_subset = mynn_monan_data[["qc", "theta", "pressure"]]
    mynn_monan_data_subset['qt'] = mynn_monan_data_subset['qc'] + mynn_monan_data_subset['qv']
    mynn_monan_data_subset['wind_speed'] = np.sqrt(
        mynn_monan_data_subset['u']**2 + mynn_monan_data_subset['v']**2
    )
    mynn_monan_data.close()


    for date in pd.date_range(
        "2014-09-03T01:00", "2014-09-06T00:00", freq="1H"
    ):
        date = np.datetime64(date)
        if False:
            plot_side_by_side(
                e3sm_data_subset,
                monan_data_subset,
                "pbl_height",
                "hpbl",
                vmin=0,
                vmax=3000,
                cmap="turbo",
                date=date,
            )
            plot_side_by_side(
                e3sm_data_subset,
                monan_data_subset,
                "surf_sens_flux",
                "hfx",
                vmin=-200,
                vmax=500,
                cmap="bwr",
                date=date,
                central_value=0.0,
            )
            plot_side_by_side(
                e3sm_data_subset,
                monan_data_subset,
                "surface_upward_latent_heat_flux",
                "lh",
                vmin=-100,
                vmax=600,
                cmap="bwr",
                date=date,
                central_value=0.0,
            )
            plot_paper_grade_panel(
                monan_data=monan_data_subset,
                e3sm_data=e3sm_data_subset,
                date=date,
            )

            coordinates = {
                "Atlantic Ocean": (-14, -24),
                "Amazon Rainforest": (-3, -60),
                "African Desert": (20, 0),
                "Siberia": (60, 100),
                "Australia": (-25, 135),
            }
            vmax = {
                "Atlantic Ocean": 0.2,
                "Amazon Rainforest": 1.0,
                "African Desert": 2.0,
                "Siberia": 2.0,
                "Australia": 2.0,
            }
            for coord_name, (lat, lon) in coordinates.items():
                plot_vertical_profile_tke_hourly_mean(
                    monan_data=monan_data_subset,
                    e3sm_data=e3sm_data_subset,
                    point_lat=lat,
                    point_lon=lon,
                    region_name=coord_name,
                    monan_var="tke_pbl",
                    e3sm_var="tke_pbl",
                    half_box_deg=0.5,
                    vmin=0.0,
                    vmax=vmax[coord_name],
                    start_date=np.datetime64("2014-09-03T00:00"),
                    n_days=3,
                    output_dir=(
                        "plots/tke_vertical_profile_hourly_mean_hpbl_qc_hfx"
                    ),
                )
        else:
            pass

    if False:
        plot_cross_section_transect(
            monan_data=monan_data_subset,
            e3sm_data=e3sm_data_subset,
            start_lat=-10.0,
            start_lon=-70.0,
            end_lat=2.0,
            end_lon=-50.0,
            start_date=np.datetime64("2014-09-03T00:00"),
            end_date=np.datetime64("2014-09-06T00:00"),
            monan_var="tke_pbl",
            e3sm_var="tke_pbl",
            grid_resolution_km=30.0,
            output_dir="plots/cross_section_tke",
        )
        plot_precipitation_monan(monan_data_subset)
        plot_diurnal_cycle_amplitude_pblh(
            monan_data=monan_data_subset,
            e3sm_data=e3sm_data_subset,
            monan_var="hpbl",
            e3sm_var="hpbl",
            start_date=np.datetime64("2014-09-03"),
            n_days=3,
        )
        plot_diurnal_peak_phase_pblh(
            monan_data=monan_data_subset,
            e3sm_data=e3sm_data_subset,
            monan_var="hpbl",
            e3sm_var="hpbl",
            start_date=np.datetime64("2014-09-03"),
            n_days=3,
        )
    else:
        coordinates = [()]
        times = pd.date_range("2014-09-03T00:00", "2014-09-06T00:00", freq="1H")
        # Convert times to list of np.datetime64
        times = [np.datetime64(time) for time in times]
        for coordinate in coordinates:
            for time in times:
                lat, lon = coordinate
                plot_vertical_profiles_panel_at_point(
                    dataset_1=shoc_monan_data_subset,
                    point_lat=lat,
                    point_lon=lon,
                    time=time,
                    var_names_1=["theta", "tke_pbl", "qt", "wind_speed"],
                    panel_labels=["Potential Temperature", "TKE", "Total Water Mixing Ratio", "Wind Speed"],
                    x_units=["K", "m²/s²", "kg/kg", "m/s"],
                    vertical_axis="pressure",
                    dataset_2=mynn_monan_data_subset,
                    var_names_2=["theta", "tke_pbl", "qt", "wind_speed"],
                    pressure_var_1="pressure",
                    pressure_var_2="pressure",
                    shade_cloud_layer=True,
                    cloud_liquid_var_1="qc",
                    cloud_liquid_var_2="qc",
                    cloud_hatch_target="both",
                    dataset_1_label="MONAN - SHOC scheme",
                    dataset_2_label="MONAN - MYNN scheme",
                    output_dir="plots/vertical_profiles_panel_at_point",
                    output_name_prefix=f"vertprofile_{lat}_{lon}_theta_tke_qt_wspeed_shocxmynn"
            )


if __name__ == "__main__":
    main()
