# Initial plan: time-series recipe

Status: draft for discussion.

## Goal

Create a generic time-series recipe that can compose one or more
`TimeSeriesPlotData` layers into one or more panels.

The generic recipe must remain reusable, but its first concrete scenario is
the 3-panel GoAmazon/NWP/ERA5 comparison described below.

The recipe should let callers compose one or more time-series layers inside
one or more panels, using the same architecture already used by profiles,
maps and cross sections.

Primary use cases:

- plot fixed-point meteorological surface-station time series;
- compare surface-station, NWP and reanalysis sources in the same panel;
- compare multiple sources in the same panel;
- create multi-panel figures where each panel has compatible time-series
  layers;
- build the planned 3-panel source-comparison figure:
  - panel 1: 2-meter temperature;
  - panel 2: 2-meter specific humidity;
  - panel 3: 10-meter horizontal wind speed magnitude;
  - each panel has 4 layers, one per source;
- reuse `DataAdapter` and `TimeSeriesRequest` instead of opening data
  directly.

## Context references

Read only these files before implementing:

- [07-como-criar-um-recipe.md](./07-como-criar-um-recipe.md)
  - official project guide for creating a new recipe;
- [profiles.py](../../../plot_core/recipes/profiles.py)
  - closest generic layer/panel recipe pattern;
- [maps.py](../../../plot_core/recipes/maps.py)
  - useful pattern for prepared layer inputs;
- [time_vertical.py](../../../plot_core/recipes/time_vertical.py)
  - current use of `TimeSeriesPlotData`;
- [plot_data.py](../../../plot_core/plot_data.py)
  - `TimeSeriesPlotData` contract;
- [requests.py](../../../plot_core/requests.py)
  - `TimeSeriesRequest` contract;
- [adapter.py](../../../plot_core/adapter.py)
  - `to_time_series_plot_data(...)`;
- [readers.py](../../../plot_core/readers.py)
  - current `FileFormatReader` support for NetCDF and CSV;
- [geometry.py](../../../plot_core/geometry.py)
  - gridded point extraction and fixed-point time-series preparation;
- [rendering.py](../../../plot_core/rendering.py)
  - `SpecializedPlotter` support for `TimeSeriesPlotData`;
- [scenarios/source_specifications.py](../../../plot_core/scenarios/source_specifications.py)
  - existing source-specification builder style;
- [scenarios/adapters.py](../../../plot_core/scenarios/adapters.py)
  - existing adapter-builder style;
- [scenarios/requests.py](../../../plot_core/scenarios/requests.py)
  - existing request-builder patterns.

Avoid re-reading the whole repository unless blocked by a concrete error.

## Architecture constraints

- Follow the established `visualize_thesis` architecture. The implementation
  should compose existing project objects instead of inventing a parallel
  plotting path.
- The recipe must live in `plot_core/recipes/`.
- The recipe must not open files directly.
- The recipe must not manipulate raw `xarray.Dataset` objects.
- The recipe must call `DataAdapter.to_time_series_plot_data(...)`.
- The recipe must not call low-level `matplotlib` directly, except through
  existing `RenderSpecification`, `PlotLayer`, `PlotPanel`,
  `FigureSpecification` and `SpecializedPlotter` contracts.
- The public API should grow by lists of layers and panels, not by
  `primary_`, `secondary_` or source-specific arguments.
- Scenario-specific defaults, paths and adapters must stay in
  `plot_core/scenarios/`, not in the generic recipe.
- Batch generation and `savefig(...)` belong in `scripts/recipes/`, not in
  the generic recipe.
- The generic recipe must not hardcode the planned "3 panels x 4 sources"
  layout. That concrete figure should be assembled by scenario builders or a
  wrapper built on top of the generic recipe.
- Use the existing responsibilities as designed:
  - `FileFormatReader`s read source files into `xarray.Dataset`;
  - `GeometryHandler`s handle point, bbox, vertical and temporal selection;
  - `SourceSpecification`s map source-specific names and units to canonical
    variables;
  - `DataAdapter`s orchestrate readers, geometry handlers, source
    specifications, unit handling and derivations;
  - `TimeSeriesRequest` describes the concrete temporal, spatial and vertical
    selection;
  - `TimeSeriesPlotData` is the prepared data contract consumed by rendering;
  - `RenderSpecification`, `PlotLayer`, `PlotPanel`,
    `FigureSpecification` and `SpecializedPlotter` handle figure assembly and
    rendering.
