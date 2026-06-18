# Plan: HPBL observation 30-minute rolling-statistics preprocessing

This document plans a parallel preprocessing workflow for the GoAmazon
ceilometer PBL-height observations used by the HPBL time-series plot.

The existing preprocessing workflow creates hourly values by selecting the
nearest finite `bl_height_1` value within `+/-5 min`. This new workflow should
preserve the raw observation time grid and compute a true centered rolling
statistic over a 30-minute window.

## References

- [HPBL time-series comparison plan](./09-single-variable-time-series-plan.md)
- [Existing nearest-value preprocessor](
  ../../../scripts/preprocessing/preprocess_hpbl_observation_hourly_nearest.py
  )
- [Scenario paths](../../../plot_core/scenarios/paths.py)
- [Scenario adapters](../../../plot_core/scenarios/adapters.py)
- [HPBL plot scenario](../../../plot_core/scenarios/recipes.py)

## Goal

Add another preprocessing script for the same raw observation files:

```text
/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/a0 (Derived Minimal Quality Control)/maoceilpblhtM1.a0/*.cdf
```

The new script should:

- read raw 16-second `bl_height_1` observations;
- keep the original observation timestamps for each output day;
- compute a centered 30-minute rolling statistic at each raw timestamp;
- support both rolling mean and rolling median;
- ignore `NaN` and non-finite values inside each rolling window;
- write one processed file per day;
- keep the raw dataset filename pattern in the processed output directory.

## Rolling-Statistic Rule

For each raw timestamp `T`, compute one of:

```text
mean(valid bl_height_1 samples in [T - 15 min, T + 15 min])
median(valid bl_height_1 samples in [T - 15 min, T + 15 min])
```

Rules:

- the 30-minute period is centered on each raw timestamp;
- both window endpoints are included;
- `NaN` and non-finite values are ignored;
- if no finite samples exist inside the 30-minute window, write `NaN`;
- output times keep the raw timestamps for the target day;
- output units remain meters.

To handle edge timestamps correctly, the preprocessor should include
neighboring raw files when available, so timestamps near midnight can use
samples from the previous or next day.

## Output Products

Create one processed-data directory per rolling statistic beside the raw data:

```text
/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/a0 (Derived Minimal Quality Control)/maoceilpblhtM1.a0/rolling_mean_30min/
/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/a0 (Derived Minimal Quality Control)/maoceilpblhtM1.a0/rolling_median_30min/
```

Output one file per day, preserving the raw filename pattern:

```text
maoceilpblhtM1.a0.YYYYMMDD.cdf
```

The generated NetCDF-compatible file should contain:

- coordinate:
  - `time`;
- variable:
  - `bl_height_1`;
- variable units:
  - `m`;
- metadata:
  - source path pattern;
  - source files used;
  - processing method:
    - `rolling_mean_ignore_nan`; or
    - `rolling_median_ignore_nan`;
  - processing window: `30 minutes`;
  - centered window: `true`.

## CLI Shape

Add a parallel script:

```text
scripts/preprocessing/preprocess_hpbl_observation_rolling_statistic.py
```

The script should support:

- `--method {mean,median}`
  - required rolling statistic selector;
- `--init-date {20141002,20140802,20140216}`
  - process the 5-day window for one initialization date;
- `--all`
  - process all supported initialization dates;
- `--output-dir`
  - optional override for the default method-specific processed-data
    directory;
- `--window-minutes`
  - default `30`;
- `--overwrite`
  - rewrite existing processed files;
- default behavior without `--overwrite`
  - skip existing files with an explicit message.

Example commands:

```bash
python scripts/preprocessing/preprocess_hpbl_observation_rolling_statistic.py --method mean --all --overwrite
python scripts/preprocessing/preprocess_hpbl_observation_rolling_statistic.py --method median --all --overwrite
```

## Scenario Integration

The rolling-statistics products should be added as parallel observation
products, not as replacements for the nearest-value product.

Implementation should add:

- scenario path constants for the rolling-mean and rolling-median output
  directories;
- scenario path builders returning exact daily rolling-statistic files for an
  init date;
- optionally, dedicated adapter builders for the rolling-mean and
  rolling-median products.

The existing nearest-value adapter and plot behavior should remain unchanged
until the plot or metrics workflow explicitly chooses one of the rolling
products.

## Tests

Add focused tests for the rolling-statistic logic using synthetic arrays:

- rolling mean with all finite values:
  - output arithmetic mean inside each centered window;
- rolling median with all finite values:
  - output median inside each centered window;
- mixed finite and `NaN` values:
  - ignore `NaN` and non-finite values;
- all values inside the window are `NaN`:
  - output `NaN`;
- finite values exist only outside `+/-15 min`:
  - output `NaN`;
- samples exactly at `T - 15 min` and `T + 15 min`:
  - include both endpoint samples;
- target-day edge timestamps:
  - allow neighboring raw-file samples to influence the rolling value.

Operational validation on the data machine:

```bash
python scripts/preprocessing/preprocess_hpbl_observation_rolling_statistic.py --method mean --all --overwrite
python scripts/preprocessing/preprocess_hpbl_observation_rolling_statistic.py --method median --all --overwrite
```

If a workflow is switched to one of these products later, rerun the relevant
HPBL plot or metrics command against the selected adapter.

## Assumptions

- The raw files contain `time` and `bl_height_1`.
- The raw data path is available on the machine where preprocessing runs.
- The rolling-statistics files are data products and should not be committed
  to git.
- Rolling mean and rolling median should coexist with the nearest-value
  product.
- The HPBL plot should not switch to rolling-statistic observations until that
  is explicitly requested.
