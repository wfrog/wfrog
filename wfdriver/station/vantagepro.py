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

class VantageProStation(object):

    '''
    Station driver for the Davis VantagePro. It is a wrapper around PyWeather, thus
    need this package installed on your system (sudo easy_install weather).

    [Properties]

    port [string] (optional):
        Serial port tty to use. Defaults to /dev/ttyS0.

    period [numeric] (optional):
        Polling interval in seconds. Defaults to 60.
    '''

    ARCHIVE_INTERVAL=10

    port='/dev/ttyS0'
    period=60

    logger = logging.getLogger('station.vantagepro')

    def run(self, generate_event, send_event, context={}):

        import weather.stations.davis
        station = weather.stations.davis.VantagePro(self.port, self.ARCHIVE_INTERVAL)

        while True:

            try:
                station.parse()

                e = generate_event('press')
                e.value = units.InHgToHPa(station.fields['Pressure'])
                send_event(e)
                
                e = generate_event('temp')
                e.sensor = 0
                e.value = units.FToC(station.fields['TempIn'])
                send_event(e)

                e = generate_event('hum')
                e.sensor = 0
                e.value = station.fields['HumIn']
                send_event(e)
                                
                e = generate_event('temp')
                e.sensor = 1
                e.value = units.FToC(station.fields['TempOut'])
                send_event(e)

                e = generate_event('hum')
                e.sensor = 1
                e.value = station.fields['HumOut']
                send_event(e)

                e = generate_event('rain')
                e.rate = units.InToMm(station.fields['RainRate'])
                e.total = units.InToMm(station.fields['RainYear'])
                send_event(e)

                e = generate_event('wind')
                e.create_child('mean')
                e.mean.speed = units.MphToMps(station.fields['WindSpeed'])
                e.mean.dir = station.fields['WindDir']             
                rec = station.fields['Archive']      
                if rec:
                    e.create_child('gust')
                    e.gust.speed = units.MphToMps(rec['WindHi'])
                    e.gust.dir = rec['WindHiDir']                                    
                send_event(e)

            except Exception, e:
                self.logger.error(e)

            # pause until next update time
            next_update = self.period - (time.time() % self.period)
            time.sleep(next_update)