- If a needed behavior already exists in `DataAdapter`, `FileFormatReader`,
  `GeometryHandler`, `PlotData`, rendering contracts or scenarios, use it.
  Do not duplicate that behavior inside the new recipe.

## Proposed MVP files

Required:

- `plot_core/recipes/time_series.py`
- `plot_core/recipes/__init__.py`

Recommended for a complete first slice:

- `plot_core/canonical_variables.py`
- `plot_core/derivations.py`
- `plot_core/scenarios/paths.py`
- `plot_core/scenarios/source_specifications.py`
- `plot_core/scenarios/adapters.py`
- `plot_core/scenarios/requests.py`
- `plot_core/scenarios/recipes.py`
- `plot_core/scenarios/__init__.py`
- `docs/c4/plot-core/03c-source-and-requests.md`
- `docs/c4/plot-core/recipes/18-time-series-panels.md`
- `docs/c4/plot-core/06-recipes.md`

Additional files needed if ERA5 GRIB support is implemented in the same
patch:

- `plot_core/readers.py`
- `plot_core/adapter.py`
- `docs/c4/plot-core/03d-readers.md`
- `docs/c4/plot-core/03f-data-adapter.md`

Optional only if we want an executable artifact immediately:

- `scripts/recipes/generate_time_series_comparison.py`

## Source contract for the 3-panel comparison

The first concrete figure compares 4 sources:

In this plan, `NWP` refers to the two MONAN experiments below:

- `MONAN MYNN`;
- `MONAN SHOC`.

Comparison period:

- start date: `2014-10-02`;
- exclusive end date: `2014-10-07`;
- total span: 5 days.

1. `MONAN MYNN`
   - source kind: NWP;
   - raw geometry: gridded;
   - file format: NetCDF;
   - adapter shape: based on `build_legacy_monan_e3sm_adapter(...)`;
   - source path:

```text
/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_mynn_dry_season/2014100200/diag/posprocess/*.nc
```

2. `MONAN SHOC`
   - source kind: NWP;
   - raw geometry: gridded;
   - file format: NetCDF;
   - adapter shape: based on `build_legacy_monan_e3sm_adapter(...)`;
   - source path:

```text
/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/dataout/REGNOL2_GFdef_ERA5_10km_shoc_dry_season/2014100200/diag/posprocess/*.nc
```

3. `ERA5`
   - source kind: reanalysis;
   - raw geometry: gridded;
   - file format: GRIB;
   - `latitude_name="latitude"`;
   - `longitude_name="longitude"`;
   - source path:

```text
/lustre/projetos/monan_atm/guilherme.farache/ERA5/sl_20141002.grib
```

4. `GoAmazon surface station`
   - source kind: meteorological surface station;
   - raw geometry: fixed point;
   - file format: NetCDF/CDF;
   - fixed-point coordinates are stored in the dataset coordinates `lat` and
     `lon`;
   - source path:

```text
/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/b1 (Quality Control applied)/MET/*.cdf
```

For the station source, open only files matching:

```text
maometM1.b1.{YYYYMMDD}*.cdf
```

where `YYYYMMDD` ranges from `20141002` to `20141006`, inclusive. With the
current `NetCDFFileFormatReader` interface, one viable glob pattern is:

```text
/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/b1 (Quality Control applied)/MET/maometM1.b1.2014100[2-6]*.cdf
```

The GoAmazon surface-station `DataAdapter` should use empty
`reader_options`. The station files do not need special `base_time` or
`time_offset` handling in order to be opened together.

For the GoAmazon surface-station `SourceSpecification`, map:

- `latitude_name="lat"`;
- `longitude_name="lon"`.

Do not hardcode station latitude and longitude when the dataset coordinates
are available and compatible with `FixedPointGeometryHandler`.

## Spatial-selection contract

NWP and reanalysis sources must remain gridded in the pipeline:

```python
DataAdapter(
    file_format="netcdf",
    geometry_type="gridded",
    source_specification=...,
)
```

