# Author:  Duarte Carreira
# Date:    Agosto 2019
# Purpose: processa bandas numa pasta sentinel2 em jp2 16 bits para tif 8bits etrs89
#          usando um script de comandos gdal externo (gdal_sentinel2_rgbi_reproj_msk4.sh)
# Parameters: pasta com ficheiros a processar e onde se guardam os resultados

import sys, os, glob, subprocess, platform
from datetime import date, datetime, timedelta
from pathlib import Path, PurePath, PureWindowsPath

#obter pasta a processar
pasta_str = str(sys.argv[1])  #'20190822'

dir_actual = Path('.')
dir_dados = Path('.', pasta_str) #str_data_ini)
print ("Pasta com dados: " + str(dir_dados.absolute()))

#a pasta pode conter vários granulos: T29SPB, T29SPC, etc.
#por isso temos de obter uma lista de cada granulos
#para executar o script um-a-um

#lista dos jp2 (1 por banda, por granulo), eg: T29SPC_20190818T112119_B03_10m.jp2
#file_list = glob.glob(dir_dados / "*.jp2")
file_list = list(dir_dados.glob('*.jp2'))
print ("Ficheiros jp2 encontrados: " + str(len(file_list)))

#se nao houver jp2 tentar processar tifs
if(not file_list ):
  file_list = list(dir_dados.glob('*.tif'))
  print ("Ficheiros tif encontrados: " + str(len(file_list)))


#obter os granulos, eg: T29SPC_20190818T112119
#basta fazer split por "_" e concatenar os 2 primeiros resultados
granulos_list = ["_".join(i.name.split("_", 2)[:2]) for i in file_list]
#remover duplicados
granulos_list = list(dict.fromkeys(granulos_list))

print ("Granulos encontrados: " + str(granulos_list))

#chamar o bat de gdal para cada granulo na pasta...
#filepath = dir_actual + "gdal_sentinel2_rgbi_reproj.bat"
if (platform.system() == 'Windows'):
  filepath = dir_actual / "gdal_sentinel2_rgbi_reproj_msk4.bat"
else:
  filepath = dir_actual / "gdal_sentinel2_rgbi_reproj_msk4.sh"
  
for granulo_id in granulos_list:
  #comando = filepath + " " + granulo_id
  comando = str(filepath.absolute()) + " " + str(dir_dados / granulo_id)
  print ("A processar comando: " + comando)

  comando = comando.split(" ")

  process = subprocess.Popen(comando, universal_newlines=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
  #stdout, stderr = p.communicate()
  for line in process.stdout:
      line = line.rstrip()
      print (line)
  process.stdout.close()
  returnCode = process.wait()
  print (returnCode) # is 0 if success
  if(returnCode>0):
    print ("Erro ao processar com gdal...")
    sys.exit(1)
  print ("Comando executado com sucesso.")

print ("Fim.")
