#!/usr/bin/python

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

# Before loading other modules add wfrog directory to sys.path to be able to use wfcommon
import os.path
import sys
if __name__ == "__main__": sys.path.append(os.path.abspath(sys.path[0] + '/..'))

import input
import collector
import wfcommon.generic
import wfcommon.storage
import optparse
import logging
import time
import wfcommon.config
import wfdriver.wfdriver
#import wfrender.wfrender
from threading import Thread
from Queue import Queue, Full
import copy

def gen(type):
    return event.Event(type)

class FlushEvent(object):
    _type = '_flush'
    def __str__(self):
        return "*FLUSH*"

class Logger(object):

    logger = logging.getLogger('datalogger')

    queue_size=10
    period = 300

    embedded = {}
    context = None

    def __init__(self):

        # Prepare the configurer
        module_map = (
            ( "Inputs" , input ),
            ( "Collectors" , collector ),
            ( "Storages" , wfcommon.storage ),
            ( "Generic Elements", wfcommon.generic)
        )
        configurer = wfcommon.config.Configurer("config/wflogger.yaml", module_map)

        # Initilize the option parser
        opt_parser = optparse.OptionParser()
        configurer.add_options(opt_parser)

        # Parse the options and create object trees from configuration
        (options, args) = opt_parser.parse_args()
        (config, self.context) = configurer.configure(options, self)

        # Initialize the logger from object trees

        self.input = config['input']
        self.collector = config['collector']

        if config.has_key('queue_size'):
            self.queue_size = config['queue_size']
        if config.has_key('period'):
            self.period = config['period']
        if config.has_key('embed'):
            self.embedded = config['embed']

        self.event_queue = Queue(self.queue_size)

    def enqueue_event(self, event):
        self.logger.debug('Queue size: '+str(self.event_queue.qsize()))
        try:
            self.event_queue.put(event, block=False)
        except Full:
            self.logger.critical('Consumer of events is dead or not consuming quickly enough')

    def input_loop(self):
        self.input.run(self.enqueue_event)

    def output_loop(self):
        context = copy.deepcopy(self.context)
        while True:
            event = self.event_queue.get(block=True)
            self.collector.send_event(event, context=context)

    def flush_loop(self):
        while True:
            time.sleep(self.period)
            event = FlushEvent()
            self.enqueue_event(event)

    def run(self):

        # Start the logger thread
        logger_thread = Thread(target=self.output_loop)
        logger_thread.setDaemon(True)
        logger_thread.start()

        # Start the input thread
        input_thread = Thread(target=self.input_loop)
        input_thread.setDaemon(True)
        input_thread.start()

        # Start the embedded processes
        if self.embedded.has_key('wfdriver'):
            driver = wfdriver.wfdriver.Driver(self.embedded['wfdriver']['config'])
            driver_thread = Thread(target=driver.run)
            driver_thread.setDaemon(True)
            driver_thread.start()
        #if self.embedded.has_key('wfrender'):
            #renderer = wfrender.wfrender.Driver(embedded['wfrender']['config'])
            #renderer_thread = Thread(target=renderer.run)
            #renderer_thread.setDaemon(True)
            #renderer_thread.start()

        # Start the flush thread
        self.flush_loop()


if __name__ == "__main__":
    driver = Logger()
    driver.logger.debug("Started main()")
    driver.run()
    driver.logger.debug("Finished main()")
