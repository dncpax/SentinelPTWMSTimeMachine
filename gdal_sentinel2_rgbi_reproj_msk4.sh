#!/bin/bash
echo "converter as 4 bandas de jp2 16bits para tif 8bits, e projectar para etrs89"
echo "e construir 2 mosaicos: rgb e irg"
echo "sintaxe: indicar nome da tile, eg: T29SPB_20190813T112121"
echo "tem de existir 4 ficheiros jp2 para converter, eg: b02, b03, b04, b08"
echo obter a pasta com o ficheiro footprints em geojson, pressupoe argumento de entrada do tipo pasta/granulo
pasta=$(echo ${1} | cut -d'/' -f 1) 
echo pasta com os ficheiros = $pasta
echo obter nome do granulo/prefixo dos ficheiros a processar
prefixo=$(echo ${1} | cut -d'/' -f 2)
#so se executa caso os ficheiros nao existam!
if [ ! -f "${1}_B02_10m.tif" ]; then
echo "criar imagens virtuais de 8 bit porque o gdalwarp não tem a opção scale!"
gdal_translate -scale -ot Byte -of VRT ${1}_B02_10m.jp2 ${1}_B02_10m_8bit_temp.vrt
gdal_translate -scale -ot Byte -of VRT ${1}_B03_10m.jp2 ${1}_B03_10m_8bit_temp.vrt
gdal_translate -scale -ot Byte -of VRT ${1}_B04_10m.jp2 ${1}_B04_10m_8bit_temp.vrt
gdal_translate -scale -ot Byte -of VRT ${1}_B08_10m.jp2 ${1}_B08_10m_8bit_temp.vrt
echo "transformar e reprojectar as imagens em tif 8bit etrs89"
gdalwarp -multi -wo NUM_THREADS=ALL_CPUS -t_srs "EPSG:3763" -r average -wm 640 --config  GDAL_CACHEMAX 512 -co compress=jpeg -co tiled=yes -co jpeg_quality=70 -co INTERLEAVE=PIXEL ${1}_B02_10m_8bit_temp.vrt ${1}_B02_10m.tif
gdalwarp -multi -wo NUM_THREADS=ALL_CPUS -t_srs "EPSG:3763" -r average -wm 640 --config  GDAL_CACHEMAX 512 -co compress=jpeg -co tiled=yes -co jpeg_quality=70 -co INTERLEAVE=PIXEL ${1}_B03_10m_8bit_temp.vrt ${1}_B03_10m.tif
gdalwarp -multi -wo NUM_THREADS=ALL_CPUS -t_srs "EPSG:3763" -r average -wm 640 --config  GDAL_CACHEMAX 512 -co compress=jpeg -co tiled=yes -co jpeg_quality=70 -co INTERLEAVE=PIXEL ${1}_B04_10m_8bit_temp.vrt ${1}_B04_10m.tif
gdalwarp -multi -wo NUM_THREADS=ALL_CPUS -t_srs "EPSG:3763" -r average -wm 640 --config  GDAL_CACHEMAX 512 -co compress=jpeg -co tiled=yes -co jpeg_quality=70 -co INTERLEAVE=PIXEL ${1}_B08_10m_8bit_temp.vrt ${1}_B08_10m.tif
echo "remover vrt's 8bit temporarios"
rm ${1}_*_8bit_temp.vrt
fi
if [ ! -f "${1}_rgb_10m_base.vrt" ]; then
echo "construir o mosaico virtual rgb - nao sei se ainda e util..."
gdalbuildvrt -separate ${1}_rgb_10m_base.vrt ${1}_B04_10m.tif ${1}_B03_10m.tif ${1}_B02_10m.tif
fi
if [ ! -f "${1}_irg_10m_base.vrt" ]; then
echo "construir tb o mosaico irg"
gdalbuildvrt -separate ${1}_irg_10m_base.vrt ${1}_B08_10m.tif ${1}_B04_10m.tif ${1}_B03_10m.tif
fi
if [ ! -f "${1}_mask.tif" ]; then
echo "criar mascara a partir do nearblack do mosaico base"
nearblack --config GDAL_CACHEMAX 2048 -near 1 -setmask -o ${1}_mask.tif -co compress=deflate -co nbits=1 -co interleave=band -co tiled=yes ${1}_rgb_10m_base.vrt
fi
if [ ! -f "${1}_rgb_mask.vrt" ]; then
echo "criar novo _mask.vtr com msk copiada da mascara.tif.msk"
cp ${1}_rgb_10m_base.vrt ${1}_rgb_mask.vrt
cp ${1}_mask.tif.msk ${1}_rgb_mask.vrt.msk
fi
if [ ! -f "${1}_irg_mask.vrt" ]; then
echo "idem para irg"
cp ${1}_irg_10m_base.vrt ${1}_irg_mask.vrt
cp ${1}_mask.tif.msk ${1}_irg_mask.vrt.msk
fi
if [ ! -f "${1}_rgb_mask.vrt.ovr" ]; then
echo criar piramides para este vrt, que pode ser ja usado para visualizacao
gdaladdo -ro -r average --config COMPRESS_OVERVIEW JPEG --config PHOTOMETRIC_OVERVIEW YCBCR --config JPEG_QUALITY_OVERVIEW 85 ${1}_rgb_mask.vrt 2 4 8 16 32 64
fi
if [ ! -f "${1}_irg_mask.vrt.ovr" ]; then
echo idem irg
gdaladdo -ro -r average --config COMPRESS_OVERVIEW JPEG --config PHOTOMETRIC_OVERVIEW YCBCR --config JPEG_QUALITY_OVERVIEW 85 ${1}_irg_mask.vrt 2 4 8 16 32 64
fi
echo "calcular estatisticas do mosaico rgb mascarado"
gdalinfo -stats ${1}_rgb_mask.vrt
echo "calcular estatisticas do mosaico irg mascarado"
gdalinfo -stats ${1}_irg_mask.vrt
if [ ! -f "${1}_rgb_10m.vrt" ]; then
echo criar ficheiros para serem usados pelos scripts seguintes
#cd $pasta
mv "${1}_rgb_mask.vrt" "${1}_rgb_10m.vrt"
mv "${1}_rgb_mask.vrt.ovr" "${1}_rgb_10m.vrt.ovr"
mv "${1}_rgb_mask.vrt.msk" "${1}_rgb_10m.vrt.msk"
mv "${1}_rgb_mask.vrt.msk.ovr" "${1}_rgb_10m.vrt.msk.ovr"
fi
if [ ! -f "${1}_irg_10m.vrt" ]; then
echo "idem para irg"
mv "${1}_irg_mask.vrt" "${1}_irg_10m.vrt"
mv "${1}_irg_mask.vrt.ovr" "${1}_irg_10m.vrt.ovr"
mv "${1}_irg_mask.vrt.msk" "${1}_irg_10m.vrt.msk"
mv "${1}_irg_mask.vrt.msk.ovr" "${1}_irg_10m.vrt.msk.ovr"
fi
echo "mosaicos vrt prontos a usar no qgis"
echo "proximo script ira definir a simbologia com stretch para max/min, corte desvio padrão 2,90%"
