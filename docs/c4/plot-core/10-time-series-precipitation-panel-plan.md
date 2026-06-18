# Add Precipitation Panel to Time-Series Comparison

## Summary

Extend `generate_time_series_comparison.py` from a 3x1 figure to a 4x1
figure by adding a precipitation panel below wind speed.

The existing temperature, humidity and wind panels keep their current line
and standard-deviation-band behavior. The new precipitation panel uses bars,
because precipitation is time-indexed accumulation/rate data; a histogram
would show value distribution and would lose event timing.

## References

- [Recipe guide](./07-como-criar-um-recipe.md)
- [Generic time-series recipe](./recipes/18-time-series-panels.md)
- [Time-series comparison plan](./08-time-series-recipe-plan.md)
- [Scenario recipe builders](../../../plot_core/scenarios/recipes.py)
- [Scenario source specifications](../../../plot_core/scenarios/source_specifications.py)
- [Renderer](../../../plot_core/rendering.py)
- [Plot data](../../../plot_core/plot_data.py)

## Target Behavior

- The meteorological comparison becomes 4 panels in this order:
  - `temperature_2m`: line plot, unchanged;
  - `specific_humidity_2m`: line plot, unchanged;
  - `wind_speed_10m`: line plot, unchanged;
  - `precipitation`: bar plot, new.
- The same sources are compared in the same order:
  - SHOC;
  - MYNN;
  - ERA5;
  - Observation.
- The same CLI remains unchanged:
  - `--mode {full,hourly-mean}`;
  - `--init-date {20141002,20140802,20140216}`;
  - `--output PATH`.
- The same local-time display convention remains unchanged:
  - internal timestamps stay UTC;
  - labels use GMT-4/local time.
- Default output naming remains unchanged.

## Bar Rendering Support

Add a generic bar-capable time-series plot data type instead of drawing bars
directly in scenario code.

Required reusable changes:

- Add `TimeSeriesBarPlotData` to `plot_core/plot_data.py`.
  - Fields should mirror `TimeSeriesPlotData` where possible:
    - `label`;
    - `times`;
    - `values`;
    - `units`;
    - optional `site_label`;
    - optional `vertical_label`;
    - `value_axis="value"`;
    - optional `draw_mask`.
- Extend `SpecializedPlotter` in `plot_core/rendering.py`.
  - Add `bar` to `ArtistMethod`.
  - Add `TimeSeriesBarPlotData` to `PlotDataType`.
  - Support `TimeSeriesBarPlotData` with `Axes.bar(...)`.
  - Infer axis semantics as `("time", value_axis)`.
- Extend `PreparedTimeSeriesLayerInput` in
  `plot_core/recipes/time_series.py` to accept `TimeSeriesBarPlotData`.
- Do not add precipitation reduction logic to the generic time-series recipe.

## Precipitation Data Semantics

The precipitation panel should plot hourly precipitation rate/intensity in
`mm/h`.

Use these rules:

- For MONAN:
  - resolve accumulated precipitation as the existing canonical
    `precipitation = rainc + rainnc`;
  - units are `mm`;
  - sort by time;
  - compute hourly precipitation from consecutive differences against the
    previous hour;
  - because the interval is hourly, the numeric difference is plotted as
    `mm/h`;
  - use `NaN` for the first sample if no previous accumulation exists;
  - if accumulation resets and the difference is negative, treat that
    increment as `NaN` rather than clipping to zero.
- For ERA5:
  - open the single-level GRIB with
    `backend_kwargs={"filter_by_keys": {"shortName": "tp"}}`;
  - source variable is `tp`;
  - `tp` is already accumulated over the previous hour;
  - source units are `m/h`;
  - convert to `mm/h` by multiplying by `1000`;
  - do not deaccumulate ERA5 `tp`.
