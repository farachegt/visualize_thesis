# Pontos de atencao

## 1. Inconsistencia potencial de variaveis em `visualizations.py`

- O subset de `monan_data` atual inclui `["qc", "pressure", "hpbl", "tke_pbl"]`.
- A funcao `plot_vertical_profile_tke_hourly_mean(...)` usa por padrao tambem `hfx`.
- Se `hfx` nao estiver presente no dataset passado, pode ocorrer erro de chave.

## 2. Inconsistencia potencial de variaveis renomeadas em chamadas desativadas

- Em alguns blocos (`if False`), ha chamadas com nomes que podem nao existir no subset atual (ex.: `"pbl_height"` em E3SM apos renomeacao para `"hpbl"`).
- Ao ativar esses blocos, revisar nomes de variaveis antes.

## 3. Dependencia de caminhos hardcoded

- Paths de entrada estao fixos no codigo.
- Isso dificulta reproducao em outros ambientes sem edicao.

## 4. Custo computacional/memoria

- Uso de `open_mfdataset(..., parallel=True)` e varios `.compute()`.
- Para dominio grande, pode exigir ajuste de chunking e estrategia de leitura.

## 5. Acoplamento do periodo temporal

- Datas de 2014 estao espalhadas no codigo.
- Para cenarios novos, ha manutencao manual em mais de um ponto.

## 6. `__pycache__` versionado no diretorio

- Existem artefatos compilados em `visualize_thesis/__pycache__/`.
- Nao afeta logica, mas gera ruido de contexto para leitura/manual handoff.
