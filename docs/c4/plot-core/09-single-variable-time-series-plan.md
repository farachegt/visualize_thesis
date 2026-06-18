# Plan: HPBL time-series comparison

This document is an implementation brief for a new official time-series
comparison plot.

The new plot compares boundary-layer height between:

- SHOC;
- MYNN;
- ERA5;
- Observation.

The implementation should reuse the existing generic time-series recipe and
mirror the execution behavior of the surface-flux comparison script where it
makes sense. The surface-flux plot is a reference workflow, not the target
plot.

## References

- [Recipe guide](./07-como-criar-um-recipe.md)
- [Generic time-series recipe](./recipes/18-time-series-panels.md)
- [Reference script](
  ../../../scripts/recipes/generate_surface_flux_time_series_comparison.py
  )
- [Scenario builders](../../../plot_core/scenarios/recipes.py)
- [Scenario paths](../../../plot_core/scenarios/paths.py)
- [Scenario adapters](../../../plot_core/scenarios/adapters.py)
- [Scenario source specifications](
  ../../../plot_core/scenarios/source_specifications.py
  )

## Goal

Create a new one-panel time-series comparison figure for the existing
canonical variable `hpbl`.

The new figure should:

- plot `hpbl` as PBL height in meters;
- compare SHOC, MYNN, ERA5 and Observation;
- support the same execution modes as the reference:
  - `full`;
  - `hourly-mean`;
- support the same init-date choices as the reference:
  - `20141002`;
  - `20140802`;
  - `20140216`;
- include Observation for all three init dates, including `20140216`;
- use one panel instead of the two surface-flux panels.

The target script name is:

```text
scripts/recipes/generate_hpbl_time_series_comparison.py
```

The target default output-name pattern is:

```text
time_series_hpbl_{season}_season_{mode}.png
```

## What the Reference Does

The reference script is
`scripts/recipes/generate_surface_flux_time_series_comparison.py`.

It generates a SHOC/MYNN/ERA5/Observation comparison for surface fluxes and
is useful because it already implements the CLI, adapter lifecycle,
time-window handling, local-time display and `full` versus `hourly-mean`
mode split needed by the new HPBL plot.

The new HPBL plot should not copy the surface-flux variable mappings or the
surface-flux observation omission rule.

CLI behavior:

- `--mode full`
  - plots the full 5-day time series;
- `--mode hourly-mean`
  - plots local-hour means over the same 5-day window;
- `--init-date`
  - accepts `20141002`, `20140802`, and `20140216`;
- default init date:
  - `20141002`;
- optional `--output`
  - otherwise writes under `tests/output/`.

The default reference output path is:

```text
tests/output/time_series_comparison_sf_{season}_{mode}.png
```

The new HPBL script should use its own output pattern instead:

```text
tests/output/time_series_hpbl_{season}_season_{mode}.png
```

## Reference Data Flow

The reference script is intentionally thin. The new script should keep the
same division of responsibilities.

The script should:

1. parse CLI options;
2. normalize `hourly-mean` to the scenario mode `hourly_mean`;
3. build adapters through `plot_core/scenarios`;
4. build the figure through `plot_core/scenarios`;
5. save the figure;
6. close all adapters.

The scenario builder should do the real composition work. Batch behavior and
`savefig(...)` should remain in `scripts/recipes/`.

## Reference Sources

The surface-flux reference uses this source order:

- SHOC;
- MYNN;
- ERA5;
- Observation.

The new HPBL plot should use the same source order.

For init date `20140216`, the observation source is omitted by the scenario
builder because surface-flux observations are marked unavailable for that
case.

For the new recipe, `20140216` does have observation data. The new scenario
should not reuse the surface-flux observation omission rule as-is.

Current reference source styles:

- SHOC: blue;
- MYNN: orange;
- ERA5: gray;
- Observation: black.

## Reference Time Semantics

The comparison window starts at init date `00:00` and lasts 5 days.

The display uses local time with a GMT-4 offset.

In `full` mode:

- the x-axis keeps UTC values internally;
- tick labels are displayed as local time;
- tick step is 12 hours;
- the final hour is included as a tick when needed.

In `hourly_mean` mode:

- data are reduced to 24 local-hour means;
- the x-axis is local hour `0..23`;
- tick step is 3 hours.

## Reference Layer Behavior

For SHOC and MYNN:

