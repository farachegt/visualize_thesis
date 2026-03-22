# Faseamento sugerido

## Objetivo do faseamento

O objetivo deste faseamento e transformar a arquitetura documentada em uma
ordem de implementacao pragmatica para o MVP, reduzindo retrabalho e
separando claramente:

- o nucleo reutilizavel em `plot_core`;
- cenarios oficiais e exemplos concretos baseados nos arquivos em
  `datafiles`;
- recipes que substituirao gradualmente os scripts antigos da raiz.

## Estrutura-alvo inicial

Para o MVP, a estrutura sugerida e esta:

```text
scripts/
└── recipes/
    └── generate_*.py
legacy/
├── code/
└── docs/
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
├── scenarios/
│   └── source_specifications.py
└── recipes/
    ├── __init__.py
    ├── profiles.py
    ├── diurnal.py
    └── maps.py
```

Leitura correta dessa organizacao:

- `scripts/recipes/` contem os entrypoints oficiais para execucao batch;
- `legacy/` preserva a implementacao e a documentacao anteriores;
- `plot_core` contem apenas contratos e implementacoes reutilizaveis;
- `plot_core/scenarios/source_specifications.py` contem
  `SourceSpecification`s concretos dos arquivos de teste presentes em
  `datafiles`;
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
- validacao inicial do contrato:
  - `PlotLayer` -> `PlotPanel` -> `FigureSpecification`.

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
- cachear o `Dataset` aberto para reutilizacao em multiplas requests da mesma
  fonte;
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
- scripts e recipes batch poderem reutilizar o mesmo `DataAdapter` por fonte
  ao longo de loops temporais ou espaciais, fechando o cache explicitamente
  ao final.

## Fase 6

Criar cenarios oficiais reais para os arquivos em `datafiles`.

Arquivo foco:

- `plot_core/scenarios/source_specifications.py`

Esses cenarios devem conter `SourceSpecification`s especificos para os dados
de teste, por exemplo:

- modelo em NetCDF;
- radiossonda observada em NetCDF;
- ceilometro observado em CSV.

Diretriz importante:

- essas specifications pertencem ao pacote oficial de cenarios;
- os dados de apoio continuam em `tests/datafiles/`;
- o core continua desacoplado desses cenarios concretos.

Resultado esperado:

- validacao do core com dados reais desde o inicio;
- menor risco de uma arquitetura correta no papel e ruim em uso real.

## Fase 7

Traduzir os fluxos antigos para recipes apoiados no core.

Prioridade sugerida:

1. `legacy/code/plot_profiles.py`
2. `legacy/code/plot_diurnal.py`
3. `legacy/code/plot_maps.py`

Resultado esperado desta fase:

- os fluxos legados deixam de ser a superficie oficial do projeto;
- os recipes reconstruidos passam a cobrir os mesmos casos de uso, sem
  manipular diretamente:
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
- os recipes reconstruidos devem manter flexibilidade composicional:
  - adicionar uma nova camada deve significar adicionar um novo item em uma
    lista de entradas;
  - adicionar um novo painel deve significar adicionar um novo item em uma
    lista de paineis;
  - a API publica dos recipes nao deve voltar a crescer por duplicacao de
    parametros por fonte, por camada ou por variavel.

## Fase 8

Remover compatibilidade temporaria restante apos a promocao da nova
arquitetura.

Resultado esperado desta fase:

- `plot_core/`, `plot_core/scenarios/` e `scripts/recipes/` tornam-se a
  unica superficie oficial do projeto;
- wrappers temporarios da raiz e de `tests/` deixam de existir;
- `tests/` volta a concentrar apenas dados de apoio e testes reais;
- `legacy/` passa a ser a unica referencia do codigo e da documentacao
  anteriores.

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
- cenarios oficiais = contratos concretos para validar o MVP com dados reais;
- recipes = camada de orquestracao de casos de uso concretos.
