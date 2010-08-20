## Copyright 2009 Laurent Bovet <laurent.bovet@windmaster.ch>
##                Jordi Puigsegur <jordi.puigsegur@gmail.com>
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

import logging
import wfcommon.meteo
from wfcommon.formula.base import AverageFormula
import datetime

class BaseCollector(object):
    '''
    Base class for collectors.
    '''

    _temp_last = None
    _hum_last = None
    _mean_temp = None
    _mean_temp_last_time = None

    storage = None

    def send_event(self, event, context={}):

        self.init()

        if event._type == "_flush":
            self.flush(context)
        elif event._type == 'rain':
            self._report_rain(event.total, event.rate)
        elif event._type == 'wind':
            self._report_wind(event.mean.speed, event.mean.dir, event.gust.speed, event.gust.dir)
        elif event._type == 'press':
            if hasattr(event, 'code'):
                if event.code == 'RAW' or event.code == 'QFE':
                    self._report_barometer_absolute(event.value)
                else:
                    self._report_barometer_sea_level(event.value)
            else:
                self._report_barometer_absolute(event.value, context)
        elif event._type == 'temp':
            self._report_temperature(event.value, event.sensor)
            if event.sensor == 1:
                self._temp_last = event.value
        elif event._type == 'hum':
            self._report_humidity(event.value, event.sensor)
            if event.sensor == 1:
                self._hum_last = event.value
        elif event._type == 'uv':
            self._report_uv(event.value)

    def _get_mean_temp(self, current_temp, context):  # Last 12 hours mean temp

        if self.storage is None:
            return current_temp

        if self._mean_temp != None:
            if (datetime.datetime.now()-self._mean_temp_last_time).seconds < 3600: # New value each hour
                return self._mean_temp
        try:

            average = AverageFormula(self.storage.keys().index('temp'))

            for sample in self.storage.samples(datetime.datetime.now() - datetime.timedelta(hours=12), context=context):
                average.append(sample)
            self._mean_temp = average.value()
            if self._mean_temp is None:
                return current_temp

            self._mean_temp_last_time = datetime.datetime.now()
            self.logger.info("Calculated last 12 hours mean temp: %4.1f" % self._mean_temp)
            return self._mean_temp
        except Exception, e:
            self.logger.warning("Error calculating last 12 hours mean temp: %s, returning current temperature" % str(e))
            return current_temp

        return current_temp


    def _report_barometer_absolute(self, pressure, context):
        if self._temp_last != None and self._hum_last != None:
            seaLevelPressure = wfcommon.meteo.StationToSeaLevelPressure(
                                  pressure,
                                  context['altitude'],
                                  self._temp_last,
                                  self._get_mean_temp(self._temp_last, context),
                                  self._hum_last,
                                  'paDavisVP')
            self._report_barometer_sea_level(seaLevelPressure)
