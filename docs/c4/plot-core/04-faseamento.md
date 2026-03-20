# Faseamento sugerido

## Objetivo do faseamento

O objetivo deste faseamento e transformar a arquitetura documentada em uma
ordem de implementacao pragmatica para o MVP, reduzindo retrabalho e
separando claramente:

- o nucleo reutilizavel em `plot_core`;
- fixtures de teste e exemplos concretos baseados nos arquivos em `datafiles`;
- recipes que substituirao gradualmente os scripts antigos da raiz.

## Estrutura-alvo inicial

Para o MVP, a estrutura sugerida e esta:

```text
plot_core/
├── __init__.py
├── canonical_variables.py
├── derivations.py
├── specifications.py
├── requests.py
├── plot_data.py
├── rendering.py
├── adapter.py
├── readers.py
├── geometry.py
└── recipes/
    ├── __init__.py
    ├── profiles.py
    ├── diurnal.py
    └── maps.py

tests/
└── fixtures/
    └── source_specifications.py
```

Leitura correta dessa organizacao:

- `plot_core` contem apenas contratos e implementacoes reutilizaveis;
- `tests/fixtures/source_specifications.py` contem `SourceSpecification`s
  concretos dos arquivos de teste presentes em `datafiles`;
- `plot_core/recipes/` ou recipes equivalentes substituem gradualmente os
  scripts antigos da raiz, passando a operar como clientes do core.

## Fase 1

Criar os contratos centrais do `plot_core`.

Arquivos foco:

- `specifications.py`
- `requests.py`
- `plot_data.py`
- `rendering.py`
- `canonical_variables.py`

Componentes a implementar:

- `SourceSpecification`
- `VariableSpecification`
- `VerticalProfileRequest`
- `HorizontalFieldRequest`
- `VerticalCrossSectionRequest`
- `TimeSeriesRequest`
- `TimeVerticalSectionRequest`
- `VerticalProfilePlotData`
- `HorizontalFieldPlotData`
- `VerticalCrossSectionPlotData`
- `TimeSeriesPlotData`
- `TimeVerticalSectionPlotData`
- `RenderSpecification`
- `ColorbarSpecification`
- `PlotLayer`
- `PlotPanel`
- `FigureSpecification`
- lista de nomes canonicios em `canonical_variables.py`

Resultado esperado:

- contratos estaveis para requests, dados de plot e renderizacao;
- nenhum acoplamento ainda com leitura real de arquivos;
- base pronta para desenvolvimento incremental.

## Fase 2

Implementar o nucleo de renderizacao.

Arquivo foco:

- `rendering.py`

Componente principal:

- `SpecializedPlotter`

Escopo do MVP:

- suporte aos metodos:
  - `plot`
  - `contourf`
  - `contour`
  - `pcolormesh`
- matriz suportada:
  - `VerticalProfilePlotData` -> `plot`
  - `TimeSeriesPlotData` -> `plot`
  - `HorizontalFieldPlotData` -> `contourf`, `contour`, `pcolormesh`
  - `VerticalCrossSectionPlotData` -> `contourf`, `contour`, `pcolormesh`
  - `TimeVerticalSectionPlotData` -> `contourf`, `contour`, `pcolormesh`

Resultado esperado:

- ja ser possivel montar figuras a partir de `PlotData` manualmente criadas;
- validacao inicial do contrato `PlotLayer` -> `PlotPanel` -> `FigureSpecification`.

## Fase 3

Implementar leitura e preparo geometrico base.

Arquivos foco:

- `readers.py`
- `geometry.py`

Componentes:

- `FileFormatReader`
- `NetCDFFileFormatReader`
- `CSVFileFormatReader`
- `GeometryHandler`
- `GriddedGeometryHandler`
- `FixedPointGeometryHandler`
- `MovingPointGeometryHandler`

Decisoes importantes desta fase:

- `FileFormatReader` apenas le do disco e converte para `xarray.Dataset`;
- a normalizacao semantica nao acontece no reader;
- `CSVFileFormatReader` no MVP suporta apenas:
  - `path`
  - um unico CSV
  - caso `fixed_point`
  - tabela observacional simples.

Resultado esperado:

- leitura funcional dos arquivos de teste em NetCDF e CSV;
- recortes espaciais, temporais e verticais basicos disponiveis por geometria.

## Fase 4

Implementar semantica de variaveis e derivacoes.

Arquivo foco:

- `derivations.py`

Componentes:

- wrappers locais para `MetPy`
- `DERIVATION_REGISTRY`

Derivacoes iniciais do MVP:

- `theta_from_pressure_temperature`
- `wind_speed_from_uv`
- `rh_from_qv_temperature_pressure`
- `height_from_pressure_standard_atmosphere`
- `pressure_from_height_standard_atmosphere`

Resultado esperado:

- o core passa a resolver variaveis diretas e derivadas sob um contrato unico.

## Fase 5

Implementar o `DataAdapter`.

Arquivo foco:

- `adapter.py`

Responsabilidades:

- abrir a fonte via `FileFormatReader`;
- aplicar `SourceSpecification`;
- resolver `required_variable_names` como conjunto expandido de dependencias
  da chamada atual;
- acionar o `GeometryHandler` adequado;
- montar e devolver uma unica `PlotData` por chamada.

Metodos publicos do MVP:

- `open_data()`
- `to_vertical_profile_plot_data(...)`
- `to_horizontal_field_plot_data(...)`
- `to_vertical_cross_section_plot_data(...)`
- `to_time_series_plot_data(...)`
- `to_time_vertical_section_plot_data(...)`

Resultado esperado:

- ja ser possivel gerar `PlotData` reais a partir dos arquivos de teste.

## Fase 6

Criar fixtures de teste reais para os arquivos em `datafiles`.

Arquivo foco:

- `tests/fixtures/source_specifications.py`

Essas fixtures devem conter `SourceSpecification`s especificos para os dados de
teste, por exemplo:

- modelo em NetCDF;
- radiossonda observada em NetCDF;
- ceilometro observado em CSV.

Diretriz importante:

- essas specifications de teste nao pertencem ao `plot_core`;
- elas existem apenas para desenvolvimento, validacao e testes do MVP.

Resultado esperado:

- validacao do core com dados reais desde o inicio;
- menor risco de uma arquitetura correta no papel e ruim em uso real.

## Fase 7

Refatorar os scripts antigos para recipes apoiados no core.

Prioridade sugerida:

1. `plot_profiles.py`
2. `plot_diurnal.py`
3. `plot_maps.py`

Resultado esperado desta fase:

- os scripts antigos deixam de manipular diretamente:
  - `xarray`
  - `matplotlib`
  - selecao espacial e temporal
  - derivacao de variaveis
  - conversao de unidades
- passam a montar o fluxo via:
  - `DataAdapter`
  - `PlotData`
  - `RenderSpecification`
  - `PlotLayer`
  - `PlotPanel`
  - `FigureSpecification`
  - `SpecializedPlotter`

## Diretriz geral de migracao

Ao longo das fases acima, a diretriz deve ser esta:

- os scripts antigos da raiz do projeto nao devem ser apenas mantidos em
  paralelo ao novo core;
- eles devem ser gradualmente adaptados para virar recipes que usam o
  `plot_core`;
- a logica reutilizavel deve migrar para o core;
- os scripts finais devem ficar mais enxutos e mais proximos de descricao de
  caso de uso do que de implementacao detalhada.

Leitura correta dessa estrategia:

- `plot_core` = nucleo reutilizavel da arquitetura;
- fixtures de teste = contratos concretos para validar o MVP com dados reais;
- recipes = camada de orquestracao de casos de uso concretos.
