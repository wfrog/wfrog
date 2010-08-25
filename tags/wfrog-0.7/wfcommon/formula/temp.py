## Copyright 2010 Laurent Bovet <laurent.bovet@windmaster.ch>
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

import sys

from wfcommon import meteo

class WindChillMinFormula(object):
    '''
    Minimum WindChill temperature. Requires temperature and wind speed in Km/h.
    '''

    def __init__(self, index):
        self.index = index

    index = None
    min_windchill = None

    def append(self, sample):
        value_temp = sample[self.index[0]]
        value_wind = sample[self.index[1]]

        if value_temp is not None and value_wind is not None :
            sample_windchill = meteo.WindChill(value_temp, meteo.msToKmh(value_wind))
            if sample_windchill is not None:
                if self.min_windchill is None or self.min_windchill > sample_windchill:
                    self.min_windchill = sample_windchill

    def value(self):
        return self.min_windchill


class HeatIndexMaxFormula(object):
    '''
    Maximum Heat Index temperature. Requires temperature and humidity.
    '''

    def __init__(self, index):
        self.index = index

    index = None
    max_heatindex = None

    def append(self, sample):
        value_temp = sample[self.index[0]]
        value_hum = sample[self.index[1]]

        if value_temp is not None and value_hum is not None :
            sample_heatindex = meteo.HeatIndex(value_temp, value_hum)
            if sample_heatindex is not None:
                if self.max_heatindex is None or self.max_heatindex < sample_heatindex:
                    self.max_heatindex = sample_heatindex

    def value(self):
        return self.max_heatindex


class HumidexMaxFormula(object):
    '''
    Maximum Humidex temperature. Requires temperature and humidity.
    '''

    def __init__(self, index):
        self.index = index

    index = None
    max_humidex = None

    def append(self, sample):
        value_temp = sample[self.index[0]]
        value_hum = sample[self.index[1]]

        if value_temp is not None and value_hum is not None :
            sample_humidex = meteo.Humidex(value_temp, value_hum)
            if sample_humidex is not None:
                if self.max_humidex is None or self.max_humidex < sample_humidex:
                    self.max_humidex = sample_humidex

    def value(self):
        return self.max_humidex

