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
import wfcommon.meteo
import itertools
import logging
import heapq

class BufferCollector(object):
    '''
    Collects events and wait for some rentention time before sending
    them to an underlying collector. This allow for later receiving of events
    dated before the buffered ones. This collector re-orders them.

    This collector replaces the !flush collector to support weather stations
    with internal log.

    [ Properties ]

    collector [collector]:
        The underlying collector receiving the timestamped events in the
        correct order.

    period [numeric] (optional):
        Minimum number of seconds between flush events. Defaults to 600.

    retention [numeric] (optional):
        The retention time (in seconds) for current events before forwarding
        them to give a chance to upcoming "events from the past" to be treated.
        Defaults to 30.
    '''

    collector = None
    period = 600
    retention = 30

    queue = None  # Queue for retained events
    count = itertools.count()
    last_flush = None # Timestamp of the event following the last flush event
    last_receive_past = None # When the last event arrived "from the past"
    last_sent = None # Timestamp of the last event forwarded

    logger = logging.getLogger('collector.buffer')

    def init(self):
        if self.queue is None:
            self.queue = []
            self.retention_delta = datetime.timedelta(0, self.retention)
            self.period_delta = datetime.timedelta(0, self.period)
            self.last_sent = datetime.datetime(2001,1,1)
            self.last_receive_past = datetime.datetime(2001,1,1)

    def send_event(self, event, context={}):
        self.init()
        now = datetime.datetime.now()
        expiry = now - self.retention_delta

        if not hasattr(event, 'timestamp') or event.timestamp is None:
            # If event has no timestamp, give it one.
            event.timestamp = now

        if event.timestamp < expiry:
            self.logger.debug("Got event from past: %s", event)
            # The event is historic, we send it immediately (assuming they come ordered).
            if event.timestamp >= self.last_sent:
                # Send it only if is not older as the last one we sent. Otherwise, discard it.
                self.forward_event(event, context)
                self.last_sent = event.timestamp
                self.last_receive_past = now
        else:
            # Put the event in the retention queue, it is recent enough.
            self.logger.debug("Got a recent %s event, keep it in retention queue", event._type)
            self.push(event)

        # Dump the event queue if we are no more receiving events from the past
        if self.last_receive_past < expiry:
            self.logger.debug("Dumping retention queue.")
            while True:
                event_to_send = self.pop_older(expiry)
                if event_to_send is not None:
                    self.forward_event(event_to_send, context)
                    self.last_sent = event_to_send.timestamp
                else:
                    break

    def push(self, event):
        heapq.heappush(self.queue, (event.timestamp, self.count.next(), event))

    def oldest(self):
        if len(self.queue) > 0:
            (timestamp, count, event) = self.queue[0]
            return event
        else:
            return None

    def pop_older(self, timestamp):
        if len(self.queue) ==0:
            return None
        if(self.queue[0][0] < timestamp):
             (timestamp, count, event) = heapq.heappop(self.queue)
             return event
        else:
             return None

    def forward_event(self, event, context):
        if self.last_flush is None:
            # Initialize flush timer with first event.
            self.last_flush = event.timestamp
        flush_time = self.last_flush + self.period_delta

        if event.timestamp > flush_time:
            # Flushes if needed
            flush_event = FlushEvent()
            flush_event.timestamp = flush_time
            self.do_send(flush_event, context)
            self.last_flush = event.timestamp
        self.do_send(event, context)

    def do_send(self, event, context):
        self.logger.debug("Forwarding event: %s", event)
        self.collector.send_event(event, context)

class FlushEvent(object):
    _type = '_flush'
    def __str__(self):
        return "*FLUSH*"