For ERA5 GRIB, the same geometry rule applies, but the reader layer needs GRIB
support:

```python
DataAdapter(
    file_format="grib",
    geometry_type="gridded",
    source_specification=...,
    path=...,
    reader_options={"engine": "cfgrib"},
)
```

The current code supports `file_format="netcdf"` and `file_format="csv"`.
Therefore, one implementation decision is required before using the ERA5 GRIB
source:

- add a `GRIBFileFormatReader` that uses xarray methods with the cfgrib
  backend:
  - `xarray.open_dataset(path, engine="cfgrib", **reader_options)` for a
    single GRIB file;
  - `xarray.open_mfdataset(glob_pattern, engine="cfgrib",
    **reader_options)` if multi-file GRIB support is needed later;
- default `engine` to `"cfgrib"` inside the reader when the caller does not
  provide it in `reader_options`;
- extend `DataAdapter.FileFormat` and `_get_reader()` to support
  `file_format="grib"`;
- keep semantic normalization in `DataAdapter`, not in the GRIB reader.

To extract station-like time series from NWP or reanalysis grids, put the
station coordinates in `TimeSeriesRequest`:

```python
TimeSeriesRequest(
    times=np.asarray([start_time, end_time], dtype="datetime64[ns]"),
    point_lat=station_lat,
    point_lon=station_lon,
)
```

Then the recipe calls:

```python
adapter.to_time_series_plot_data(
    variable_name=...,
    request=request,
)
```

The spatial selection happens inside
`GriddedGeometryHandler.prepare_time_series_dataset(...)`, not in the recipe
or script.

Current gridded time-series behavior:

- `point_lat` + `point_lon`: nearest grid-point extraction;
- `bbox`: regional subset followed by horizontal average;
- neither: explicit error for gridded time series.

Rule for the implementation agent:

- NWP and reanalysis sources remain `geometry_type="gridded"`;
- the fixed-point/station-like extraction is requested with
  `TimeSeriesRequest(point_lat=..., point_lon=...)`;
- `GriddedGeometryHandler` executes the spatial selection;
- the time-series recipe must not perform spatial selection itself.

Concrete station point for gridded extraction:

- latitude: `-3.21297`;
- longitude: `-60.5981`;
- all sources already use the same longitude convention for this workflow.

## Variable and derivation contract

Add explicit surface canonical variables:

- `temperature_2m`;
- `specific_humidity_2m`;
- `wind_speed_10m`;
- `surface_pressure`.

These should be added to `plot_core/canonical_variables.py` and documented in
`docs/c4/plot-core/03c-source-and-requests.md`.

### NWP: MONAN MYNN and MONAN SHOC

Source-variable mapping:

- `temperature_2m`
  - source variable: `t2m`;
  - input units: `K`;
  - target units: `degC`.
- `specific_humidity_2m`
  - source variable: `q2`;
  - input units: `kg kg-1`;
  - target units: `g kg-1`.
- `wind_speed_10m`
  - derived from:
    - `u10`, source variable `u10`;
    - `v10`, source variable `v10`;
  - target units: `m s-1`.

Required derivation support:

- derive `wind_speed_10m` from `u10` and `v10`, equivalent to
  `sqrt(u10**2 + v10**2)`;
- convert 2-meter temperature from Kelvin to Celsius;
- convert 2-meter specific humidity from `kg kg-1` to `g kg-1`.

### Reanalysis: ERA5

Source-variable mapping:

- `temperature_2m`
  - source variable: `t2m`;
  - input units: `K`;
  - target units: `degC`.
- `specific_humidity_2m`
  - derived from:
    - 2-meter dewpoint temperature, source variable `d2m`;
    - surface pressure, source variable `sp`;
  - target units: `g kg-1`.
- `surface_pressure`
  - source variable: `sp`;
  - input units: `Pa`.
- `wind_speed_10m`
  - derived from:
    - `u10`, source variable `u10`;
    - `v10`, source variable `v10`;
  - target units: `m s-1`.

Required derivation support:

- derive `wind_speed_10m` from `u10` and `v10`;
- derive `specific_humidity_2m` using MetPy:

