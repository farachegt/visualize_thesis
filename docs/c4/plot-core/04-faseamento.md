# Faseamento sugerido

## Fase 1

Criar a estrutura inicial de `plot_core`, com foco nos contratos centrais:

- `VerticalProfilePlotData`
- `HorizontalFieldPlotData`
- `VerticalCrossSectionPlotData`
- `TimeSeriesPlotData`
- `SourceSpecification`
- `RenderSpecification`
- `PlotLayer`
- `PlotPanel`
- `FigureSpecification`

sem alterar os plotadores ainda.

## Fase 2

Introduzir os componentes-base de preparo dentro da arquitetura de
`plot_core`, sem ainda migrar todos os plotadores:

- `DataAdapter`
- `FileFormatReader`
- `GeometryHandler`

Nesta fase, a API publica deve privilegiar o uso do `DataAdapter` como ponto
de entrada principal, resolvendo internamente:

- o `FileFormatReader` concreto adequado ao formato informado;
- o `GeometryHandler` concreto adequado a geometria informada.

## Fase 3

Refatorar `plot_vertical_profiles_panel_at_point(...)` para separar:

- preparo de dados;
- renderizacao.

Nesta etapa, a figura em paineis deve passar a ser modelada explicitamente por:

- `PlotPanel`
- `FigureSpecification`

Nesta etapa, a preparacao de dados deve passar a considerar familias de
componentes como:

- `DataAdapter`
- `FileFormatReader`
- `NetCDFFileFormatReader`
- `CSVFileFormatReader`
- `GeometryHandler`
- `GriddedGeometryHandler`
- `FixedPointGeometryHandler`
- `MovingPointGeometryHandler`
- `SourceSpecification`

## Fase 4

Refatorar `plot_diurnal.py` para reduzir acoplamento com nomes fixos de
fontes e aceitar fontes ou, no minimo, nomes genericos (`source_1`,
`source_2`).

## Fase 5

Criar novos plotadores horizontais genericos para comparacoes com ERA5.

## Fase 6

Adaptar e generalizar plots de secao transversal vertical usando
`VerticalCrossSectionPlotData`.

## Fase 7

Criar plotadores de series temporais de observacoes pontuais usando
`TimeSeriesPlotData`.

## Questao em aberto

Definir como organizar internamente `plot_core`:

- um submodulo mais focado em contratos (`PlotData`, `RenderSpecification`,
  `PlotLayer`, `SourceSpecification`); e
- submodulos separados para `DataAdapter`, `FileFormatReader` e
  `GeometryHandler`; ou
- uma estrutura inicial mais enxuta, com menos separacao interna.

Sugestao inicial:

- manter `plot_core` como o pacote central da arquitetura;
- separar contratos, classes base e implementacoes concretas em submodulos
  especificos dentro dele.
