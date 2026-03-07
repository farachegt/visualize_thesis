# Contexto rapido para usar em outros chats

Copie e cole o bloco abaixo no inicio de outro chat:

```md
Projeto: `pgmet/Tese` (ignorar `pgmet/Tese/egeon`).

Objetivo:
- Comparar campos atmosfericos de MONAN vs E3SM e gerar figuras (mapas, ciclo diurno, perfis verticais e transectos).

Arquivos principais:
- `main.py`: entrypoint.
- `visualizations.py`: orquestra carga, subset e chamadas de plot.
- `io_utils.py`: leitura com xarray e padronizacao de `time`.
- `plot_maps.py`: lado a lado, painel "paper-grade", precipitacao.
- `plot_diurnal.py`: amplitude/fase diaria da PBLH.
- `plot_profiles.py`: perfil vertical horario e transecto vertical.
- `plot_profiles.py` (novo): `plot_vertical_profiles_panel_at_point` para 3-4 paineis de perfil por ponto/horario, com Y em pressao ou altura e hachura opcional de nuvem liquida (`ql > 1e-5`).

Fluxo atual:
- `main.py -> visualizations.main()`.
- Carrega E3SM (`../E3SM_in_MONAN*.nc`) e MONAN (path absoluto `/mnt/beegfs/...`).
- Renomeia E3SM: `pbl_height -> hpbl`, `tke -> tke_pbl`.
- Loop principal chama `plot_vertical_profile_tke_hourly_mean` (as demais rotinas estao em `if False`).

Convencoes de dados:
- Tempo: `time`.
- Espaco: `latitude/longitude` com fallback para `lat/lon`.
- Variaveis centrais: `qc`, `hpbl`, `tke_pbl`, `pressure`, `hfx`, (`rainnc/rainc` para chuva).

Atencoes:
- Possivel falta de `hfx` no subset MONAN atual.
- Blocos desativados podem ter nomes de variaveis desatualizados.
- Datas e paths hardcoded.
```
