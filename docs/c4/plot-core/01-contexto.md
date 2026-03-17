# Contexto de `plot_core`

Este documento registra a proposta de arquitetura para introduzir um modulo
`plot_core` no projeto `visualize_thesis`, com foco em desacoplar:

- preparo dos dados;
- abstracao das fontes comparaveis;
- metodos de plot por geometria.

O objetivo principal e permitir comparacoes flexiveis como:

- Modelo vs Modelo
- Modelo(s) vs ERA5
- Modelo(s) vs observacao

sem acoplar os metodos de plot a nomes fixos de modelos.

Neste contexto, `Modelo` significa qualquer fonte com grade estruturada.
O tratamento arquitetural deve ser o mesmo; o que pode variar entre fontes e:

- nome das coordenadas;
- nome das variaveis;
- unidades.

## Problema atual

Os metodos de plot existentes ainda carregam conhecimento sobre pares
especificos de comparacao e nomes fixos de fontes. Isso torna mais dificil:

- reaproveitar metodos para outras comparacoes;
- incluir observacoes;
- incluir multiplos esquemas fisicos do mesmo modelo;
- evoluir para novos tipos de visualizacao.

## Objetivo arquitetural

Introduzir `plot_core` como o nucleo da arquitetura de visualizacao, cobrindo
do preparo dos dados ate os plotadores especializados, para que as figuras
sejam produzidas a partir de contratos claros em vez de datasets brutos.

Em outras palavras:

- `DataAdapter`s orquestram o preparo dos dados;
- `FileFormatReader`s leem e normalizam o formato bruto;
- `GeometryHandler`s interpretam a estrutura espacial da fonte;
- `SourceSpecification`s descrevem como interpretar variaveis, coordenadas e
  unidades;
- `plot_core` organiza contratos de `PlotData`, `RenderSpecification`,
  `PlotLayer` e
  plotadores especializados.

## Visao geral do fluxo

```mermaid
flowchart LR
    A[Fontes brutas<br/>Modelo netCDF<br/>Observacao pontual netCDF<br/>Observacao pontual CSV] --> D[DataAdapter]
    B[FileFormatReader] --> D
    C[GeometryHandler] --> D
    E[SourceSpecification] --> D
    D --> F[PlotData pronta para plot]
    R[RenderSpecification] --> L[PlotLayer]
    F --> L
    L --> G[Plotador especializado]
    G --> H[Figura final]
```
