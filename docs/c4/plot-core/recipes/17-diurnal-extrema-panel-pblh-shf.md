# Recipe: `build_monan_e3sm_diurnal_extrema_panel_figure`

## Objetivo

Oferecer o cenario oficial `MONAN x E3SM` para uma figura `2 x 3` com:

- linha 1: minimo ou maximo diario da `PBLH`;
- linha 2: minimo ou maximo diario do `SHF`;
- coluna 1: `MONAN`;
- coluna 2: `E3SM`;
- coluna 3: `Delta (MONAN - E3SM)`.

Esse builder aceita `time_reduce="min"` ou `time_reduce="max"`.

## Imagem de referencia

Atualizar este link para uma imagem real:

- [diurnal_extrema_panel_pblh_shf.png](
  ../../../../tests/output/PLACEHOLDER_diurnal_extrema_panel_pblh_shf.png
  )

## Classes principais

- `DataAdapter`
- `DiurnalExtremaMatrixSourceInput`
- `DiurnalExtremaMatrixRowInput`
- `FigureSpecification`
- `plot_diurnal_extrema_matrix_rows`

## Fluxo visual de alto nivel

```mermaid
flowchart LR
    A[Script oficial] --> B[build_monan_e3sm_diurnal_extrema_panel_figure]
    B --> C[rows PBLH e SHF]
    C --> D[plot_diurnal_extrema_matrix_rows]
    D --> E[Figure]
```

## Fluxo visual completo

```mermaid
flowchart LR
    A[generate_*.py] --> B[build_legacy_monan_e3sm_adapter]
    A --> C[build_legacy_e3sm_adapter]
    A --> D[day_start]
    A --> E[time_reduce]
    B --> F[scenario builder]
    C --> F
    D --> F
    E --> F
    F --> G[DiurnalExtremaMatrixRowInput PBLH]
    F --> H[DiurnalExtremaMatrixRowInput SHF]
    F --> I[FigureSpecification 2x3]
    G --> J[plot_diurnal_extrema_matrix_rows]
    H --> J
    I --> J
    J --> K[Figure]
```

## Como adicionar mais uma layer

Para reproducao rapida do cenario oficial, use o builder pronto.

Se a necessidade for adicionar layers extras em um painel especifico, o
melhor caminho e descer um nivel para o recipe generico
`plot_diurnal_extrema_matrix_rows`.

Exemplo conceitual:

```python
rows, figure_specification = (
    build_monan_e3sm_diurnal_extrema_panel_inputs(
        day_start=np.datetime64("2014-02-24"),
        time_reduce="max",
    )
)
rows[0].left_extra_layers = [extra_layer]
figure = plot_diurnal_extrema_matrix_rows(
    rows=rows,
    figure_specification=figure_specification,
)
```

## Observacao

Esse cenario usa a mesma gramatica matricial da recipe de amplitude, mas
troca a reducao diaria:

- `time_reduce="min"` para minimos diarios;
- `time_reduce="max"` para maximos diarios.
