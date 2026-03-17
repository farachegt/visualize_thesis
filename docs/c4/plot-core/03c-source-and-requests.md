# SourceSpecification e Requests

## `SourceSpecification`

`SourceSpecification` descreve como uma determinada fonte deve ser interpretada
antes de virar uma ou mais `PlotData`.

Campos sugeridos:

- `label`
- nomes das coordenadas (`lat`, `lon`, `time`, `vertical`)
- nomes das variaveis de interesse
- unidades de entrada ou unidade alvo
- configuracoes de conversao necessarias
- aliases de variaveis, quando necessario
- regras de derivacao, quando uma variavel precisa ser montada a partir de
  outras

Seu papel e permitir que a mesma arquitetura trate fontes diferentes com a
mesma logica, mesmo quando mudam:

- nome das coordenadas;
- nome das variaveis;
- unidades.

Exemplos de especializacao:

- `ModelSourceSpecification`
- `ReanalysisSourceSpecification`
- `PointObservationSourceSpecification`

Importante:

- `SourceSpecification` define nomes de coordenadas e variaveis, unidades,
  aliases e regras de derivacao;
- ela nao define os valores concretos de recorte para um caso de uso
  especifico.

## Requests de preparo

Esses requests representam o recorte e a selecao concretos para cada tipo de
saida, sem carregar informacao semantica da fonte.

Regras gerais:

- um request deve representar um caso de preparo de dados e pode ser
  reutilizado por multiplas fontes e multiplas variaveis;
- requests nao carregam nomes de variaveis nem nomes de coordenadas, porque
  isso pertence a `SourceSpecification`;
- `times` deve ser tratado como uma lista de instantes;
- para um unico tempo, a lista deve conter apenas um elemento;
- quando `times` tiver mais de um instante e `time_reduce` nao for informado,
  o comportamento esperado e gerar uma figura por tempo da lista;
- quando `times` tiver mais de um instante e `time_reduce` for informado,
  esse campo controla a agregacao temporal desejada, por exemplo `average`;
- campos de selecao espacial devem ser obrigatorios apenas quando fizerem
  sentido para a geometria da fonte;
- combinacoes contraditorias entre request e geometria devem falhar com erro
  explicito.

## `BaseRequest`

Classe base sugerida para os demais requests.

Campos obrigatorios:

- `times`

Campos opcionais:

- `time_reduce`

Uso esperado:

- concentrar o contrato temporal comum entre requests;
- padronizar o comportamento de multiplos tempos entre os diferentes tipos de
  preparo.

Os requests abaixo herdam esse contrato temporal comum.

Observacao importante:

- quando a origem do dado for um intervalo temporal (`start_time`, `end_time`),
  a lista `times` deve ser montada antes, por exemplo com
  `pandas.date_range`.

Distincao importante:

- `vertical_axis` indica o sistema do eixo vertical que sera usado no plot,
  por exemplo `pressure` ou `height`;
- `vertical_selection` indica o nivel ou a faixa vertical do dado a ser
  recortada antes do plot.

## `VerticalProfileRequest`

Campos obrigatorios:

- `vertical_axis`

Campos opcionais:

- `point_lat`
- `point_lon`
- `time_reduce`

Uso esperado:

- informar o ponto e o tempo a serem usados na geracao de um
  `VerticalProfilePlotData`.

Regras:

- `point_lat` e `point_lon` sao obrigatorios para fontes com
  `GriddedGeometryHandler`;
- para `FixedPointGeometryHandler`, esses campos podem ser omitidos;
- para `MovingPointGeometryHandler`, o caso esperado e perfil movel sem
  selecao de ponto fixo;
- para perfis verticais em fontes gridded, nao deve haver media espacial: o
  perfil deve ser extraido no ponto mais proximo das coordenadas indicadas.

## `HorizontalFieldRequest`

Campos opcionais:

- `bbox`, como tupla de recorte espacial, quando houver recorte horizontal
- `vertical_selection`, quando aplicavel
- `time_reduce`

Uso esperado:

- informar o recorte de tempo, area e nivel para um
  `HorizontalFieldPlotData`.

Regras:

- `bbox` e opcional, mas quando informado deve recortar o dominio horizontal;
- `vertical_selection` pode representar:
  - um nivel unico, por exemplo `500 hPa`;
  - ou uma faixa vertical, quando isso fizer sentido para o produto;
- quando `times` tiver mais de um instante sem `time_reduce`, o comportamento
  esperado e gerar um plot por tempo.

## `VerticalCrossSectionRequest`

Campos obrigatorios:

- `start_lat`
- `start_lon`
- `end_lat`
- `end_lon`
- `vertical_axis`

Campos opcionais:

- `n_points`
- `spacing_km`
- `time_reduce`

Uso esperado:

- informar o transecto horizontal e o recorte temporal usados na geracao de
  uma `VerticalCrossSectionPlotData`.

Regras:

- exatamente um entre `n_points` e `spacing_km` deve ser informado;
- a estrategia inicial de amostragem ao longo do transecto deve ser
  `nearest`;
- esse request faz sentido apenas para `GriddedGeometryHandler`;
- com `n_points`, os pontos do transecto devem ser distribuidos de forma
  igualmente espacada entre o inicio e o fim;
- com `spacing_km`, deve ser adicionado um ponto a cada distancia informada ao
  longo do transecto;
- quando `times` tiver mais de um instante sem `time_reduce`, o comportamento
  esperado e gerar uma secao por tempo.

## `TimeSeriesRequest`

Campos opcionais:

- `point_lat`
- `point_lon`
- `vertical_selection`, quando aplicavel
- `time_frequency`, quando houver reamostragem
- `time_reduce`, quando houver agregacao por janela

Uso esperado:

- informar a lista de tempos e, quando aplicavel, o ponto usado na geracao de
  uma `TimeSeriesPlotData`.

Regras:

- `point_lat` e `point_lon` sao obrigatorios para fontes com
  `GriddedGeometryHandler`;
- para `FixedPointGeometryHandler`, esses campos podem ser omitidos;
- esse request nao deve ser usado com `MovingPointGeometryHandler` na fase
  atual da arquitetura;
- `time_frequency` e `time_reduce` devem controlar reamostragem e agregacao
  temporal quando necessario;
- quando houver necessidade de construir `times` a partir de um intervalo, a
  lista deve ser montada antes de instanciar o request.

## Resumo

- `SourceSpecification` responde "como interpretar esta fonte?";
- os requests respondem "quais valores concretos devo recortar para este plot?".
