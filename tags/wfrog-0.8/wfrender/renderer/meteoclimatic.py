# -*- coding: latin-1 -*-

## Copyright 2010 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##
##  This file is part of wfrog
##
##  wfrog is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math
import logging
import sys
import time
import wfcommon.database
from wfcommon.formula.base import LastFormula
from wfcommon.formula.base import SumFormula
from wfcommon.formula.base import MinFormula
from wfcommon.formula.base import MaxFormula
try:
    from wfrender.datasource.accumulator import AccumulatorDatasource
except ImportError, e:
    from datasource.accumulator import AccumulatorDatasource
from wfcommon.units import MpsToKmh

class MeteoclimaticRenderer(object):
    """
    Renders the data chunk to send to the meteoclimatic website using local time.
    See www.meteoclimatic.com.

    Meteoclimatic has not disclosed its direct upload protocol. 
    Therefore it is necessary to upload (FTP) or publish (HTTP) the data.

    render result [string]:
        The generated chunk.

    [ Properties ]

    id [string]:
        meteoclimatic station ID.

    storage: 
        The storage service.
    """

    id = None
    storage = None
    accuY = None
    accuM = None
    accuD = None
    lastTemplate = None
    
    logger = logging.getLogger("renderer.meteoclimatic")

    def render(self, data={}, context={}):
        try:
            assert self.id is not None, "'meteoclimatic.id' must be set"
            assert self.storage is not None, "'meteoclimatic.storage' must be set"

            if self.accuD == None:
                self.logger.info("Initializing accumulators")

                # Accumulator for yearly data
                self.accuY = AccumulatorDatasource()
                self.accuY.slice = 'year'
                self.accuY.span = 1
                self.accuY.caching = True
                self.accuY.storage = self.storage
                self.accuY.formulas = {'data': {
                     'max_temp' : MaxFormula('temp'),
                     'min_temp' : MinFormula('temp'),
                     'max_hum' : MaxFormula('hum'),
                     'min_hum' : MinFormula('hum'),
                     'max_pressure' : MaxFormula('pressure'),
                     'min_pressure' : MinFormula('pressure'),
                     'max_gust' : MaxFormula('wind_gust'),
                     'rain_fall' : SumFormula('rain') } }

                # Accumulator for monthly data
                self.accuM = AccumulatorDatasource()
                self.accuM.slice = 'month'
                self.accuM.span = 1
                self.accuM.storage = self.storage
                self.accuM.caching = True
                self.accuM.formulas = {'data': {
                     'max_temp' : MaxFormula('temp'),
                     'min_temp' : MinFormula('temp'),
                     'max_hum' : MaxFormula('hum'),
                     'min_hum' : MinFormula('hum'),
                     'max_pressure' : MaxFormula('pressure'),
                     'min_pressure' : MinFormula('pressure'),
                     'max_gust' : MaxFormula('wind_gust'),
                     'rain_fall' : SumFormula('rain') } }

                # Accumulator for daily and current data
                self.accuD = AccumulatorDatasource()
                self.accuD.slice = 'day'
                self.accuD.span = 1
                self.accuD.storage = self.storage
                self.accuD.caching = True
                self.accuD.formulas = {
                     'data': {
                         'max_temp' : MaxFormula('temp'),
                         'min_temp' : MinFormula('temp'),
                         'max_hum' : MaxFormula('hum'),
                         'min_hum' : MinFormula('hum'),
                         'max_pressure' : MaxFormula('pressure'),
                         'min_pressure' : MinFormula('pressure'),
                         'max_gust' : MaxFormula('wind_gust'),
                         'rain_fall' : SumFormula('rain') },
                     'current': {
                         'temp' : LastFormula('temp'),
                         'hum' : LastFormula('hum'),
                         'pressure' : LastFormula('pressure'),
                         'gust' : LastFormula('wind_gust'),
                         'wind_deg' : LastFormula('wind_dir'),
                         'time' : LastFormula('localtime') } }

            self.logger.info("Calculating ...")

            template = "*VER=DATA2*COD=%s*%s*%s*%s*%s*EOT*" % (
                       self.id, 
                       self._calculateCurrentData(self.accuD), 
                       self._calculateAggregData('D', self.accuD), 
                       self._calculateAggregData('M', self.accuM), 
                       self._calculateAggregData('Y', self.accuY))

            self.lastTemplate = template

            self.logger.info("Template calculated: %s" % template)

            return ['text/plain', template]

        except Exception, e:
            self.logger.warning("Error rendering meteoclimatic data: %s" % str(e))
            if self.lastTemplate == None:
                return ['text/plain', "*VER=DATA2*COD=%s*EOT*" % self.id]
            else:
                return ['text/plain', self.lastTemplate] 

    def _calculateCurrentData(self, accu):
        data = accu.execute()['current']['series']
        index = len(data['lbl'])-1
        template = "UPD=%s*TMP=%s*WND=%s*AZI=%s*BAR=%s*HUM=%s*SUN=" % (
               self._format(data['time'][index].strftime("%d/%m/%Y %H:%M")), 
               self._format(data['temp'][index]),  
               self._format(MpsToKmh(data['gust'][index])), 
               self._format(data['wind_deg'][index]), 
               self._format(data['pressure'][index]), 
               self._format(data['hum'][index]) )
        self.logger.debug("Calculating current data (index: %d): %s" % (index, template))
        return template

    def _calculateAggregData(self, time_span, accu):
        data = accu.execute()['data']['series']
        index = len(data['lbl'])-1
        template = "%sHTM=%s*%sLTM=%s*%sHHM=%s*%sLHM=%s*%sHBR=%s*%sLBR=%s*%sGST=%s*%sPCP=%s" % (
               time_span, self._format(data['max_temp'][index]), 
               time_span, self._format(data['min_temp'][index]), 
               time_span, self._format(data['max_hum'][index]), 
               time_span, self._format(data['min_hum'][index]),
               time_span, self._format(data['max_pressure'][index]), 
               time_span, self._format(data['min_pressure'][index]), 
               time_span, self._format(MpsToKmh(data['max_gust'][index])), 
               time_span, self._format(data['rain_fall'][index]) )
        self.logger.debug("Calculating %s data (index: %d): %s" % (time_span, index, template))
        return template

    def _format(self, value, default='-'):
        return value if value != None else default


