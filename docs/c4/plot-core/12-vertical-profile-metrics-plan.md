# Vertical-Profile Error Metrics Plan

## Summary

Extend the existing metrics project to compute full-mode vertical-profile
error metrics for SHOC and MYNN against GoAmazon radiosonde observations.

The vertical-profile metrics are separate from the surface metrics outputs.
They evaluate the same vertical-profile comparison scenario used by
`generate_vertical_profile_comparison.py`, but export tabular metrics instead
of figures.

V1 implements full mode only. Hourly-mean vertical-profile metrics remain out
of scope because radiosonde launches have moving horizontal positions and
irregular/native pressure levels that require additional averaging decisions.

## References

- [Surface error metrics plan](./11-error-metrics-project-plan.md)
- [Recipe guide](./07-como-criar-um-recipe.md)
- [Source specifications and requests](./03c-source-and-requests.md)
- [Data adapter](./03f-data-adapter.md)
- [Scenario paths](../../../plot_core/scenarios/paths.py)
- [Scenario adapters](../../../plot_core/scenarios/adapters.py)
- [Scenario source specifications](../../../plot_core/scenarios/source_specifications.py)
- [Scenario requests](../../../plot_core/scenarios/requests.py)
- [Scenario recipes](../../../plot_core/scenarios/recipes.py)
- [Metrics extraction](../../../metrics/extraction.py)
- [Metrics registry](../../../metrics/registry.py)
- [Metrics scores](../../../metrics/scores.py)

## Goals

- Add vertical-profile metrics for supported cases:
  - `20141002` / transition season;
  - `20140802` / dry season;
  - `20140216` / wet season.
- Use full-mode synoptic profiles only.
- Compare SHOC and MYNN against radiosonde Observation.
- Evaluate the same four synoptic UTC hours used by the vertical-profile
  recipe: `00`, `06`, `12`, and `18 UTC`.
- Evaluate all five forecast days, for a maximum of 20 target profiles per
  case.
- Report one metric value per source, variable, season and synoptic hour over
  the whole `1000-700 hPa` layer.
- Reuse `plot_core` data access, canonical variable names, source
  specifications, requests, geometry handling, derivations and adapters.

## Non-Goals

- Do not implement hourly-mean vertical-profile metrics in v1.
- Do not produce one metric row per pressure level in v1.
- Do not add plotting code.
- Do not bypass `DataAdapter`, `SourceSpecification`,
  `VerticalProfileRequest`, `GeometryHandler` or existing scenario path and
  adapter builders.
- Do not compare vertical profiles against ERA5 when radiosonde observation is
  available.
- Do not include ERA5 in v1 vertical-profile metrics.
- Do not add precipitation or surface-flux logic to the vertical-profile
  metrics path.

## Variables

Compute metrics for:

- `theta`
  - label: `Potential temperature`;
  - units: `K`.
- `qv`
  - label: `Specific humidity`;
  - units: `g kg^-1`.
- `wind_speed`
  - label: `Wind speed`;
  - units: `m s^-1`.

Use the same canonical variables and derivations as the vertical-profile plot
recipe:

- SHOC/MYNN:
  - `theta` from raw `theta`;
  - `qv` from raw `qv`, converted from `kg kg^-1` to `g kg^-1`;
  - `wind_speed` derived from `u` and `v`.
- Radiosonde:
  - `theta` derived from `tdry` and `pres`;
  - `qv` derived from dewpoint `dp` and pressure `pres`;
  - `wind_speed` from `wspd`.

## Reference Rules

For all vertical-profile variables and all seasons:

- reference source: `Observation`;
- reference data: GoAmazon radiosonde;
- candidate sources: `SHOC`, `MYNN`.

If the nearest radiosonde launch for a target time is unavailable or outside
the accepted tolerance, skip that target profile for every candidate source
and record the reduced sample count in the output.

## Target Times

For each supported init date:

- build target times from the init datetime plus forecast-day offsets `0..4`;
- for each forecast day, evaluate `00`, `06`, `12`, and `18 UTC`;
- use UTC internally for matching and metrics;
- local-time labels are not needed in metrics outputs.

Use the same radiosonde nearest-launch selection strategy as the
vertical-profile plot recipe:

- reuse `build_goamazon_radiosonde_glob_patterns(...)` for the exact
  five-day file window;
