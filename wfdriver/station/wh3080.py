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

class WH3080Station(object):

    '''
    Station driver for Fine Offset WH3080

    This driver is a wrapper around pywws, thus
    needs this package installed on your system.
    '''

    logger = logging.getLogger('station.wh3080')

    name = 'Fine Offset WH3080 and compatibles'

    def run(self, generate_event, send_event, context={}):

        from pywws import WeatherStation

	# pywws manages a wh1080 by default. Therefore '3080' shall be passed.
        station = WeatherStation.weather_station('3080')

        for data, last_ptr, logged in station.live_data():
            if not logged:
                try:
                    if data['abs_pressure'] is not None:
                        e = generate_event('press')
                        e.value = (10*(4.5+230+(data['abs_pressure'])))/10
                        #e.value = (10*(data['abs_pressure']))/10
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
                        e.total = (136*(data['rain']))/100 
                        e.rate = 0
                        send_event(e)

                    if data['wind_ave'] is not None and data['wind_dir'] < 16:
                        e = generate_event('wind')
                        e.create_child('mean')
                        e.mean.speed = data['wind_ave']
                        e.mean.dir = 22.5*(data['wind_dir']) 

                        e.create_child('gust')
                        e.gust.speed = 0.0;
                        e.gust.dir = 0.0;
                        if data['wind_gust']:
                            #e.create_child('gust')
                            e.gust.speed = data['wind_gust']
                            e.gust.dir = 22.5*(data['wind_dir'])
                        send_event(e)

                    # pywws manages "uv" in the case of 3080 stations 
                    if data['uv'] is not None:
                        e = generate_event('uv')
                        e.sensor = 1
                        e.value = data['uv']
                        send_event(e)

                    # pywws manages the "illuminance" in the case of 3080 stations 
                    if data['illuminance'] is not None:
                        e = generate_event('rad')
                        e.sensor = 1
                        e.value = (convert_illuminance_wm2(data['illuminance']))
			send_event(e)

                except Exception, e:
                    self.logger.error(e)


                except Exception, e:
                    self.logger.error(e)
