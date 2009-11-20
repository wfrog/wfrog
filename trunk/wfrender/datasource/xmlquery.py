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

import xml.dom.minidom
from datetime import datetime

class WxDataXmlDataSource(object):
    """
    Reads data from a WxData file
    """

    def __init__(self, path):
        self.path=path

    def execute(self,data={}, context={}):
        dom = xml.dom.minidom.parse(self.path)
        result = {}
        result['temp1'] = {}
        result['temp1']['value'] = float(dom.getElementsByTagName('th1')[0].getElementsByTagName('temp')[0].childNodes[0].data)
        result['temp1']['unit'] = "C"

        result['hum1'] = {}
        result['hum1']['value'] = float(dom.getElementsByTagName('th1')[0].getElementsByTagName('humidity')[0].childNodes[0].data)
        result['hum1']['unit'] = "%"

        result['temp0'] = {}
        result['temp0']['value'] = float(dom.getElementsByTagName('thInt')[0].getElementsByTagName('temp')[0].childNodes[0].data)
        result['temp0']['unit'] = "C"

        result['hum0'] = {}
        result['hum0']['value'] = float(dom.getElementsByTagName('thInt')[0].getElementsByTagName('humidity')[0].childNodes[0].data)
        result['hum0']['unit'] = "%"

        result['press'] = {}
        result['press']['value'] = float(dom.getElementsByTagName('barometer')[0].getElementsByTagName('pressure')[0].childNodes[0].data)
        result['press']['unit'] = "mb"

        result['rain'] = {}
        result['rain']['value'] = float(dom.getElementsByTagName('rain')[0].getElementsByTagName('rate')[0].childNodes[0].data)
        result['rain']['unit'] = "mm/h"

        result['wind'] = {}
        result['wind']['value'] = float(dom.getElementsByTagName('wind')[0].getElementsByTagName('avgSpeed')[0].childNodes[0].data)
        result['wind']['max'] = float(dom.getElementsByTagName('wind')[0].getElementsByTagName('gustSpeed')[0].childNodes[0].data)
        result['wind']['deg'] = int(dom.getElementsByTagName('wind')[0].getElementsByTagName('dirDeg')[0].childNodes[0].data)
        result['wind']['dir'] = dom.getElementsByTagName('wind')[0].getElementsByTagName('dirStr')[0].childNodes[0].data
        result['wind']['unit'] = "m/s"

        result['info'] = {}
        result['info']['timestamp'] = datetime.strptime(dom.getElementsByTagName('timestampt')[0].childNodes[0].data, "%Y.%m.%d.%H.%M.%S")

        return result

