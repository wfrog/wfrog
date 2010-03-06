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

def add_options(opt_parser):
    opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Issues all debug messages on the console.")
    
def configure(options, config, context):

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
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
                if hasattr(handler, '_init'):
                    handler = handler._init(context)
                
                if handler_config.has_key('level'):
                    handler.setLevel(levels[handler_config['level']])
                
                handler.setFormatter(formatter)
                
                logger.addHandler(handler)            
    
    if options.debug:
        level=logging.DEBUG
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        handler.setFormatter(formatter)
        
    logger.setLevel(level)

    
