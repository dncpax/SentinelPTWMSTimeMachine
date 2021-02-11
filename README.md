# SentinelPTWMSTimeMachine
Criador de mosaicos de imagens Sentinel-2 RGB e IRG para Portugal, com serviço WMS, com suporte temporal



##sentinelsat_band_parallel.py

Pesquisa arquivo Sentinel 2, por tiles específicas, para um dia específico, e faz download apenas das bandas 2, 3, 4, e 8 .
E faz o download banda-a-banda.
Versão que abre 2 sessoes em paralelo, que é o máximo de conexoes permitido pelo sci-hub.
Parameters: data no formato yyyymmdd - pesquisa 5 dias anteriores.
 Notes: codigo inicial obtido em: https://gis.stackexchange.com/questions/233670/sentinel2-get-jpeg200-bands-only
        utiliza sentinelsat: https://github.com/sentinelsat/sentinelsat
        só procede com o download se todas as tiles forem encontradas nesse dia
 Example: tiles=29SNB, 29SNC, 29SPB, 29SPC (para o alqueva)

É preciso substituir "user" e "pass" pelo login no scihub.
