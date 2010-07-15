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
if __name__ == "__main__": sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

import config
import copy
import optparse
import logging
import logging.handlers
import wfcommon.units
from wfcommon.config import wfrog_version

class RenderEngine(object):
    '''
Root Elements
-------------

context [dict] (optional):
    Contains context values propagated to all renderers during traversal.

renderer [renderer]:
    Root renderer executed at wfrender execution.

logging [logging configuration] (optional):
    See below the Logging Configuration section.
'''

    logger = logging.getLogger('wfrender')

    root_renderer = None
    configurer = None
    initial_context = { "version": wfrog_version, "units" : wfcommon.units.reference }
    initial_data = {}
    daemon = False
    output = False

    config_file = None
    opt_parser = None

    def __init__(self, opt_parser=optparse.OptionParser()):
        """Creates the engine using a specific configurer or a yaml configurer if none specified"""

        self.configurer = config.RendererConfigurer(opt_parser)

        opt_parser.add_option("-D", "--data", dest="data_string", help="Passes specific data value/pairs to renderers", metavar="key1=value1,key2=value2")
        opt_parser.add_option("-O", dest="output", action="store_true", help="Outputs the result (if any) on standard output")
        self.opt_parser = opt_parser

    def configure(self):
        (options, args) = self.opt_parser.parse_args()

        if options.data_string:
            pairs = options.data_string.split(',')
            for pair in pairs:
                pieces = pair.split('=')
                assert len(pieces) == 2, "Key-value pair not in the form key=value: %s" % pair
                self.initial_data[pieces[0].strip()] = pieces[1].strip()

        if options.output:
            self.output=True

        self.reconfigure(options, args, init=True)


    def reconfigure(self, options=None, args=[], init=False):

        self.configurer.configure_engine(self,options, args, init, self.config_file)

    def process(self, config_file, data=initial_data, context={}):

        self.config_file = config_file

        self.configure()

        try:
            if self.daemon:
                self.logger.info("Running as daemon")
                while self.daemon:
                    self.logger.debug("Starting root rendering.")
                    current_context = copy.deepcopy(self.initial_context)
                    current_context.update(context)
                    self.root_renderer.render(data=data, context=current_context)
            else:
                self.logger.debug("Starting root rendering.")
                current_context = copy.deepcopy(self.initial_context)
                current_context.update(context)
                return self.root_renderer.render(data=data, context=current_context)
        except KeyboardInterrupt:
            self.logger.info("Stopping daemon...")
            return
        except AssertionError, e:
            if logging.root.level > logging.DEBUG:
                self.logger.exception(e)
                return
            else:
                raise
        except Exception, e:
            self.logger.exception(e)
            raise
        finally:
            self.daemon = False

    def run(self, config_file='config/wfrender.yaml'):
        self.process(config_file)

if __name__ == "__main__":
    engine = RenderEngine()
    result = engine.run()
    if engine.output:
        print str(result)
    engine.logger.debug("Finished main()")
