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

Resultado esperado desta fase:

- o codigo antigo de perfil vertical deixa de manipular diretamente
  `xarray` e `matplotlib`;
- passa a ser um recipe de alto nivel que usa o `plot_core`.

## Fase 4

Refatorar `plot_diurnal.py` para reduzir acoplamento com nomes fixos de
fontes e aceitar fontes ou, no minimo, nomes genericos (`source_1`,
`source_2`).

Resultado esperado desta fase:

- `plot_diurnal.py` deixa de concentrar leitura, preparo e renderizacao de
  baixo nivel;
- passa a montar o fluxo via `DataAdapter`, `PlotData`, `PlotLayer`,
  `PlotPanel`, `FigureSpecification` e `SpecializedPlotter`.

## Fase 5

Criar novos plotadores horizontais genericos para comparacoes com ERA5.

## Fase 6

Adaptar e generalizar plots de secao transversal vertical usando
`VerticalCrossSectionPlotData`.

## Fase 7

Criar plotadores de series temporais de observacoes pontuais usando
`TimeSeriesPlotData`.

## Diretriz geral de migracao

Ao longo das fases acima, a diretriz deve ser esta:

- os scripts antigos da raiz do projeto nao devem ser apenas "mantidos em
  paralelo" ao novo core;
- eles devem ser gradualmente adaptados para virar modulos de recipes que usam
  o `plot_core`;
- a logica reutilizavel deve migrar para o core;
- os scripts finais devem ficar mais enxutos e mais proximos de descricao de
  caso de uso do que de implementacao detalhada.

Leitura correta dessa estrategia:

- `plot_core` = nucleo reutilizavel da arquitetura;
- scripts/refatoracoes na raiz = recipes de alto nivel apoiados no core.

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
