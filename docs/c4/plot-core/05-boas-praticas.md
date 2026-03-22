# Boas praticas de implementacao

Este documento registra principios de implementacao do `plot_core`.

Objetivo:

- manter consistencia entre os modulos;
- reduzir retrabalho durante a migracao do codigo legado;
- evitar que o core novo reproduza acoplamentos da implementacao antiga.

Os pontos abaixo devem ser fechados de forma incremental, antes da
implementacao completa de cada fase.

## 1. Organizacao de codigo

Regras base:

- `plot_core` deve conter apenas codigo reutilizavel de producao;
- tudo que for fixture, dado de apoio e exemplo concreto deve ficar em
  `tests/`;
- cada modulo deve ter uma responsabilidade principal clara;
- evitar arquivos que misturem contrato, IO, transformacao e renderizacao;
- recipes devem apenas orquestrar o core, sem reintroduzir logica de baixo
  nivel;
- se uma funcao precisar conhecer demais de reader, geometry, derivation e
  plot ao mesmo tempo, ela provavelmente esta no lugar errado.
- recipes devem ser pensados para crescimento por composicao, e nao por
  aumento continuo da assinatura publica;
- adicionar uma nova camada ou uma nova fonte deve significar adicionar um
  novo item em uma estrutura de lista apropriada;
- evitar APIs de recipe com proliferacao de parametros como `primary_`,
  `secondary_`, `tertiary_` e similares.

Estrutura recomendada:

- `specifications.py`
  - contratos de fonte e variavel;
- `requests.py`
  - contratos de entrada para preparo;
- `plot_data.py`
  - contratos de dado pronto para plot;
- `rendering.py`
  - contratos de renderizacao e `SpecializedPlotter`;
- `readers.py`
  - leitura de disco para `xarray.Dataset`;
- `geometry.py`
  - recorte e preparo geometrico;
- `adapter.py`
  - orquestracao do preparo semantico;
- `derivations.py`
  - derivacoes e registry;
- `recipes/`
  - casos de uso concretos apoiados no core.

## 2. Tipagem e contratos

Regras base:

- usar `type hints` em assinaturas de classes, funcoes e metodos;
- priorizar tipos simples, claros e legiveis;
- validar entradas quando necessario;
- falhar cedo com erros explicitos quando houver combinacoes invalidas;
- mensagens de erro devem ser claras e informativas;
- usar `is None` e `is not None` para checagem de nulos.

Docstrings:

- usar docstrings no padrao do PEP 257 em modulos, classes importantes,
  funcoes publicas e metodos publicos;
- as docstrings devem ser objetivas;
- quando relevante, devem explicitar:
  - explicacao geral do metodo;
  - parametros;
  - retorno;
  - erros levantados.

## 3. Tratamento de dados

Regras base:

- priorizar `numpy.ndarray` em `PlotData`;
- usar `numpy.datetime64` para eixos temporais normalizados;
- manter separacao clara entre:
  - leitura de disco;
  - interpretacao semantica;
  - recorte geometrico;
  - derivacao;
  - renderizacao;
- preferir retorno explicito de valores a mudancas implicitas de estado;
- evitar efeitos colaterais desnecessarios;
- usar `pathlib` quando fizer sentido para caminhos.
- em loops de geracao de figuras com a mesma fonte, reutilizar o mesmo
  `DataAdapter` por fonte em vez de reabrir datasets a cada iteracao;
- selecoes temporais distintas devem variar pela `request`, nao por nova
  abertura do dataset;
- scripts batch devem chamar `adapter.close()` ao final para liberar handles
  NetCDF explicitamente.

## 4. Renderizacao e API

Regras base:

- `SpecializedPlotter` deve permanecer fino;
- a biblioteca de plot do core e `matplotlib`;
- `RenderSpecification` deve continuar como interface fina para a chamada do
  artist;
- a API deve ser explicita e previsivel, evitando automatismos excessivos;
- combinacoes invalidas entre `PlotData` e `artist_method` devem falhar cedo;
- o core deve separar claramente logica de negocio, IO e visualizacao.
- recipes publicos devem preferir entradas composicionais, como listas de
  camadas e paineis, em vez de assinaturas que crescem a cada novo caso de
  uso.

## 5. Tests e fixtures

Regras base:

- tudo que for fixture, dado real de exemplo e apoio a validacao deve ficar em
  `tests/`;
- os arquivos atualmente em `tests/datafiles/` devem ser tratados como dados
  de apoio ao desenvolvimento e aos testes do MVP;
- `SourceSpecification`s concretos desses dados devem ficar em
  `tests/fixtures/`;
- o core nao deve depender desses fixtures para funcionar.

## Regras gerais de estilo Python

Ao escrever codigo Python neste projeto:

- priorizar legibilidade, simplicidade e consistencia;
- seguir o PEP 8;
- usar indentacao de 4 espacos, nunca tabs;
- usar nomes descritivos e claros para variaveis, funcoes, classes e modulos;
- usar `snake_case` para funcoes, variaveis e metodos;
- usar `PascalCase` para classes;
- usar `UPPER_CASE` para constantes;
- evitar abreviacoes desnecessarias e nomes ambiguos;
- escrever funcoes curtas, coesas e com responsabilidade unica;
- evitar funcoes excessivamente longas ou com responsabilidades demais;
- organizar imports em tres grupos:
  - biblioteca padrao;
  - terceiros;
  - modulos locais;
- separar grupos de imports com uma linha em branco;
- evitar imports nao utilizados;
- preferir codigo explicito a codigo excessivamente compacto;
- usar espacos em branco de forma consistente;
- manter limite maximo de 79 caracteres por linha;
- quebrar linhas de forma legivel quando necessario;
- evitar duplicacao de codigo;
- extrair trechos repetidos em funcoes auxiliares quando apropriado;
- manter consistencia de estilo em todo o projeto;
- produzir codigo pronto para manutencao, revisao e testes;
- buscar compatibilidade com `ruff`, `flake8` e `black`.