```python
specific_humidity_from_dewpoint(
    sp * units.Pa,
    d2m * units.K,
).to("g/kg")
```

- convert 2-meter temperature from Kelvin to Celsius.

### GoAmazon Surface Station

Source-variable mapping:

- `temperature_2m`
  - source variable: `temp_mean`;
  - input and target units: `degC`.
- `specific_humidity_2m`
  - derived from:
    - temperature, source variable `temp_mean`;
    - relative humidity, source variable `rh_mean`, stored as percent
      from `0` to `100`;
    - pressure, source variable `atmos_pressure`, stored in `kPa`;
  - target units: `g kg-1`.
- `wind_speed_10m`
  - source variable: `wspd_arith_mean`;
  - target units: `m s-1`.

Required derivation support:

1. calculate saturation vapor pressure with MetPy:

```python
e_s = saturation_vapor_pressure(temp_mean * units.degC)
```

2. calculate vapor pressure:

```python
e = (rh_mean / 100.0) * e_s
```

3. calculate specific humidity using the project-requested approximation:

```python
specific_humidity = (e / (pressure - e)) * 0.622
```

4. convert the result to `g kg-1`.

The station derivation must convert `atmos_pressure` from `kPa` to a unit
compatible with the vapor pressure returned by MetPy before evaluating the
specific-humidity approximation.

## Time-handling contract

The comparison is parameterized by `init_date` and always spans 5 forecast
days.

For the current case:

- `init_date = np.datetime64("2014-10-02T00:00:00")`;
- `end_time = np.datetime64("2014-10-07T00:00:00")`;
- `end_time` is exclusive and should not be plotted as part of the 5-day
  window.

Coordinate names:

- ERA5 reanalysis uses temporal coordinate `time`;
- NWP sources use temporal coordinate `Time`;
- GoAmazon surface-station files should be opened by the configured reader
  without special `reader_options`.

Sampling and display:

- all sources are in UTC;
- the plotted x-axis should display local time GMT-4;
- the generic `plot_time_series_panels(...)` recipe should not perform this
  conversion;
- the scenario builder should keep UTC values in `TimeSeriesPlotData.times`
  and customize x-axis tick labels to show GMT-4 local time;
- NWP and reanalysis are hourly;
- GoAmazon station has finer temporal resolution and should be reduced to
  hourly samples by selecting the nearest station sample to each hourly time.

## Figure contract

Layout:

- `3 x 1`;
- shared x-axis representing time;
- one panel per variable;
- four layers per panel.

Panels and y-axis labels:

- panel 1: `2 m temperature [°C]`;
- panel 2: `Specific humidity [g/kg]`;
- panel 3: `10 m wind speed [m/s]`.

Legend:

- legend only in the first panel;
- source color and source label must remain consistent across all three
  panels.
- layer labels:
  - `SHOC`;
  - `MYNN`;
  - `ERA5`;
  - `Observation`;
- use default line style;
- the implementation agent may choose the colors in the scenario builder,
  keeping them stable across panels.

## Proposed public API

### `TimeSeriesLayerInput`

Describes a time series resolved by an adapter.

Fields:

- `adapter: DataAdapter`
- `request: TimeSeriesRequest`
- `variable_name: str`
- `render_specification: RenderSpecification`
- `legend_label: str | None = None`

### `PreparedTimeSeriesLayerInput`

Describes a time series that is already prepared.

This mirrors `PreparedMapLayerInput` and makes the recipe useful for derived
or post-processed series without expanding the adapter contract.

Fields:

- `plot_data: TimeSeriesPlotData`
- `render_specification: RenderSpecification`
- `legend_label: str | None = None`

### `TimeSeriesPanelInput`

Describes one subplot.

Fields:

- `layers: Sequence[TimeSeriesLayerDefinition]`
- `axes_set_kwargs: dict[str, Any] = field(default_factory=dict)`
- `grid_kwargs: dict[str, Any] | None = None`
- `legend_kwargs: dict[str, Any] | None = None`
- `axes_calls: list[dict[str, Any]] = field(default_factory=list)`

Where:

```python
TimeSeriesLayerDefinition = Union[
    TimeSeriesLayerInput,
    PreparedTimeSeriesLayerInput,
]
```

