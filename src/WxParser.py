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

## TODO: Add support for UV sensor
##       Prepare por null windchill and heatindex values
##       Improve aggregation so that it is not necessary to query the database each time

import time, logging
from uWxUtils import StationToSeaLevelPressure, DewPoint, WindChill, HeatIndex
from threading import Lock

class WxParser ():
    def __init__(self, config):
        self._lock = Lock()
        self._logger = logging.getLogger('WxLogger.WxParser')
        ## Configuration
        self.ALTITUDE = config.getfloat('WxParser', 'ALTITUDE')
        self.MEAN_TEMP = config.getfloat('WxParser', 'MEAN_TEMP')
        ## Init internal data
        self._rain_last = None
        self._rain_last_time = None
        self._new_period()
        
    def _new_period(self):
        ## Temperature
        self._temp = []
        self._temp_min = None
        self._temp_min_time = None
        self._temp_max = None
        self._temp_max_time = None
        ## Humidity
        self._hum = []
        self._hum_min = None
        self._hum_min_time = None
        self._hum_max = None
        self._hum_max_time = None
        ## Wind
        self._wind = []
        self._wind_dir = []
        ## Wind gust
        self._wind_gust = 0.0
        self._wind_gust_dir = None
        self._wind_gust_time = None
        ## Rain
        if self._rain_last != None:
            self._rain_first = self._rain_last
        else:    
            self._rain_first = None
        self._rain_rate = 0.0
        self._rain_rate_time = None
        ## Pressure
        self._pressure = []
        ## Log
        self._logger.info ('new_period')

    def _report_rain(self, total, rate):
        self._lock.acquire()
        if self._rain_first == None:
            self._rain_first = total    
        self._rain_last = total
        if self._rain_rate < rate:
            self._rain_rate = rate
            self._rain_rate_time = time.localtime()
        self._lock.release()

    def _report_wind(self, dirDeg, avgSpeed, gustSpeed):  
        self._lock.acquire()
        self._wind_dir.append(dirDeg)
        self._wind.append(avgSpeed)
        if self._wind_gust < gustSpeed:
            self._wind_gust = gustSpeed
            self._wind_gust_dir = dirDeg
            self._wind_gust_time = time.localtime()
        self._lock.release()

    def _report_barometer(self, pressure):
        self._lock.acquire()
        self._pressure.append(pressure)
        self._lock.release()

    def _report_temperature(self, temp, humidity):
        self._lock.acquire()
        self._temp.append(temp)
        self._hum.append(humidity)
        if self._temp_min == None or self._temp_min > temp:
            self._temp_min = temp
            self._temp_min_time = time.localtime()
        if self._temp_max == None or self._temp_max < temp:
            self._temp_max = temp
            self._temp_max_time = time.localtime()
        if self._hum_min == None or self._hum_min > humidity:
            self._hum_min = humidity
            self._hum_min_time = time.localtime()
        if self._hum_max == None or self._hum_max < humidity:
            self._hum_max = humidity
            self._hum_max_time = time.localtime()
        self._lock.release()

    def _report_uv(self, uv):
        self._lock.acquire()
        pass
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
        
        data = {
            'temp': sum(self._temp)/len(self._temp),
            'temp_min': self._temp_min,
            'temp_min_time': self._temp_min_time,
            'temp_max': self._temp_max,
            'temp_max_time': self._temp_max_time,
            'hum': sum(self._hum)/len(self._hum),
            'hum_min': self._hum_min,
            'hum_min_time': self._hum_min_time,
            'hum_max': self._hum_max,
            'hum_max_time': self._hum_max_time,
            'wind': sum(self._wind)/len(self._wind),
            'wind_dir': sum(self._wind_dir)/len(self._wind_dir),
            #'wind_dir_str': f(data['wind_dir'])
            'wind_gust': self._wind_gust,
            'wind_gust_dir': self._wind_gust_dir, 
            'wind_gust_time': self._wind_gust_time, 
        }
        
        ## Rain
        if self._rain_last > self._rain_first:
            data['rain'] = self._rain_last - self._rain_first
            data['rain_rate'] = self._rain_rate
            data['rain_rate_time'] = self._rain_rate_time
        else:
            data['rain'] = 0.0
            data['rain_rate'] = 0.0
            data['rain_rate_time'] = None
        
        ## QFF pressure (Sea Level Pressure)
        pressure = sum(self._pressure)/len(self._pressure)
        data['sea_level_pressure'] = round(StationToSeaLevelPressure(
                                                   sum(self._pressure)/len(self._pressure),
                                                   self.ALTITUDE, data['temp'], self.MEAN_TEMP, 
                                                   data['hum'], 'paDavisVP'),1)
        
        ## Dew Point
        data['dew_point'] = round(DewPoint(data['temp'], data['hum'], 'vaDavisVP'), 1)
        
        ## Wind Chill
        data['wind_chill'] = round(WindChill(data['temp'], data['wind']), 1)            
        
        ## Heat Index
        data['heat_index'] = round(HeatIndex(data['temp'], data['hum']), 1) 

        ## Log
        self._logger.info('get_data')
        self._logger.debug('data = %s', data)

        self._new_period()
        self._lock.release()
        return data