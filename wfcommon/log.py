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

import optparse
import logging
import logging.handlers

levels = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

class LogConfigurer(object):
    '''Logging Configuration
---------------------

level [debug|info|error|critical]:
    The root level of logging

handlers [dict]:
    Dictionary configuring handlers. Keys are free names, values are:
    - handler: A python loghandler object, the actual log destination.
    - level: Optional log level for this handler.
'''

    def add_options(self, opt_parser):
        opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Issues all debug messages on the console.")
        opt_parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Issues errors on the console.")

    def configure(self, options, config, context):

        formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

        logger = logging.getLogger() # root logger

        level = logging.INFO

        if config.has_key('logging'):

            logging_config = config['logging']

            if logging_config.has_key('level'):
                level = levels[logging_config['level']]

            if logging_config.has_key('format'):
                formatter = logging.Formatter(logging_config['format'])

            if logging_config.has_key('handlers'):
                handlers_config = logging_config['handlers']

                for handler_config in handlers_config.values():
                    handler = handler_config['handler']

                    # Hack to bypass !include element because log handlers are not class instances
                    # (they don't provide __getattribute__
                    # do it recursively
                    if hasattr(handler, '_init'):
                        while hasattr(handler, '_init'):
                            handler = handler._init(context)

                    if handler_config.has_key('level'):
                        handler.setLevel(levels[handler_config['level']])

                    handler.setFormatter(formatter)

                    logger.addHandler(handler)

            # If no handler is specified, by default a RotatingFileHandler with a 
            # {$process.log} filename  (see issue 85)
            else:
                filename = logging_config['filename'] if logging_config.has_key('filename') else 'wfrog'
 
                # Bypass !user elements
                if hasattr(filename, '_init'):
                    while hasattr(filename, '_init'):
                        filename = filename._init(context)

                handler = logging.handlers.RotatingFileHandler(filename = filename, 
                                                               maxBytes = 262144, 
                                                               backupCount = 3)
                handler.setFormatter(formatter)
                logger.addHandler(handler)

        if options.debug or options.verbose:
            if options.debug:
                level=logging.DEBUG
            else:
                level=logging.ERROR
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        logger.setLevel(level)
