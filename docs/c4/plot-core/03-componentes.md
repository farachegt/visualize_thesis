# Componentes de `plot_core`

O detalhamento do nivel de componentes foi dividido por assunto para facilitar
revisao e manutencao.

## Conteudo

- [03a-plot-data.md](./03a-plot-data.md): contratos de `PlotData`.
- [03b-renderizacao.md](./03b-renderizacao.md): `RenderSpecification`,
  `PlotLayer`, `PlotPanel` e `FigureSpecification`.
- [03c-source-and-requests.md](./03c-source-and-requests.md):
  `SourceSpecification` e requests de preparo.
- [03d-readers.md](./03d-readers.md): `FileFormatReader`,
  `NetCDFFileFormatReader` e `CSVFileFormatReader`.
- [03e-geometry-handlers.md](./03e-geometry-handlers.md):
  `GeometryHandler`, especializacoes e compatibilidades.
- [03f-data-adapter.md](./03f-data-adapter.md): papel do `DataAdapter` e
  relacao entre os componentes.
- [03g-exemplos.md](./03g-exemplos.md): exemplos concretos de uso da
  arquitetura.

## Roteiro de leitura

Uma leitura produtiva deste bloco costuma ser:

1. [03a-plot-data.md](./03a-plot-data.md)
2. [03c-source-and-requests.md](./03c-source-and-requests.md)
3. [03d-readers.md](./03d-readers.md)
4. [03e-geometry-handlers.md](./03e-geometry-handlers.md)
5. [03f-data-adapter.md](./03f-data-adapter.md)
6. [03b-renderizacao.md](./03b-renderizacao.md)
7. [03g-exemplos.md](./03g-exemplos.md)

## Papel deste nivel

Neste nivel, estamos descrevendo:

- contratos de dados prontos para plot;
- contratos de renderizacao;
- contratos de preparo;
- componentes que orquestram leitura, interpretacao geometrica e producao de
  `PlotData`;
- exemplos de composicao em figuras com uma ou multiplas fontes.
