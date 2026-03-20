# SourceSpecification e Requests

## `SourceSpecification`

`SourceSpecification` descreve como uma determinada fonte deve ser interpretada
antes de virar uma ou mais `PlotData`.

Campos sugeridos:

- `label`
- nomes das coordenadas (`latitude`, `longitude`, `time`, `vertical`)
- especificacao das variaveis canonicas de interesse
- unidades de entrada ou unidade alvo
- configuracoes de conversao necessarias
- regras de derivacao, quando uma variavel precisa ser montada a partir de
  outras

Seu papel e permitir que a mesma arquitetura trate fontes diferentes com a
mesma logica, mesmo quando mudam:

- nome das coordenadas;
- nome das variaveis;
- unidades.

Simplificacao importante para a implementacao inicial:

- nao e necessario introduzir subclasses como `ModelSourceSpecification`,
  `ReanalysisSourceSpecification` ou `PointObservationSourceSpecification`;
- uma unica `SourceSpecification` ja cobre o que precisamos;
- tambem nao e necessario carregar `source_type` como parte do contrato da
  primeira versao do codigo;
- se em algum momento isso fizer falta, `source_type` pode voltar depois como
  metadado opcional, sem alterar a ideia central da arquitetura;
- `SourceSpecification` define nomes de coordenadas e variaveis, unidades,
  unidades alvo e regras de derivacao;
- nomes de coordenadas podem ser opcionais quando a fonte seguir convencoes
  homogeneas;
- ela nao define os valores concretos de recorte para um caso de uso
  especifico.

## Estrutura sugerida

### `VariableSpecification`

`VariableSpecification` deve descrever como uma variavel canonica e resolvida
dentro de uma fonte especifica.

Campos sugeridos:

- `source_name`
- `input_units`
- `target_units`
- `derivation_kind`
- `derivation_options`, opcional

Leitura correta desses campos:

- `source_name`
  - nome real da variavel na fonte;
- `input_units`
  - unidade de entrada esperada;
  - se nao for explicitada, o sistema deve tentar recuperar
    `attrs["units"]` da variavel no `xarray.Dataset` ou `xarray.DataArray`;
- `target_units`
  - unidade interna ou de saida desejada;
- `derivation_kind`
  - identifica uma derivacao fechada e registrada no sistema;
- `derivation_options`
  - parametros adicionais da derivacao, quando necessarios;
  - deve ser tratado como opcional e raro;
  - so faz sentido quando uma derivacao registrada aceitar configuracao fina
    por fonte.

Exemplos curtos:

- `VariableSpecification(derivation_kind="wind_speed_from_uv")`
- `VariableSpecification(derivation_kind="rh_from_qv_temperature_pressure")`
- `VariableSpecification(
    derivation_kind="pressure_from_height_standard_atmosphere",
    derivation_options={"lapse_rate": 0.0065},
  )`

Regra importante:

- uma variavel pode ser resolvida diretamente pela fonte, via `source_name`;
- ou pode ser resolvida por derivacao, via `derivation_kind`;
- `source_name` e `derivation_kind` podem coexistir;
- quando coexistirem, o comportamento esperado e:
  - tentar `source_name` primeiro;
  - se a variavel nao estiver disponivel, tentar a derivacao.

### `SourceSpecification`

`SourceSpecification` deve descrever uma fonte completa.

Campos sugeridos:

- `label`
- `latitude_name`
- `longitude_name`
- `time_name`
- `vertical_name`
- `site_latitude`, opcional
- `site_longitude`, opcional
- `site_altitude`, opcional
- `site_label`, opcional
- `variables`

Regra de organizacao:

- `variables` deve ser um dicionario;
- a chave do dicionario deve ser o nome canonico interno da variavel;
- o valor associado a cada chave deve ser uma `VariableSpecification`.

Leitura correta dos metadados de sitio:

- `site_latitude`, `site_longitude` e `site_altitude` devem ser usados quando
  a fonte representar um ponto fixo e essas informacoes nao estiverem no
  proprio arquivo;
