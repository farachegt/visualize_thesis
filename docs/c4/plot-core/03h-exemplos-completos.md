# Exemplos Completos

Este documento reune exemplos mais completos de uso da arquitetura de
`plot_core`, desde a configuracao das fontes ate o ponto de gerar a figura.

Observacao importante:

- estes exemplos sao conceituais e servem para orientar a implementacao;
- a API publica do `DataAdapter` deve receber explicitamente a variavel
  canonica desejada, por exemplo `variable_name="theta"` em
  `to_vertical_profile_plot_data(...)`.

## Exemplo 1: modelo + radiossonda em um unico subplot

Objetivo:

- abrir uma fonte de modelo MONAN e uma radiossonda;
- preparar perfis verticais de `theta`;
- sobrepor as duas fontes no mesmo subplot;
- gerar uma figura com apenas um painel.

### 1. Definir as fontes

```python
from pathlib import Path

from plot_core.adapters import DataAdapter
from plot_core.rendering import (
    FigureSpecification,
    PlotLayer,
    PlotPanel,
    RenderSpecification,
)
from plot_core.requests import VerticalProfileRequest
from plot_core.source_specifications import (
    SourceSpecification,
    VariableSpecification,
)
from plot_core.specialized_plotters import SpecializedPlotter
```

```python
monan_spec = SourceSpecification(
    label="MONAN",
    latitude_name="latitude",
    longitude_name="longitude",
    time_name="time",
    vertical_name="pres",
    variables={
        "theta": VariableSpecification(source_name="theta", target_units="K"),
        "pressure": VariableSpecification(source_name="pres", target_units="hPa"),
    },
)

radiosonde_spec = SourceSpecification(
    label="GOAMAZON_RADIOSONDE",
    time_name="time",
    vertical_name="pressure",
    variables={
        "temperature": VariableSpecification(source_name="temperature", target_units="K"),
        "pressure": VariableSpecification(source_name="pressure", target_units="hPa"),
        "theta": VariableSpecification(
            derivation_kind="theta_from_pressure_temperature",
            target_units="K",
        ),
    },
)
```

Leitura correta:

- no MONAN, `theta` vem diretamente da fonte;
- na radiossonda, `theta` e derivada de `pressure` e `temperature`.

### 2. Instanciar os adapters

```python
monan_adapter = DataAdapter(
    path=Path("/dados/monan/monan_history_20140215_1200.nc"),
    file_format="netcdf",
    geometry_type="gridded",
    source_specification=monan_spec,
    reader_options={"engine": "netcdf4"},
)

radiosonde_adapter = DataAdapter(
    path=Path("/dados/goamazon/radiosonde_20140215_1200.nc"),
    file_format="netcdf",
    geometry_type="moving_point",
    source_specification=radiosonde_spec,
)
```

### 3. Abrir os dados

Se quisermos explicitar a abertura:

```python
monan_dataset = monan_adapter.open_data()
radiosonde_dataset = radiosonde_adapter.open_data()
```

Observacao:

- essa chamada pode ser opcional na implementacao final, caso o adapter abra o
  dataset sob demanda;
- aqui ela aparece apenas para deixar o fluxo completo visivel.

### 4. Definir o request

```python
request = VerticalProfileRequest(
    times=[t0],
    vertical_axis="pressure",
    point_lat=-3.21,
    point_lon=-60.60,
)
```

Leitura correta:

- o modelo usa `point_lat` e `point_lon` para selecionar o ponto mais proximo;
- a radiossonda usa o mesmo request, mas sem precisar de selecao espacial
  horizontal fixa.

### 5. Gerar os `PlotData`

```python
monan_theta = monan_adapter.to_vertical_profile_plot_data(
    variable_name="theta",
    request=request,
)

radiosonde_theta = radiosonde_adapter.to_vertical_profile_plot_data(
    variable_name="theta",
    request=request,
)
```

Aqui:

