# Author:  Duarte Carreira
# Date:    Agosto 2019
# Purpose: Pesquisa arquivo Sentinel 2, por tiles específicas, para um dia específico, e faz download apenas
#           das bandas 2, 3, 4, e 8 
#           E faz o download banda-a-banda
#          PARALELL: versao que abre 2 sessoes em paralelo, que é o máximo
#          de conexoes permitido pelo sci-hub
# Parameters: data no formato yyyymmdd - pesquisa 5 dias anteriores
#             cloudcov_int =  70 cobertura de nuvens aceitavel (opcional)
#             tiles_str = 'T29SMC|T29SMD|T29SND|T29SPD|T29TNE|T29TNF|T29TNG|T29TPE|T29TPF|T29TPG|T29TQF|T29TQG' #'T29SMC|T29SMD|T29SNB|T29SNC|T29SND|T29SPB|T29SPC|T29SPD|T29TNE|T29TNF|T29TNG|T29TPE|T29TPF|T29TPG|T29TQF|T29TQG'
#                          ou usamos as tiles indicadas no comando ou pesquisamos as tiles de portugal
# Notes: codigo inicial obtido em: https://gis.stackexchange.com/questions/233670/sentinel2-get-jpeg200-bands-only
#        utiliza sentinelsat: https://github.com/sentinelsat/sentinelsat
#        só procede com o download se todas as tiles forem encontradas nesse dia
# Example: tiles=29SNB, 29SNC, 29SPB, 29SPC (para o alqueva)
# É preciso definir o login no scihub com as vars de ambiente API_USER e API_PWD.


from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import requests, shutil, sys, os, json
from collections import OrderedDict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import date, datetime, timedelta
from six.moves.urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

#obter bytes a partir de uma string humana de kb, mb, gb
#obtida em: https://stackoverflow.com/questions/42865724/python-parse-human-rea$
def parseSize(size):
    units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}
    number, unit = [string.strip() for string in size.split()]
    return int(float(number)*units[unit])

#código de conexão obtido em: https://www.peterbe.com/plog/best-practice-with-retries-with-requests
#necessário porque há erros esporádicos 504
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

#funcao que remove produtos que referem a mesma tile
def produtos_remove_dups(produtos,tiles):
    tiles_encontradas = []
    produtos_a_apagar = []
    for prod in produtos:
        # product UUID you want to download a single band for
        #prod_id = "22e2fbfe-0aa7-423d-b0b5-df46527f03f5"
        prod_id = prod #list(products.keys())[0]
#        print ("A obter dados do produto: "+ prod_id)

        #filename = productname
        prod_desc = produtos[prod_id]

        #print (prod_desc)
        prod_name = prod_desc["filename"]
        #filename: S2B_MSIL2A_20190709T112119_N0213_R037_T29SPC_20190709T140254$
        #nos queremos ver  T29SPC
        print ("Ficheiro: " + prod_name)
        #str_tile = prod_name.split("_")[6]
        for tile in tiles_a_encontrar:
            #se este filename corresponde a uma tile
            if ("_" + tile + "_" in prod_name):
                #se este filename repetir uma tile, remover dos produtos antes $
                if (tile in tiles_encontradas):
                    produtos_a_apagar.append(prod_id)
                    break #passar ao proximo produto
                else:  #este produto corresponde a uma tile e nao repete
                    tiles_encontradas.append(tile)
    print ("Tiles nao repetidas encontradas: %s" % len( tiles_encontradas))
    print ( tiles_encontradas )
    print ("Produtos que repetem tiles: %s" % len(produtos_a_apagar))
    print (produtos_a_apagar)

    #apagar produtos repetidos
    for prod_id in produtos_a_apagar:
        del produtos[prod_id]
    return produtos

