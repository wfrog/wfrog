## Copyright 2010 Jordi Puigsegur <jordi.puigsegur@gmail.com>
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

import math
import logging
import sys
import time
import wfcommon.database
from wfcommon.formula.base import LastFormula
from wfcommon.formula.base import SumFormula
try:
    import wfrender.datasource.accumulator
except ImportError, e:
    import datasource.accumulator
from wfcommon.units import HPaToInHg
from wfcommon.units import CToF
from wfcommon.units import MmToIn
from wfcommon.units import MpsToMph

class WeatherUndergroundPublisher(object):
    """
    Render and publisher for Weather Underground. It is a wrapper 
    around PyWeather, thus needs this package installed on your 
    system, version 0.9.1 or superior. (sudo easy_install weather)

    [ Properties ]

    id [string]:
        Weather Underground station ID.

    password [string]:
        Weather Underground password.

    period [numeric]:
        The update period in seconds.

    storage: 
        The storage service.

    real_time [boolean] (optional):
        If true then uses real time server. period must be < 30 secs.
        Default value is false. 
    """

    id = None
    password = None
    publisher = None
    real_time = False
    storage = None
    alive = False

    logger = logging.getLogger("renderer.wunderground")

    def render(self, data={}, context={}):
        try:
            assert self.id is not None, "'wunderground.id' must be set"
            assert self.password is not None, "'wunderground.password' must be set"
            assert self.period is not None, "'wunderground.period' must be set"

            self.real_time = self.real_time and self.period < 30

            rtfreq = None
            if self.real_time: rtfreq = self.period

            self.logger.info("Initializing Wunderground publisher (station %s)" % self.id)
            import weather.services
            self.publisher = weather.services.Wunderground(self.id, self.password, rtfreq)

            self.alive = True
            if not self.real_time:

                accu = datasource.accumulator.AccumulatorDatasource()
                accu.slice = 'day'
                accu.span = 1
                accu.storage = self.storage
                accu.formulas = {'current': {
                     'temp' : LastFormula('temp'),
                     'dew_point': LastFormula('dew_point'),
                     'hum' : LastFormula('hum'),
                     'pressure' : LastFormula('pressure'),
                     'wind' : LastFormula('wind'),
                     'wind_deg' : LastFormula('wind_dir'),
                     'gust' : LastFormula('wind_gust'),
                     'gust_deg' : LastFormula('wind_gust_dir'),
                     'rain_rate' : LastFormula('rain_rate'),
                     'rain_fall' : SumFormula('rain'), 
                     'utctime' : LastFormula('utctime') } }

                while self.alive:
                    try:
                        data = accu.execute()['current']['series']
                        index = len(data['lbl'])-1

                        # <float> pressure: in inches of Hg
                        pressure = HPaToInHg(data['pressure'][index])
                        # <float> dewpoint: in Fahrenheit
                        dewpoint = CToF(data['dew_point'][index])
                        # <float> humidity: between 0.0 and 100.0 inclusive
                        humidity = data['hum'][index]
                        # <float> tempf: in Fahrenheit
                        tempf = CToF(data['temp'][index])
                        # <float> rainin: inches/hour of rain
                        rainin = MmToIn(data['rain_rate'][index])
                        # <float> rainday: total rainfall in day (localtime)
                        rainday = MmToIn(data['rain_fall'][index])
                        # <string> dateutc: date "YYYY-MM-DD HH:MM:SS" in GMT timezone
                        dateutc = data['utctime'][index].strftime('%Y-%m-%d %H:%M:%S')
                        # <float> windspeed: in mph
                        windspeed = MpsToMph(data['wind'][index])
                        # <float> winddir: in degrees, between 0.0 and 360.0
                        winddir = data['wind_deg'][index]
                        if winddir == None and windspeed != None: 
                            winddir = 0.0
                        # <float> windgust: in mph
                        windgust = MpsToMph(data['gust'][index])
                        # <float> windgustdir:in degrees, between 0.0 and 360.0
                        windgustdir = data['gust_deg'][index]
                        if windgustdir == None: 
                            windgustdir = windgust

                        self.publisher.set(pressure = pressure, 
                                           dewpoint = dewpoint, 
                                           humidity = humidity,
                                           tempf = tempf,
                                           rainin = rainin, 
                                           rainday = rainday, 
                                           dateutc = dateutc, 
                                           windgust = windgust,
                                           windgustdir = windgustdir, 
                                           windspeed = windspeed, 
                                           winddir = winddir)

                        self.logger.info("Publishing Wunderground data (normal server, %s station): %s / %.1fF / %d%% / %.1finHg / %.1finh / %.1fin / %.1fMph(%.0fdeg.) / %.1fMph(%.0fdeg.) " % (
                               self.id, dateutc, tempf, humidity, pressure, rainin, rainday, windgust, windgustdir, windspeed, winddir))
                        response = self.publisher.publish()               
                        self.logger.info('Result Wunderground publisher: %s' % str(response))

                    except Exception, e:
                        self.logger.exception(e)

                    time.sleep(self.period)
            else:
                self.logger.error("Wunderground real time server not yet supported")
#                while self.alive:
#                    self.logger.debug("Publishing weather underground data (real time server).")
#    
#                    time.sleep(self.period)

        except Exception, e:
            self.logger.exception(e)
            raise

    def close(self):
        self.alive = False

