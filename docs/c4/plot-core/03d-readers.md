# FileFormatReader

## Visao geral

`FileFormatReader` define como abrir o formato bruto da fonte.

Ele deve ser tratado como uma classe abstrata, responsavel por definir a
interface comum de leitura.

Metodo esperado na interface abstrata:

- `open_data()`

Esse metodo deve retornar um `xarray.Dataset`, para que as etapas seguintes do
pipeline operem sobre uma estrutura homogenea.

Exemplos:

- `NetCDFFileFormatReader`
- `CSVFileFormatReader`

Na pratica, essas implementacoes concretas funcionam como readers
configurados para uma fonte em disco.

Campos sugeridos para as classes concretas:

- `path`, quando a leitura parte de um arquivo unico;
- `glob_pattern`, quando a fonte for definida por wildcard;
- opcoes complementares de leitura, como `engine`, `encoding`, estrategia de
  combinacao/concatenacao e `chunks`, quando necessario.

## Responsabilidades

- armazenar a referencia da fonte em disco;
- abrir com a biblioteca adequada, como `xarray` ou `pandas`;
- preservar comportamento lazy quando o backend permitir;
- lidar com parsing basico de tempo, colunas e tipos;
- devolver um objeto interno consistente para o `DataAdapter`.

Importante:

- nesta arquitetura, o `FileFormatReader` nao deve aplicar
  `SourceSpecification`;
- tambem nao deve resolver nomes canonicos de variaveis;
- a normalizacao semantica de coordenadas e variaveis deve ficar no
  `DataAdapter`.

## `NetCDFFileFormatReader`

Comportamento esperado:

- implementa `open_data()`;
- quando receber `path`, deve usar `xarray.open_dataset`;
- quando receber `glob_pattern`, deve usar `xarray.open_mfdataset`;
- pode receber `engine`;
- pode receber parametros adicionais do metodo de backend efetivamente usado;
- quando usar `open_mfdataset`, pode receber parametros de
  combinacao/concatenacao;
- pode receber `chunks`;
- pode receber um metodo `preprocess`, se necessario;
- deve suportar leitura de multiplos arquivos apenas por meio de
  `glob_pattern`;
- deve devolver um `xarray.Dataset`.

Exemplos curtos:

```python
NetCDFFileFormatReader(path="/dados/monan/history_20140215.nc")
```

```python
NetCDFFileFormatReader(
    glob_pattern="/dados/monan/history_201402*.nc",
    chunks={"time": 1},
)
```

## `CSVFileFormatReader`

Comportamento esperado:

- implementa `open_data()`;
- deve usar `pandas.read_csv`;
- pode receber opcoes como `encoding`, `sep`, `decimal` e `parse_dates`;
- apos a leitura, deve converter o conteudo para `xarray.Dataset`;
- deve devolver um `xarray.Dataset`.

Escopo recomendado para a primeira implementacao:

- suportar apenas `path`, e nao `glob_pattern`;
- nao tentar concatenar multiplos CSVs nesta primeira fase;
- esperar um CSV tabular simples, em formato "tidy", em que cada linha
  represente uma observacao em um instante;
- deixar o mapeamento de colunas para nomes canonicos a cargo do
  `DataAdapter`, com base em `SourceSpecification`;
- converter a tabela para `xarray.Dataset` sem introduzir pivots ou reshapes
  complexos demais.

Casos que eu priorizaria no CSV logo de inicio:

- observacao em sitio fixo para `TimeSeriesPlotData`;
- estacao de superficie em CSV como caso principal de uso;
- produtos observacionais tabulares simples em ponto fixo.

Casos que eu nao tentaria suportar logo de inicio:

- grade horizontal vindo de CSV;
- radiossonda em CSV;
- multiplos arquivos CSV por wildcard;
- formatos "wide" muito especificos, que exigem pivot manual antes de virar
  `Dataset`.

Campos de `reader_options` mais importantes para CSV neste comeco:

- `sep`
- `encoding`
- `decimal`
- `parse_dates`
- `header`
- `na_values`
- `skiprows`

Regra pratica importante:

- `CSVFileFormatReader` nao deve tentar adivinhar estruturas tabulares muito
  heterogeneas;
- para o MVP, ele deve assumir uma tabela observacional relativamente limpa e
  previsivel;
- no caso real priorizado desta arquitetura, ele deve ser pensado para uma
  estacao de superficie em geometria `fixed_point`;
- quando latitude, longitude ou altitude do sitio nao estiverem no CSV, esses
  metadados devem ser informados explicitamente pelo usuario em
  `SourceSpecification`;
- se um CSV exigir preprocessamento pesado antes de virar um `Dataset`,
  isso deve ser tratado como excecao especifica e nao como responsabilidade
  padrao do reader.

Exemplo curto:

```python
CSVFileFormatReader(
    path="/dados/obs/estacao_superficie.csv",
    sep=",",
    parse_dates=True,
)
```

## Resumo

- `FileFormatReader` responde "como ler este formato?".
