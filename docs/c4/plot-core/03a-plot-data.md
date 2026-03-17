# PlotData

## Visao geral

`PlotData` e a familia de contratos de dados prontos para plot.

Essas estruturas:

- nao carregam regra de leitura de arquivo;
- nao carregam regra de interpretacao semantica da fonte;
- nao carregam detalhes completos de renderizacao;
- representam apenas o dado ja preparado para um tipo de plot.

## `VerticalProfilePlotData`

Representa dados prontos para plot em perfis verticais.

Campos sugeridos:

- `label`
- `profiles`
- `y_values`
- `vertical_axis`
- `units`
- `cloud_mask`
- `coordinate_label`

Uso esperado:

- perfil vertical de modelo;
- perfil vertical observado;
- media temporal de perfis.

## `HorizontalFieldPlotData`

Representa dados prontos para plot em mapas e produtos horizontais.

Campos sugeridos:

- `label`
- `field`
- `lon`
- `lat`
- `units`
- `time_label`
- `mask`

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
- `field`
- `x_values`
- `x_label`
- `y_values`
- `vertical_axis`
- `units`
- `coordinate_labels`
- `mask`

Uso esperado:

- secoes transversais em campos 3D de modelo;
- media temporal de transectos verticais;
- sobreposicao de superficie colorida, isolinhas e mascaras em um plano
  vertical.

## `TimeSeriesPlotData`

Representa dados prontos para plot em series temporais.

Campos sugeridos:

- `label`
- `times`
- `values`
- `units`
- `site_label`

Uso esperado:

- series temporais em observacoes pontuais em sitio fixo;
- series temporais em estacoes de superficie, torres de fluxo ou sensores como
  ceilometer;
- comparacao modelo vs observacao;
- comparacao entre configuracoes do mesmo modelo.

## Leitura correta

- `PlotData` = dado pronto para plot;
- `PlotData` nao substitui `SourceSpecification`;
- `PlotData` nao substitui `RenderSpecification`;
- `PlotData` e o resultado do preparo realizado pelo `DataAdapter`.
