from __future__ import annotations

from typing import Sequence

import numpy as np

from plot_core.adapter import DataAdapter
from plot_core.plot_data import TimeSeriesPlotData
from plot_core.scenarios.adapters import (
    build_surface_flux_goamazon_eddy_correlation_adapter,
    build_surface_flux_time_series_era5_adapter,
    build_surface_flux_time_series_mynn_adapter,
    build_surface_flux_time_series_shoc_adapter,
    build_time_series_era5_adapter,
    build_time_series_era5_precipitation_adapter,
    build_time_series_goamazon_ceilometer_pbl_height_adapter,
    build_time_series_goamazon_surface_station_adapter,
    build_time_series_mynn_adapter,
    build_time_series_shoc_adapter,
)
from plot_core.scenarios.paths import (
    TIME_SERIES_DEFAULT_INIT_DATE,
    TIME_SERIES_FORECAST_DAYS,
    TIME_SERIES_INIT_DATE_TO_MONAN_SEASON,
    build_time_series_init_datetime_string,
    normalize_time_series_init_date,
)
from plot_core.scenarios.requests import (
    build_time_series_comparison_gridded_request,
    build_time_series_comparison_station_request,
)

from .processing import (
    build_cross_5_time_series_request,
    build_era5_hourly_precipitation_rate_plot_data,
    build_hourly_last_plot_data,
    build_hourly_nearest_station_plot_data,
    build_monan_hourly_precipitation_rate_plot_data,
)
from .registry import (
    HPBL_RECIPE_FAMILY,
    METEOROLOGICAL_RECIPE_FAMILY,
    SURFACE_FLUX_RECIPE_FAMILY,
)