- For Observation:
  - use the GoAmazon rain-gauge product, not the MET station product;
  - source variable is `rain_rate`;
  - source sampling is one value per minute;
  - source units are `mm/hr`, converted/normalized to `mm/h`;
  - compute an hourly series by averaging minute `rain_rate` samples inside
    each hour.
  - This is an arithmetic mean of rates, not a sum:
    - all valid samples from `HH:00` through `HH:59` contribute to the hour
      labeled `HH:00`;
    - `hourly_rate = mean(minute rain_rate values in that hour)`;
    - the unit remains `mm/h`;
    - do not multiply by `1/60` and do not sum the minute values, because the
      source variable is already a rate rather than per-minute accumulated
      depth.
- For `full` mode:
  - plot the hourly `mm/h` values through the full 5-day window;
  - SHOC/MYNN should use nearest-point precipitation for v1, not `cross_5`
    spatial mean/std bars.
- For `hourly_mean` mode:
  - compute source-specific hourly `mm/h` values first;
  - group increments by local hour `0..23`;
  - plot the mean precipitation rate for each local hour.

## Source Specifications

Current state:

- MONAN already has canonical `precipitation = rainc + rainnc` in the legacy
  MONAN source spec.
- The active surface time-series SHOC/MYNN source specs do not yet expose
  precipitation.
- ERA5 time-series specs and GoAmazon rain-gauge observation specs do not yet
  expose precipitation for this comparison.

Required source-spec and adapter changes:

- SHOC/MYNN surface time-series specs:
  - add `rainc`;
  - add `rainnc`;
  - add canonical `precipitation` with derivation
    `precipitation_from_rainc_rainnc`;
  - source units: `mm`.
- ERA5 precipitation must use a separate precipitation-specific adapter.
  - Reuse the existing `sl_{YYYYMMDD}.grib` path.
  - Open with
    `backend_kwargs={"filter_by_keys": {"shortName": "tp"}}`.
  - Add a precipitation-specific ERA5 source spec mapping
    `precipitation -> tp`.
  - Use `input_units="m h^-1"` and `target_units="mm h^-1"` if Pint accepts
    the string; otherwise convert from `m/h` to `mm/h` in the scenario helper.
- GoAmazon rain-gauge Observation must use a separate precipitation-specific
  adapter.
  - Directory:
    `/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/b1 (Quality Control applied)/Rain Gauge`
  - Exact daily file pattern:
    `maoraintbS10.b1.{YYYYMMDD}.*.cdf`
  - Build exact daily glob patterns from `init_date` through the 5-day
    comparison window. Each daily file contains minute-resolution samples
    that are reduced to hourly rates in scenario code.
  - Add a rain-gauge source spec mapping `precipitation -> rain_rate`.
  - Use `input_units="mm hr^-1"` and target/display units `mm h^-1`.
  - Keep site metadata as the existing GoAmazon point if the files do not
    expose usable fixed-point latitude/longitude coordinates.

The existing SHOC/MYNN/ERA5/Observation adapters used for temperature,
humidity and wind should remain unchanged for those panels. The precipitation
panel may use the same SHOC/MYNN adapters after their specs gain rain
variables, but it must use the precipitation-specific ERA5 and rain-gauge
Observation adapters.

## Adapter Wiring Decisions

Use explicit precipitation adapters inside the scenario builder instead of
changing the public script CLI.

Required behavior:

- `build_time_series_comparison_adapters(...)` may continue returning the
  four existing adapters used by temperature, humidity and wind:
  - SHOC;
  - MYNN;
  - ERA5 single-level meteorology;
  - GoAmazon MET station.
- `build_surface_nwp_reanalysis_time_series_comparison_inputs(...)` should
  build or receive the two precipitation-only adapters internally:
  - ERA5 `tp` adapter;
  - GoAmazon rain-gauge adapter.
- Keep the public script call unchanged:
  - `adapters = build_time_series_comparison_adapters(init_date=...)`;
  - `build_surface_nwp_reanalysis_time_series_comparison_figure(adapters=...)`.
- Do not require callers to pass six adapters.
- Close any precipitation-only adapters created inside the scenario builder
  before returning, because precipitation layers should be prepared data
  layers.
