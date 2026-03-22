# Contratos de dados

## Convencoes gerais esperadas

- Coordenada temporal: `time`.
- Coordenadas espaciais:
  - preferencia por `latitude`/`longitude`;
  - fallback para `lat`/`lon` em varios pontos do codigo.

## Variaveis relevantes no fluxo atual

### E3SM

- `qc`
- `pbl_height` (renomeada para `hpbl`)
- `tke` (renomeada para `tke_pbl`)
- Em perfis: tambem sao assumidas `hfx` e eixo vertical `lev` (ou equivalente).

### MONAN

- `qc`
- `pressure` (normalmente em Pa; convertido para hPa em plots)
- `hpbl`
- `tke_pbl`
- Em perfis: tambem e assumida `hfx`.
- Em precipitacao: `rainnc` e `rainc`.

## Contrato da nova rotina de painel vertical por ponto

Metodo: `plot_vertical_profiles_panel_at_point(...)`.

- Entradas de variavel:
  - recebe variaveis ja prontas para plot por painel (ex.: `theta`, `qc_plus_qv`, `wind_speed`);
  - nao calcula internamente somas/modulos (como `qc+qv` ou velocidade do vento).
- Parametro temporal:
  - `time` pode ser `np.datetime64` unico ou lista de `np.datetime64`;
  - em lista, o metodo seleciona as datas e calcula media em `time`.
- Quantidade de paineis:
  - exatamente 3 ou 4 variaveis.
- Eixo vertical:
  - `vertical_axis="pressure"`: exige variavel de pressao e converte para hPa;
    - neste modo, o plot e limitado de superficie ate `700 hPa`;
  - `vertical_axis="height"`: exige variavel de altura geometrica.
- Multi-dataset:
  - 1 dataset: uma linha por painel;
  - 2 datasets: duas linhas por painel (uma por dataset).
- Nuvem liquida (hachura opcional):
  - regra fixa: hachurar onde `ql > 1e-5`;
  - controlado por parametro booleano explicito;
  - variavel de nuvem liquida deve ser informada no metodo quando hachura ativada.

## Dimensoes tipicas usadas

- Horizontal: `latitude/longitude` (ou `lat/lon`).
- Vertical:
  - MONAN: `level` (ou qualquer dim nao horizontal).
  - E3SM: `lev` (ou qualquer dim nao horizontal).

## Regra de isolinhas de nuvem no transecto

No metodo `plot_cross_section_transect(...)`, as isolinhas de `qc` agora usam
um limiar minimo configuravel via parametro `qc_contour_min` (default `1e-5`).
Os niveis de contorno passam a ser definidos de `qc_contour_min` ate o valor
maximo de `qc` no campo.

## Janela temporal padrao no codigo

- Intervalo recorrente: `2014-02-24` ate `2014-02-27`.
- Em loops horarios: de `2014-02-24T01:00` ate `2014-02-27T00:00`.

## Caminhos de dados hardcoded (atual)

- E3SM: `../E3SM_in_MONAN*.nc`
- MONAN: caminho absoluto em `/mnt/beegfs/.../diag.*`

Isso torna a execucao dependente do ambiente local/HPC.
