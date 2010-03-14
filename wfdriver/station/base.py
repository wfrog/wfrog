## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <lbovet@windmaster.ch>
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

    def _report_rain(self, total, rate):
        event = self.generate_event('rain')
        event.total = total
        event.rate = rate
        self.send_event(event)

    def _report_wind(self, dirDeg, avgSpeed, gustSpeed):
        event = self.generate_event('wind')
        event.create_child('mean')
        event.mean.dir = dirDeg
        event.mean.speed = avgSpeed
        event.create_child('gust')
        event.gust.dir = dirDeg
        event.gust.speed = gustSpeed
        self.send_event(event)

    def _report_barometer_absolute(self, pressure):
        event = self.generate_event('press')
        event.value = pressure
        self.send_event(event)

    def _report_temperature(self, temp, humidity, sensor):
        event = self.generate_event('temp')
        event.sensor = sensor
        event.value = temp
        self.send_event(event)

        event = self.generate_event('hum')
        event.sensor = sensor
        event.value = humidity
        self.send_event(event)

    def _report_uv(self, uv_index):
        event = self.generate_event('uv')
        event.value = uv_index
        self.send_event(event)
