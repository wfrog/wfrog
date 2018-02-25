## Copyright 2010 Laurent Bovet <laurent.bovet@windmaster.ch>,
##                Jan Commandeur <duinzicht@gmail.com>
##                derived from pywws by Jim Easterbrook
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
      - PCE-FWS 20

    This driver is a wrapper around pywws, thus
    needs this package installed on your system.
    '''

    logger = logging.getLogger('station.wh1080')

    name = 'Fine Offset WH1080 and compatibles'

    def run(self, generate_event, send_event, context={}):
        from pywws import WeatherStation

        # cyclic try connecting to weather station (when USB is disconnected)
        while True:
            try:
                station = WeatherStation.weather_station()

                for data, last_ptr, logged in station.live_data():

                    if not logged:
                        try:
                            if data['abs_pressure'] is not None:
                                e = generate_event('press')
                                e.value = data['abs_pressure']
                                send_event(e)

                            if data['temp_in'] is not None:
                                e = generate_event('temp')
                                e.sensor = 0
                                e.value = data['temp_in']
                                send_event(e)

                            if data['hum_in'] is not None:
                                e = generate_event('hum')
                                e.sensor = 0
                                e.value = data['hum_in']
                                send_event(e)

                            if data['temp_out'] is not None:
                                e = generate_event('temp')
                                e.sensor = 1
                                e.value = data['temp_out']
                                send_event(e)

                            if data['hum_out'] is not None:
                                e = generate_event('hum')
                                e.sensor = 1
                                e.value = data['hum_out']
                                send_event(e)

                            if data['rain'] is not None:
                                e = generate_event('rain')
                                e.total = data['rain']
                                e.rate = 0
                                send_event(e)

                            if data['wind_ave'] is not None and 0 <= data['wind_dir'] < 16:
                                dir_degrees = data['wind_dir'] * 22.5  # 360 / 16 = 22.5
                                e = generate_event('wind')
                                e.create_child('mean')
                                e.mean.speed = data['wind_ave']
                                e.mean.dir = dir_degrees
                                e.create_child('gust')
                                if data['wind_gust'] is not None:
                                    e.gust.speed = data['wind_gust']
                                    e.gust.dir = dir_degrees
                                else:
                                    e.gust.speed = None
                                    e.gust.dir = None
                                send_event(e)

                        except Exception, e:
                            self.logger.error(e)
            except IOError, e:
                self.logger.error('Exception IOError: ' + str(e))
            finally:
                time.sleep(30)