### `plot_time_series_panels(...)`

Generic public entrypoint.

Suggested signature:

```python
def plot_time_series_panels(
    *,
    panels: Sequence[TimeSeriesPanelInput],
    figure_specification: FigureSpecification,
    plotter: SpecializedPlotter | None = None,
) -> Figure:
    ...
```

Behavior:

1. require at least one panel;
2. require at least one layer per panel;
3. resolve each adapter-backed layer into `TimeSeriesPlotData`;
4. inject `legend_label` into `artist_kwargs["label"]` when no label already
   exists;
5. build `PlotLayer`s and `PlotPanel`s;
6. render via `SpecializedPlotter.plot(...)`;
7. return the `Figure`.

## Implementation outline

### Step 1. Add `plot_core/recipes/time_series.py`

Implement:

- dataclasses listed above;
- `plot_time_series_panels(...)`;
- `_build_time_series_plot_panel(...)`;
- `_build_time_series_plot_layer(...)`;
- `_build_time_series_render_specification(...)`;
- `_copy_optional_mapping(...)`;
- `_copy_artist_calls(...)`.

Use `profiles.py` as the closest shape for generic panel assembly, and
`maps.py` for the adapter-backed versus prepared layer input pattern.

Do not add default axes labels in the generic recipe. The caller should pass
labels through `axes_set_kwargs`, because units and site labels vary by
case.

### Step 2. Export the recipe

Update `plot_core/recipes/__init__.py` to export:

- `TimeSeriesLayerInput`
- `PreparedTimeSeriesLayerInput`
- `TimeSeriesPanelInput`
- `plot_time_series_panels`

Keep imports lightweight and consistent with the existing recipe exports.

### Step 3. Add the planned 3-panel comparison builder

After the generic recipe is working, add a scenario-level builder for the
actual target figure.

The target figure has:

- 3 panels:
  - 2-meter temperature;
  - 2-meter specific humidity;
  - 10-meter horizontal wind speed magnitude;
- 4 layers per panel:
  - one layer per source;
  - sources are expected to include meteorological surface station, NWP and
    reanalysis products;
  - same source order in every panel;
  - same color and legend label for each source across all panels.

This builder should live in `plot_core/scenarios/recipes.py`, not in the
generic `plot_core/recipes/time_series.py` module.

Likely builder names:

- `build_surface_nwp_reanalysis_time_series_comparison_inputs(...)`
- `build_surface_nwp_reanalysis_time_series_comparison_figure(...)`

The exact names can still be adjusted to match the final scenario naming.

Design notes:

- use `TimeSeriesPanelInput` for each variable panel;
- use `TimeSeriesLayerInput` for each source layer;
- pass panel titles and axis labels through `axes_set_kwargs`;
- use one shared style table for the 4 sources;
- use `legend_kwargs` only on the first panel unless the final figure needs
  legends on every panel.

Implementation decision:

- use explicit surface canonical variables:
  - `temperature_2m`;
  - `specific_humidity_2m`;
  - `wind_speed_10m`;
  - `surface_pressure`.

### Step 4. Add recipe documentation

Create `docs/c4/plot-core/recipes/18-time-series-panels.md`.

It should mirror the existing recipe docs:

- objective;
- image placeholder;
- main classes;
- high-level flow;
- complete flow;
- minimal example;
- how to add another layer.

Update `docs/c4/plot-core/06-recipes.md` to include the new recipe doc.

### Step 5. Optional script

Only add a script if we want an executable artifact in the first patch.

Candidate:

- `scripts/recipes/generate_time_series_comparison.py`

Behavior:

- build or receive the 4 source adapters;
- call `build_surface_nwp_reanalysis_time_series_comparison_figure(...)`;
- save to `tests/output/time_series_comparison.png`;
- call `adapter.close()` for every adapter in `finally`;
- print the saved path from `main()`.

This can be deferred if we only want the core recipe and scenario builder.

## Validation plan

Run from the `visualize_thesis` directory.

Basic import check:

```bash
python - <<'PY'
from plot_core.recipes import (
    TimeSeriesLayerInput,
    TimeSeriesPanelInput,
    plot_time_series_panels,
)
print("ok")
PY
```

