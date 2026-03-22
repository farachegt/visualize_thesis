# Recipe: `plot_precipitation_monan`

## Objetivo

Montar um mapa horario de precipitacao do `MONAN`, derivando primeiro a
variavel acumulada `precipitation = rainc + rainnc` e deacumulando apenas
essa variavel entre o horario atual e o horario anterior.

## Imagem de referencia

Atualizar este link para uma imagem real:

- [precipitation_monan.png](
  ../../../../tests/output/PLACEHOLDER_precipitation_monan.png
  )

## Classes principais

- `DataAdapter`
- `HorizontalFieldRequest`
- `HorizontalFieldPlotData`
- `PreparedMapLayerInput`
- `MapPanelInput`
- `FigureSpecification`
- `SpecializedPlotter`

## Fluxo visual de alto nivel

```mermaid
flowchart LR
    A[Script externo] --> B[MONAN adapter]
    A --> C[date]
    B --> D[plot_precipitation_monan]
    C --> D
    D --> E[current and previous hour requests]
    E --> F[HorizontalFieldPlotData for precipitation]
    F --> G[hourly precipitation field]
    G --> H[PreparedMapLayerInput]
    H --> I[MapPanelInput]
    I --> J[plot_map_panels]
    J --> K[Figure]
```

## Fluxo visual completo

```mermaid
flowchart LR
    A[Script externo] --> B[date]
    A --> C[MONAN DataAdapter]
    A --> D[optional extra_layers]
    B --> E[HorizontalFieldRequest current]
    B --> F[HorizontalFieldRequest previous]
    E --> C
    F --> C
    G[SourceSpecification] --> C
    H[FileFormatReader] --> C
    I[GeometryHandler] --> C
    C --> J[to_horizontal_field_plot_data precipitation current]
    C --> K[to_horizontal_field_plot_data precipitation previous]
    J --> N[HorizontalFieldPlotData]
    K --> N
    N --> O[hourly precipitation difference]
    O --> P[PreparedMapLayerInput]
    D --> P
    P --> Q[MapPanelInput]
    Q --> R[plot_map_panels]
    R --> S[SpecializedPlotter]
    S --> T[Figure]
```

## Exemplo minimo

```python
import numpy as np

from plot_core.recipes import plot_precipitation_monan

figure = plot_precipitation_monan(
    monan_adapter=monan_adapter,
    date=np.datetime64("2014-02-24T01:00:00"),
)
```

## Como adicionar mais uma layer

Essa recipe tambem segue a constraint do projeto.

A extensao acontece por `extra_layers`.

Voce pode adicionar, por exemplo:

- contornos de outra variavel horizontal;
- outra camada `PreparedMapLayerInput` precomputada;
- qualquer layer compativel com `plot_map_panels`.

Exemplo de contorno sobre o sombreado de precipitacao:

```python
from plot_core.recipes import MapLayerInput
from plot_core.rendering import RenderSpecification
from plot_core.requests import HorizontalFieldRequest

figure = plot_precipitation_monan(
    monan_adapter=monan_adapter,
    date=np.datetime64("2014-02-24T01:00:00"),
    extra_layers=[
        MapLayerInput(
            adapter=monan_adapter,
            request=HorizontalFieldRequest(
                times=np.asarray(
                    ["2014-02-24T01:00:00"],
                    dtype="datetime64[ns]",
                ),
            ),
            variable_name="hpbl",
            render_specification=RenderSpecification(
                artist_method="contour",
                artist_kwargs={"colors": "black", "linewidths": 0.8},
            ),
            legend_label="HPBL",
        )
    ],
)
```

O que faz sentido aqui:

- novas layers de campo horizontal georreferenciado;
- overlays de contorno ou campo preparado;
- manter a compatibilidade com a mesma grade espacial.

O que nao faz sentido aqui:

- adicionar `VerticalProfileLayerInput`;
- adicionar `CrossSectionLayerInput`;
- misturar geometrias que nao sejam de mapa horizontal.
