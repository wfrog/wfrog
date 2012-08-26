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
import time
import os.path
from lxml import etree
from lxml.builder import E

def element(parent, name):
    result = parent.find(name)
    if result is None:
        result = etree.SubElement(parent, name)
    return result

class XmlFileCollector(base.BaseCollector):
    '''
    Keep the latest event values and flush them in an XML file on
    'flush events'. Should be wrapped in a !flush elements to receive
    the 'flush events'.

    [ Properties ]

    path [string]:
        Location of the XML file to write.
    '''

    path = None
    doc = None
    initialized = False


    logger = logging.getLogger('collector.xmlfile')

    def init(self):
        if not self.initialized:
            self.reset()
            self.initialized = True
    def _report_rain(self, total, rate):
        rain_elt = element(self.doc, 'rain')
        element(rain_elt, 'rate').text = str(rate)

    def _report_wind(self, avgSpeed, dirDeg, gustSpeed, gustDir):
        wind_elt = element(self.doc, 'wind')

        element(wind_elt, 'avgSpeed').text = str(avgSpeed)
        element(wind_elt, 'dirDeg').text = str(dirDeg)
        element(wind_elt, 'gustSpeed').text = str(gustSpeed)

    def _report_barometer_sea_level(self, pressure):
        press_elt = element(self.doc, 'barometer')
        element(press_elt, 'pressure').text = str(pressure)

    def _report_temperature(self, temp, sensor):
        if sensor == 0:
            temp_elt = element(self.doc, 'thInt')
        elif sensor == 1:
            temp_elt = element(self.doc, 'th1')
        else:
            return

        element(temp_elt, 'temp').text = str(temp)

    def _report_humidity(self, humidity, sensor):
        if sensor == 0:
            hum_elt = element(self.doc, 'thInt')
        elif sensor == 1:
            hum_elt = element(self.doc, 'th1')
        else:
            return

        element(hum_elt, 'humidity').text = str(humidity)

    def _report_uv(self, uv_index):
        return

    def _report_solar_rad(self, solar_rad):
        return

    def flush(self, context={}):

        time_elt = element(self.doc, 'time')
        time_elt.text = time.strftime("%Y-%m-%d %H:%M:%S")

        doc_string = etree.tostring(self.doc)

        self.logger.debug("Flushing: %s to %s", doc_string, self.path)

        dir = os.path.realpath(os.path.dirname(self.path))
        if not os.path.exists(dir):
            os.makedirs(dir)

        file = open(self.path, 'w')
        file.write(doc_string)
        file.close()

    def reset(self, context={}):
        self.doc = E.current()