- `monan_theta` e um `VerticalProfilePlotData`;
- `radiosonde_theta` tambem e um `VerticalProfilePlotData`;
- cada um ja traz arrays prontos para o plotador.

### 6. Definir como cada camada sera desenhada

```python
monan_render = RenderSpecification(
    artist_method="plot",
    artist_kwargs={
        "color": "tab:blue",
        "linewidth": 2.0,
        "label": "MONAN",
    },
)

radiosonde_render = RenderSpecification(
    artist_method="plot",
    artist_kwargs={
        "color": "black",
        "linewidth": 1.5,
        "linestyle": "--",
        "label": "GOAMAZON Radiosonde",
    },
)
```

### 7. Montar as camadas

```python
monan_layer = PlotLayer(
    plot_data=monan_theta,
    render_specification=monan_render,
)

radiosonde_layer = PlotLayer(
    plot_data=radiosonde_theta,
    render_specification=radiosonde_render,
)
```

### 8. Montar o painel unico

```python
panel = PlotPanel(
    layers=[monan_layer, radiosonde_layer],
    axes_set_kwargs={
        "title": "Theta",
        "xlabel": "Theta (K)",
        "ylabel": "Pressure (hPa)",
    },
    grid_kwargs={"visible": True, "linestyle": ":"},
    legend_kwargs={"loc": "best"},
    axes_calls=[
        {"method": "invert_yaxis"},
    ],
)
```

Leitura correta:

- a figura tera apenas um subplot;
- esse subplot contem duas `PlotLayer`s, uma para o modelo e outra para a
  radiossonda.

### 9. Montar a figura

```python
figure_spec = FigureSpecification(
    nrows=1,
    ncols=1,
    suptitle="Perfil vertical de theta",
    figure_kwargs={"figsize": (6, 8), "constrained_layout": True},
)
```

### 10. Gerar o plot

```python
plotter = SpecializedPlotter()
fig = plotter.plot(
    panels=[panel],
    figure_specification=figure_spec,
)
```

Resumo do fluxo:

- 2 fontes;
- 2 `DataAdapter`s;
- 2 `VerticalProfilePlotData`;
- 2 `PlotLayer`s;
- 1 `PlotPanel`;
- 1 figura com 1 subplot.

## Exemplo 2: dois modelos em dois subplots com `tke` e `sensible_heat_flux`

Objetivo:

- abrir `MONAN_SHOC` e `MONAN_MYNN`;
- plotar em dois subplots:
  - um painel para SHOC;
  - um painel para MYNN;
- em cada subplot:
  - `tke` como campo preenchido;
  - `sensible_heat_flux` como isolinhas;
- gerar uma figura 1x2.

### 1. Definir as fontes

```python
from pathlib import Path

from plot_core.adapters import DataAdapter
from plot_core.rendering import (
    FigureSpecification,
    PlotLayer,
    PlotPanel,
    RenderSpecification,
)
from plot_core.requests import HorizontalFieldRequest
from plot_core.source_specifications import (
    SourceSpecification,
    VariableSpecification,
)
from plot_core.specialized_plotters import SpecializedPlotter
```

```python
shoc_spec = SourceSpecification(
    label="MONAN_SHOC",
    variables={
        "tke": VariableSpecification(source_name="tke", target_units="m2 s-2"),
        "sensible_heat_flux": VariableSpecification(
            source_name="sensible_heat_flux",
            target_units="W m-2",
        ),
    },
)

mynn_spec = SourceSpecification(
    label="MONAN_MYNN",
    variables={
        "tke": VariableSpecification(source_name="tke", target_units="m2 s-2"),
        "sensible_heat_flux": VariableSpecification(
            source_name="sensible_heat_flux",
            target_units="W m-2",
        ),
    },
)
```

Observacao:

- o exemplo assume `sensible_heat_flux` como nome canonico suportado pela
  arquitetura;
- se o nome real na fonte for outro, ele deve ser mapeado em `source_name`.

### 2. Instanciar os adapters

