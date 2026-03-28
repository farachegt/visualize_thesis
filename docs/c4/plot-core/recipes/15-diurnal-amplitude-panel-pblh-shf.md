# Recipe: `build_legacy_monan_e3sm_diurnal_amplitude_panel_figure`

## Objetivo

Oferecer o cenario oficial `MONAN x E3SM` para uma figura `2 x 3` com:

- linha 1: amplitude diaria da `PBLH`;
- linha 2: amplitude diaria do `SHF`;
- coluna 1: `MONAN`;
- coluna 2: `E3SM`;
- coluna 3: `Delta (MONAN - E3SM)`.

## Imagem de referencia

Atualizar este link para uma imagem real:

- [diurnal_amplitude_panel_pblh_shf.png](
  ../../../../tests/output/PLACEHOLDER_diurnal_amplitude_panel_pblh_shf.png
  )

## Classes principais

- `DataAdapter`
- `DiurnalAmplitudeMatrixSourceInput`
- `DiurnalAmplitudeMatrixRowInput`
- `FigureSpecification`
- `plot_diurnal_amplitude_matrix_rows`

## Fluxo visual de alto nivel

```mermaid
flowchart LR
    A[Script oficial] --> B[build_legacy_monan_e3sm_diurnal_amplitude_panel_figure]
    B --> C[rows PBLH e SHF]
    C --> D[plot_diurnal_amplitude_matrix_rows]
    D --> E[Figure]
```

## Fluxo visual completo

```mermaid
flowchart LR
    A[generate_legacy_*.py] --> B[build_legacy_monan_e3sm_adapter]
    A --> C[build_legacy_e3sm_adapter]
    A --> D[day_start]
    B --> E[scenario builder]
    C --> E
    D --> E
    E --> F[DiurnalAmplitudeMatrixRowInput PBLH]
    E --> G[DiurnalAmplitudeMatrixRowInput SHF]
    E --> H[FigureSpecification 2x3]
    F --> I[plot_diurnal_amplitude_matrix_rows]
    G --> I
    H --> I
    I --> J[Figure]
```

## Como adicionar mais uma layer

Para reproducao rapida do cenario oficial, use o builder pronto.

Se a necessidade for adicionar layers extras em um painel especifico, o
melhor caminho e descer um nivel para o recipe generico
`plot_diurnal_amplitude_matrix_rows`.

Exemplo conceitual:

```python
rows, figure_specification = (
    build_legacy_monan_e3sm_diurnal_amplitude_panel_inputs(...)
)
rows[0].left_extra_layers = [extra_layer]
figure = plot_diurnal_amplitude_matrix_rows(
    rows=rows,
    figure_specification=figure_specification,
)
```

## Observacao

Esse cenario combina:

- a semantica diurna de amplitude;
- a gramatica visual matricial do paper-grade;
- sem depender diretamente de helpers privados de outros recipes finais.
