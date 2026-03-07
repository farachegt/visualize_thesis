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
)


def main() -> None:
    """Load MONAN/E3SM subsets and execute the configured comparisons."""
    e3sm_data = open_e3sm_data("../E3SM_in_MONAN*.nc")
    monan_data = open_monan_data(
        "/mnt/beegfs/guilherme.farache/runs/MONAN/model/"
        "GLOBAL_GFdef_ERA5_x1.655362_shoc_petervalidation_glw/"
        "2014022400/diag/posprocess/diag.*"
    )

    e3sm_data_subset = e3sm_data[["qc", "pbl_height", "tke"]]
    e3sm_data.close()
    e3sm_data_subset = e3sm_data_subset.rename(
        {
            "pbl_height": "hpbl",
            "tke": "tke_pbl",
        }
    )

    monan_data_subset = monan_data[["qc", "pressure", "hpbl", "tke_pbl"]]
    monan_data.close()

    for date in pd.date_range(
        "2014-02-24T01:00", "2014-02-27T00:00", freq="1H"
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
        else:
            coordinates = {
            #    "Atlantic Ocean": (-14, -24),
                "Amazon Rainforest": (-3, -60),
            #    "African Desert": (20, 0),
            #    "Siberia": (60, 100),
            #    "Australia": (-25, 135),
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
                    start_date=np.datetime64("2014-02-24T00:00"),
                    n_days=3,
                    output_dir=(
                        "plots/tke_vertical_profile_hourly_mean_hpbl_qc_hfx"
                    ),
                )

    if False:
        plot_cross_section_transect(
            monan_data=monan_data_subset,
            e3sm_data=e3sm_data_subset,
            start_lat=-10.0,
            start_lon=-70.0,
            end_lat=2.0,
            end_lon=-50.0,
            start_date=np.datetime64("2014-02-24T00:00"),
            end_date=np.datetime64("2014-02-27T00:00"),
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
            start_date=np.datetime64("2014-02-24"),
            n_days=3,
        )
        plot_diurnal_peak_phase_pblh(
            monan_data=monan_data_subset,
            e3sm_data=e3sm_data_subset,
            monan_var="hpbl",
            e3sm_var="hpbl",
            start_date=np.datetime64("2014-02-24"),
            n_days=3,
        )


if __name__ == "__main__":
    main()
