# Author:  Duarte Carreira
# Date:    Agosto 2019
# Purpose: Pesquisa arquivo Sentinel 2, por tiles específicas, para um dia específico, e faz download apenas
#           das bandas 2, 3, 4, e 8 
#          É útil porque faz apenas a pesquisa e não processa nada... é cópia do código de pesquisa usado no sentinelsat_band_parallel.py.
# Parameters: data no formato yyyymmdd - pesquisa 5 dias anteriores
# Notes: codigo inicial obtido em: https://gis.stackexchange.com/questions/233670/sentinel2-get-jpeg200-bands-only
#        utiliza sentinelsat: https://github.com/sentinelsat/sentinelsat
#        só procede com o download se todas as tiles forem encontradas nesse dia
# Example: tiles=29SNB, 29SNC, 29SPB, 29SPC (para o alqueva)


from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import requests, shutil, sys, os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import date, datetime, timedelta
from collections import OrderedDict
from six.moves.urllib.parse import urljoin
from osgeo import ogr
from osgeo import osr

#obter bytes a partir de uma string humana de kb, mb, gb
#obtida em: https://stackoverflow.com/questions/42865724/python-parse-human-readable-filesizes-into-bytes
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
#tiles_str = 'T29SMD|T29SMC|T29SNC|T29SNB|T29TNE|T29TPG|T29TPE|T29TNG|T29SPC|T29SPB|T29SPD|T29SND|T29TPF|T29TNF|T29TQG|T29TQF'
try:
    tiles_str = str(sys.argv[3])
except:
    print("Tiles nao foram indicadas. Pesquisando Portugal...")
    tiles_str = 'T29SMD|T29SMC|T29SNC|T29SNB|T29TNE|T29TPG|T29TPE|T29TNG|T29SPC|T29SPB|T29SPD|T29SND|T29TPF|T29TNF|T29TQG|T29TQF'


#obter data do comando
data_str = str(sys.argv[1])  #'20190822'

# connect to the API
api = SentinelAPI('user', 'pass', 'https://scihub.copernicus.eu/dhus')

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
    sys.exit(0)

print ("Produtos encontrados: " + str(len(products)))
#ordenar os resultados por cobertura de nuvens
#produtos.sort(key=lambda x: x.cloudcoverpercentage, reverse=True)
#teste = sorted(products, key=lambda x: x.cloudcoverpercentage, reverse=True)
teste = OrderedDict(sorted(products.items(), key=lambda kv: kv[1]["cloudcoverpercentage"]))
products = teste

for prod in products:
    print("Ficheiro: %s, size: %s, clouds: %s" % (products[prod]["filename"],products[prod]["size"],products[prod]["cloudcoverpercentage"]))

#só prosseguimos se existirem todas as tiles!
if(len(products)<len(tiles_str.split("|"))):
    print("Não foram encontradas todas as tiles! Apenas " + str(len(products)) + " de " + str(len(tiles_str.split("|"))))
    sys.exit(0)

#remover produtos "incompletos" ie com imagens muito incompletas
#a forma rude e rapida é verificar o tamanho: 1,08GB é completa, abaixo incompleta
#a forma inteligente será analisar a área não nula pelo overview!
prods_a_apagar = []
strLimite = "840 MB"
intLimite = parseSize(strLimite)
print ("A remover ficheiros menores que %s." % strLimite)
for prod_id in products:
    #print("%s = %s" % (products[prod_id]["filename"], products[prod_id]["size"]))
    #removemos tudo abaixo dos 850MB
    if(parseSize(products[prod_id]["size"]) < intLimite):
        #excepcao da T29SMC e T29SMD porque passa meses abaixo do limite!
        if(
           "T29SMC_" in products[prod_id]["filename"]
           or "T29SMD_" in products[prod_id]["filename"]):
            continue
        prods_a_apagar.append(prod_id)

print ("Produtos incompletos a remover: %s" % len(prods_a_apagar))

#apagar produtos repetidos
if(len(prods_a_apagar)>0):
    for prod_id in prods_a_apagar:
        del products[prod_id]
#só prosseguimos se existirem todas as tiles!
if(len(products)<len(tiles_str.split("|"))):
    print("Não foram encontradas todas as tiles! Apenas " + str(len(products)) + " de " + str(len(tiles_str.split("|"))))
    sys.exit(0)

#agora verificar que temos tiles pretendidas e remover repetidas!
print ("Verificar se todas as tiles foram encontradas, e remover duplicados")
tiles_a_encontrar = tiles_str.split("|")

products = produtos_remove_dups(products, tiles_a_encontrar)
print ("Produtos a obter: %s" % len(products))
if (len(products)!=len(tiles_a_encontrar)):
    print("Tiles insuficientes depois de removidos os duplicados!")
    sys.exit(0)

for prod_id in products:
    print("%s = %s" % (products[prod_id]["filename"], products[prod_id]["size"]))
    print("%s bytes" %  parseSize(products[prod_id]["size"]))
    print("%s%% nuvens" % (products[prod_id]["cloudcoverpercentage"]))
    wkt = products[prod_id]["footprint"] #"POLYGON ((1162440.5712740074 672081.4332727483, 1162440.5712740074 647105.5431482664, 1195279.2416228633 647105.5431482664, 1195279.2416228633 672081.4332727483, 1162440.5712740074 672081.4332727483))"
    poly = ogr.CreateGeometryFromWkt(wkt)
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    target = osr.SpatialReference()
    target.ImportFromEPSG(3763)
    transform = osr.CoordinateTransformation(source, target)
    #a area normal é de 12283267042,560 m2
    poly.Transform(transform)
    print ("Area coberta = %d" % (poly.GetArea()/12283267042 *100))


print ("Fim.")