- If the implementer chooses to expose a helper, use a private helper such as
  `_build_time_series_precipitation_adapters(init_date=...)`; do not make a
  new CLI-visible concept.

This keeps the original four-source adapter contract for existing callers and
contains the extra precipitation-only data wiring in the scenario layer.

## Scenario Recipe Changes

Update only `plot_core/scenarios/recipes.py` for scenario-specific
composition.

Add precipitation panel metadata:

- variable: `precipitation`;
- y-axis label: `Precipitation [mm/h]`;
- y-axis limits: leave autoscaled in v1 unless real-data review shows a
  fixed range is needed.

Add helper functions near the existing time-series helpers:

- `_build_monan_hourly_precipitation_rate_plot_data(...)`
  - input: accumulated `TimeSeriesPlotData`;
  - output: hourly `mm/h` `TimeSeriesPlotData`.
- `_build_era5_hourly_precipitation_rate_plot_data(...)`
  - input: ERA5 `tp` `TimeSeriesPlotData`;
  - output: hourly `mm/h` `TimeSeriesPlotData`;
  - converts `m/h` to `mm/h`;
  - perform the conversion in this helper if Pint unit conversion from
    `m h^-1` to `mm h^-1` is not reliable in the adapter;
  - does not take consecutive differences.
- `_build_observed_hourly_precipitation_rate_plot_data(...)`
  - input: minute rain-gauge `rain_rate` `TimeSeriesPlotData`;
  - output: hourly `mm/h` `TimeSeriesPlotData`;
  - averages all minute samples in each hour.
  - Must implement rate averaging equivalent to
    `rain_rate.resample(time="1h").mean()`:
    - sort source times first;
    - group minute samples by hour floor;
    - ignore `NaN` values with `np.nanmean`;
    - return `NaN` for hours with no valid minute samples;
    - never sum minute rates.
- `_build_hourly_mean_precipitation_plot_data(...)`
  - input: hourly `mm/h` `TimeSeriesPlotData`;
  - output: 24 local-hour means in `mm/h`.
- `_build_precipitation_bar_layers(...)`
  - returns `PreparedTimeSeriesLayerInput` layers using
    `TimeSeriesBarPlotData`.

Bar placement:

- In `full` mode:
  - use grouped bars around each hourly timestamp;
  - use small minute offsets per source so all four sources remain visible;
  - use the source colors with alpha around `0.55`;
  - legend labels remain one per source.
- In `hourly_mean` mode:
  - use grouped bars around local-hour positions `0..23`;
  - use numeric offsets and width values appropriate for 24 hourly bins.

Use fixed bar geometry constants:

- Source display order and colors stay identical to the line panels.
- For `full` mode:
  - center each group on the hourly timestamp;
  - use bar width `12 minutes`;
  - use offsets `[-18, -6, 6, 18] minutes` for
    `SHOC`, `MYNN`, `ERA5`, `Observation`;
  - if a source has `NaN`, do not render a visible bar for that source/time.
  - extend only the x-axis limits enough to show grouped bars at the first
    and last timestamps:
    - left limit: `start_time - 30 minutes`;
    - right limit: `end_time_exclusive - 1 ns + 30 minutes`;
    - keep tick positions and tick labels unchanged from the existing
      local-time axis helper.
- For `hourly_mean` mode:
  - center each group on integer local-hour positions `0..23`;
  - use bar width `0.18`;
  - use offsets `[-0.27, -0.09, 0.09, 0.27]` for
    `SHOC`, `MYNN`, `ERA5`, `Observation`;
  - keep the x-axis limits as `0..23`, matching the existing hourly-mean
    axis behavior.
- Bar render kwargs:
  - `color`: source color;
  - `alpha`: `0.55`;
  - `align`: `"center"`;
  - `linewidth`: `0.0`.

Panel construction:

- Continue the existing line-panel path for the first three variables.
- For the precipitation panel, use precipitation-specific adapter selection:
  - SHOC/MYNN: existing model adapters with new precipitation mappings;
  - ERA5: precipitation-specific `tp` adapter;
  - Observation: precipitation-specific rain-gauge adapter.
