# PlotData

## Visao geral

`PlotData` e a familia de contratos de dados prontos para plot.

Essas estruturas:

- nao carregam regra de leitura de arquivo;
- nao carregam regra de interpretacao semantica da fonte;
- nao carregam kwargs de `matplotlib`;
- representam apenas o dado ja preparado para um tipo de plot;
- devem, sempre que possivel, carregar arrays ja prontos para o `matplotlib`,
  e nao objetos mais pesados como `xarray.Dataset`.

Convencao recomendada para a implementacao inicial:

- arrays numericos devem preferencialmente ser `numpy.ndarray`;
- eixos temporais devem preferencialmente ser `numpy.ndarray` com
  `datetime64[ns]`;
- o objetivo e manter `PlotData` leve, eficiente em memoria e diretamente
  compativel com `matplotlib`.

Regra importante:

- na implementacao inicial, nao e necessario criar uma classe base concreta
  `PlotData`;
- basta implementar diretamente as dataclasses concretas abaixo;
- `PlotData` deve conter o dado principal da camada;
- se existir uma sobreposicao semantica adicional, como uma regiao hachurada de
  nebulosidade, essa sobreposicao deve preferencialmente virar outra
  `PlotLayer`, com sua propria `PlotData` e sua propria `RenderSpecification`;
- o campo `draw_mask`, quando existir, deve ser entendido principalmente como
  mecanismo para ocultar ou invalidar pontos da propria camada, e nao como
  descricao completa de uma camada visual extra.

## `VerticalProfilePlotData`

Representa dados prontos para plot em perfis verticais.

Campos sugeridos:

- `label`
  - identifica a fonte ou a camada na legenda;
  - exemplos: `MONAN_SHOC`, `MONAN_MYNN`, `GOAMAZON`.
- `values`
  - array 1D com os valores da variavel ao longo do eixo vertical;
  - exemplo: perfil de `theta`, `rh` ou `wind_speed`.
- `vertical_values`
  - array 1D com os valores do eixo vertical usados no plot;
  - exemplo: niveis de pressao ou altura.
- `vertical_axis`
  - semantica do eixo vertical;
  - exemplos: `pressure`, `height`;
  - esse campo ajuda o plotador a saber, por exemplo, se deve inverter o eixo
    quando ele estiver em pressao.
- `auxiliary_vertical_values`, opcional
  - eixo vertical auxiliar apenas para exibicao;
  - exemplo: altura calculada a partir de pressao para montar um eixo
    secundario.
- `units`
  - unidade da variavel armazenada em `values`.
- `draw_mask`, opcional
  - mascara booleana 1D, com o mesmo tamanho de `values`;
  - deve ser usada para ocultar pontos invalidos da propria camada.

Uso esperado:

- perfil vertical de modelo;
- perfil vertical observado;
- media temporal de perfis.

Observacao importante:

- se o objetivo for representar, por exemplo, faixas com agua liquida ou
  nebulosidade como hachura, isso deve preferencialmente ser modelado como
  outra camada de plot, e nao apenas como `draw_mask` da curva principal.

## `HorizontalFieldPlotData`

Representa dados prontos para plot em mapas e produtos horizontais.

Campos sugeridos:

- `label`
  - identifica a fonte ou a camada na legenda.
- `field`
  - array 2D com o campo a ser desenhado.
  - a convencao recomendada para o array e `(y, x)`, em que:
    - `y` representa o eixo latitude;
    - `x` representa o eixo longitude.
- `longitude`
  - coordenadas de longitude compativeis com `field`;
  - pode ser array 1D ou 2D, dependendo da malha.
- `latitude`
  - coordenadas de latitude compativeis com `field`;
  - pode ser array 1D ou 2D, dependendo da malha.
- `units`
  - unidade do campo.
- `time_label`, opcional
  - string pronta para exibicao temporal;
  - exemplos: `2014-02-15 12 UTC`, `media 00-06 UTC`.
- `vertical_label`, opcional
  - string pronta para indicar o nivel vertical do campo;
  - exemplos: `500 hPa`, `925 hPa`, `surface`.
- `draw_mask`, opcional
  - mascara booleana 2D, com o mesmo dominio horizontal de `field`;
  - deve ser usada para ocultar pontos invalidos ou excluidos da propria
    camada.

Uso esperado:

- campos instantaneos;
- medias temporais;
- amplitude de ciclo diurno;
- fase de pico;
- modelo, ERA5 ou observacao gridded.

## `VerticalCrossSectionPlotData`

Representa dados prontos para plot em secoes transversais verticais.

Campos sugeridos:

- `label`
  - identifica a fonte ou a camada na legenda.
- `field`
  - array 2D com o campo da secao transversal.
  - a convencao recomendada para o array e `(y, x)`, em que:
    - `y` representa o eixo vertical;
    - `x` representa o eixo horizontal do transecto.
