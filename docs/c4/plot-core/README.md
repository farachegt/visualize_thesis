# C4 de `plot_core`

Este diretorio concentra a documentacao C4 do modulo `plot_core`.

## Superficie oficial atual

O codigo oficial do projeto, a partir desta fase da migracao, esta
organizado assim:

- `plot_core/`
  - contratos, adapters, renderizacao e recipes genericos;
- `plot_core/scenarios/`
  - cenarios oficiais concretos do projeto;
- `scripts/recipes/`
  - scripts oficiais de geracao de figuras;
- `legacy/`
  - referencia historica do codigo e da documentacao anteriores.

## Conteudo

- [01-contexto.md](./01-contexto.md):
  problema, objetivo e exemplos de comparacao.
- [02-estrutura-macro.md](./02-estrutura-macro.md):
  blocos macro da solucao e separacao entre preparo, contratos e plotadores.
- [03-componentes.md](./03-componentes.md): indice do nivel de componentes.
- [03a-plot-data.md](./03a-plot-data.md): contratos de `PlotData`.
- [03b-renderizacao.md](./03b-renderizacao.md):
  `RenderSpecification`, `PlotLayer`, `PlotPanel` e
  `FigureSpecification`.
- [03c-source-and-requests.md](./03c-source-and-requests.md):
  `SourceSpecification` e requests de preparo.
- [03d-readers.md](./03d-readers.md):
  `FileFormatReader`, `NetCDFFileFormatReader` e
  `CSVFileFormatReader`.
- [03e-geometry-handlers.md](./03e-geometry-handlers.md):
  `GeometryHandler`, especializacoes e compatibilidades.
- [03f-data-adapter.md](./03f-data-adapter.md):
  papel do `DataAdapter` e relacao entre os componentes.
- [03g-exemplos.md](./03g-exemplos.md):
  exemplos concretos de uso da arquitetura.
- [03h-exemplos-completos.md](./03h-exemplos-completos.md):
  exemplos mais completos, da abertura da fonte ate a chamada do plot.
- [04-faseamento.md](./04-faseamento.md): ordem sugerida de implementacao.
- [05-boas-praticas.md](./05-boas-praticas.md):
  principios de implementacao e estilo.
- [06-recipes.md](./06-recipes.md): indice visual dos recipes publicos.
- [07-como-criar-um-recipe.md](./07-como-criar-um-recipe.md):
  guia pratico para criar um recipe novo.
