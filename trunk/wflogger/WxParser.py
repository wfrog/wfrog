## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <lbovet@windmaster.ch>
##
##  This file is part of WFrog
##
##  WFrog is free software: you can redistribute it and/or modify
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

## TODO: Prepare por null windchill and heatindex values

import time, logging
from wfcommon.WxUtils import DewPoint, WindChill, HeatIndex, StationToSeaLevelPressure
from threading import Lock

class WxParser ():
    def __init__(self, config):
        self._lock = Lock()
        self._logger = logging.getLogger('WxLogger.WxParser')
        ## Configuration
        self.ALTITUDE = config.getfloat('WxParser', 'ALTITUDE')
        self.MEAN_TEMP = config.getfloat('WxParser', 'MEAN_TEMP')
        ## Init internal data
        self._temp_last = None
        self._hum_last = None
        self._rain_last = None
        self._rain_last_time = None
        self._new_period()
        
    def _new_period(self):
        ## Temperature
        self._temp = []
        ## Humidity
        self._hum = []
        ## Wind
        self._wind = []
        self._wind_dir = []
        ## Wind gust
        self._wind_gust = 0.0
        self._wind_gust_dir = None
        ## Rain
        if self._rain_last != None:
            self._rain_first = self._rain_last
        else:    
            self._rain_first = None
        self._rain_rate = 0.0
        ## Pressure
        self._pressure = []
        ## UV
        self._uv_index = None
        ## Log
        self._logger.info ('new_period')

    def _report_rain(self, total, rate):
        self._lock.acquire()
        if self._rain_first == None:
            self._rain_first = total    
        self._rain_last = total
        if self._rain_rate < rate:
            self._rain_rate = rate
        self._lock.release()

    def _report_wind(self, dirDeg, avgSpeed, gustSpeed):  
        self._lock.acquire()
        self._wind_dir.append(dirDeg)
        self._wind.append(avgSpeed)
        if self._wind_gust < gustSpeed:
            self._wind_gust = gustSpeed
            self._wind_gust_dir = dirDeg
        self._lock.release()

    def _report_barometer_sea_level(self, pressure):
        self._lock.acquire()
        self._pressure.append(pressure)
        self._lock.release()

    def _report_barometer_absolute(self, pressure):
        if self._temp_last != None and self._hum_last != None:
            seaLevelPressure = round(StationToSeaLevelPressure(
                                     pressure, self.ALTITUDE, self._temp_last, 
                                     self.MEAN_TEMP, self._hum_last, 'paDavisVP'),1)
            self._lock.acquire()
            self._pressure.append(seaLevelPressure)
            self._lock.release()

    def _report_temperature(self, temp, humidity):
        self._lock.acquire()
        self._temp.append(temp)
        self._hum.append(humidity)
        self._temp_last = temp
        self._hum_last = humidity
        self._lock.release()

    def _report_uv(self, uv_index):
        self._lock.acquire()
        if self._uv_index == None or self._uv_index < uv_index:
            self._uv_index = uv_index
        self._lock.release()
    
    def get_data(self):
        self._lock.acquire()
        data = None
        if len(self._temp) == 0 \
           or len(self._wind) == 0 \
           or self._rain_first == None \
           or len(self._pressure) == 0:
            self._lock.release()
            return None
        
        # Calculate wind dominant direction (simple algorithm)
        histo = {}
        for d in self._wind_dir:
            if not histo.has_key(d):
                histo[d]=1
            else:
                histo[d]+=1
        max_n = 0
        dom_wind_dir = 0
        for d, n in histo.iteritems():
            if n > max_n:
                max_n = n
                dom_wind_dir = d

        data = {
            'temp': sum(self._temp)/len(self._temp),
            'hum': sum(self._hum)/len(self._hum),
            'wind': sum(self._wind)/len(self._wind),
            'wind_dir': dom_wind_dir,
            'wind_gust_dir': self._wind_gust_dir
        }

        # Wind gust cannot be smaller than wind average 
        # (might happen due to different sampling periods)
        if data['wind'] <= self._wind_gust:
            data['wind_gust'] = self._wind_gust
        else:
            data['wind_gust'] = data['wind']
        
        ## Rain
        if self._rain_last > self._rain_first:
            data['rain'] = self._rain_last - self._rain_first
            data['rain_rate'] = self._rain_rate
        else:
            data['rain'] = 0.0
            data['rain_rate'] = 0.0
        
        ## QFF pressure (Sea Level Pressure)
        pressure = sum(self._pressure)/len(self._pressure)
        data['sea_level_pressure'] = pressure
        
        ## Dew Point
        data['dew_point'] = round(DewPoint(data['temp'], data['hum'], 'vaDavisVP'), 1)
        
        ## Wind Chill
        data['wind_chill'] = round(WindChill(data['temp'], data['wind']*3.6), 1)            
        
        ## Heat Index
        data['heat_index'] = round(HeatIndex(data['temp'], data['hum']), 1) 
        
        ## UV
        if self._uv_index != None:
            data['uv_index'] = self._uv_index

        ## Log
        self._logger.info('get_data')
        self._logger.debug('data = %s', data)

        self._new_period()
        self._lock.release()
        return data