- `site_label` pode identificar textualmente o sitio, por exemplo `ATTO` ou
  `T3`;
- esses campos sao especialmente uteis para o caso de `CSVFileFormatReader`
  com `geometry_type="fixed_point"`.

Exemplo conceitual:

```python
SourceSpecification(
    label="MONAN_SHOC",
    variables={
        "theta": VariableSpecification(source_name="theta"),
        "qv": VariableSpecification(source_name="QV"),
        "temperature": VariableSpecification(source_name="T"),
        "pressure": VariableSpecification(source_name="pres"),
        "rh": VariableSpecification(
            derivation_kind="rh_from_qv_temperature_pressure",
            target_units="percent",
        ),
    },
)
```

Exemplo curto de request associado:

```python
VerticalProfileRequest(
    times=[t0],
    vertical_axis="pressure",
    point_lat=-3.21,
    point_lon=-60.60,
)
```

## Variaveis canonicas

A fonte de verdade dos nomes canonicos deve ficar no codigo, em um modulo
simples dedicado, por exemplo:

- `plot_core/canonical_variables.py`

Nesse modulo, a forma recomendada e manter apenas uma lista ou conjunto simples
de nomes canonicos, sem introduzir estruturas mais complexas do que o
necessario.

A lista documentada abaixo representa o estado atual esperado da arquitetura:

- `theta`
- `rh`
- `wind_speed`
- `u_wind`
- `v_wind`
- `pressure`
- `height`
- `hpbl`
- `qc`
- `qv`
- `temperature`
- `tke`
- `sensible_heat_flux`
- `rthblten`
- `rublten`
- `rvblten`
- `rqvblten`
- `rqcblten`
- `rtkeblten`

Esses nomes sao a interface semantica esperada pelo restante do `plot_core`.
A `SourceSpecification` mapeia cada nome canonico para:

- o nome real da variavel na fonte, quando existir;
- unidades de entrada;
- unidade alvo, quando desejado;
- regra de derivacao, quando a variavel nao existir diretamente.

Importante:

- a presenca de todas essas variaveis nao e obrigatoria em uma fonte;
- essa lista representa o vocabulario canonico que a arquitetura sabe tratar
  internamente;
- a lista documentada aqui e descritiva;
- a fonte de verdade deve ser o modulo dedicado no codigo, para que a
  atualizacao de variaveis canonicas permaneça simples;
- quando uma dessas variaveis existir na fonte, a `SourceSpecification` pode
  declarar o `source_name` correspondente para que ela seja tratada de forma
  uniforme;
- quando nao existir, ela simplesmente nao precisa ser mapeada, a menos que
  seja necessaria para um caso de uso especifico ou possa ser derivada a
  partir de outras.
- `qv` deve ser tratado como `water vapor mixing ratio`;
- `qc` deve ser tratado como `liquid water mixing ratio`.

## Derivacoes suportadas

As derivacoes declaradas em `SourceSpecification` podem incluir, entre outras:

- `theta` a partir de `pressure` e `temperature`;
- `wind_speed` a partir de `u_wind` e `v_wind`;
- `rh` a partir de `qv`, `temperature` e `pressure`, quando nao existir
  diretamente na fonte;
- `height` a partir de `pressure`;
- `pressure` a partir de `height`.

Sempre que houver suporte direto no MetPy, a derivacao registrada no sistema
deve apontar para a funcao oficial de `metpy.calc`, em vez de reimplementar a
formula manualmente.

Casos fechados para esta arquitetura:

- `theta_from_pressure_temperature`
  - usar `metpy.calc.potential_temperature(pressure, temperature)`;
- `rh_from_qv_temperature_pressure`
  - usar `metpy.calc.relative_humidity_from_mixing_ratio(...)`, com
    `pressure`, `temperature` e `mixing_ratio`;
- `height_from_pressure_standard_atmosphere`
  - usar `metpy.calc.pressure_to_height_std(pressure)`;
- `pressure_from_height_standard_atmosphere`
  - usar `metpy.calc.height_to_pressure_std(height)`.

