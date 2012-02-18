## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <laurent.bovet@windmaster.ch>
##
##  This file is part of WFrog
##
##  WFrog is free software: you can redistribute it and/or modify
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

class BaseStation(object):
    '''
    Convenience class used for migrating station code.
    New station support should work directly with events.
    '''

    def _report_rain(self, total, rate, timestamp=None):
        event = self.generate_event('rain')
        event.total = total
        event.rate = rate
        if timestamp:
            event.timestamp = timestamp
        self.send_event(event)

    def _report_wind(self, dirDeg, avgSpeed, gustSpeed, timestamp=None):
        event = self.generate_event('wind')
        event.create_child('mean')
        event.mean.dir = dirDeg
        event.mean.speed = avgSpeed
        event.create_child('gust')
        event.gust.dir = dirDeg
        event.gust.speed = gustSpeed
        if timestamp:
            event.timestamp = timestamp        
        self.send_event(event)

    def _report_barometer_absolute(self, pressure, timestamp=None):
        event = self.generate_event('press')
        event.value = pressure
        if timestamp:
            event.timestamp = timestamp        
        self.send_event(event)

    def _report_temperature(self, temp, humidity, sensor, timestamp=None):
        event = self.generate_event('temp')
        event.sensor = sensor
        event.value = temp
        if timestamp:
            event.timestamp = timestamp        
        self.send_event(event)

        if humidity != None:
            event = self.generate_event('hum')
            event.sensor = sensor
            event.value = humidity
            if timestamp:
                event.timestamp = timestamp        
            self.send_event(event)

    def _report_uv(self, uv_index, timestamp=None):
        event = self.generate_event('uv')
        event.value = uv_index
        if timestamp:
            event.timestamp = timestamp           
        self.send_event(event)
