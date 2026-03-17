# GeometryHandler

## Visao geral

`GeometryHandler` define como interpretar a estrutura espacial da fonte.

Ele deve ser tratado como uma classe abstrata, responsavel por definir a
interface comum de interpretacao geometrica.

Exemplos:

- `GriddedGeometryHandler`
- `FixedPointGeometryHandler`
- `MovingPointGeometryHandler`

## Responsabilidades

- centralizar a logica espacial, evitando `if gridded`, `if fixed_point` ou
  `if moving_point` espalhados no `DataAdapter`;
- descrever se a fonte e grade estruturada, ponto fixo ou ponto movel;
- explicitar se latitude/longitude sao fixas ou variam no tempo;
- definir regras estruturais de selecao espacial;
- validar se a geometria do `Dataset` e compativel com o handler escolhido;
- fornecer ao `DataAdapter` a leitura correta da geometria da fonte.

## Interface abstrata sugerida

- `assert_geometry_compatible(dataset, source_specification)`
- `supported_plot_data_kinds(dataset, source_specification)`
- `prepare_vertical_profile_dataset(dataset, source_specification, request)`
- `prepare_horizontal_field_dataset(dataset, source_specification, request)`
- `prepare_vertical_cross_section_dataset(dataset, source_specification, request)`
- `prepare_time_series_dataset(dataset, source_specification, request)`

Nessa interface:

- `SourceSpecification` informa nomes de coordenadas, variaveis e unidades;
- os requests informam os valores concretos de recorte, como ponto, periodo,
  area, transecto ou selecao vertical.

## Retorno dos metodos `prepare_*`

Os metodos `prepare_*` devem retornar um `xarray.Dataset` intermediario ja:

- com o dominio espacial e temporal requerido aplicado;
- com a estrutura geometrica correta para o tipo de saida solicitado;
- com as coordenadas necessarias preservadas;
- com a variavel alvo e, quando necessario, variaveis auxiliares exigidas pela
  `SourceSpecification`;
- com metadados uteis preservados, quando eles puderem ser relevantes para o
  `DataAdapter`.

Em outras palavras:

- o `GeometryHandler` prepara a estrutura e o recorte do `Dataset`;
- o `DataAdapter` usa esse resultado para completar transformacoes,
  agregacoes, derivacoes e montagem da `PlotData`.

Regra de implementacao:

- todos os metodos `prepare_*` devem existir na classe abstrata;
- subclasses que nao suportarem um tipo de saida devem falhar explicitamente,
  com erro claro.

## Validacao geometrica

Uma forma de nomear essa validacao de maneira mais clara e:

- `assert_geometry_compatible()`

Exemplos do que essa validacao deve verificar em cada especializacao:

- `GriddedGeometryHandler`
  - existencia de coordenadas de latitude e longitude;
  - presenca de mais de um valor espacial em latitude/longitude;
  - compatibilidade com operacoes tipicas de grade, como extrair campo
    horizontal ou selecionar ponto mais proximo;
  - para recortes pontuais, a estrategia inicial deve ser ponto mais proximo
    (`nearest`);
  - para secoes transversais, deve permitir amostragem ao longo de um
    transecto horizontal.

- `FixedPointGeometryHandler`
  - latitude/longitude representando um ponto fixo;
  - ausencia de grade horizontal completa;
  - garantia de que a posicao nao varia no tempo, embora possa existir
    dimensao vertical;
  - o caso esperado e um unico sitio fixo, como uma estacao de superficie.

- `MovingPointGeometryHandler`
  - latitude/longitude associadas a amostras, perfis ou tempo;
  - variacao espacial do ponto ao longo do conjunto de dados;
  - ausencia de grade estruturada horizontal;
  - o caso esperado e de perfis moveis, como radiossonda, e nao de dados
    moveis genericos, como aeronaves.

Observacao importante:

- `FixedPoint` significa apenas que a amostragem horizontal e fixa;
- a fonte ainda pode ter dimensao vertical, como no caso de um ceilometer em
  sitio fixo.

## Compatibilidade entre `GeometryHandler` e `PlotData`

Essa relacao existe como restricao de compatibilidade, mas nao deve ser tratada
como acoplamento estrutural rigido.

Casos esperados:

- `GriddedGeometryHandler`
  - pode produzir `HorizontalFieldPlotData`;
  - pode produzir `VerticalProfilePlotData`, quando houver dimensao vertical;
  - pode produzir `VerticalCrossSectionPlotData`, quando houver dimensao
    vertical e grade horizontal;
  - pode produzir `TimeSeriesPlotData`, quando houver selecao temporal pontual.

- `FixedPointGeometryHandler`
  - pode produzir `TimeSeriesPlotData`;
  - pode produzir `VerticalProfilePlotData`, quando houver dimensao vertical;
  - nao deve produzir `VerticalCrossSectionPlotData`;
  - nao deve produzir `HorizontalFieldPlotData`.

- `MovingPointGeometryHandler`
  - pode produzir `VerticalProfilePlotData`;
  - nao deve produzir `VerticalCrossSectionPlotData`;
  - nao deve produzir `HorizontalFieldPlotData`;
  - nao deve produzir `TimeSeriesPlotData`.

Consequencia para a implementacao:

- o `DataAdapter` deve validar se a combinacao entre `GeometryHandler` e o tipo
  de `PlotData` solicitado e suportada;
- combinacoes impossiveis devem falhar cedo, com erro explicito;
- quando `VerticalProfilePlotData` for solicitado, a ausencia de dimensao
  vertical deve falhar com erro explicito.

## Resumo

- `GeometryHandler` responde "como esta fonte se organiza no espaco?".
