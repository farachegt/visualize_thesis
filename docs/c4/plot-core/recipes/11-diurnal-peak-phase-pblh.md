# Recipe: `plot_diurnal_peak_phase_pblh`

## Objetivo

Oferecer um wrapper de conveniencia para reproduzir o layout legado de fase
do pico diario de `hpbl` entre MONAN e E3SM.

## Imagem de referencia

Atualizar este link para uma imagem real:

- [diurnal_peak_phase_pblh.png](
  ../../../../tests/output/PLACEHOLDER_diurnal_peak_phase_pblh.png
  )

## Classes principais

- `DataAdapter`
- `DiurnalPeakPhaseSourceInput`
- `DiurnalPeakPhaseRowInput`
- `RenderSpecification`
- `FigureSpecification`
- `SpecializedPlotter`

## Fluxo visual de alto nivel

```mermaid
flowchart LR
    A[Script externo] --> B[plot_diurnal_peak_phase_pblh]
    B --> C[DiurnalPeakPhaseRowInput]
    C --> D[plot_diurnal_peak_phase_rows]
    D --> E[Figure]
```

## Fluxo visual completo

```mermaid
flowchart LR
    A[Script externo] --> B[monan_adapter]
    A --> C[e3sm_adapter]
    A --> D[day_start]
    B --> E[plot_diurnal_peak_phase_pblh]
    C --> E
    D --> E
    E --> F[DiurnalPeakPhaseSourceInput]
    E --> G[DiurnalPeakPhaseRowInput]
    F --> H[HorizontalFieldPlotData de fase]
    G --> I[RenderSpecification absoluta]
    G --> J[RenderSpecification de diferenca]
    H --> K[plot_diurnal_peak_phase_rows]
    I --> K
    J --> K
    L[FigureSpecification] --> K
    K --> M[plot_map_panels]
    M --> N[Figure]
```

## Observacao

Este recipe e especifico para a migracao do metodo legado
`plot_diurnal_peak_phase_pblh`, mas e construido sobre a API mais generica
`plot_diurnal_peak_phase_rows`.

## Como adicionar mais uma layer

Vale a mesma logica do wrapper legado de amplitude diaria:

- o wrapper existe para reproduzir o caso legado com rapidez;
- a superficie mais flexivel para adicionar layers continua sendo
  `plot_diurnal_peak_phase_rows`.

Entao:

- se a alteracao for de colormap, limites ou variavel principal, o wrapper
  ainda faz sentido;
- se a alteracao for adicionar uma layer extra sobre MONAN, E3SM ou delta,
  prefira descer um nivel para `plot_diurnal_peak_phase_rows`.

Exemplo conceitual:

```python
row = DiurnalPeakPhaseRowInput(
    left_source=...,
    right_source=...,
    day_start=np.datetime64("2014-02-24"),
    field_label="Peak Hour PBLH",
    absolute_render_specification=...,
    difference_render_specification=...,
    right_extra_layers=[extra_right_layer],
)
```

Resumo:

- para reproduzir o legado rapidamente, use o wrapper;
- para extensao livre por layer, prefira o recipe generico.
