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

import config
import copy
import optparse
import logging
import logging.handlers
import units


class RenderEngine(object):
    """Entry point of the rendering"""

    root_renderer = None
    configurer = None
    initial_context = { "version": "0.1", "units" : units.reference }
    initial_data = {}
    daemon = False
    output = False

    ## Logging setup
    LOG_FILENAME = '/var/log/wfrender.log'
    LOG_SIZE = 512000
    LOG_BACKUPS = 4
    logger = logging.getLogger()  ## get root logger so that all properties are transfered to all loggers
    handler = logging.handlers.RotatingFileHandler(
                      filename=LOG_FILENAME,  maxBytes=int(LOG_SIZE), backupCount=int(LOG_BACKUPS))
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    def __init__(self, configurer=None, main=False):
        """Creates the engine using a specific configurer or a yaml configurer if none specified"""
        if configurer:
            self.configurer = configurer
        else:
            if main:
                opt_parser = optparse.OptionParser()
            self.configurer = config.YamlConfigurer(opt_parser)
            if main:
                opt_parser.add_option("-D", "--data", dest="data_string", help="Passes specific data value/pairs to renderers", metavar="key1=value1,key2=value2")
                opt_parser.add_option("-O", dest="output", action="store_true", help="Outputs the result (if any) on standard output")
                (options, args) = opt_parser.parse_args()

                if options.data_string:
                    pairs = options.data_string.split(',')
                    for pair in pairs:
                        pieces = pair.split('=')
                        assert len(pieces) == 2, "Key-value pair not in the form key=value: %s" % pair
                        self.initial_data[pieces[0].strip()] = pieces[1].strip()

                if options.output:
                    self.output=True

        self.reconfigure(options, args)

    def reconfigure(self, options=None, args=[]):
        self.configurer.configure(self,options,args)

    def process(self, data=initial_data, context={}):

        try:
            if self.daemon:
                self.logger.info("Running as daemon")
                while self.daemon:
                    self.logger.debug("Starting root rendering.")
                    current_context = copy.deepcopy(self.initial_context)
                    current_context.update(context)
                    self.root_renderer.render(data, current_context)
            else:
                self.logger.debug("Starting root rendering.")
                current_context = copy.deepcopy(self.initial_context)
                current_context.update(context)
                return self.root_renderer.render(data, current_context)
        except KeyboardInterrupt:
            self.logger.info("Stopping daemon...")
            return
        except AssertionError, e:
            if logging.root.level > logging.DEBUG:
                self.logger.error(e.message)
                return
            else:
                raise
        except Exception, e:
            self.logger.exception(e.message)
            raise
        finally:
            self.daemon = False

if __name__ == "__main__":
    engine = RenderEngine(main=True)
    result = engine.process()
    if engine.output:
        print str(result)
    engine.logger.debug("Finished main()")