- reuse `parse_goamazon_radiosonde_launch_datetime(...)` to parse launch time
  from `maosondewnpnM1.b1.{YYYYMMDD}.{HHMMSS}.cdf`;
- reuse `find_nearest_goamazon_radiosonde_path(...)` to choose the file with
  minimum absolute time difference from the target time.

Add a maximum launch-time tolerance on top of the existing nearest-path
selection:

- recommended v1 tolerance: `3 hours`;
- after selecting the nearest path, parse its launch datetime with
  `parse_goamazon_radiosonde_launch_datetime(...)`;
- if nearest launch is farther than the tolerance, skip that target profile;
- include the count of accepted target profiles in the output metadata or row
  fields.

## Spatial Sampling

Use reference coordinate:

- latitude: `-3.21`;
- longitude: `-60.6`.

For candidate sources:

- SHOC:
  - use `VerticalProfileRequest(point_sample_pattern="cross_5")`;
  - compute the mean profile across the five sampled grid points;
  - use the mean profile for metrics.
- MYNN:
  - same as SHOC.

For radiosonde:

- use moving-point geometry;
- do not spatially sample to the reference coordinate;
- preserve the radiosonde native pressure coordinate and profile values.

## Vertical Alignment

Each MONAN candidate profile defines its own pressure levels for comparison.
SHOC and MYNN pressure levels are not assumed to match exactly, so align each
candidate source independently against the radiosonde profile.

For each target time, source and variable:

1. Load the nearest radiosonde profile.
2. Load the MONAN candidate profile using `cross_5` and compute the spatial
   mean profile.
3. Use the MONAN candidate pressure levels as the comparison levels.
4. Keep only MONAN pressure levels within `1000-700 hPa`, inclusive.
5. For each kept MONAN pressure level, select the radiosonde sample whose
   observed `pres` value is nearest in pressure.
6. Compare the MONAN candidate value at the MONAN pressure level against the
   radiosonde value at the nearest observed pressure level.
7. Keep only paired finite values.

Important details:

- interpolation is nearest-neighbor in pressure, not linear interpolation;
- do not interpolate the model to radiosonde levels;
- do not use a fixed pressure grid in v1;
- SHOC pressure comes from SHOC's model `pressure` variable;
- MYNN pressure comes from MYNN's model `pressure` variable;
- SHOC and MYNN may produce different comparison pressure levels and sample
  counts;
- the radiosonde may reuse the same observed pressure sample for adjacent
  MONAN levels if nearest-neighbor matching selects it more than once;
- display/metric pressure units are `hPa`.

## Metric Aggregation

Aggregate valid paired samples separately for each synoptic UTC hour.

For each source, variable and synoptic hour, aggregate across:

- forecast days;
- MONAN pressure levels in the `1000-700 hPa` layer.

For each `(season, source, variable, synoptic_hour_utc)` group, compute one
set of metrics over all valid paired samples. The four output groups are:

- `00 UTC`;
- `06 UTC`;
- `12 UTC`;
- `18 UTC`.

Metrics:

- `bias`;
- `mae`;
- `rmse`;
- `corr`.

Use `xskillscore` for deterministic metrics, consistent with the existing
surface metrics module. Keep custom code limited to alignment, finite-pair
filtering and sample-count metadata.

## Output Files

Write outputs separately from surface metrics using the `vp` marker:

```text
error_metrics_vp_{season_slug}_long.csv
error_metrics_vp_{season_slug}_wide.csv
error_metrics_vp_{season_slug}_table.tex
```

The long CSV should keep the current row-per-metric style:

```text
case_init_date,season,metric_family,variable,variable_label,source,
reference_source,synoptic_hour_utc,metric,value,units,n_samples,n_profiles
```

The wide CSV should keep one row per source, variable and synoptic hour:

```text
case_init_date,season,metric_family,variable,variable_label,source,
reference_source,synoptic_hour_utc,units,n_samples,n_profiles,bias,mae,rmse,corr
```

The LaTeX table should mirror the current selected table format:

- separate `Source` column;
- source cells grouped with `\multirow`;
- rows grouped by synoptic hour, then source;
- columns:
  - `Synoptic hour (UTC)`;
  - `Source`;
  - `Variable`;
  - `Unit`;
  - `Bias`;
  - `MAE`;
  - `RMSE`;
  - `$r$`;
- include SHOC and MYNN unless a source has no valid samples.

