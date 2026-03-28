# `plot_core/recipes/_shared`

Este diretorio concentra helpers compartilhados entre recipes finais.

## Regra de uso

- recipes finais podem depender de `_shared`;
- recipes finais nao devem depender de helpers privados umas das outras;
- se uma logica passar a ser usada por mais de um recipe final, ela pode ser
  candidata a extracao para este diretorio.

## O que deve existir aqui

- primitivas reutilizaveis e estaveis;
- funcoes auxiliares genericas para mais de um recipe;
- contratos auxiliares pequenos, quando fizer sentido.

## O que nao deve existir aqui

- wrappers finais de plots;
- defaults de cenarios concretos;
- scripts batch;
- codigo que ainda pertence claramente a um unico recipe.

## Modulos atuais

- `comparison_matrix.py`
  logica compartilhada para comparacoes `left / right / delta`
- `diurnal_reductions.py`
  logica compartilhada para amplitude e fase diurna

## Manutencao

Ao alterar um helper deste diretorio:

1. localizar os recipes consumidores;
2. revisar o impacto em cada consumidor;
3. alinhar os recipes afetados;
4. rerodar validacoes minimas;
5. atualizar a documentacao se a semantica mudou.
