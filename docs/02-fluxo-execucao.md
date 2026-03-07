# Fluxo de execucao

## 1. Entrada

- `main.py` importa `main` de `visualizations.py` e executa.

## 2. Carga de dados

- `open_e3sm_data(path)`:
  - abre multiplos arquivos com `combine="by_coords"`;
  - converte coordenada `time` para `datetime64[ns]` quando possivel.
- `open_monan_data(path)`:
  - abre multiplos arquivos com `combine="nested"` e `concat_dim="Time"`;
  - reconstrui serie horaria iniciando em `2014-02-24T00:00`;
  - renomeia `Time` para `time`.

## 3. Subset e normalizacao

Em `visualizations.main()`:

- E3SM subset: `["qc", "pbl_height", "tke"]`.
- Renomeacao E3SM: `pbl_height -> hpbl`, `tke -> tke_pbl`.
- MONAN subset: `["qc", "pressure", "hpbl", "tke_pbl"]`.

## 4. Rotinas acionadas

O codigo atual esta configurado para rodar principalmente:

- `plot_vertical_profile_tke_hourly_mean(...)` para coordenadas predefinidas.

Outras rotinas estao no codigo, mas protegidas por blocos `if False`:

- `plot_side_by_side(...)`
- `plot_paper_grade_panel(...)`
- `plot_cross_section_transect(...)`
- `plot_precipitation_monan(...)`
- `plot_diurnal_cycle_amplitude_pblh(...)`
- `plot_diurnal_peak_phase_pblh(...)`
- `plot_vertical_profiles_panel_at_point(...)`

## 5. Persistencia

- Cada rotina cria seu diretorio de saida em `plots/...` e salva imagens `.png` com `dpi=300`.
