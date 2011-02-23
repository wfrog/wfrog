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
import datetime

class FlushEvent(object):
    _type = '_flush'
    def __str__(self):
        return "*FLUSH*"

class FlushCollector(object):
    '''
    Forwards incoming events to a wrapped collector and periodically issues
    a 'flush event'. Flush events are issued only together with a forwarded
    event, there is no internal thread and no flushing occurs during periods
    where no events are received. If an event is timestamped and older than
    an already treated event, it is discarded.

    [ Properties ]

    collector [collector]:
        The wrapped collector the events are forwarded to.

    period [numeric] (optional):
        Minimum number of seconds between flush events. Defaults to 10.
    '''

    period = 300
    collector = None

    last_flush_time = None
    max_event_time = datetime.datetime(2001, 01, 01)

    logger = logging.getLogger('collector.flush')

    def send_event(self, event, context={}):
        if self.collector == None:
            raise Exception('Attribute collector must be set')

        now = datetime.datetime.now()

        if hasattr(event, "timestamp"):
            timestamp = event.timestamp
        else:
            timestamp = now

        if timestamp >= self.max_event_time and timestamp >= now - datetime.timedelta(0, self.period):
            self.max_event_time = timestamp
        else:
            self.logger.debug("Discarded old event")
            return

        current_time = time.time()

        # Initialization. Do not flush at startup
        if self.last_flush_time == None:
            self.last_flush_time = current_time

        # Send the event
        self.collector.send_event(event, context)

        # Flush if needed.
        if self.last_flush_time + self.period <= current_time:
            self.logger.debug('Flushing')
            self.last_flush_time = current_time

            self.collector.send_event(FlushEvent(), context)
