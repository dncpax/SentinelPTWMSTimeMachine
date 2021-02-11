# SentinelPTWMSTimeMachine
Criador de mosaicos de imagens Sentinel-2 RGB e IRG para Portugal, com serviço WMS, com suporte temporal

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
Notes: codigo inicial obtido em: https://gis.stackexchange.com/questions/233670/sentinel2-get-jpeg200-bands-only\
        utiliza sentinelsat: https://github.com/sentinelsat/sentinelsat\
        só procede com o download se todas as tiles forem encontradas nesse dia\
 
Example: tiles=29SNB, 29SNC, 29SPB, 29SPC (para o alqueva)\

É preciso substituir "user" e "pass" pelo login no scihub.
