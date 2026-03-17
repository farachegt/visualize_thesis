# Renderizacao

## Visao geral

Este documento descreve os contratos que ligam dado pronto para plot com a
figura final.

## `RenderSpecification`

`RenderSpecification` descreve como uma camada especifica de `PlotData` deve
ser renderizada.

Campos sugeridos:

- `render_kind` (`surface`, `contour`, `line`, `scatter`, `vector`, `hatch`)
- `label`
- `units_label`, quando fizer sentido sobrescrever a exibicao
- `cmap`
- `vmin`
- `vmax`
- `levels`
- `colors`
- `linestyle`
- `linewidth`
- `marker`
- `alpha`
- `zorder`

Essa separacao e util para desacoplar:

- o conteudo do dado pronto para plot; e
- a forma como cada camada sera desenhada.

## `PlotLayer`

`PlotLayer` representa uma camada renderizavel.

Ela associa:

- uma `PlotData`;
- uma `RenderSpecification`.

Com isso:

- o `PlotData` continua sendo um contrato puro de dado;
- a `RenderSpecification` continua sendo um contrato puro de render.

## `PlotPanel`

`PlotPanel` representa um subplot individual dentro de uma figura.

Ela agrupa:

- uma ou mais `PlotLayer`s;
- metadados especificos do painel.

Campos sugeridos:

- `layers`
- `title`
- `x_label`
- `y_label`
- `x_limits`
- `y_limits`
- `show_grid`
- `legend_mode`, quando necessario

Uso esperado:

- um painel de perfil vertical para uma variavel;
- um painel horizontal com superficie colorida e isolinhas;
- um painel temporal com uma ou mais fontes comparadas.

No caso de paineis multi-fonte:

- cada fonte gera sua propria `PlotLayer`;
- todas as camadas da mesma variavel entram no mesmo `PlotPanel`.

## `FigureSpecification`

`FigureSpecification` descreve como uma figura completa deve ser organizada.

Campos sugeridos:

- `nrows`
- `ncols`
- `figsize`
- `suptitle`
- `sharex`
- `sharey`
- `shared_legend`
- `output_name`, quando fizer sentido

Uso esperado:

- organizar uma figura com multiplos `PlotPanel`s;
- definir layout de figuras como 1x3, 2x2 ou outros arranjos;
- permitir painel unico ou multiplos paineis com metadados compartilhados.

## O que o plotador recebe

O plotador nao recebe:

- `DataAdapter`;
- `FileFormatReader`;
- `GeometryHandler`;
- `SourceSpecification`;
- dado bruto;
- regra de preprocessamento.

O plotador recebe:

- uma ou mais `PlotPanel`s prontas;
- uma `FigureSpecification`.

## Resumo

- `RenderSpecification` = instrucao de render por camada;
- `PlotLayer` = camada renderizavel;
- `PlotPanel` = subplot com uma ou mais camadas;
- `FigureSpecification` = layout da figura completa.