```python
shoc_adapter = DataAdapter(
    path=Path("/dados/monan_shoc/history_20140215_1200.nc"),
    file_format="netcdf",
    geometry_type="gridded",
    source_specification=shoc_spec,
)

mynn_adapter = DataAdapter(
    path=Path("/dados/monan_mynn/history_20140215_1200.nc"),
    file_format="netcdf",
    geometry_type="gridded",
    source_specification=mynn_spec,
)
```

### 3. Abrir os dados

```python
shoc_dataset = shoc_adapter.open_data()
mynn_dataset = mynn_adapter.open_data()
```

### 4. Definir o request horizontal

```python
request = HorizontalFieldRequest(
    times=[t0],
    vertical_selection="surface",
)
```

Leitura correta:

- o caso e um unico tempo;
- o campo horizontal e recortado na superficie.

### 5. Gerar os `PlotData`

```python
shoc_tke = shoc_adapter.to_horizontal_field_plot_data(
    variable_name="tke",
    request=request,
)

shoc_shf = shoc_adapter.to_horizontal_field_plot_data(
    variable_name="sensible_heat_flux",
    request=request,
)

mynn_tke = mynn_adapter.to_horizontal_field_plot_data(
    variable_name="tke",
    request=request,
)

mynn_shf = mynn_adapter.to_horizontal_field_plot_data(
    variable_name="sensible_heat_flux",
    request=request,
)
```

Ao final, teremos:

- 2 `HorizontalFieldPlotData` para SHOC;
- 2 `HorizontalFieldPlotData` para MYNN.

### 6. Definir as `RenderSpecification`s

```python
tke_render = RenderSpecification(
    artist_method="contourf",
    artist_kwargs={
        "levels": 21,
        "cmap": "magma",
        "extend": "max",
    },
    colorbar_kwargs={"label": "TKE (m2 s-2)"},
)

shf_render = RenderSpecification(
    artist_method="contour",
    artist_kwargs={
        "levels": [-50, -25, 25, 50, 100],
        "colors": "black",
        "linewidths": 0.8,
    },
)
```

### 7. Montar as camadas

```python
shoc_layers = [
    PlotLayer(plot_data=shoc_tke, render_specification=tke_render),
    PlotLayer(plot_data=shoc_shf, render_specification=shf_render),
]

mynn_layers = [
    PlotLayer(plot_data=mynn_tke, render_specification=tke_render),
    PlotLayer(plot_data=mynn_shf, render_specification=shf_render),
]
```

Leitura correta:

- cada subplot recebe duas camadas;
- a primeira camada desenha `tke` preenchido;
- a segunda desenha as isolinhas de `sensible_heat_flux`.

### 8. Montar os paineis

```python
panel_shoc = PlotPanel(
    layers=shoc_layers,
    axes_set_kwargs={
        "title": "MONAN_SHOC",
        "xlabel": "Longitude",
        "ylabel": "Latitude",
    },
    grid_kwargs={"visible": True, "linestyle": ":"},
)

panel_mynn = PlotPanel(
    layers=mynn_layers,
    axes_set_kwargs={
        "title": "MONAN_MYNN",
        "xlabel": "Longitude",
        "ylabel": "Latitude",
    },
    grid_kwargs={"visible": True, "linestyle": ":"},
)
```

### 9. Montar a figura 1x2

```python
figure_spec = FigureSpecification(
    nrows=1,
    ncols=2,
    suptitle="TKE e sensible heat flux na superficie",
    figure_kwargs={"figsize": (12, 5), "constrained_layout": True},
    subplot_kwargs={"sharex": True, "sharey": True},
)
```

### 10. Gerar o plot

```python
plotter = SpecializedPlotter()
fig = plotter.plot(
    panels=[panel_shoc, panel_mynn],
    figure_specification=figure_spec,
)
```

Resumo do fluxo:

- 2 fontes;
- 2 `DataAdapter`s;
- 4 `HorizontalFieldPlotData`;
- 4 `PlotLayer`s;
- 2 `PlotPanel`s;
- 1 figura com 2 subplots.
