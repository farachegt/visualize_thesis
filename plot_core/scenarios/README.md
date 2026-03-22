# Cenarios oficiais

Este diretorio concentra os cenarios oficiais concretos do projeto.

## Conteudo esperado

- `SourceSpecification`s;
- adapters concretos;
- requests concretas;
- builders de recipes e figuras para os fluxos suportados oficialmente.

## Papel arquitetural

- `plot_core/` permanece como nucleo reutilizavel;
- `plot_core/scenarios/` liga esse nucleo aos casos reais do projeto;
- `scripts/recipes/` consome esses cenarios como entrypoints oficiais.
