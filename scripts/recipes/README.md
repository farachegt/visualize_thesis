# Scripts oficiais de recipes

Este diretorio concentra os entrypoints oficiais de geracao de figuras.

## Regras

- cada script deve consumir `plot_core/scenarios/`;
- loops batch devem reutilizar o mesmo `DataAdapter` por fonte;
- selecoes temporais ou espaciais devem variar pela `request`, nao por
  reabertura do dataset;
- ao final, scripts batch devem chamar `adapter.close()`.
