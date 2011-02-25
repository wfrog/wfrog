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
import base
import datetime
import os.path
import yaml
import copy

class CurrentConditionCollector(base.BaseCollector):
    '''
    Keep the latest event values and optionally flush them in a yaml file on
    'flush events'. Should be wrapped in a !flush elements to receive
    the 'flush events'.

    [ Properties ]

    path [string] (optional):
        Location of the yaml file to write.
    '''

    path = None
    initialized = False

    data = {}
    data['temp1'] = {}
    data['temp1']['value'] = 99
    data['hum1'] = {}
    data['hum1']['value'] = 0
    data['temp0'] = {}
    data['temp0']['value'] = 99
    data['hum0'] = {}
    data['hum0']['value'] = 0
    data['press'] = {}
    data['press']['value'] = 0
    data['rain'] = {}
    data['rain']['value'] = 9999
    data['wind'] = {}
    data['wind']['value'] = 9999
    data['wind']['max'] = 9999
    data['wind']['deg'] = 0
    data['wind']['dir'] = 'N'
    data['info'] = {}
    data['info']['timestamp'] = datetime.datetime(2001, 01, 01)

    logger = logging.getLogger('collector.current')

    def init(self, context={}):
        if not self.initialized:
            self.data = copy.deepcopy(self.data)
            self.initialized = True

    def _report_rain(self, total, rate):
        self.data['rain']['value'] = rate
        self.touch()

    def _report_wind(self, avgSpeed, dirDeg, gustSpeed, gustDir):
        self.data['wind']['avg'] = avgSpeed
        self.data['wind']['dir'] = dirDeg
        self.data['wind']['max'] = gustSpeed
        self.touch()

    def _report_barometer_sea_level(self, pressure):
        self.data['press']['value'] = pressure
        self.touch()

    def _report_temperature(self, temp, sensor):
        self.data['temp'+str(sensor)]['value'] = temp
        self.touch()

    def _report_humidity(self, humidity, sensor):
        self.data['hum'+str(sensor)]['value'] = humidity
        self.touch()

    def _report_uv(self, uv_index):
        self.data['uv']['value'] = uv_index
        self.touch()

    def touch(self):
        self.data['info']['timestamp'] = datetime.datetime.now()

    def flush(self, context={}):

        if self.path is None:
            self.logger.warn('No path specified, ignoring flush')
            return
        self.logger.debug("Flushing: data to %s", self.path)

        dir = os.path.realpath(os.path.dirname(self.path))
        if not os.path.exists(dir):
            os.makedirs(dir)

        yaml.dump(target, file(self.path, 'w'), default_flow_style=False)

    # called by current datasource
    def get_data(self, context={}):
        return self.data