## CLI Behavior

Use a separate command from the surface metrics command:

```text
scripts/metrics/compute_vertical_profile_error_metrics.py
```

CLI options:

```text
--init-date {20141002,20140802,20140216}
--output-dir PATH
```

No `--mode` option in v1. Full mode is the only implemented mode.

Default output directory:

```text
tests/output/metrics
```

## Proposed Package Changes

Extend the existing `metrics` package instead of creating an unrelated
implementation.

Recommended additions:

- `metrics/vertical_profiles.py`
  - target-time construction;
  - nearest radiosonde profile extraction;
  - candidate profile extraction;
  - pressure nearest-neighbor alignment;
  - aggregation into paired arrays.
- `metrics/registry.py`
  - add vertical-profile metric family;
  - add labels/units for `theta`, `qv`, and `wind_speed`.
- `metrics/tables.py`
  - add vertical-profile default output names;
  - add a vertical-profile LaTeX table builder or generalize the current
    table builder.
- `scripts/metrics/compute_vertical_profile_error_metrics.py`
  - orchestrate init-date selection, extraction, scoring and output writing.

Avoid importing private plotting helpers from `plot_core/scenarios/recipes.py`.
If the vertical-profile recipe contains reusable non-plotting logic, move that
logic into a neutral scenario/metrics helper before sharing it.

## Implementation Notes

- Keep adapter closing explicit with `try/finally`.
- Reuse the radiosonde filename parsing and nearest-file selector from
  `plot_core.scenarios.paths`; do not duplicate glob or launch-time parsing
  logic in the metrics package.
- Preserve the fixed row-order bug fix from the plot recipe: when target times
  are displayed or processed in a reordered form, radiosonde selections must
  follow the same target time, not a stale row index.
- For SHOC/MYNN `cross_5` profiles, use the mean profile returned by
  `DataAdapter.to_vertical_profile_mean_std_plot_data(...)`; std bands are
  plot-only and not used in metrics v1.
- For radiosonde profiles, use `DataAdapter.to_vertical_profile_plot_data(...)`
  with moving-point geometry.
- Do not build or open the ERA5 vertical-profile adapter in v1 metrics.
- Do not compute metrics independently for each profile and then average the
  metrics. Instead, for each source, variable and synoptic hour, concatenate
  all valid paired samples from the five forecast days first, then compute one
  metric over that synoptic-hour sample set.

## Test Plan

Static checks:

```bash
python -m py_compile \
  metrics/registry.py \
  metrics/tables.py \
  metrics/vertical_profiles.py \
  scripts/metrics/compute_vertical_profile_error_metrics.py
```

Synthetic checks:

- nearest-pressure matching selects expected radiosonde levels for a given
  MONAN pressure level;
- nearest-pressure matching handles descending and ascending pressure arrays;
- pressure-window filtering keeps only `1000-700 hPa`;
- missing/NaN candidate or reference values are excluded pairwise;
- SHOC/MYNN extraction uses `cross_5`;
- SHOC and MYNN alignment paths are independent and can produce different
  sample counts;
- ERA5 is not extracted in v1;
- radiosonde launch selection respects the maximum time tolerance;
- metric aggregation computes one value for each source, variable and
  synoptic hour over all valid forecast-day/pressure samples;
- output rows include `synoptic_hour_utc` and contain all four expected hours
  when enough valid samples exist.

CLI smoke:

```bash
python scripts/metrics/compute_vertical_profile_error_metrics.py --help
```

Real-data smoke, where data and dependencies are available:

```bash
python scripts/metrics/compute_vertical_profile_error_metrics.py \
  --init-date 20141002

python scripts/metrics/compute_vertical_profile_error_metrics.py \
  --init-date 20140802

python scripts/metrics/compute_vertical_profile_error_metrics.py \
  --init-date 20140216
```

## Assumptions

- Full mode is the only vertical-profile metrics mode in v1.
- Radiosonde is always the reference source.
- Each MONAN source's pressure levels define its own comparison levels.
- Radiosonde profiles are matched to MONAN levels by nearest pressure.
- Metrics are aggregated over the whole `1000-700 hPa` layer separately for
  each synoptic UTC hour.
- SHOC/MYNN use `cross_5` spatial mean.
- ERA5 is excluded from v1 vertical-profile metrics.
- Metrics use paired finite samples only.
