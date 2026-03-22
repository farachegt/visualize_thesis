# Documentacao oficial do projeto `visualize_thesis`

Este diretorio concentra a documentacao oficial da arquitetura atual do
projeto.

## Comece por aqui

- [c4/README.md](./c4/README.md): indice principal da documentacao
  arquitetural.
- [c4/plot-core/README.md](./c4/plot-core/README.md): arquitetura oficial do
  `plot_core`.

## Superficie oficial do codigo

- `plot_core/`
  - nucleo de preparo, contratos e renderizacao;
- `plot_core/scenarios/`
  - cenarios oficiais, `SourceSpecification`s, adapters, requests e builders
    concretos;
- `scripts/recipes/`
  - entrypoints oficiais para geracao de figuras e execucao batch.

## Material legado

O material da implementacao anterior foi preservado separadamente em:

- `legacy/code/`
  - codigo legado mantido apenas para referencia historica;
- `legacy/docs/README.md`
  - documentacao legada preservada.

## Escopo desta documentacao

- esta documentacao cobre apenas a arquitetura oficial atual de
  `visualize_thesis`;
- wrappers de compatibilidade na raiz e em `tests/` nao sao a superficie
  recomendada para extensao futura.
