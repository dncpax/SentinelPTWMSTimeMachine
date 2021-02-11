# -*- coding: utf-8 -*-
# Author:  EDIA, S.A.
# Date:    Agosto 2019
# Purpose: Cria vrt's com constrast stretch, a partir de originais também vrt's
#          para facilitar uma melhor visualização
# Parameters: pasta com ficheiros a processar (data, eg 20190804)
# Parte do código obtido em: https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
from osgeo import gdal, gdalconst
from osgeo.gdalconst import *
import sys, os, glob, subprocess
from datetime import date, datetime, timedelta
from pathlib import Path, PurePath, PureWindowsPath
gdal.UseExceptions()
#obter data a processar
data_str = str(sys.argv[1])  #'20190822'
dir_actual = Path('.')
dir_dados = Path('.', data_str) #str_data_ini)
print ("Pasta com dados: " + str(dir_dados.absolute()))
#lista dos vrt rgb e irg, eg: T29SPC_20190813T112121_rgb_10m.vrt
#file_list = glob.glob(dir_dados / "*.jp2")
file_list = list(dir_dados.glob('*_10m.vrt'))
#file_list = list(dir_dados.glob('T29SPB_20200112T111329_rgb_10m.vrt'))
print ("Ficheiros vrt encontrados: " + str(len(file_list)))
for input_file in file_list:
    print("A ler: %s" % input_file)
    output_file = Path(input_file.parent, input_file.stem + "_viz.vrt") #input_file.replace("_10m.vrt","_10m_viz.vrt")
    
    src_ds = gdal.Open( str(input_file) )
    if src_ds is None:
        print ('Unable to open %s' % input_file)
        sys.exit(1)
    
    stats_col = []
    scales = []
    scales_str = ""
    #calcular para cada banda o min e max a clipar
    #aplicar stretch de std dev: Mean +- 2.8*std
    #usamos 2.8stddev porque se ajusta bem ao sentinel e é simples de calcular
    for band_num in range( src_ds.RasterCount ):
        band_num += 1
        print ("[ GETTING BAND ]: ", band_num)
        try:
            srcband = src_ds.GetRasterBand(band_num)
        except RuntimeError as e:
            print ('No band %i found' % band_num)
            print (e)
            sys.exit(1)
            
        stats = srcband.GetStatistics( True, True )
        if stats is None:
            print ('Não existem estatísticas para a banda %s' % band_num)
            sys.exit(1)
        print ("[ NO DATA VALUE ] = ", srcband.GetNoDataValue())
        print ("[ STATS ] =  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                stats[0], stats[1], stats[2], stats[3] ))
        #print "[ MIN ] = ", srcband.GetMinimum()
        #print "[ MAX ] = ", srcband.GetMaximum()
        #print "[ SCALE ] = ", srcband.GetScale()
        #print "[ UNIT TYPE ] = ", srcband.GetUnitType()
        stats_col.append(stats)
        #calcular para cada banda o min e max a clipar
        #calcular stats considerando a mascara!
        data = srcband.ReadAsArray()
        mask = srcband.GetMaskBand().ReadAsArray()
        masked_data = data[mask>0]
        min = masked_data.min()
        max = masked_data.max()
        media = masked_data.mean()
        stddev = masked_data.std()
        print ("[ STATS MASK ] =  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                min, max, media, stddev ))
        min_scale = media - 2.8* stddev  #usamos 2.8stddev porque se ajusta bem ao sentinel e é simples de calcular
        max_scale = media + 2.8* stddev
        print ("Escalas Banda %s: %s" % (band_num, [min_scale,max_scale, 0,255]))
        scales.append( [min_scale,max_scale, 0,255] )
        scales_str = scales_str + " -scale_{} {} {} 0 255".format(band_num, min_scale, max_scale)
        
    srd_ds = None
    #aplicar stretch de std dev: Mean +- 2*std
    #usando o scale do gdal_translate
    print("A criar vrt com stretch e banda alfa: %s" % output_file)
    #trans_options = gdal.TranslateOptions(format="VRT", scaleParams=scales)
    #criar um vrt com banda alfa pq o mapserver nao trabalha bem com mascaras no tileindex!
    trans_options = gdal.TranslateOptions(gdal.ParseCommandLine("-of VRT -b 1 -b 2 -b 3 -b mask -colorinterp red,green,blue,alpha " + scales_str))
    gdal.Translate(str(output_file), str(input_file), options=trans_options)
    
    viz_ds = gdal.Open( str(output_file), GA_Update )
    alfaband = viz_ds.GetRasterBand(4)
    alfaband.SetRasterColorInterpretation( GCI_AlphaBand )
    viz_ds = None