Scenario smoke check, if the scenario builder is added and the 4 source
adapters are defined:

```bash
python - <<'PY'
from plot_core.scenarios import (
    build_surface_nwp_reanalysis_time_series_comparison_figure,
    build_time_series_comparison_adapters,
)

adapters = build_time_series_comparison_adapters()
try:
    figure = build_surface_nwp_reanalysis_time_series_comparison_figure(
        adapters=adapters,
    )
    print(type(figure).__name__)
finally:
    for adapter in adapters:
        adapter.close()
PY
```

Optional visual smoke output:

```bash
python - <<'PY'
from plot_core.scenarios import (
    OUTPUT_DIR,
    build_surface_nwp_reanalysis_time_series_comparison_figure,
    build_time_series_comparison_adapters,
)

adapters = build_time_series_comparison_adapters()
try:
    figure = build_surface_nwp_reanalysis_time_series_comparison_figure(
        adapters=adapters,
    )
    output_path = OUTPUT_DIR / "smoke_time_series_comparison.png"
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    print(output_path)
finally:
    for adapter in adapters:
        adapter.close()
PY
```

If a script is added, also run:

```bash
python scripts/recipes/generate_time_series_comparison.py
```

## Acceptance criteria

- A caller can build a time-series figure without touching raw `xarray`.
- Multiple time-series layers can be composed in the same panel.
- Multiple panels can be rendered in one figure.
- The recipe returns a `matplotlib.figure.Figure`.
- Legend labels can be injected per layer without mutating caller-provided
  `RenderSpecification` objects.
- The recipe uses existing `TimeSeriesPlotData` and `SpecializedPlotter`
  behavior.
- The implementation does not change `DataAdapter`, `GeometryHandler` or
  `SpecializedPlotter` unless a concrete bug is found.
- The scenario smoke check works with the meteorological surface station, NWP
  and reanalysis sources once their adapters are defined.
- The concrete comparison figure has 3 panels and 4 layers per panel.
- The concrete comparison figure uses:
  - 2-meter temperature in Celsius;
  - 2-meter specific humidity in `g kg-1`;
  - 10-meter wind speed in `m s-1`.
- The plotted time axis represents GMT-4 local time for the scenario figure.
- The scenario figure keeps UTC values internally and displays GMT-4 through
  x-axis tick labels.
- Documentation links use relative paths.

## Implementation phasing

This work should be split into phases because it touches readers,
derivations, scenarios and recipe composition.

### Phase 1. Generic time-series recipe

Implement only the reusable recipe surface:

- `plot_core/recipes/time_series.py`;
- exports in `plot_core/recipes/__init__.py`;
- recipe documentation.

This phase should not depend on the new data sources.

Reason for keeping Phase 1 separate:

- the generic recipe can be implemented and reviewed without GRIB, new
  derivations or the real source paths;
- this reduces risk because later phases touch lower-level reader, adapter and
  derivation behavior;
- if the generic recipe API needs adjustment, it is cheaper to change before
  wiring the full 4-source scenario.

### Phase 2. Reader and adapter support for GRIB

Implement:

- `GRIBFileFormatReader`;
- `file_format="grib"` support in `DataAdapter`;
- reader and adapter documentation updates.

Validate ERA5 can be opened through the same adapter pipeline as other
sources.

### Phase 3. Canonical variables and derivations

Implement:

- `temperature_2m`;
- `specific_humidity_2m`;
- `wind_speed_10m`;
- `surface_pressure`;
- NWP 10-meter wind-speed derivation;
- ERA5 2-meter specific-humidity derivation from `d2m` and `sp`;
- station 2-meter specific-humidity derivation from `temp_mean`, `rh_mean`
  and pressure.

Keep derivation behavior in `plot_core/derivations.py` and variable mapping
in `SourceSpecification`s.

### Phase 4. Scenario source specifications, adapters and requests

Implement concrete builders for:

- MONAN MYNN;
- MONAN SHOC;
- ERA5;
- GoAmazon surface station.

Add the parameterized 5-day request builder:

- input: `init_date`;
- default: `2014-10-02T00:00:00`;
- duration: 5 days;
- gridded sources use nearest point at `(-3.21297, -60.5981)`;
- station source uses fixed-point geometry and empty `reader_options`.