- full mode samples the model point with the `cross_5` pattern;
- full mode plots mean plus standard-deviation band;
- hourly-mean mode computes local-hour mean and standard-deviation bands.

For ERA5:

- full mode plots a line directly from the gridded request;
- hourly-mean mode plots local-hour means;
- no standard-deviation band is added.

For Observation:

- the raw station series is reduced to nearest hourly samples first;
- full mode plots those hourly samples;
- hourly-mean mode computes local-hour means from those hourly samples;
- no standard-deviation band is added.

## Reference Panels

The reference has two stacked panels:

- `sensible_heat_flux`
  - y-axis label: `Sensible heat flux [W/m2]`;
- `latent_heat_flux`
  - y-axis label: `Latent heat flux [W/m2]`.

The new plot should use one panel instead.

## New Plot Variable

Resolved variable decisions:

- canonical variable name:
  - `hpbl`;
- SHOC raw source variable:
  - `hpbl`;
- MYNN raw source variable:
  - `hpbl`;
- SHOC adapter glob patterns:
  - `/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_shoc_transition_season/2014100200/diag/posprocess/*.nc`;
  - `/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_shoc_dry_season/2014080200/diag/posprocess/*.nc`;
  - `/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_shoc_wet_season/2014021600/diag/posprocess/*.nc`;
- MYNN adapter glob patterns:
  - `/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_mynn_transition_season/2014100200/diag/posprocess/*.nc`;
  - `/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_mynn_dry_season/2014080200/diag/posprocess/*.nc`;
  - `/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_mynn_wet_season/2014021600/diag/posprocess/*.nc`;
- ERA5 raw source variable:
  - `blh`;
- ERA5 dataset files:
  - `sl_20141002.grib`;
  - `sl_20140802.grib`;
  - `sl_20140216.grib`;
- Observation raw source variable:
  - `bl_height_1`;
- Observation adapter glob pattern:
  - `/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/a0 (Derived Minimal Quality Control)/maoceilpblhtM1.a0/*.cdf`;
- source units:
  - meters;
- target units:
  - meters, with no unit conversion needed;
- y-axis label:
  - `PBL Height [m]`.

Implementation note:

- the project already uses `hpbl` as the canonical name for PBL height;
- this recipe should keep that existing canonical name instead of introducing
  a new `pblh` alias.

## Reference Figure Layout

The reference figure uses:

- `nrows=2`;
- `ncols=1`;
- shared x-axis;
- constrained layout;
- legend only on the first panel;
- full-mode figure size `(13, 8)`;
- hourly-mean figure size `(10, 8)`;
- title including:
  - source labels;
  - `Surface-Flux Time-Series Comparison`;
  - season label;
  - init date.

For the new one-panel plot, the likely layout is:

- `nrows=1`;
- `ncols=1`;
- same source styling;
- same local-time x-axis handling;
- legend on the only panel;
- adjusted figure size.

## Likely Implementation Shape

The generic time-series recipe already exists:

- `plot_time_series_panels(...)`
- `TimeSeriesLayerInput`
- `PreparedTimeSeriesLayerInput`
- `TimeSeriesPanelInput`

Because of that, this work likely does not need a new generic recipe in
`plot_core/recipes/`.

The likely implementation is a new scenario-level figure builder plus a new
script:

- add or reuse source specifications for the new variable;
- add or reuse adapters for the relevant sources;
- add scenario builders in `plot_core/scenarios/recipes.py`;
- export new scenario builders in `plot_core/scenarios/__init__.py`;
- add a script under `scripts/recipes/`;
- optionally add a recipe/scenario doc if this becomes an official documented
  plot.

## Adapter Reuse Strategy

The new recipe should reuse the reference behavior, but not all
surface-flux-specific adapters.

SHOC and MYNN:

- do not reuse `build_surface_flux_time_series_shoc_adapter(...)` or
  `build_surface_flux_time_series_mynn_adapter(...)` directly, because their
  source specifications only expose surface-flux variables;
- reuse the existing MONAN time-series path and reader setup through the
  generic SHOC/MYNN time-series adapters;
- add or align the generic SHOC/MYNN time-series source specifications so
  canonical `hpbl` maps to the raw MONAN variable `hpbl`.

ERA5:

- prefer reusing the generic ERA5 time-series adapter, because it already
  points to the `sl_*.grib` single-level files;
- add or align its source specification so canonical `hpbl` maps to ERA5
  `blh`;