- `transect_values`
  - array 1D com o eixo horizontal da secao;
  - exemplo: distancia acumulada em km ao longo do transecto.
- `transect_label`
  - label do eixo horizontal da secao;
  - exemplo: `Distance (km)`.
- `vertical_values`
  - array 1D ou 2D com o eixo vertical usado no plot.
- `vertical_axis`
  - semantica do eixo vertical;
  - exemplos: `pressure`, `height`.
- `auxiliary_vertical_values`, opcional
  - eixo vertical auxiliar apenas para exibicao.
- `units`
  - unidade do campo.
- `draw_mask`, opcional
  - mascara booleana 2D com o mesmo shape de `field`;
  - deve ser usada para ocultar pontos invalidos da propria camada.
- `transect_latitude`, opcional
  - latitudes dos pontos amostrados ao longo do transecto.
- `transect_longitude`, opcional
  - longitudes dos pontos amostrados ao longo do transecto.
- `start_label`, opcional
  - label textual do inicio do transecto;
  - exemplo: `A` ou `Manaus`.
- `end_label`, opcional
  - label textual do fim do transecto;
  - exemplo: `B` ou `T3`.

Uso esperado:

- secoes transversais em campos 3D de modelo;
- media temporal de transectos verticais;
- sobreposicao de superficie colorida, isolinhas e mascaras em um plano
  vertical.

Observacao importante:

- `start_label` e `end_label` sao apenas metadados textuais dos extremos do
  transecto;
- eles nao substituem `transect_latitude` e `transect_longitude`, que carregam
  a geometria real amostrada.

## `TimeSeriesPlotData`

Representa dados prontos para plot em series temporais.

Campos sugeridos:

- `label`
  - identifica a fonte ou a camada na legenda.
- `times`
  - sequencia temporal ja normalizada para um formato de referencia unico;
  - para esta arquitetura, o formato de referencia recomendado e
    `numpy.ndarray` com `datetime64[ns]`;
  - o `DataAdapter` deve aceitar entradas como `DatetimeIndex`, `np.ndarray`
    temporal ou objetos `datetime`, mas deve converter tudo para esse formato
    de referencia antes de montar a `PlotData`.
- `values`
  - array 1D com os valores da variavel ao longo do tempo.
- `units`
  - unidade da variavel.
- `site_label`, opcional
  - identificacao textual do sitio ou ponto fixo;
  - exemplos: `T3`, `GOAMAZON`, `ATTO`.
- `vertical_label`, opcional
  - identificacao textual de um nivel vertical, quando aplicavel;
  - exemplos: `50 m`, `925 hPa`.
- `draw_mask`, opcional
  - mascara booleana 1D com o mesmo tamanho de `values`;
  - deve ser usada para ocultar pontos invalidos da propria camada.

Uso esperado:

- series temporais em observacoes pontuais em sitio fixo;
- series temporais em estacoes de superficie, torres de fluxo ou sensores como
  ceilometer;
- comparacao modelo vs observacao;
- comparacao entre configuracoes do mesmo modelo.

## `TimeVerticalSectionPlotData`

Representa dados prontos para plot em uma secao vertical x tempo.

Campos sugeridos:

- `label`
  - identifica a fonte ou a camada na legenda.
- `field`
  - array 2D com shape compativel com vertical x tempo;
  - esse e o campo principal a ser desenhado por `contourf`, `contour` ou
    `pcolormesh`.
  - a convencao recomendada para o array e `(y, x)`, em que:
    - `y` representa o eixo vertical;
    - `x` representa o eixo temporal.
- `times`
  - eixo temporal ja normalizado;
  - deve preferencialmente ser `numpy.ndarray` com `datetime64[ns]`.
- `vertical_values`
  - array 1D ou 2D com o eixo vertical usado no plot;
  - exemplo: niveis de pressao ao longo do tempo.
- `vertical_axis`
  - semantica do eixo vertical;
  - exemplos: `pressure`, `height`.
- `auxiliary_vertical_values`, opcional
  - eixo vertical auxiliar apenas para exibicao.
- `units`
  - unidade do campo.
- `region_label`, opcional
  - identificacao textual da regiao media usada para montar a secao;
  - exemplo: `African Desert` ou `Amazonia central`.
- `draw_mask`, opcional
  - mascara booleana 2D com o mesmo shape de `field`;
  - deve ser usada para ocultar pontos invalidos da propria camada.

Uso esperado:

- evolucao temporal de um perfil vertical medio em uma regiao;
- exemplo: `tke` medio em uma area da Amazonia ao longo de 24 h;
- sobreposicao com uma serie temporal no mesmo painel, como `hpbl`
  convertido para pressao equivalente.

## Leitura correta

- `PlotData` = dado pronto para plot;
- `PlotData` nao substitui `SourceSpecification`;
- `PlotData` nao substitui `RenderSpecification`;
- `PlotData` e o resultado do preparo realizado pelo `DataAdapter`.