# Information on the data template can be found at     
# http://www.meteoclimatic.com/index/wp/plantilla_es.html
#
# Formato del fichero de datos
# ############################
# El fichero de datos está compuesto por una serie de campos. Cada campo está compuesto por 
# una etiqueta identificativa y el valor correspondiente. La etiqueta se indicará en caracteres 
# en mayúscula, está precedida por un asterisco y finaliza con un signo de igual. Esta etiqueta 
# identifica el valor que lo sigue.
# A grandes rasgos, este fichero se divide en:
#
#    * Cabecera
#    * Datos actuales
#    * Datos diarios (máximas, mínimas y precipitación)
#    * Datos mensuales (máximas, mínimas y precipitación)
#    * Datos anuales (máximas, mínimas y precipitación)
#    * Final de fichero
#
# Importante: El objetivo de este fichero es que sea comprendido por un programa y no mostrado 
# a un usuario. Por ello, es muy importante que no se formatee la información para hacerla bonita 
# visualmente. Es necesario que sea un fichero de texto neto, sin marcas ni etiquetas de 
# hipertexto entre sus marcas de cabecera y final de fichero.
#
# Cabecera
# ########
# Tiene como objetivo marcar el inicio del bloque de datos y la identificación de la estación. 
# Contiene los siguientes campos:
# *VER=DATA2
#       Marca de inicio del fichero. Versión del fichero de datos. Valor constante.
# *COD=[código_estación]
#       Identificación del código de la estación
# *UPD=[actualización]
#       Fecha y hora de los datos. La fecha se ha de indicar en formato normalizado de 
#       día/mes/año. No se entiende el formato anglosajón de tipo mes/día/año. A continuación
#       de la fecha se debe indicar la hora, preferiblemente en formato de 24 horas. 
#       Excepción: Si el usuario requiere específicamente que el formato de fecha sea el 
#       anglosajón, se precederá esta fecha por los caracteres US_ 
#       Ejemplo: *UPD=US_03/14/2007 14:25
# 
# Datos actuales
# ##############
# Contiene los datos del momento de envío del fichero y lo forman los siguientes campos:
# *TMP=[temperatura]
#       Temperatura en grados Celsius
# *WND=[velocidad_viento]
#       Velocidad del viento en km/h
# *AZI=[dirección]
#       Dirección del viento. Se puede indicar en grados, donde los 0º o 360º son 
#       el norte y 90º, 180º y 270º son el este, sur y oeste, respectivamente. También 
#       se pueden indicar en el formato geográfico o literal (N, NNE, NE, ENE, E, ESE, 
#       SE, SSE, S, SSW, SSO, SW, SO, WSW, OSO, W, O, WNW, ONO, NW, NO, NNW, NNO)
# *BAR=[presión]
#       Presión en hPa o mb.
# *HUM=[humedad]
#       Humedad relativa
# *SUN=[radiación_solar]
#       Radiación solar W/m2. En blanco si no se proporciona.

