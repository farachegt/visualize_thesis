# FileFormatReader

## Visao geral

`FileFormatReader` define como abrir e normalizar o formato bruto da fonte.

Ele deve ser tratado como uma classe abstrata, responsavel por definir a
interface comum de leitura e normalizacao.

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
- normalizar a estrutura minima de entrada para a etapa seguinte;
- lidar com parsing basico de tempo, colunas e tipos;
- devolver um objeto interno consistente para o `DataAdapter`.

## Normalizacao estrutural minima

Por normalizacao estrutural minima, entende-se:

- padronizar nomes de coordenadas, por exemplo evitando misturar `lon` com
  `longitude` ou `lat` com `latitude`;
- padronizar longitude para o intervalo `[-180, 180]`;
- manter a estrutura em `xarray.Dataset` para homogeneizar as etapas
  seguintes.

Essa normalizacao nao deve incluir transformacoes cientificas, como medias,
derivacoes meteorologicas ou selecoes espaciais/temporais de analise.

## `NetCDFFileFormatReader`

Comportamento esperado:

- implementa `open_data()`;
- deve usar `xarray.open_mfdataset`;
- pode receber `engine`;
- pode receber parametros de combinacao/concatenacao do `open_mfdataset`;
- pode receber `chunks`;
- pode receber um metodo `preprocess`, se necessario;
- deve suportar leitura de multiplos arquivos apenas por meio de
  `glob_pattern`;
- deve devolver um `xarray.Dataset`.

## `CSVFileFormatReader`

Comportamento esperado:

- implementa `open_data()`;
- deve usar `pandas.read_csv`;
- pode receber opcoes como `encoding`, `sep`, `decimal` e `parse_dates`;
- apos a leitura, deve converter o conteudo para `xarray.Dataset`;
- deve devolver um `xarray.Dataset`.

## Resumo

- `FileFormatReader` responde "como ler este formato?".
