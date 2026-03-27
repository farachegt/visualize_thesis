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

## Convencao de longitude

Quando a fonte usar grade georreferenciada, o cenario deve declarar a
convencao de longitude sempre que ela for conhecida.

Valores suportados hoje:

- `-180_180`
- `0_360`

Essa informacao entra na `SourceSpecification` e e usada pela camada
geometrica para normalizar:

- selecao de ponto;
- selecao por `bbox`;
- amostragem de transectos.

Quando a convencao nao for declarada, o core ainda tenta inferi-la pela
grade do dataset. Mesmo assim, declarar explicitamente continua sendo o
caminho recomendado nos cenarios oficiais.