- if `cfgrib` cannot open the mixed single-level GRIB cleanly, create a
  HPBL-specific ERA5 adapter with a `shortName="blh"` filter.

Observation:

- do not reuse the surface-flux eddy-correlation observation adapter, because
  it only maps flux variables;
- create or identify an observation adapter/source specification for the
  dataset that contains `bl_height_1`.

## Decisions Needed

- [x] Canonical variable name to plot.
      Decision: `hpbl`.
- [x] Raw source variable name for SHOC.
      Decision: `hpbl`.
- [x] Raw source variable name for MYNN.
      Decision: `hpbl`.
- [x] SHOC and MYNN adapter paths.
      Decision: use the existing MONAN time-series glob pattern under
      `/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout`
      for the `shoc` and `mynn` schemes and the dry, transition, and wet
      season init dates.
- [x] Adapter reuse strategy.
      Decision: reuse generic SHOC/MYNN and ERA5 time-series adapter
      structure where possible, but do not reuse the surface-flux-specific
      adapters directly. Observation needs a separate adapter for
      `bl_height_1`.
- [x] ERA5 variable or GRIB `shortName`, if ERA5 remains in the comparison.
      Decision: `blh`.
- [x] ERA5 dataset files.
      Decision: use the single-level ERA5 GRIB files
      `sl_20141002.grib`, `sl_20140802.grib`, and `sl_20140216.grib`.
- [x] Observation raw variable, if Observation remains in the comparison.
      Decision: `bl_height_1`.
- [x] Observation dataset or adapter to use for `bl_height_1`.
      Decision: use
      `/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/a0 (Derived Minimal Quality Control)/maoceilpblhtM1.a0/*.cdf`.
- [x] Target units and any unit conversion.
      Decision: all sources are already in meters, with target units meters.
- [x] Y-axis label.
      Decision: `PBL Height [m]`.
- [x] Figure title wording.
      Decision:
      `PBL Height Time-Series Comparison: SHOC, MYNN, ERA5 and Observation - {Season} (init {YYYY-MM-DD})`.
- [x] Output filename slug.
      Decision: `time_series_hpbl_{season}_season_{mode}.png`.
- [x] Whether autoscaling is acceptable or fixed y-axis limits are needed.
      Decision: use y-axis autoscaling for now.
- [x] Whether the `20140216` observation omission should be reused exactly.
      Decision: no. Observation data exists for `20140216` in this new
      recipe.
- [x] Whether the same MONAN `cross_5` mean/std behavior should be reused.
      Decision: yes.
- [x] Whether the same GMT-4 local-time display should be reused.
      Decision: yes.
- [x] Preferred script name.
      Decision: `generate_hpbl_time_series_comparison.py`.

## Working Assumptions To Confirm

- The source set remains SHOC/MYNN/ERA5/Observation for all three init
  dates, including `20140216`.
  - In this plan, "source set" means the figure should be built with these
    four sources in the same conceptual order used by the reference:
    SHOC, MYNN, ERA5, then Observation.
  - The legend should show all four labels whenever the figure is generated.
  - The scenario builder should not apply the surface-flux special case that
    drops Observation for `20140216`.
  - If one of these four sources is unavailable during execution, that should
    be treated as a missing-input problem to fix explicitly, not as a reason
    to silently remove the source from the plot.
- The init-date choices remain `20141002`, `20140802`, and `20140216`.
- The default init date remains `20141002`.
- The time window remains 5 days.
- The plot location and request geometry remain the same as the reference.
- The new figure has one panel.
- The line colors remain the same as the reference.
- SHOC and MYNN keep mean plus standard-deviation bands.
- ERA5 and Observation remain line-only.
- `hourly-mean` keeps the same local-hour reduction behavior.
- MONAN uses the same `cross_5` mean/std behavior as the surface-flux
  reference.
- The x-axis uses the same GMT-4 local-time display as the surface-flux
  reference.

## Candidate Validation

Once implemented, run smoke checks for the new script:

```bash
python scripts/recipes/generate_hpbl_time_series_comparison.py \
  --mode full \
  --init-date 20141002

python scripts/recipes/generate_hpbl_time_series_comparison.py \
  --mode hourly-mean \
  --init-date 20141002
```

Then repeat for:

- `20140802`;
- `20140216`.

The `20140216` check should verify that Observation is included.