def extract_hourly_series_by_source(
    *,
    recipe_family: str,
    variable_name: str,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> dict[str, TimeSeriesPlotData]:
    """Extract and preprocess hourly series by source label."""
    compact_date = normalize_time_series_init_date(init_date)
    if recipe_family == METEOROLOGICAL_RECIPE_FAMILY:
        return _extract_meteorological_hourly_series_by_source(
            variable_name=variable_name,
            init_date=compact_date,
        )
    if recipe_family == HPBL_RECIPE_FAMILY:
        return _extract_hpbl_hourly_series_by_source(
            variable_name=variable_name,
            init_date=compact_date,
        )
    if recipe_family == SURFACE_FLUX_RECIPE_FAMILY:
        return _extract_surface_flux_hourly_series_by_source(
            variable_name=variable_name,
            init_date=compact_date,
        )

    raise ValueError(f"Unsupported recipe family {recipe_family!r}.")


def _extract_meteorological_hourly_series_by_source(
    *,
    variable_name: str,
    init_date: str,
) -> dict[str, TimeSeriesPlotData]:
    """Extract hourly meteorological series for one canonical variable."""
    start_time, end_time_exclusive = _build_time_window(init_date)
    gridded_request = build_time_series_comparison_gridded_request(
        init_date=init_date
    )
    cross_5_request = build_cross_5_time_series_request(gridded_request)
    station_request = build_time_series_comparison_station_request(
        init_date=init_date
    )

    adapters = _build_time_series_comparison_adapters(init_date=init_date)
    shoc_adapter, mynn_adapter, era5_adapter, station_adapter = adapters
    try:
        if variable_name == "precipitation":
            return _extract_precipitation_hourly_series_by_source(
                shoc_adapter=shoc_adapter,
                mynn_adapter=mynn_adapter,
                init_date=init_date,
                cross_5_request=cross_5_request,
                gridded_request=gridded_request,
                start_time=start_time,
                end_time_exclusive=end_time_exclusive,
            )

        shoc_plot_data = _extract_monan_hourly_mean_cross_5_plot_data(
            adapter=shoc_adapter,
            variable_name=variable_name,
            request=cross_5_request,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        mynn_plot_data = _extract_monan_hourly_mean_cross_5_plot_data(
            adapter=mynn_adapter,
            variable_name=variable_name,
            request=cross_5_request,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        era5_raw = era5_adapter.to_time_series_plot_data(
            variable_name=variable_name,
            request=gridded_request,
        )
        era5_plot_data = build_hourly_last_plot_data(
            era5_raw,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        station_raw = station_adapter.to_time_series_plot_data(
            variable_name=variable_name,
            request=station_request,
        )
        station_plot_data = build_hourly_nearest_station_plot_data(
            station_raw,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )

        return {
            shoc_plot_data.label: shoc_plot_data,
            mynn_plot_data.label: mynn_plot_data,
            era5_plot_data.label: era5_plot_data,
            station_plot_data.label: station_plot_data,
        }
    finally:
        _close_adapters(adapters)


def _extract_hpbl_hourly_series_by_source(
    *,
    variable_name: str,
    init_date: str,
) -> dict[str, TimeSeriesPlotData]:
    """Extract hourly HPBL series for SHOC, MYNN, ERA5 and ceilometer."""
    if variable_name != "hpbl":
        raise ValueError(
            f"Unsupported HPBL metrics variable {variable_name!r}."
        )

    start_time, end_time_exclusive = _build_time_window(init_date)
    gridded_request = build_time_series_comparison_gridded_request(
        init_date=init_date
    )
    cross_5_request = build_cross_5_time_series_request(gridded_request)
    station_request = build_time_series_comparison_station_request(
        init_date=init_date
    )

    adapters = _build_hpbl_time_series_comparison_adapters(
        init_date=init_date
    )
    shoc_adapter, mynn_adapter, era5_adapter, ceilometer_adapter = adapters
    try:
        shoc_plot_data = _extract_monan_hourly_mean_cross_5_plot_data(
            adapter=shoc_adapter,
            variable_name=variable_name,
            request=cross_5_request,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        mynn_plot_data = _extract_monan_hourly_mean_cross_5_plot_data(
            adapter=mynn_adapter,
            variable_name=variable_name,
            request=cross_5_request,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        era5_raw = era5_adapter.to_time_series_plot_data(
            variable_name=variable_name,
            request=gridded_request,
        )
        era5_plot_data = build_hourly_last_plot_data(
            era5_raw,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        ceilometer_raw = ceilometer_adapter.to_time_series_plot_data(
            variable_name=variable_name,
            request=station_request,
        )
        ceilometer_plot_data = build_hourly_nearest_station_plot_data(
            ceilometer_raw,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )

        return {
            shoc_plot_data.label: shoc_plot_data,
            mynn_plot_data.label: mynn_plot_data,
            era5_plot_data.label: era5_plot_data,
            ceilometer_plot_data.label: ceilometer_plot_data,
        }
    finally:
        _close_adapters(adapters)


def _extract_surface_flux_hourly_series_by_source(
    *,
    variable_name: str,
    init_date: str,
) -> dict[str, TimeSeriesPlotData]:
    """Extract hourly surface-flux series for one canonical variable."""
    start_time, end_time_exclusive = _build_time_window(init_date)
    gridded_request = build_time_series_comparison_gridded_request(
        init_date=init_date
    )
    cross_5_request = build_cross_5_time_series_request(gridded_request)
    station_request = build_time_series_comparison_station_request(
        init_date=init_date
    )

    adapters = _build_surface_flux_time_series_comparison_adapters(
        init_date=init_date
    )
    try:
        if len(adapters) < 3:
            raise ValueError(
                "Surface-flux comparison adapters must contain at least "
                "SHOC, MYNN and ERA5."
            )

        shoc_adapter = adapters[0]
        mynn_adapter = adapters[1]
        era5_adapter = adapters[2]

        shoc_plot_data = _extract_monan_hourly_mean_cross_5_plot_data(
            adapter=shoc_adapter,
            variable_name=variable_name,
            request=cross_5_request,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        mynn_plot_data = _extract_monan_hourly_mean_cross_5_plot_data(
            adapter=mynn_adapter,
            variable_name=variable_name,
            request=cross_5_request,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
        era5_raw = era5_adapter.to_time_series_plot_data(
            variable_name=variable_name,
            request=gridded_request,
        )
        era5_plot_data = build_hourly_last_plot_data(
            era5_raw,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )

        series_by_source: dict[str, TimeSeriesPlotData] = {
            shoc_plot_data.label: shoc_plot_data,
            mynn_plot_data.label: mynn_plot_data,
            era5_plot_data.label: era5_plot_data,
        }

        if len(adapters) > 3:
            observation_adapter = adapters[3]
            observation_raw = observation_adapter.to_time_series_plot_data(
                variable_name=variable_name,
                request=station_request,
            )
            observation_plot_data = build_hourly_nearest_station_plot_data(
                observation_raw,
                start_time=start_time,
                end_time_exclusive=end_time_exclusive,
            )
            series_by_source[observation_plot_data.label] = (
                observation_plot_data
            )

        return series_by_source
    finally:
        _close_adapters(adapters)


def _extract_precipitation_hourly_series_by_source(
    *,
    shoc_adapter: DataAdapter,
    mynn_adapter: DataAdapter,
    init_date: str,
    cross_5_request,
    gridded_request,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> dict[str, TimeSeriesPlotData]:
    """Extract SHOC/MYNN/ERA5 hourly precipitation-rate series."""
    shoc_mean, _ = shoc_adapter.to_time_series_mean_std_plot_data(
        variable_name="precipitation",
        request=cross_5_request,
    )
    mynn_mean, _ = mynn_adapter.to_time_series_mean_std_plot_data(
        variable_name="precipitation",
        request=cross_5_request,
    )

    shoc_rates = build_monan_hourly_precipitation_rate_plot_data(
        shoc_mean,
        start_time=start_time,
        end_time_exclusive=end_time_exclusive,
    )
    mynn_rates = build_monan_hourly_precipitation_rate_plot_data(
        mynn_mean,
        start_time=start_time,
        end_time_exclusive=end_time_exclusive,
    )

    era5_precipitation_adapter = build_time_series_era5_precipitation_adapter(
        init_date=init_date
    )
    try:
        era5_raw = era5_precipitation_adapter.to_time_series_plot_data(
            variable_name="precipitation",
            request=gridded_request,
        )
        era5_rates = build_era5_hourly_precipitation_rate_plot_data(
            era5_raw,
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
        )
    finally:
        era5_precipitation_adapter.close()

    return {
        shoc_rates.label: shoc_rates,
        mynn_rates.label: mynn_rates,
        era5_rates.label: era5_rates,
    }


def _extract_monan_hourly_mean_cross_5_plot_data(
    *,
    adapter: DataAdapter,
    variable_name: str,
    request,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> TimeSeriesPlotData:
    """Extract cross-5 mean series from MONAN and reduce to hourly."""
    mean_plot_data, _ = adapter.to_time_series_mean_std_plot_data(
        variable_name=variable_name,
        request=request,
    )
    return build_hourly_last_plot_data(
        mean_plot_data,
        start_time=start_time,
        end_time_exclusive=end_time_exclusive,
    )


def _build_time_window(
    init_date: str,
) -> tuple[np.datetime64, np.datetime64]:
    """Return [start, end) window for one 5-day case."""
    start_time = np.datetime64(
        build_time_series_init_datetime_string(init_date),
        "ns",
    )
    end_time_exclusive = start_time + np.timedelta64(
        TIME_SERIES_FORECAST_DAYS,
        "D",
    )
    return start_time, end_time_exclusive


def _close_adapters(adapters: Sequence[DataAdapter]) -> None:
    """Close all adapters, ignoring individual close errors."""
    for adapter in adapters:
        adapter.close()


def _build_time_series_comparison_adapters(
    *,
    init_date: str,
) -> list[DataAdapter]:
    """Build SHOC, MYNN, ERA5 and station adapters for meteorology metrics."""
    return [
        build_time_series_shoc_adapter(init_date=init_date),
        build_time_series_mynn_adapter(init_date=init_date),
        build_time_series_era5_adapter(init_date=init_date),
        build_time_series_goamazon_surface_station_adapter(
            init_date=init_date
        ),
    ]


def _build_surface_flux_time_series_comparison_adapters(
    *,
    init_date: str,
) -> list[DataAdapter]:
    """Build SHOC/MYNN/ERA5 and optional observation adapters for fluxes."""
    adapters = [
        build_surface_flux_time_series_shoc_adapter(init_date=init_date),
        build_surface_flux_time_series_mynn_adapter(init_date=init_date),
        build_surface_flux_time_series_era5_adapter(init_date=init_date),
    ]
    season_slug = TIME_SERIES_INIT_DATE_TO_MONAN_SEASON[init_date]
    if season_slug != "wet_season":
        adapters.append(
            build_surface_flux_goamazon_eddy_correlation_adapter(
                init_date=init_date
            )
        )
    return adapters


def _build_hpbl_time_series_comparison_adapters(
    *,
    init_date: str,
) -> list[DataAdapter]:
    """Build SHOC, MYNN, ERA5 and ceilometer adapters for HPBL metrics."""
    return [
        build_time_series_shoc_adapter(init_date=init_date),
        build_time_series_mynn_adapter(init_date=init_date),
        build_time_series_era5_adapter(init_date=init_date),
        build_time_series_goamazon_ceilometer_pbl_height_adapter(
            init_date=init_date
        ),
    ]


__all__ = ["extract_hourly_series_by_source"]
