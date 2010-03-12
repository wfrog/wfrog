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
import wfcommon.WxUtils

class XmlInput(object):
    '''
    Base class for inputs receiving events as WESTEP XML messages.
    '''
    
    send_event = None
    
    logger = logging.getLogger("input.xml")
    
    def run(self, send_event):
        self.send_event = send_event
        self.do_run()
    
    def process_message(self, message):
        from lxml import objectify
        event = objectify.XML(message)
        event._type = event.tag
        self.logger.debug("Received: "+message)
        self.send_event(event)

class BaseCollector(object):
    '''
    Base class for collectors.
    '''
    
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
                self._report_barometer_sea_level(event.value) 
                # Should be this: must be fixed: self._report_barometer_absolute(event.value, context['altitude'])
        elif event._type == 'temp':
            self._report_temperature(event.value, event.sensor)
        elif event._type == 'hum':
            self._report_humidity(event.value, event.sensor)
        elif event._type == 'uv':
            self._report_uv(event.value)
    
    def _get_mean_temp(self, current_temp):  # Last 12 hours mean temp
        if self._mean_temp != None:
            if (datetime.datetime.now()-self._mean_temp_last_time).seconds < 3600: # New value each hour
                return self._mean_temp
            #TODO: Get last 12-hours mean temp from storage
        
        return current_temp
        
        
    # TODO: Clean that !
    def _report_barometer_absolute(self, pressure, altitude):
        if self._temp_last != None and self._hum_last != None:
            seaLevelPressure = wfcommon.WxUtils.StationToSeaLevelPressure(
                                  pressure, 
                                  altitude, 
                                  self._temp_last, 
                                  self._get_mean_temp(self._temp_last), 
                                  self._hum_last, 
                                  'paDavisVP')
            self._report_barometer_sea_level(seaLevelPressure)
