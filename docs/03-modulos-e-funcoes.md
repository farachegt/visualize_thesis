# Modulos e funcoes

## `io_utils.py`

- `open_monan_data(path) -> xr.Dataset`
  - abre arquivos MONAN;
  - ajusta coordenada de tempo horaria.
- `open_e3sm_data(path) -> xr.Dataset`
  - abre arquivos E3SM;
  - padroniza coordenada `time`.

## `plot_maps.py`

- `plot_side_by_side(...)`
  - mapa MONAN, mapa E3SM e diferenca MONAN-E3SM para um horario.
- `plot_paper_grade_panel(...)`
  - painel multi-linha (variaveis configuraveis) com MONAN/E3SM/delta.
- `plot_precipitation_monan(data)`
  - calcula chuva horaria (`diff` de `rainnc` e `rainc`) e plota mapas.

## `plot_diurnal.py`

- `plot_diurnal_cycle_amplitude_pblh(...)`
  - por dia: `max(time) - min(time)` para PBLH em MONAN e E3SM.
- `plot_diurnal_peak_phase_pblh(...)`
  - por dia: hora local de pico (`idxmax`) e diferenca de fase.

## `plot_profiles.py`

Funcoes auxiliares de geodesia, mascara espacial, ordenacao de dimensoes e limites de plot:

- `_haversine_circle_mask`, `_haversine_distance_km`
- `_spatial_select_in_bbox`, `_spatial_mean_in_circle`
- `_solar_offset_hours`, `_ensure_dim_order`
- `_height_to_pressure_hpa`, `_pressure_to_hpa`
- `_build_contour_levels`, `_compute_hfx_limits`
- `_nearest_lon_index`

Funcoes principais:

- `plot_vertical_profile_tke_hourly_mean(...)`
  - seleciona caixa lat/lon;
  - converte para hora solar local;
  - calcula media horaria multi-dia;
  - gera painel 2x2:
    - TKE + contorno QC + linha PBLH (MONAN)
    - TKE + contorno QC + linha PBLH (E3SM)
    - serie HFX (MONAN)
    - serie HFX (E3SM)
- `plot_cross_section_transect(...)`
  - constroi transecto geodesico entre dois pontos;
  - projeta em grade de ambos modelos por ponto mais proximo;
  - para cada hora, plota secao vertical MONAN e E3SM com contornos QC;
  - possui `qc_contour_min` (default `1e-5`) para iniciar os niveis de isolinha em `qc_contour_min`.
- `plot_vertical_profiles_panel_at_point(...)`
  - plota 3 ou 4 paineis de perfil vertical em um unico horario e ponto;
  - `time` pode ser uma data unica ou uma lista de datas;
  - quando `time` for lista, plota a media temporal das variaveis nas datas passadas;
  - X = valor da variavel (ja pronta, sem transformacoes internas);
  - Y configuravel:
    - `pressure`: usa variavel de pressao e converte para hPa;
    - `height`: usa variavel de altura geometrica;
  - quando `vertical_axis="pressure"`, o eixo Y fica limitado de superficie ate `700 hPa`;
  - funciona com 1 dataset (uma curva por painel) ou 2 datasets (duas curvas por painel);
  - opcionalmente hachura camada de nuvem onde `ql > 1e-5` (agua liquida);
  - titulo inclui coordenada solicitada e coordenada real de grade usada (`N/S`, `E/W`).
