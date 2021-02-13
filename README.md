# SentinelPTWMSTimeMachine
Gerador de mosaicos de imagens Sentinel-2 RGB e IRG para Portugal, com serviço WMS, com suporte temporal.\
Descrevem-se os ficheiros por ordem de execução.
Um viewer está disponível aqui: http://sentinelpt.viasig.com/.
As imagens obtidas são do nível S2MSI2A, que são "Bottom-of-atmosphere reflectance in cartographic geometry", ou seja, com correção atmosférica incluída. Mais info: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/product-types.

![image](https://user-images.githubusercontent.com/2836636/107666615-9cfa5100-6c86-11eb-84bf-a9490f91b4e1.png)
![image](https://user-images.githubusercontent.com/2836636/107667135-3164b380-6c87-11eb-9ea4-dfe838d6acd3.png)![image](https://user-images.githubusercontent.com/2836636/107667326-640eac00-6c87-11eb-8176-8bc5f7abe5f8.png)

## sentinelptTM_total3.sh
Script que executa todos os passos para obter, processar, e publicar as imagens para uma data especificada pelo utilizador. Deve ser executado quando se pretende uma data nova ou substituir uma que já exista em disco.
Cria nova pasta com as imagens, e actualiza o shapefile de índice que é simultaneamente a bd com as imagens disponíveis. Exporta este shp para json que é depois usado no viewer html.

## sentinelsat_band_parallel.py

Pesquisa arquivo Sentinel 2, por tiles específicas, para um dia específico, e faz download apenas das bandas 2, 3, 4, e 8. E faz o download banda-a-banda.\
Versão que abre 2 sessoes em paralelo, que é o máximo de conexoes permitido pelo sci-hub.\
\
Parameters: data no formato yyyymmdd - pesquisa 5 dias anteriores. (obrigatório)\
            cloudcov_int =  70 cobertura de nuvens aceitavel (opcional)\
            tiles_str = 'T29SMC|T29SMD|T29SND|T29SPD|T29TNE|T29TNF|T29TNG|T29TPE|T29TPF|T29TPG|T29TQF|T29TQG'\
                         usamos as tiles indicadas no comando ou pesquisamos as tiles de portugal (opcional)\
\
Notes: codigo inicial obtido em: https://gis.stackexchange.com/questions/233670/sentinel2-get-jpeg200-bands-only \
        utiliza sentinelsat: https://github.com/sentinelsat/sentinelsat \
        só procede com o download se todas as tiles forem encontradas nesse dia\
\
Exemplo: tiles=29SNB, 29SNC, 29SPB, 29SPC (para o alqueva)\
\
É preciso substituir "user" e "pass" pelo login no scihub.\

## gdal_processa_pasta3.py
Processa bandas numa pasta sentinel2 em jp2 16 bits para tif 8bits etrs89 usando um script de comandos gdal externo (gdal_sentinel2_rgbi_reproj_msk4.sh).\
Parameters: pasta com ficheiros a processar e onde se guardam os resultados.

## gdal_sentinel2_rgbi_reproj_msk4.sh
Script para converter as 4 bandas de jp2 16bits para tif 8bits, e projectar para etrs89, e construir 2 mosaicos: rgb e irg.\
Os mosaicos são TILE_rgb_mask.vrt e TILE_irg_mask.vrt.\
Ou seja, este script é chamado pelo gdal_processa_pasta para cada tile sentinel, e produz para cada TILE: 4 jpeg 8bit, 1 vrt rgb, 1 vrt irg, 1 máscara para cada vrt. Calcula pirâmides e estatísticas para os 2 vrt.
Sintaxe: indicar nome da tile, eg: T29SPB_20190813T112121"\
Têm de existir 4 ficheiros jp2 para converter, eg: b02, b03, b04, b08"\
Cria máscara automaticamente usando o comando nearblack do gdal.

## gdal_stretch2.py
Cria vrt's com constrast stretch, a partir de originais em formato vrt.\
Este stretch serve apenas para facilitar uma melhor visualização, já que as imagens sentinel tendem a ser muito escuras.\
Parameters: pasta com ficheiros a processar (data, eg 20190804)\
Parte do código obtido em: https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
\
Calcula para cada banda o min e max a clipar com a fórmula do desvio padrão: Mean +- 2.8*std\
Usamos 2.8stddev porque se ajusta bem ao sentinel e é simples de calcular.\
Recalcula as stats considerando a mascara, sendo diferente das calculadas pelo gdalinfo.\
Aplica o stretch usando o SCALE do formato VRT, sem alterar as imagens originais.\
E cria 2 vrt rgb+alpha e irg+alpha: TILE_*_viz.vrt

## gdal_criartileindex.py
Processa tileindexes para termos um tileindex time-aware para o mapserver, usando um script de comandos ogr (gdal_tileindexes.sh).\
Mantem 2 tileindex globais - 1 para rgb e outro para irg.\
Também cria 2 tileindexes na pasta dos jp2 (1 para rgb, 1 para irg). Estes são importados para os globais.\
Antes de importar apaga registos que já existam para esta pasta/data para evitar duplicados.\
Ou seja, para cada pasta de data temos 2 vrt (rgb e irg), e um shapefile com a listagem destas imagens.
Depois temos um shapefile global onde estão todas as imagens de todas as datas. Este é usado pelo MapServer.\
Parameters: pasta com ficheiros a processar (data, eg 20190804)

## gdal_tileindexes.sh
Cria tileindexes para os vrt numa data usando o comando gdaltindex do gdal.\
E actualiza tileindexes globais, usando o comando ogrinfo e sql para copiar os registos.\
No fim, exporta o shapefile global para json para criar uma lista de datas que possa ser usada no viewer html.\
Sintaxe: par1=pasta com ficheiros eg 20190803.

## sentinelpt.map
Mapfile que publica todos os vrt RGB e IRG em WMS e com suporte temporal (parametro TIME).
Usa os tileindex criados antes, quer para mostrar a quadrícula das imagens, quer para visualizar as próprias imagens.
Inicialmente tentava aplicar um stretch às imagens, mas esse stretch é agora aplicado pelos scripts de processamento.

# Estrutura em disco
Os scripts assumem uma estrutura em disco onde se colocam os ficheiros.\
dados - pasta mãe com os scripts, e onde ficam os tileindex globais\
&nbsp; &nbsp; &nbsp; &nbsp; |-- 20200501 - pasta criada pelos scripts com ficheiros para o dia 20200501\
&nbsp; &nbsp; &nbsp; &nbsp; |-- aaaammdd - idem
