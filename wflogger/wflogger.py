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
from threading import Thread
from Queue import Queue, Full
import copy

def gen(type):
    return event.Event(type)

class Logger(object):
    '''
Root Elements
-------------

context [dict] (optional):
    Contains context values propagated to input and collector.

input [input]:
    Source of events, usually a listening object receiving events
    from the driver.

collector [collector]:
    Where events are forwarded to be logged. Events are forwarded
    one-by-one, so no concurrency must be handled by the collector.

embed [dict] (optional):
    Dictionary specifying which module must be run embedded in the same
    process as the logger. Keys can be 'wfdriver' or 'wfrender'. Values
    are dictionaries with the following key-values:
    - config: specifies the configuration file of the embedded module.

logging [logging configuration] (optional):
    See below the Logging Configuration section.
'''

    logger = logging.getLogger('wflogger')

    queue_size=10

    embedded = {}
    context = None

    config_file = None
    opt_parser = None

    def __init__(self, opt_parser=optparse.OptionParser()):

        # Prepare the configurer
        module_map = (
            ( "Inputs" , input ),
            ( "Collectors" , collector ),
            ( "Storages" , wfcommon.storage ),
            ( "Generic Elements", wfcommon.generic)
        )
        self.configurer = wfcommon.config.Configurer(module_map)

        self.configurer.add_options(opt_parser)
        self.opt_parser = opt_parser

    def configure(self, config_file):
        # Parse the options and create object trees from configuration
        (options, args) = self.opt_parser.parse_args()
        (config, self.context) = self.configurer.configure(options, self, config_file)

        self.config_file = self.configurer.config_file

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
        self.logger.debug("Got '%s' event. Queue size: %d", event._type, self.event_queue.qsize())
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
            try:
                self.collector.send_event(event, context=context)
            except Exception:
                self.logger.exception("Could not send event to "+str(self.collector))

    def run(self, config_file="config/wflogger.yaml"):
        self.configure(config_file)

        # Start the logger thread
        logger_thread = Thread(target=self.output_loop)
        logger_thread.setDaemon(True)
        logger_thread.start()

        # Start the input thread
        input_thread = Thread(target=self.input_loop)
        input_thread.setDaemon(True)
        input_thread.start()

        dir_name = os.path.dirname(self.config_file)

        # Start the embedded processes
        if self.embedded.has_key('wfdriver'):
            self.logger.debug("Starting embedded wfdriver")
            import wfdriver.wfdriver
            driver = wfdriver.wfdriver.Driver(self.opt_parser)
            driver_thread = Thread(target=driver.run, kwargs={'config_file':os.path.join(dir_name, self.embedded['wfdriver']['config'])})
            driver_thread.setDaemon(True)
            driver_thread.start()
        if self.embedded.has_key('wfrender'):
            self.logger.debug("Starting embedded wfrender")
            import wfrender.wfrender
            renderer = wfrender.wfrender.RenderEngine(self.opt_parser)
            renderer_thread = Thread(target=renderer.process, args=[os.path.join(dir_name, self.embedded['wfrender']['config']), True] )
            renderer_thread.setDaemon(True)
            renderer_thread.start()

        # Wait for ever
        while True:
            time.sleep(99999999)


if __name__ == "__main__":
    logger = Logger()
    logger.logger.debug("Started main()")
    logger.run()
    logger.logger.debug("Finished main()")