# Datos diarios
# Contiene las máximas y mínimas diarias y el total de precipitación del día, según 
# los siguientes campos:
# DHTM=[temperatura]
#       Temperatura máxima del día en grados Celsius
# DLTM=[temperatura]
#       Temperatura mínima del día en grados Celsius
# DHHM=[humedad]
#       Humedad relativa máxima del día
# DLHM=[humedad]
#       Humedad relativa mínima del día
# DHBR=[presión]
#       Presión máxima del día
# DLBR=[presión]
#       Presión mínima del día
# DGST=[velocidad_viento]
#       Racha de viento máxima del día
# DPCP=[precipitación]
#       Precipitación total del día en mm
#
# Datos mensuales
# ###############
# Contiene las máximas y mínimas mensuales y el total de precipitación del mes, según 
# los siguientes campos:
# MHTM=[temperatura]
#       Temperatura máxima del mes en grados Celsius
# MLTM=[temperatura]
#       Temperatura mínima del mes en grados Celsius
# MHHM=[humedad]
#       Humedad relativa máxima del mes
# MLHM=[humedad]
#       Humedad relativa mínima del mes
# MHBR=[presión]
#       Presión máxima del mes
# MLBR=[presión]
#       Presión mínima del mes
# MGST=[velocidad_viento]
#       Racha de viento máxima del mes
# MPCP=[precipitación]
#       Precipitación total del mes en mm
#
# Datos anuales
# #############
# Contiene las máximas y mínimas anuales y el total de precipitación del año, según 
# los siguientes campos:
# YHTM=[temperatura]
#       Temperatura máxima del año en grados Celsius
# YLTM=[temperatura]
#       Temperatura mínima del año en grados Celsius
# YHHM=[humedad]
#       Humedad relativa máxima del año
# YLHM=[humedad]
#       Humedad relativa mínima del año
# YHBR=[presión]
#       Presión máxima del año
# YLBR=[presión]
#       Presión mínima del año
# YGST=[velocidad_viento]
#       Racha de viento máxima del año
# YPCP=[precipitación]
#       Precipitación total del año en mm
#
# Final del fichero
# #################
# El fichero de datos finaliza con una marca de fin de texto *EOT*
# Debido a que muchos servicios gratuítos de alojamiento de pàginas web basan su 
# financiación en la inserción de publicidad, a menudo modifican las páginas que 
# envían los usuarios para hacer que esta aparezca. Para que se pueda discriminar 
# entre la publicidad y los datos, se marca el inicio y final del fichero de datos 
# con estas etiquetas.

