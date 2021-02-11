#!/bin/bash
echo "cria tileindexes para os vrt numa data"
echo "e actualizar tileindexes globais"
echo "Sintaxe: par1=pasta com ficheiros eg 20190803"
# criar um index rgb na pasta para os vrt de rgb: 20190803\tileindex_209108083_rgb.shp
# a partir dos *_rgb_10m.vrt
echo gdaltindex -write_absolute_path ${1}/tileindex_${1}_rgb.shp ${1}/*_rgb_10m.vrt
gdaltindex -write_absolute_path ${1}/tileindex_${1}_rgb.shp ${1}/*_rgb_10m.vrt
# criar um index irg na pasta para os vrt de rgb: 20190803\tileindex_209108083_irg.shp
# a partir dos *_irg_*.vrt
echo gdaltindex -write_absolute_path tileindex_${1}_irg.shp *_irg_10m.vrt
gdaltindex -write_absolute_path ${1}/tileindex_${1}_irg.shp ${1}/*_irg_10m.vrt
echo "processar o tileindex global que contem todos os vrts disponíveis e indica a data de cada um"
echo "há 2 tileindex, 1 para rgb e 1 para irg"
echo "Adicionar tiles ao indice global de tiles tileindex_global_rgb.shp"
# 1-limpar registos que possam já existir
echo "apagar registos existentes"
echo ogrinfo -dialect SQLITE tileindex_global_rgb.shp -sql "DELETE FROM tileindex_global_rgb where location like '%_${1}%_rgb_10m.vrt'"
ogrinfo -dialect SQLITE tileindex_global_rgb.shp -sql "DELETE FROM tileindex_global_rgb where location like '%_${1}%_rgb_10m.vrt'"
# 2-copiar registos e calcular a data dos registos
# é preciso inserir - entre as componentes da data (20190803 -> 2019-08-03)
echo "adicionar registos dos rgb ao tileindex global"
echo ogr2ogr -dialect SQLITE -f "ESRI Shapefile" -update -append tileindex_global_rgb.shp ${1}/tileindex_${1}_rgb.shp -nln tileindex_global_rgb -sql "SELECT *, date(substr('${1}',1,4)||'-'||substr('${1}',5,2)||'-'||substr('${1}',7)) as time from tileindex_${1}_rgb"
ogr2ogr -dialect SQLITE -f "ESRI Shapefile" -update -append tileindex_global_rgb.shp ${1}/tileindex_${1}_rgb.shp -nln tileindex_global_rgb -sql "SELECT geometry, location, REPLACE(location, '_10m.vrt', '_10m_viz.vrt') as localviz, date(substr('${1}',1,4)||'-'||substr('${1}',5,2)||'-'||substr('${1}',7)) as time, substr(location,instr(location, '_')+1,8) as dataimg from tileindex_${1}_rgb"
echo "Repetir para o IRG..."
# 1-limpar registos que possam já existir
echo "apagar registos existentes"
echo ogrinfo -dialect SQLITE tileindex_global_irg.shp -sql "DELETE FROM tileindex_global_irg where location like '%_${1}%_irg_10m.vrt'"
ogrinfo -dialect SQLITE tileindex_global_irg.shp -sql "DELETE FROM tileindex_global_irg where location like '%_${1}%_irg_10m.vrt'"
# 2-copiar registos e calcular a data dos registos
# é preciso inserir - entre as componentes da data (20190803 -> 2019-08-03)
echo "adicionar registos dos irg ao tileindex global"
echo ogr2ogr -dialect SQLITE -f "ESRI Shapefile" -update -append tileindex_global_irg.shp ${1}/tileindex_${1}_irg.shp -nln tileindex_global_irg -sql "SELECT *, date(substr('${1}',1,4)||'-'||substr('${1}',5,2)||'-'||substr('${1}',7)) as time from tileindex_${1}_irg"
ogr2ogr -dialect SQLITE -f "ESRI Shapefile" -update -append tileindex_global_irg.shp ${1}/tileindex_${1}_irg.shp -nln tileindex_global_irg -sql "SELECT geometry, location, REPLACE(location, '_irg_10m.vrt', '_irg_10m_viz.vrt') as localviz, date(substr('${1}',1,4)||'-'||substr('${1}',5,2)||'-'||substr('${1}',7)) as time, substr(location,instr(location, '_')+1,8) as dataimg from tileindex_${1}_irg"
echo "Actualizar ficheiro com lista de datas disponiveis"
rm tileindex_datas.json
#ogrinfo -dialect SQLITE tileindex_datas.json -sql "DELETE FROM sentinelpt_datas"
ogr2ogr -dialect SQLITE -sql "SELECT distinct(time) from tileindex_global_rgb ORDER BY time" -nln sentinelpt_datas tileindex_datas.json tileindex_global_rgb.shp
echo "Fim."