### Phase 5. Scenario figure builder and optional script

Implement the 3-panel comparison builder and, if useful, the executable
script.

The builder should:

- create a `3 x 1` figure;
- use one shared source-style table;
- put the legend in the first panel only;
- keep UTC values internally and customize x-axis tick labels to GMT-4;
- downsample the station to hourly nearest samples before plotting.

## Non-goals for the MVP

- No rolling means or smoothing helpers.
- No local-hour conversion in the generic recipe. The scenario-level builder
  for this comparison may convert the plotted time axis to GMT-4.
- No model-observation interpolation beyond what adapters and requests already
  provide. The required nearest-hour downsampling of the station source is in
  scope for the scenario builder.
- No automatic y-axis synchronization helper unless a real use case needs it.
- No new `TimeSeriesPlotData` fields.
- No change to `draw_mask` semantics.

## Remaining decisions

1. Should the MVP include `PreparedTimeSeriesLayerInput`, or should we keep
   only adapter-backed layers for the first patch?
2. Should we add the script in the first patch, or stop at recipe plus
   scenario builder?
3. Should Phase 1 be implemented and reviewed alone before starting GRIB and
   derivation work? This means first implementing only the generic
   `plot_time_series_panels(...)` API, checking that API, and only then
   implementing the lower-level source support.
4. Should the generic recipe offer a convenience wrapper such as
   `plot_time_series_at_point(...)`, or should that live only in scenarios
   once a real use case appears?
5. Should the recipe docs be added during the implementation patch, or after
   we settle the API?

The scientific contract is resolved for this plan. The remaining decisions are
implementation-scope and phasing choices.

## Model execution plan

Use `GPT-5.3-Codex` for the whole implementation.

Rationale:

- the work touches coupled code paths across recipes, readers, adapters,
  derivations, scenarios and docs;
- implementation should stay consistent with the established
  `visualize_thesis` architecture;
- using one coding-focused model for all phases reduces handoff drift between
  reader, adapter, derivation and scenario changes.

After implementation, use a separate review agent with `GPT-5.5` and Extra
High reasoning.

The review agent should:

- inspect the implemented diff against this plan;
- check that the recipe remains generic and the 3-panel source-specific
  orchestration lives in scenarios/scripts as planned;
- verify that file reading, spatial selection, unit conversion and derivations
  stay in the appropriate core components;
- review GRIB support, station NetCDF/CDF handling, source specifications and
  request construction;
- review tests or smoke-validation commands and any generated figure path;
- identify bugs, architectural drift, missing validation and missing docs.

## Handoff instructions for a cheaper model

Implement only the files listed in "Proposed MVP files".

Start by reading:

- [07-como-criar-um-recipe.md](./07-como-criar-um-recipe.md)
- [profiles.py](../../../plot_core/recipes/profiles.py)
- [maps.py](../../../plot_core/recipes/maps.py)
- [time_vertical.py](../../../plot_core/recipes/time_vertical.py)
- [readers.py](../../../plot_core/readers.py)
- [geometry.py](../../../plot_core/geometry.py)
- [scenarios/source_specifications.py](../../../plot_core/scenarios/source_specifications.py)
- [scenarios/adapters.py](../../../plot_core/scenarios/adapters.py)
- [scenarios/requests.py](../../../plot_core/scenarios/requests.py)

Do not re-read all docs or inspect unrelated legacy files.

Keep the implementation scoped:

- no refactors outside the named files;
- no changes to low-level adapter, geometry or rendering behavior unless
  validation exposes a concrete bug;
- use the established project structure and object model:
  `DataAdapter`, `FileFormatReader`, `GeometryHandler`,
  `SourceSpecification`, `TimeSeriesRequest`, `TimeSeriesPlotData`,
  `RenderSpecification`, `PlotLayer`, `PlotPanel`, `FigureSpecification` and
  `SpecializedPlotter`;
- do not bypass the core by reading files, selecting data, deriving
  variables, converting units or calling matplotlib directly inside the
  recipe;
- use existing recipe style and docstring style;
- run the validation commands above;
- report any skipped optional step explicitly.
