# Visao geral

## Objetivo

Comparar saidas de MONAN e E3SM para variaveis de camada limite atmosferica e campos associados, gerando figuras para analise cientifica (mapas, ciclos diurnos, perfis verticais e transectos).

## Estrutura principal

- `main.py`: ponto de entrada minimo.
- `visualizations.py`: orquestracao das rotinas de comparacao e plot.
- `io_utils.py`: abertura/padronizacao temporal de datasets.
- `plot_maps.py`: mapas lado a lado, painel combinado e precipitacao MONAN.
- `plot_diurnal.py`: amplitude e fase do ciclo diurno de PBLH.
- `plot_profiles.py`: perfis verticais medios por hora local e transectos.

## Dependencias centrais

- `xarray`, `numpy`, `pandas`
- `matplotlib`
- `cartopy`

## Saidas

- Todas as figuras sao salvas em subpastas de `plots/` (criadas sob demanda).
- Nome de arquivos inclui data/hora e contexto da figura.
