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

import config
import copy
import optparse
import logging

class RenderEngine(object):
    """Entry point of the rendering"""

    root_renderer = None
    configurer = None
    initial_context = None
    initial_data = {}
    daemon = False

    logger = logging.getLogger("engine")

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
                (options, args) = opt_parser.parse_args()

                if options.data_string:
                    pairs = options.data_string.split(',')
                    for pair in pairs:
                        pieces = pair.split('=')
                        assert(len(pieces)==2, "Key-value pair not in the form key=value: ", pair)
                        self.initial_data[pieces[0].strip()] = pieces[1].strip()
        self.reconfigure(options, args)

    def reconfigure(self, options=None, args=[]):
        self.configurer.configure(self,options,args)

    def process(self, data=initial_data, context={}):
        current_context = copy.deepcopy(self.initial_context)
        current_context.update(context)
        try:
            if self.daemon:
                self.logger.info("Running as daemon")
                while self.daemon:
                    self.logger.debug("Starting root rendering.")
                    self.root_renderer.render(data, current_context)
            else:
                self.logger.debug("Starting root rendering.")
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
        finally:
            self.daemon = False

if __name__ == "__main__":
    engine = RenderEngine(main=True)
    result = engine.process()
