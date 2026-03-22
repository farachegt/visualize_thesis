import numpy as np
import xarray as xr


def open_monan_data(path: str) -> xr.Dataset:
    """Open MONAN files, rebuild hourly `time`, and standardize coordinates."""
    print("Opening MONAN data...")
    monan_data = xr.open_mfdataset(
        path,
        combine="nested",
        concat_dim="Time",
        parallel=True,
    )

    time_len = monan_data.sizes["Time"]
    start = np.datetime64("2014-02-24T00:00")
    time_values = np.array(
        [start + np.timedelta64(i, "h") for i in range(time_len)]
    )
    monan_data = monan_data.assign_coords(Time=time_values)
    monan_data = monan_data.rename({"Time": "time"})
    return monan_data


def open_e3sm_data(path: str) -> xr.Dataset:
    """Open E3SM files and coerce `time` to `datetime64[ns]` coordinates."""
    print("Opening E3SM data...")
    e3sm_data = xr.open_mfdataset(
        path,
        combine="by_coords",
        parallel=True,
    )
    if "time" in e3sm_data.indexes:
        e3sm_time_str = [
            time_value.strftime("%Y-%m-%d %H:%M:%S")
            for time_value in e3sm_data.indexes["time"]
        ]
        e3sm_time = np.array(e3sm_time_str, dtype="datetime64[ns]")
        e3sm_data = e3sm_data.assign_coords(time=e3sm_time)
    return e3sm_data