#efectua o download de 1 produto
def download_prods_bands(prod):
    # product UUID you want to download a single band for
    #prod_id = "22e2fbfe-0aa7-423d-b0b5-df46527f03f5"
    prod_id = prod #list(products.keys())[0]
    print ("A obter dados do produto: "+ prod_id)

    #filename = productname
    prod_desc = products[prod_id]

    #print (prod_desc)
    prod_name = prod_desc["filename"]
    print ("Ficheiro: " + prod_name)

    # parse the product name
    #nodes = api_session.get(urljoin(api_url, "Products('%s')/Nodes?$format=json" % prod_id)).json()
    #prod_name = nodes["d"]["results"][0]["Id"]

    # parse the granule id
    granules_url = urljoin(api_url, "Products('%s')/Nodes('%s')/Nodes('GRANULE')/Nodes?$format=json" % (prod_id, prod_name))
    print ("A obter dados do granulo: " + granules_url)
    granules_response = requests_retry_session(session=api_session).get(granules_url)
    print ("Estado resposta: " + str(granules_response.status_code))
    granules = granules_response.json()
    #print ("granulesjson: " + str(granules))
    granules["d"]["results"][0].keys()
    gran_id = granules["d"]["results"][0]["Id"]
    print ("granule_id: " + gran_id)
    # parse the band names
    #corrigido para incluir nó em falta /Nodes('R10m')/
    bands_url = urljoin(api_url, "Products('%s')/Nodes('%s')/Nodes('GRANULE')/Nodes('%s')/Nodes('IMG_DATA')/Nodes('R10m')/Nodes?$format=json" % (prod_id, prod_name, gran_id))
    print ("A obter dados bandas: " + bands_url)
    bands_response = requests_retry_session(session=api_session).get(bands_url)
    #deviamos checar se houve erro na resposta... temos erro 504 por vezes - bad gateway!
    print ("Estado resposta: " + str(bands_response.status_code))
    bands = bands_response.json()
    #print ("bands: " + str(bands))
    #print ("banda3: " + str(bands["d"]["results"][3]))
    #Id is the same as name and .jp2 filename
    #ciclo para obter as bandas 2,3,4, e 8
    # element [0] is AOT, [1] = band 2, [2] = band 3, [3] = band 4, [4] = band 8
    bands_idx = {1,2,3,4}

    for band_idx in bands_idx:
        band_id = bands["d"]["results"][band_idx]["Id"] 
        print ("band_id ou filename: " + band_id)
        band_contentlength = int(bands["d"]["results"][band_idx]["ContentLength"])
        #metadata media_src is the url to get the band file downloaded, instead of building the url by hand
        #print ("band1 metadata: " + str(bands["d"]["results"][1]['__metadata']))
        band_url = bands["d"]["results"][band_idx]['__metadata']["media_src"]
        print ("Url da banda a descarregar: " + band_url)
        #download to file
        #api_session.get(band_url)
        print("a descarregar ficheiro: " + band_id)
        local_filename = dir_dados + "/" + band_id
        #with api_session.get(band_url, stream=True) as r:
        #    with open(local_filename, 'wb') as f:
        #        shutil.copyfileobj(r.raw, f)
        #só descarregar se não existir o ficheiro!
        if not (os.path.isfile(local_filename)):
            api._download(band_url, local_filename, api_session, band_contentlength)
            print ( "Descarregado: %s" % band_id)
        else:
            print ( "Já existente (não descarregado): %s" % band_id)

    return "Processado %s." % prod_name

#definir cobertura de nuvens aceitavel
try:
    cloudcov_int = int(sys.argv[2])
except:
    print("Cloud Coverage nao foi indicada. Usando default de 70...")
    cloudcov_int = 70

#definir os tiles a obter
#alqueva
#tiles_str = 'T29SNB|T29SNC|T29SPB|T29SPC' #'T29SNB|T29SNC|T29SPB|T29SPC'
#portugal
#tiles_str = 'T29SMC|T29SMD|T29SND|T29SPD|T29TNE|T29TNF|T29TNG|T29TPE|T29TPF|T29TPG|T29TQF|T29TQG' #'T29SMC|T29SMD|T29SNB|T29SNC|T29SND|T29SPB|T29SPC|T29SPD|T29TNE|T29TNF|T29TNG|T29TPE|T29TPF|T29TPG|T29TQF|T29TQG'
#ou usamos as tiles indicadas no comando ou pesquisamos as tiles de portugal
try:
    tiles_str = str(sys.argv[3])
    print ("A pesquisar as tiles indicadas no comando... %s" % tiles_str)
except:
    print ("Tiles não foram indicadas. Pesquisando Portugal...")
    tiles_str = 'T29SMC|T29SMD|T29SNB|T29SNC|T29SND|T29SPB|T29SPC|T29SPD|T29TNE|T29TNF|T29TNG|T29TPE|T29TPF|T29TPG|T29TQF|T29TQG'

#obter data do comando
data_str = str(sys.argv[1])  #'20190822'

# connect to the API
api = SentinelAPI(os.environ['API_USER'], os.environ['API_PWD'], 'https://scihub.copernicus.eu/dhus')

#pesquisar quads prédefinidas
#query devolve os dados de todos os itens na pesquisa, mas não todos os dados

#obter data ini e data final para pesquisa: '20190822' e '20190823'
str_data_fim = data_str # '20190822'
data = datetime.strptime(str_data_fim, "%Y%m%d")
#é preciso somar 24h para incluir o próprio dia, de outra forma
#pesquisamos só até ao propio dia  0h00
data_fim = data + timedelta(days=1)
data_ini = data - timedelta(days=5)
str_data_ini = datetime.strftime(data_ini, "%Y%m%d")
str_data_fim = datetime.strftime(data_fim, "%Y%m%d")