As conversoes entre `pressure` e `height` devem seguir a mesma ideia ja usada
na versao anterior do codigo:

- atmosfera padrao;
- lapse rate padrao.

Importante:

- essas derivacoes pertencem ao contrato semantico da fonte;
- elas nao devem aparecer como conhecimento embutido no plotador;
- a execucao dessas derivacoes fica a cargo do `DataAdapter`, a partir do que
  estiver declarado em `SourceSpecification`.
- nesta primeira versao, nao e necessario introduzir uma classe
  `DerivationSpecification`;
- o registry de derivacoes pode ser mantido como um dicionario simples;
- `derivation_kind` deve apontar para um conjunto fechado de derivacoes
  registradas no codigo;
- as dependencias de cada derivacao nao devem ser repetidas manualmente em
  `VariableSpecification`;
- o proprio registry da derivacao deve informar quais variaveis canonicas sao
  necessarias para executa-la;
- o registry deve preferir funcoes oficiais do MetPy sempre que elas
  existirem;
- no caso de `rh_from_qv_temperature_pressure`, o registry deve considerar a
  assinatura atual documentada no MetPy:
  `relative_humidity_from_mixing_ratio(
  pressure, temperature, mixing_ratio, *, phase='liquid'
  )`;
- no caso especifico de `pressure <-> height`, a conversao deve ser tratada
  apenas como apoio a exibicao no plot;
- essa conversao nao deve orientar recorte geometrico, selecao vertical ou a
  resolucao de `vertical_axis` no `GeometryHandler`.

Exemplo conceitual de `DERIVATION_REGISTRY`:

```python
DERIVATION_REGISTRY = {
    "theta_from_pressure_temperature": {
        "dependencies": ("pressure", "temperature"),
        "function": derive_theta_from_pressure_temperature,
        "accepted_options": (),
    },
    "wind_speed_from_uv": {
        "dependencies": ("u_wind", "v_wind"),
        "function": derive_wind_speed_from_uv,
        "accepted_options": (),
    },
    "rh_from_qv_temperature_pressure": {
        "dependencies": ("qv", "temperature", "pressure"),
        "function": derive_rh_from_qv_temperature_pressure,
        "accepted_options": ("phase",),
    },
    "height_from_pressure_standard_atmosphere": {
        "dependencies": ("pressure",),
        "function": derive_height_from_pressure_standard_atmosphere,
        "accepted_options": (),
    },
    "pressure_from_height_standard_atmosphere": {
        "dependencies": ("height",),
        "function": derive_pressure_from_height_standard_atmosphere,
        "accepted_options": (),
    },
}
```

Regra para esta fase:

- devemos manter apenas essas derivacoes registradas inicialmente;
- novas derivacoes devem entrar apenas quando aparecer um caso de uso real.

Exemplo curto de resolucao:

- se a fonte nao tiver `rh` diretamente;
- mas tiver `qv`, `temperature` e `pressure`;
- entao `SourceSpecification` pode declarar:
  - `rh -> derivation_kind="rh_from_qv_temperature_pressure"`.

Quando nomes de coordenadas nao forem explicitados, o sistema deve tentar
inferi-los antes de normalizar o `Dataset` para nomes internos canonicos:

- `latitude`
- `longitude`
- `time`
- `vertical`

Fallbacks iniciais permitidos:

- `longitude` ou `lon` -> `longitude`
- `latitude` ou `lat` -> `latitude`
- `time` ou `Time` -> `time`
- `level` ou `pres` -> `vertical`

Regra importante:

- a inferencia deve ser conservadora;
- em caso de ausencia ou ambiguidade, o sistema deve falhar com erro
  explicito;
- a coordenada vertical merece cuidado especial, porque `pres` pode aparecer
  como variavel de pressao e nao necessariamente como coordenada vertical.

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
- quando `times` tiver mais de um instante e `time_reduce` for informado,
  esse campo controla a agregacao temporal desejada;
