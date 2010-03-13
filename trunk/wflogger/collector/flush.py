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
import time

class FlushEvent(object):
    _type = '_flush'
    def __str__(self):
        return "*FLUSH*"

class FlushCollector(object):
    '''
    Forwards events to a wrapped collector and periodically issues
    a 'flush event'.
    
    [ Properties ]
            
    collector [collector]:
        The wrapped collector the events are sent to.
        
    period [numeric] (optional):
        Minimal number of seconds between flush events. Defaults to 300.
    '''
    
    period = 300
    collector = None
    
    last_flush_time = None
    
    logger = logging.getLogger('collector.flush')
    
    def send_event(self, event, context={}):
        if self.collector == None:
            raise Exception('Attribute collector must be set')
        
        current_time = time.time()
        
        # Initialization. Do not flush at startup
        if self.last_flush_time == None:
            self.last_flush_time = current_time
        
        # First flush if needed.
        if self.last_flush_time + self.period <= current_time:
            self.logger.debug('Flushing')
            self.last_flush_time = current_time
            
            self.collector.send_event(FlushEvent(), context)
        
        # Then send the event (but not the ticks).
        if not event._type == '_tick':
            self.collector.send_event(event, context)
