# Author:  Duarte Carreira
# Date:    Agosto 2019
# Purpose: processa tileindexes para termos um tileindex time-aware para o mapserver
#          usando um script de comandos ogr (gdal_tileindexes.sh)
#          mantem 2 tileindex globais - 1 para rgb e outro para irg
#          também cria 2 tileindexes na pasta dos jp2 (1 para rgb, 1 para irg)
#          depois importa para os globais
#          antes de importar apaga registos que já existam para esta pasta/data
# Parameters: pasta com ficheiros a processar (data, eg 20190804)
import sys, os, glob, subprocess, platform
from datetime import date, datetime, timedelta
from pathlib import Path, PurePath, PureWindowsPath
#obter data a processar
data_str = str(sys.argv[1])  #'20190822'
#derivar a pasta a partir da data
str_data_fim = data_str # '20190822'
data = datetime.strptime(str_data_fim, "%Y%m%d")
#é preciso somar 24h para incluir o próprio dia, de outra forma
#pesquisamos só até ao proprio dia  0h00
data_fim = data + timedelta(days=1)
data_ini = data - timedelta(days=1)
str_data_ini = datetime.strftime(data_ini, "%Y%m%d")
str_data_fim = datetime.strftime(data_fim, "%Y%m%d")
#dir_actual = os.getcwd() + "/"
#dir_dados = dir_actual + str_data_ini + "/"
dir_actual = Path('.')
dir_dados = Path('.', data_str) #str_data_ini)
print ("Pasta com dados: " + str(dir_dados.absolute()))
#actualizar o shapefile do time index
#construir o tileindex rgb desta pasta para cada vrt rgb
#e construir outro para cada vrt irg
#depois, adicionar ao tileindex master e actualizar o campo data!
#chamar o bat ou o sh de gdal
if (platform.system() == 'Windows'):
  filepath = dir_actual / "gdal_tileindexes.bat"
else:
  filepath = dir_actual / "gdal_tileindexes.sh"
#comando gdaltindex
comando = str(filepath.absolute()) + " " + data_str #str_data_ini
print ("Comando: %s" % (comando))
#em linux temos de splitar o comando
#comando = comando.split(" ")
process = subprocess.Popen(comando, universal_newlines=True,
                           shell=True, 
                           stdout = subprocess.PIPE, 
                           stderr = subprocess.STDOUT) 
#                           cwd = str(dir_dados))
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
