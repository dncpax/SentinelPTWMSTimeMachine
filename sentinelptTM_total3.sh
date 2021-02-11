#!/bin/bash
set -e
echo "Processamento global, com download e processamento"
echo "Indicar data para pesquisa (eg 20190101)."
echo "Termina na existencia de erros."
python3 sentinelsat_band_parallel.py ${1} ${2} ${3}
python3 gdal_processa_pasta3.py ${1}
python3 gdal_stretch2.py ${1}
python3 gdal_criartileindex.py ${1}
echo "Fim." 
