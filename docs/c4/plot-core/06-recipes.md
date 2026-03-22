# Recipes

Este documento organiza a documentacao visual dos recipes publicos de
`plot_core`.

## Objetivo

Cada recipe deve ter um markdown proprio com:

- objetivo do recipe;
- link para uma imagem de referencia do plot gerado;
- fluxo visual de alto nivel;
- fluxo visual interno mais completo;
- orientacao de extensao por layer;
- exemplo minimo de chamada.

## Constraint de extensibilidade

Sim: adicionar ou remover uma layer compativel com o tipo do plot sem
inflar a assinatura publica era uma constraint explicita do projeto.

Em termos praticos, isso significa:

- crescer por composicao de listas;
- adicionar uma nova `layer` com poucos ajustes no codigo chamador;
- evitar APIs com `primary_`, `secondary_`, `tertiary_` e variacoes;
- manter compatibilidade semantica do plot.

Compatibilidade semantica significa, por exemplo:

- um recipe de `vertical profile` aceita novas layers de perfil vertical;
- um recipe de mapa aceita novas layers de campo horizontal;
- um recipe de secao vertical aceita novas layers de secao vertical;
- nao se mistura `HorizontalFieldPlotData` em um plot de perfil vertical.

## Regra de uso em loops

Em geracao batch de figuras:

- instanciar um `DataAdapter` por fonte;
- reutilizar o mesmo adapter ao longo do loop;
- variar apenas a `request` em cada iteracao;
- chamar `adapter.close()` ao final do batch.

## Recipes documentados

- [Vertical Profiles Panel](./recipes/01-vertical-profiles-panel.md)
- [Hourly Mean Panels](./recipes/02-hourly-mean-panels.md)
- [Legacy TKE Hourly Mean](./recipes/03-legacy-tke-hourly-mean.md)
- [Cross Section Panels](./recipes/04-cross-section-panels.md)
- [Map Panels](./recipes/05-map-panels.md)
- [Map Comparison Rows](./recipes/06-map-comparison-rows.md)
- [Paper Grade Panel](./recipes/07-paper-grade-panel.md)