- Use precipitation-specific prepared bar layers only for the precipitation
  panel.
- Keep legend on the first panel only, unless the precipitation bars are hard
  to identify in review; in that case move the same source legend to the
  first panel and do not create a second legend.
- Update the figure layout:
  - `nrows=4`;
  - `ncols=1`;
  - `sharex=True`;
  - suggested figure size:
    - full: `(13, 10)`;
    - hourly_mean: `(10, 10)`.

## Important Constraints

- Do not draw bars directly with `matplotlib` inside scenario code.
  Use `TimeSeriesBarPlotData`, `RenderSpecification`, `PlotLayer`,
  `PlotPanel`, `FigureSpecification` and `SpecializedPlotter`.
- Do not put precipitation deaccumulation in `plot_core/recipes/time_series.py`.
  Keep it in scenario helper code.
- Do not change `generate_surface_flux_time_series_comparison.py`.
- Do not change existing temperature, humidity or wind behavior.
- Do not change output filenames or CLI options.

## Test Plan

Static checks:

```bash
python -m py_compile \
  plot_core/plot_data.py \
  plot_core/rendering.py \
  plot_core/recipes/time_series.py \
  plot_core/scenarios/source_specifications.py \
  plot_core/scenarios/recipes.py \
  scripts/recipes/generate_time_series_comparison.py
```

Lightweight checks:

- Verify `TimeSeriesBarPlotData` supports `artist_method="bar"`.
- Verify bar layers do not break axis semantic validation.
- Verify `build_surface_nwp_reanalysis_time_series_comparison_inputs(...)`
  returns 4 panels.
- Verify the fourth panel has ylabel `Precipitation [mm/h]`.
- Verify the fourth panel uses prepared bar layers, not line layers.
- Verify the ERA5 precipitation adapter includes
  `backend_kwargs={"filter_by_keys": {"shortName": "tp"}}`.
- Verify the rain-gauge path builder returns 5 daily patterns for a 5-day
  comparison window.
- Verify `python scripts/recipes/generate_time_series_comparison.py --help`
  remains lightweight.

Synthetic data checks:

- Build accumulated precipitation values `[0, 1, 3, 6]` and verify hourly
  increments become `[NaN, 1, 2, 3]`.
- Build an accumulation reset, for example `[0, 2, 1]`, and verify the reset
  increment becomes `NaN`.
- Build ERA5 `tp` values in `m/h` and verify they are multiplied by `1000`
  to `mm/h`.
- Build minute-resolution observed `rain_rate` values and verify hourly
  means are computed before local-hour grouping.
- Verify observed `rain_rate` uses arithmetic mean, not sum:
  - minute samples `[60, 60] mm/hr` inside the same hour must produce
    `60 mm/h`, not `120 mm/h` and not `2 mm/h`.
- Build 5 days of hourly rates and verify hourly-mean mode returns 24
  local-hour values.
- Verify grouped bar offsets keep four source layers at distinct x positions.

Real-data smoke checks where data and dependencies are mounted:

```bash
python scripts/recipes/generate_time_series_comparison.py \
  --init-date 20141002 \
  --mode full

python scripts/recipes/generate_time_series_comparison.py \
  --init-date 20141002 \
  --mode hourly-mean
```

Review outputs for:

- correct 4x1 layout;
- readable precipitation bars;
- unchanged temperature/humidity/wind panels;
- local-time x-axis labels;
- no duplicate legend entries.

## Assumptions

- Bar chart is the selected precipitation visual; histogram is explicitly not
  used.
- Precipitation is shown as hourly rate/intensity in `mm/h`.
- MONAN precipitation is accumulated and must be differenced against the
  previous hour.
- ERA5 `tp` is already the last-hour precipitation in `m/h`; only unit
  conversion to `mm/h` is needed.
- Observation comes from daily GoAmazon Rain Gauge files and uses
  minute-resolution `rain_rate` in `mm/hr`.
- MONAN precipitation bars do not show standard-deviation bands in v1.
