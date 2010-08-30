## Copyright 2010 Laurent Bovet <laurent.bovet@windmaster.ch>
##                derived from PyWeather by Patrick C. McGinty
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

import time
import logging
from wfcommon import units

class WH1080Station(object):

    '''
    Station driver for Fine Offset WH1080, WH1081, WH1090, WH1091, WH2080, WH2081. 
    This also covers all the re-branded weather stations working with EasyWeather:
      - Elecsa AstroTouch 6975
      - Watson W-8681
      - WH-1080PC
      - Scientific Sales Pro Touch Screen Weather Station
      - TOPCOM NATIONAL GEOGRAPHIC 265NE
       -PCE-FWS 20 
      
    This driver is a wrapper around pywws, thus
    needs this package installed on your system.    
    '''

    logger = logging.getLogger('station.wh1080')

    def run(self, generate_event, send_event, context={}):
    
        from pywws import WeatherStation    
        station = WeatherStation.weather_station()

        for data in station.live_data():
            try:                
                e = generate_event('press')
                e.value = data['Pressure']
                send_event(e)

                e = generate_event('temp')
                e.sensor = 0
                e.value = data['temp_in']
                send_event(e)
                
                e = generate_event('hum')
                e.sensor = 0
                e.value = data['hum_in']
                send_event(e)
                                
                e = generate_event('temp')
                e.sensor = 1
                e.value = data['temp_out']
                send_event(e)
                
                e = generate_event('hum')
                e.sensor = 1
                e.value = data['hum_out']
                send_event(e)
                
                e = generate_event('rain')
                e.total = data['rain']
                send_event(e)
                
                e = generate_event('wind')
                e.create_child('mean')
                e.mean.speed = units.MphToMps(data['wind_ave'])
                e.mean.dir = data['wind_dir']
                e.create_child('gust')
                e.gust.speed = units.MphToMps(data['wind_gust'])
                e.gust.dir = data['wind_dir']
                send_event(e)                        
                
            except (Exception) as e:
                self.logger.error(e)
