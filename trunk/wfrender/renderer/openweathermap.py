## Copyright 2013 Jordi Puigsegur <jordi.puigsegur@gmail.com>
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
import httplib
import urllib
import base64

from wfcommon.formula.base import LastFormula
from wfcommon.formula.base import SumFormula


try:
    from wfrender.datasource.accumulator import AccumulatorDatasource
except ImportError, e:
    from datasource.accumulator import AccumulatorDatasource

class OpenWeatherMapPublisher(object):
    """
    Render and publisher for www.openweathermap.org.
    Sends every record published to the storage to openweathermap API.

    [ Properties ]

    username [string]:
        Your openweathermap.org username.

    password [string]:
        Your openweathermap.org password.

    name[string]:
        Station name.

    latitude[numeric]:
        Station latitude (signed degrees format)

    longitude[numeric]:
        Station longitude (signed degrees format)

    altitude [numeric]:
        Station altitude in m.

    storage: 
        The storage service.

    send_uv[boolean] (optional):
        Send UV data (by default false).

    send_radiation[boolean] (optional):
        Send radiation data (by default false).
    """

    username = None
    password = None
    name = None
    longitude = None
    latitude = None
    altitude = None
    storage = None
    alive = False
    send_uv = False
    send_radiation = False

    logger = logging.getLogger("renderer.openweathermap")

    def render(self, data={}, context={}):
        try:
            assert self.username is not None, "'openweathermap.id' must be set"
            assert self.password is not None, "'openweathermap.password' must be set"
            assert self.name is not None, "'openweathermap.name' must be set"
            assert self.latitude is not None, "'openweathermap.latitude' must be set"
            assert self.longitude is not None, "'openweathermap.longitude' must be set"
            assert self.altitude is not None, "'openweathermap.altitude' must be set"
            
            self.logger.info("Initializing openweathermap.com (user %s)" % self.username)

            self.alive = True

            accu = AccumulatorDatasource()
            accu.slice = 'day'
            accu.span = 1
            accu.storage = self.storage

            accu.formulas =     {'current': {
                 'temp'      : LastFormula('temp'),
                 'hum'       : LastFormula('hum'),
                 'pressure'  : LastFormula('pressure'),
                 'dew_point' : LastFormula('dew_point'),
                 'wind'      : LastFormula('wind'),
                 'wind_gust' : LastFormula('wind_gust'),
                 'wind_deg'  : LastFormula('wind_dir'),
                 'rain'      : SumFormula('rain'),
                 'utctime'   : LastFormula('utctime') } }

            if self.send_uv:
                accu.formulas['current']['uv'] = LastFormula('uv')

            if self.send_radiation:
                accu.formulas['current']['solar_rad'] = LastFormula('solar_rad')

            accu24h = AccumulatorDatasource()
            accu24h.slice = 'hour'
            accu24h.span = 24
            accu24h.storage = self.storage
            accu24h.formulas =  {'current': {'rain': SumFormula('rain')} }

            accu60min = AccumulatorDatasource()
            accu60min.slice = 'minute'
            accu60min.span = 60
            accu60min.storage = self.storage
            accu60min.formulas =  {'current': {'rain': SumFormula('rain')} }

            last_timestamp = None
            while self.alive:

                try:
                    data = accu.execute()['current']['series']
                    index = len(data['lbl'])-1
                    rain_1h = sum(map(lambda x: x if x is not None else 0, accu60min.execute()['current']['series']['rain'][:60]))
                    rain_24h = sum(map(lambda x: x if x is not None else 0, accu24h.execute()['current']['series']['rain'][:24]))

                    if last_timestamp == None or last_timestamp < data['utctime'][index]:
                        last_timestamp = data['utctime'][index]

                        args = {
                            'wind_dir':   int(round(data['wind_deg'][index])), # grad
                            'wind_speed': str(data['wind'][index]),            # mps
                            'wind_gust':  str(data['wind_gust'][index]),       # mps
                            'temp':       str(data['temp'][index]),            # grad C
                            #'dewpoint':   str(data['dew_point'][index]),       # NOT WORKING PROPERLY
                            'humidity':   int(round(data['hum'][index])),      # relative humidity %
                            'pressure':   str(data['pressure'][index]),        # mb 
                            'rain_1h':    rain_1h,                             # mm 
                            'rain_24h':   rain_24h,                            # mm
                            'rain_today': str(data['rain'][index]),            # mm
                            'lat':        self.latitude,
                            'long':        self.longitude,
                            'alt':        self.altitude,
                            'name':       self.name
                            }

                        if self.send_uv:
                            args['uv'] = str(data['uv'][index])
                        if self.send_radiation: 
                            args['lum'] = str(data['solar_rad'][index])
 
                        self.logger.debug("Publishing openweathermap data: %s " % urllib.urlencode(args))
                        response = self._publish(args, 'openweathermap.org', '/data/post')

                        if response[0] == 200:
                            self.logger.info('Data published successfully')
                            self.logger.debug('Code: %s Status: %s Answer: %s' % response)
                        else:
                            self.logger.error('Error publishing data. Code: %s Status: %s Answer: %s' % response)

                except Exception, e:
                    if (str(e) == "'NoneType' object has no attribute 'strftime'") or (str(e) == "a float is required"):
                        self.logger.error('Could not publish: no valid values at this time. Retry next run...')
                    else:
                        self.logger.exception(e)

                time.sleep(60) # each minute we check for new records to send to openweathermap

        except Exception, e:
            self.logger.exception(e)
            raise

    def close(self):
        self.alive = False

    def _publish(self, args, server, uri):

      uri = uri + "?" + urllib.urlencode(args)
      
      self.logger.debug('Connect to: http://%s' % server)
      self.logger.debug('GET %s' % uri)

      auth = base64.encodestring("%s:%s" % (self.username, self.password))

      conn = httplib.HTTPConnection(server)
      if not conn:
         raise Exception, 'Remote server connection timeout!'

      conn.request("GET", uri, headers = {"Authorization" : "Basic %s" % auth})
      conn.sock.settimeout(30.0)  # 30 seconds timeout 

      http = conn.getresponse()
      data = (http.status, http.reason, http.read())
      conn.close()
      if not (data[0] == 200 and data[1] == 'OK'):
         raise Exception, 'Server returned invalid status: %d %s %s' % data
      return data


# http://openweathermap.org/wiki/API/data_upload
# 
# Data upload API
# 
# The protocol of weather station data transmission Version 1.0
# 
# This protocol is used for transmission of one measurement from a weather station.
# The data is transmitted by HTTP POST request. The http basic authentication is used for authentication.
# The server address is http://openweathermap.org/data/post
# To connect your station, please register at http://OpenWeatherMap.org/login
# The following parameters can be transmitted in POST:
# 
# wind_dir - wind direction, grad
# wind_speed - wind speed, mps
# temp - temperature, grad C
# humidity - relative humidity, %
# pressure - atmosphere pressure
# wind_gust - speed of wind gust, mps
# rain_1h - rain in recent hour, mm
# rain_24h - rain in recent 24 hours, mm
# rain_today - rain today, mm
# snow - snow in recent 24 hours, mm
# lum - illumination, W/M2
# lat - latitude
# long - longitude
# alt - altitude, m
# radiation - radiation
# dewpoint - dewpoint
# uv - UV index
# name - station name


