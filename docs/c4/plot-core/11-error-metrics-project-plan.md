# Error Metrics Project Plan

## Summary

Add a small metrics project inside `visualize_thesis` to calculate error
statistics for the same scenario data used by the comparison recipes.

The metrics code must reuse the existing `plot_core` architecture for data
access and semantic normalization:

- paths and supported init-date/season mapping from scenario path helpers;
- source builders and `SourceSpecification` canonical variables;
- `DataAdapter` for reading, unit conversion and derivations;
- `TimeSeriesRequest` and future profile requests for sampling/alignment;
- existing scenario adapter builders wherever practical.

The metrics project should not duplicate source variable names such as `t2m`,
`q2`, `rainc`, `rainnc`, `tp`, `hfx`, or `lh` outside source
specifications. It should request canonical variables such as
`temperature_2m`, `specific_humidity_2m`, `wind_speed_10m`,
`precipitation`, `sensible_heat_flux`, and `latent_heat_flux`.

## References

- [Plot-core macro structure](./02-estrutura-macro.md)
- [Source specifications and requests](./03c-source-and-requests.md)
- [Data adapter](./03f-data-adapter.md)
- [Recipe guide](./07-como-criar-um-recipe.md)
- [Time-series recipe plan](./08-time-series-recipe-plan.md)
- [Precipitation panel plan](./10-time-series-precipitation-panel-plan.md)
- [Scenario adapters](../../../plot_core/scenarios/adapters.py)
- [Scenario paths](../../../plot_core/scenarios/paths.py)
- [Scenario requests](../../../plot_core/scenarios/requests.py)
- [Scenario recipes](../../../plot_core/scenarios/recipes.py)
- [xskillscore documentation](https://xskillscore.readthedocs.io/en/stable/)
- [xskillscore API reference](https://xskillscore.readthedocs.io/en/stable/api.html)

## Goals

- Compute error metrics for supported comparison cases:
  - `20141002` / transition season;
  - `20140802` / dry season;
  - `20140216` / wet season.
- Use hourly values over the full 5-day comparison window.
- Use Observation as the reference when observation exists.
- Use ERA5 as the reference when observation is unavailable.
- Make the reference source explicit in every output row.
- Export simple tabular outputs suitable for papers, notebooks and further
  plotting.

## Non-Goals

- Do not add plotting code to the metrics project in v1.
- Do not bypass `DataAdapter`, `SourceSpecification`, requests or scenario
  path builders.
- Do not hardcode backend source variable names in metrics code.
- Do not silently change reference datasets without recording the selected
  reference source.
- Do not import private plotting helpers from `plot_core/scenarios/recipes.py`
  into metrics code.
- Do not reimplement common deterministic metrics that are available in
  `xskillscore`.
- Do not implement hourly-mean metrics in v1.
- Do not implement vertical-profile metrics in v1.
- Do not implement multiple output formats in v1; CSV is the only target.

## Proposed Package Layout

Add a separate metrics package and scripts:

```text
metrics/
  __init__.py
  registry.py
  extraction.py
  processing.py
  alignment.py
  scores.py
  tables.py

scripts/metrics/
  compute_error_metrics.py
```

Responsibilities:

- `metrics/registry.py`
  - supported variables by recipe family;
  - reference-source rules;
  - output units and display labels;
  - case metadata helpers for season/init-date.
- `metrics/extraction.py`
  - turn scenario adapters and requests into `TimeSeriesPlotData`;
  - close adapters reliably;
  - keep extraction independent from Matplotlib and plot layers.
- `metrics/processing.py`
  - reusable hourly sampling and accumulated-precipitation deaccumulation;
  - functionality currently embedded in scenario plotting helpers can move
    here if both recipes and metrics need it.
- `metrics/alignment.py`
  - align candidate and reference arrays on common hourly timestamps;
  - filter paired finite samples.
- `metrics/scores.py`
  - thin wrappers around `xskillscore` deterministic metrics;
  - custom sample-count and precipitation-total helpers that are not direct
    xskillscore scores.
- `metrics/tables.py`
  - build long row-per-metric dictionaries or data frames;
  - build wide summary row dictionaries or data frames;
  - write CSV.

## Architecture Boundary

Use `plot_core` for source semantics and data preparation. Use `metrics` for
analysis only.

`plot_core` remains responsible for:

- resolving file paths;
- opening GRIB/NetCDF files;
- applying source specifications;
- unit conversion and derivations;
- nearest-point or other geometry sampling;
- returning `PlotData` objects.

`metrics` becomes responsible for:

- choosing variables to evaluate;
- choosing the reference source;
- aligning comparable arrays;
- computing statistics;
- exporting results.

## Shared Processing Refactor

Several useful reductions currently live in scenario recipe code because they
were introduced for plotting:

- hourly nearest station sampling;
- MONAN accumulated precipitation to hourly precipitation rate;
- ERA5 precipitation unit conversion from `m/h` to `mm/h`;
- paired finite-sample filtering.

If metrics needs the same behavior, move reusable data-processing helpers out
of `plot_core/scenarios/recipes.py` into a neutral module, for example:

```text
plot_core/scenarios/time_series_processing.py
```

Both plotting recipes and metrics scripts can then import the same functions.
This keeps scientific reductions out of generic plotting recipes while also
avoiding duplicate logic.

## Reference Rules

### Meteorological Variables

Variables:

- `temperature_2m`;
- `specific_humidity_2m`;
- `wind_speed_10m`;
- `precipitation`.

Reference selection:

- `temperature_2m`, `specific_humidity_2m`, `wind_speed_10m`:
  - reference source: Observation from the GoAmazon surface station;
  - compare SHOC, MYNN and ERA5 against Observation.
- `precipitation`:
  - reference source: ERA5, because observational precipitation is not
    available for the supported comparison windows;
  - compare SHOC and MYNN against ERA5;
  - do not include an Observation row for precipitation.

### Surface-Flux Variables

Variables:

- `sensible_heat_flux`;
- `latent_heat_flux`.

Reference selection:

- dry season and transition season:
  - reference source: Observation from corrected GoAmazon C1
    eddy-correlation product;
  - compare SHOC, MYNN and ERA5 against Observation.
- wet season:
  - reference source: ERA5, because the surface-flux Observation source is
    omitted for wet season;
  - compare SHOC and MYNN against ERA5.

## Time Basis

For v1 metrics:

- use the same 5-day comparison interval as the recipes;
- sample ERA5 hourly at the nearest grid point;
- sample MONAN hourly with the existing `cross_5` spatial sample pattern and
  use the spatial mean value as the candidate series;
- sample station observations hourly using the same hourly-nearest strategy as
  the plot recipe;
- align candidate and reference by timestamp;
- compute metrics over paired finite samples only.
- do not compute local-hour means;
- do not expose a `mode` CLI option.

For precipitation:

- derive MONAN hourly precipitation first:
  - `precipitation = rainc + rainnc`;
  - use `cross_5` sampling and compute the spatial mean of accumulated
    precipitation before hourly deaccumulation;
  - hourly value is the difference from the previous hour;
  - negative increments become `NaN`;
  - first increment is `NaN` unless a previous accumulation is available.
- derive ERA5 hourly precipitation:
  - request canonical `precipitation`;
  - convert `tp` from `m/h` to `mm/h`;
  - do not deaccumulate ERA5.

## Metrics

Use `xskillscore` for deterministic scalar time-series metrics. The API
reference exposes the needed deterministic metrics:

- `xskillscore.me(...)` for mean error / bias;
- `xskillscore.mae(...)` for mean absolute error;
- `xskillscore.rmse(...)` for root mean squared error;
- `xskillscore.pearson_r(...)` for Pearson correlation.

Build aligned `xarray.DataArray` objects with dimension `time`, then call
the metrics with `dim="time"` and `skipna=True`.

Metrics for all scalar time-series variables:

- `bias = mean(candidate - reference)`;
- `mae = mean(abs(candidate - reference))`;
- `rmse = sqrt(mean((candidate - reference)^2))`;
- `corr = Pearson correlation`;
- `n = number of paired finite samples`.

Implementation mapping:

```text
bias -> xs.me(candidate, reference, dim="time", skipna=True)
mae  -> xs.mae(candidate, reference, dim="time", skipna=True)
rmse -> xs.rmse(candidate, reference, dim="time", skipna=True)
corr -> xs.pearson_r(candidate, reference, dim="time", skipna=True)
```

Use one consistent argument order everywhere: `candidate` first, `reference`
second. With this order, `xs.me(candidate, reference, ...)` must represent
`candidate - reference`.

If fewer than two paired finite samples are available, report `corr` as
`NaN`.

For precipitation, always add totals in addition to hourly rate metrics:

- `total_candidate`;
- `total_reference`;
- `total_bias = total_candidate - total_reference`;
- `relative_total_bias_percent`.

Precipitation totals and `n` are project-specific helpers, not xskillscore
metrics:

- compute `n` from the same paired finite mask used for candidate/reference
  comparison;
- compute precipitation totals after paired filtering so candidate and
  reference totals cover the same timestamps;
- keep these helpers small and local to `metrics/scores.py` or
  `metrics/tables.py`.

## Output Schemas

Write both a long row-per-metric table and a wide summary table.

### Long Metrics Table

The long table has one row per metric:

```text
case_init_date
season
recipe_family
variable
variable_label
source
reference_source
metric
value
units
n_samples
```

Example rows:

```text
20141002,transition_season,meteorological_time_series,temperature_2m,2 m temperature,SHOC,Observation,rmse,1.42,degC,120
20141002,transition_season,meteorological_time_series,precipitation,Precipitation,SHOC,ERA5,total_bias,8.6,mm,119
20140216,wet_season,surface_flux_time_series,latent_heat_flux,Latent heat flux,MYNN,ERA5,bias,-23.1,W m^-2,120
```

### Wide Metrics Table

The wide table has one row per source-variable comparison and one column per
metric:

```text
case_init_date
season
recipe_family
variable
variable_label
source
reference_source
units
n_samples
bias
mae
rmse
corr
total_candidate
total_reference
total_bias
relative_total_bias_percent
```

Example wide rows:

```text
20141002,transition_season,meteorological_time_series,temperature_2m,2 m temperature,SHOC,Observation,degC,120,-0.52,0.94,1.42,0.87,,,,
20141002,transition_season,meteorological_time_series,precipitation,Precipitation,SHOC,ERA5,mm h^-1,119,0.08,0.34,0.91,0.42,22.8,14.2,8.6,60.6
20140216,wet_season,surface_flux_time_series,latent_heat_flux,Latent heat flux,MYNN,ERA5,W m^-2,120,-23.1,55.0,81.4,0.65,,,,
```

For non-precipitation variables, leave precipitation-only total columns empty.
For precipitation, rate metrics use `mm h^-1`; total columns use accumulated
`mm` over paired timestamps.

Default output directory:

```text
tests/output/metrics/
```

Suggested default filenames:

```text
error_metrics_sfc_{season_slug}_long.csv
error_metrics_sfc_{season_slug}_wide.csv
```

## CLI Behavior

### `compute_error_metrics.py`

Options:

- `--init-date {20141002,20140802,20140216}`;
- `--output-dir PATH`.

Behavior:

- compute all v1 metrics in one run:
  - `temperature_2m`;
  - `specific_humidity_2m`;
  - `wind_speed_10m`;
  - `precipitation`;
  - `sensible_heat_flux`;
  - `latent_heat_flux`.
- write both CSV outputs:
  - long row-per-metric CSV;
  - wide summary CSV;
- when `--output-dir` is omitted, write both files under
  `tests/output/metrics/`;
- when `--output-dir` is provided, write both files into that directory using
  the same default filenames:
  - `error_metrics_sfc_{season_slug}_long.csv`;
  - `error_metrics_sfc_{season_slug}_wide.csv`;
- print a short reference summary before writing:
  - e.g. `temperature_2m reference: Observation`;
  - e.g. `precipitation reference: ERA5 (Observation unavailable)`;
  - e.g. `surface flux reference: ERA5 for wet season`.

## Implementation Phases

### Phase 1: Metrics Core

- Add `metrics/scores.py`.
- Add `xskillscore` as a runtime dependency.
- Implement wrappers around:
  - `xs.me` for `bias`;
  - `xs.mae`;
  - `xs.rmse`;
  - `xs.pearson_r`.
- Implement custom helpers only for:
  - paired finite-sample count;
  - precipitation totals;
  - total bias;
  - relative total bias percent.
- Add paired finite-sample filtering.
- Add unit tests with small `xarray.DataArray` inputs and `NaN` values.

### Phase 2: Shared Hourly Time-Series Processing

- Add `plot_core/scenarios/time_series_processing.py` or
  `metrics/processing.py`.
- Move or duplicate only as an intermediate step:
  - hourly-nearest station sampling;
  - MONAN accumulated precipitation to hourly rate;
  - ERA5 precipitation conversion helper.
- Prefer moving reusable behavior into `plot_core/scenarios` if plotting
  recipes also need it.
- Keep generic `plot_core/recipes/time_series.py` unchanged.

### Phase 3: Scalar Time-Series Metrics

- Add `metrics/extraction.py` helpers for time-series adapters.
- Reuse:
  - `build_time_series_comparison_adapters(...)`;
  - `build_time_series_era5_precipitation_adapter(...)`;
  - `build_time_series_comparison_gridded_request(...)`;
  - the existing `cross_5` time-series request pattern for MONAN sources;
  - `build_time_series_comparison_station_request(...)`.
- Reuse:
  - `build_surface_flux_time_series_comparison_adapters(...)`;
  - existing surface-flux request builders;
  - wet-season no-observation rule.
- Implement all v1 reference rules:
  - Observation reference for temperature, humidity and wind;
  - ERA5 reference for precipitation;
  - Observation reference for dry/transition;
  - ERA5 reference for wet.
- Add `scripts/metrics/compute_error_metrics.py`.

### Phase 4: Vertical Profiles

- Keep deferred.
- Before implementing vertical-profile metrics, decide how to interpolate or
  align pressure levels among MONAN, ERA5 and radiosonde profiles.
- Do not include vertical-profile code in v1.

## Test Plan

Static checks:

```text
python -m py_compile metrics/*.py scripts/metrics/*.py
```

Unit checks:

- paired finite-sample filtering removes unpaired `NaN` values;
- `bias`, `mae`, `rmse`, `corr` wrappers return the same values as direct
  `xskillscore` calls;
- `bias` uses the correct sign convention, `candidate - reference`;
- MONAN extraction uses `cross_5` spatial mean values for candidate series;
- precipitation totals ignore `NaN` increments consistently;
- full-mode timestamp alignment keeps only shared times;
- reference-selection rules choose Observation or ERA5 as expected for each
  variable and season.

CLI smoke checks:

```text
python scripts/metrics/compute_error_metrics.py --help
```

Real-data smoke checks where data and dependencies are available:

```text
python scripts/metrics/compute_error_metrics.py --init-date 20141002
python scripts/metrics/compute_error_metrics.py --init-date 20140802
python scripts/metrics/compute_error_metrics.py --init-date 20140216
```

## Assumptions

- Existing scenario path builders are the source of truth for data locations.
- Existing canonical variable names are the source of truth for variable
  semantics.
- Metrics should compare only paired finite samples.
- V1 uses hourly values only, not hourly-mean values.
- Observation is preferred when available, but ERA5 fallback is acceptable
  when explicitly recorded.
- Precipitation Observation is unavailable for the supported comparison cases.
- Real-data tests may depend on mounted data paths and optional GRIB/NetCDF
  dependencies.

## Open Questions

- What interpolation or pressure-level alignment strategy should be used when
  vertical-profile metrics are implemented later?
