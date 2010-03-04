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

import station
import output
import wfcommon.generic
from output import stdio
import optparse
import logging
import inspect
import sys
import yaml
from threading import Thread
from Queue import Queue, Full
import event

def gen(type):
    return event.Event(type)

class Driver(object):
    DEFAULT_CONFIG = "config/wfdriver.yaml"

    logger = logging.getLogger()  ## get root logger so that all properties are transfered to all loggers

    def __init__(self):
        opt_parser = optparse.OptionParser()

        opt_parser.add_option("-f", "--file", dest="config", default=self.DEFAULT_CONFIG,
                  help="Configuration file (in yaml). Defaults to '" + self.DEFAULT_CONFIG + "'", metavar="CONFIG_FILE")
        opt_parser.add_option("-L", action="store_true", dest="help_list", help="Gives the list of possible config !elements in the yaml config file")
        opt_parser.add_option("-H", dest="help_element", metavar="ELEMENT", help="Gives help about a config !element")
        opt_parser.add_option("-e", "--extensions", dest="extension_names", metavar="MODULE1,MODULE2,...", help="Comma-separated list of modules containing custom configuration elements")
        opt_parser.add_option("-q", "--quiet", action="store_true", dest="quiet", help="Issues only errors, nothing else")
        opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Issues all debug messages")

        (options, args) = opt_parser.parse_args()

        if not options.quiet:
            if options.debug:
                level=logging.DEBUG
            else:
                level=logging.INFO
            logging.basicConfig(level=level, format="%(levelname)s [%(name)s] %(message)s")

        if options.extension_names:
            for ext in options.extension_names.split(","):
                self.logger.debug("Loading extension module '"+ext+"'")
                self.extensions[ext]=__import__(ext)
        if options.help_list:
            print "\n Elements you can use in the yaml config file:\n"
            print "Stations"
            print "--------\n"
            self.print_help(station)
            print "Output"
            print "------\n"
            self.print_help(output)
            print "Generic Elements"
            print "----------------\n"
            self.print_help(wfcommon.generic)            
            if options.extension_names:
                print "Extensions"
                print "----------\n"
                for ext in self.extensions:
                    print "[" + ext + "]"
                    print
                    self.print_help(self.extensions[ext])
            print " Use option -H ELEMENT for help on a particular element"
            sys.exit()
        if options.help_element:
            element = options.help_element
            if element[0] is not '!':
                element = '!' + element
            desc = {}
            desc.update(self.get_help_desc(station))
            desc.update(self.get_help_desc(output))
            desc.update(self.get_help_desc(wfcommon.generic))
            if len(desc) == 0:
                for ext in self.extensions:
                    desc.update(self.get_help_desc(self.extensions[ext]))
            if desc.has_key(element):
                print
                print element
                print "    " + desc[element]
                print
            else:
                print "Element "+element+" not found or not documented"
            sys.exit()

        # default
        self.output = stdio.StdioOutput()
        self.queue_size = 10

        config = yaml.load( file(options.config, "r") )

        self.station = config['station']
        if config.has_key('output'):
            self.output = config['output']
        if config.has_key('queue_size'):
            self.queue_size = config['queue_size']

        self.event_queue = Queue(self.queue_size)

    def print_help(self, module):
        desc = self.get_help_desc(module, summary=True)
        sorted = desc.keys()
        sorted.sort()
        for k in sorted:
            print k
            print "    " + desc[k]
            print

    def get_help_desc(self, module, summary=False):
        self.logger.debug("Getting info on module '"+module.__name__+"'")
        elements = inspect.getmembers(module, lambda l : inspect.isclass(l) and yaml.YAMLObject in inspect.getmro(l))
        desc={}
        for element in elements:
            self.logger.debug("Getting doc of "+element[0])
            # Gets the documentation of the first superclass
            fulldoc=inspect.getmro(element[1])[1].__doc__
            firstline=fulldoc.split(".")[0]
            self.logger.debug(firstline)
            if summary:
                desc[element[1].yaml_tag] = firstline
            else:
                desc[element[1].yaml_tag] = fulldoc
        return desc

    def enqueue_event(self,event):
        self.logger.debug('Queue size: '+str(self.event_queue.qsize()))
        try:
            self.event_queue.put(event, block=False)
        except Full:
            raise Exception('Consumer of events is dead or not consuming quickly enough')

    def output_loop(self):
        while True:
            event = self.event_queue.get(block=True)
            self.output.send_event(event)

    def run(self):

        # Start the logger thread
        logger_thread = Thread(target=self.output_loop)
        logger_thread.setDaemon(True)
        logger_thread.start()

        self.station.run(gen, self.enqueue_event)

if __name__ == "__main__":
    driver = Driver()
    driver.logger.debug("Started main()")
    driver.run()
    driver.logger.debug("Finished main()")