- nesta arquitetura, os valores aceitos para `time_reduce` sao:
  - `mean`
  - `sum`
  - `min`
  - `max`;
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
- para requests em que o tempo nao seja um eixo explicito do produto final,
  `times` deve conter apenas um instante quando `time_reduce` nao for
  informado;
- se o usuario quiser gerar um plot por tempo, esse loop deve ficar fora do
  `DataAdapter`;
- `TimeSeriesRequest` e `TimeVerticalSectionRequest` sao os casos em que o
  tempo compoe diretamente um eixo do produto final.

Distincao importante:

- `vertical_axis` indica o sistema do eixo vertical que sera usado no plot,
  por exemplo `pressure` ou `height`;
- `vertical_selection` indica o nivel vertical unico do dado a ser recortado
  antes do plot, quando esse recorte for aplicavel.

Regra importante para esta fase:

- `vertical_axis="height"` nao deve ser solicitado quando a fonte possuir
  apenas coordenada vertical em `pressure`;
- quando houver conversao `pressure <-> height`, ela deve ser entendida como
  informacao auxiliar de exibicao, e nao como base para recorte vertical.

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
- quando `time_reduce` nao for informado, `times` deve conter apenas um
  instante;
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
- `vertical_selection` deve representar apenas um nivel unico, por exemplo
  `500 hPa`;
- quando `time_reduce` nao for informado, `times` deve conter apenas um
  instante.

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
- quando `time_reduce` nao for informado, `times` deve conter apenas um
  instante.

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
- `vertical_selection`, quando informada, deve representar apenas um nivel
  unico, por exemplo `925 hPa`;
- `time_frequency` e `time_reduce` devem controlar reamostragem e agregacao
  temporal quando necessario;
- para `TimeSeriesRequest`, `times` deve ser interpretado como o seletor
  temporal da serie;
- quando a selecao desejada for um intervalo temporal continuo, basta informar
  os limites do intervalo, por exemplo `[start_time, end_time]`;
- na implementacao do MVP, o `GeometryHandler` usa `min(times)` e `max(times)`
  para selecionar todos os pontos dentro desse intervalo continuo;
- se houver necessidade futura de suportar selecoes temporais discretas e nao
  contiguas, esse contrato precisara ser expandido.

## `TimeVerticalSectionRequest`

Campos obrigatorios:

- `vertical_axis`

Campos opcionais:

- `bbox`
- `time_frequency`
- `time_reduce`

Uso esperado:

- informar o periodo e, quando aplicavel, a regiao usados na geracao de uma
  `TimeVerticalSectionPlotData`;
- representar a evolucao temporal de um perfil vertical medio em uma regiao.

Regras:

- `times` define diretamente o eixo temporal do produto final;
- diferentemente de `VerticalProfileRequest`, `HorizontalFieldRequest`,
  `VerticalCrossSectionRequest` e `TimeSeriesRequest`, este request nao deve
  gerar uma `PlotData` por tempo quando `times` tiver multiplos elementos;
- em vez disso, a saida esperada e uma unica `TimeVerticalSectionPlotData`
  cobrindo toda a sequencia temporal solicitada;
- quando `bbox` for informado em uma fonte gridded, o `DataAdapter` deve usar
  essa regiao para calcular a media espacial antes de montar o campo
  vertical x tempo;
- para `GriddedGeometryHandler`, `bbox` deve ser o caso principal no MVP;
- para `FixedPointGeometryHandler`, `bbox` pode ser omitido, porque nao ha
  media espacial a realizar;
- esse request nao deve ser usado com `MovingPointGeometryHandler` na fase
  atual da arquitetura;
- `time_frequency` e `time_reduce` podem ser usados para controlar a
  reamostragem temporal ao longo do eixo do plot.
- assim como em `TimeSeriesRequest`, `times` pode ser informado apenas pelos
  limites de um intervalo temporal continuo.

## Resumo

- `SourceSpecification` responde "como interpretar esta fonte?";
- os requests respondem
  "quais valores concretos devo recortar para este plot?".