#qual a pesquisa afinal?
print ("Tiles a pesquisar: " + tiles_str)
print ("Data a pesquisar: de " + str_data_ini + " a " + str_data_fim)
print("Query de pesquisa: " + api.format_query( date = (str_data_ini, str_data_fim), platformname = 'Sentinel-2', cloudcoverpercentage = (0, cloudcov_int), producttype = 'S2MSI2A', filename = '/.+('+ tiles_str +').+/') )

products = api.query(
                     date = (str_data_ini, str_data_fim),
                     platformname = 'Sentinel-2',
                     cloudcoverpercentage = (0, cloudcov_int),
                     producttype = 'S2MSI2A',
                     filename = '/.+('+ tiles_str +').+/')

if(len(products))<1:
    print("Sem resultados.")
    sys.exit(1)

print ("Produtos encontrados: " + str(len(products)))
#ordenar os resultados por cobertura de nuvens e por tamanho
#aqui é definida a "inteligencia" da pesquisa
#ao remover duplicados, vamos remover os dups com mais nuvens e com menor size.
#por sorte e força bruta acabamos com um mosaico com pouquissimas falhas
#obviamente, deve ser subsituido por um metodo inteligente! que assegure 0 falhas.
teste = sorted(products.items(), key=lambda kv: kv[1]["cloudcoverpercentage"])
products = OrderedDict(sorted(products.items(), key=lambda kv: parseSize(kv[1]["size"]), reverse=True))

for prod in products:
    print("Ficheiro: " + products[prod]["filename"])

#só prosseguimos se existirem todas as tiles!
if(len(products)<len(tiles_str.split("|"))):
    print("Não foram encontradas todas as tiles! Apenas " + str(len(products)) + " de " + str(len(tiles_str.split("|"))))
    sys.exit(1)

#remover produtos "incompletos" ie com imagens muito incompletas
#a forma rude e rapida é verificar o tamanho: 1,08GB é completa, abaixo incompl$
#a forma inteligente será analisar a área não nula pelo overview!
#dada a ordenação acima, ja nao vamos remover ficheiros abaixo de 1 limite!
prods_a_apagar = []
strLimite = "840 MB"
#strLimite = "100 MB"
intLimite = parseSize(strLimite)
print ("A remover ficheiros menores que %s." % strLimite)
for prod_id in products:
    #print("%s = %s" % (products[prod_id]["filename"], products[prod_id]["size"$
    #removemos tudo abaixo dos 850MB
    if(parseSize(products[prod_id]["size"]) < intLimite):
        #excepcao da T29SMC e T29SMD porque passa meses abaixo do limite!
        if(
           "T29SMC_" in products[prod_id]["filename"]
           or "T29SMD_" in products[prod_id]["filename"]):
            continue
        prods_a_apagar.append(prod_id)
print ("Produtos incompletos a remover: %s" % len(prods_a_apagar))
#apagar produtos incompletos
if(len(prods_a_apagar)>0):
    for prod_id in prods_a_apagar:
        del products[prod_id]
#só prosseguimos se existirem todas as tiles!
if(len(products)<len(tiles_str.split("|"))):
    print("Não foram encontradas todas as tiles! Apenas " + str(len(products)) + " de " + str(len(tiles_str.split("|"))))
    sys.exit(1)

#agora verificar que temos tiles pretendidas e remover repetidas!
print ("Verificar se todas as tiles foram encontradas, e remover duplicados")
tiles_a_encontrar = tiles_str.split("|")
products = produtos_remove_dups(products, tiles_a_encontrar)
print ("Produtos a obter: %s" % len(products))
if (len(products)<len(tiles_a_encontrar)):
    print("Tiles insuficientes depois de removidos os duplicados!")
    sys.exit(1)

#mostrar os resultados antes do download, para referencia
#mostramos id porque é útil para obter online
#e tb filename pq tem data e outros dados, e size
print("Lista final de downloads a fazer:")
print("ProductId            Filename            Size")
for prod_id in products:
    print("%s %s %s" % (prod_id,products[prod_id]["filename"],products[prod_id]["size"]))


dir_actual = path = os.getcwd()
dir_dados = dir_actual + "/" + data_str #str_data_ini
print ("A criar pasta: " + dir_dados)
try:
    os.mkdir(dir_dados)
except OSError:
    print ("Falha ao criar directoria %s." % dir_dados)
    #sys.exit(0)

#criar ficheiro de footprints.geojson para usar na mascara de transparencias
oGeoJSON = api.to_geojson(products)
with open(dir_dados + '/search_footprints.geojson', 'w') as outfile:
    json.dump(oGeoJSON, outfile)

# connect to the api
api_session = api.session
api_url = "https://scihub.copernicus.eu/apihub/odata/v1/"

#obter os quicklooks
api.download_all_quicklooks(products)

#chamar o download de produtos usando 2 threads!
pool = ThreadPoolExecutor(max_workers=2)
for download in pool.map(download_prods_bands, products):
    print(download)

print ("Fim.")
