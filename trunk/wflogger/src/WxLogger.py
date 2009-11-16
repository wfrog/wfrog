#!/usr/bin/env python

## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <lbovet@windmaster.ch>
##
##  This file is part of WFrog
##
##  WFrog is free software: you can redistribute it and/or modify
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


## Requires to be run as root to access USB weather station

## TODO: investigate how to give permissions to other user to access USB 
##       create init script to start and stop weather logger at startup time

CONFIG_FILE = 'WxLogger.cfg'

import optparse

opt_parser = optparse.OptionParser()
opt_parser.add_option("-f", "--file", dest="config", default=CONFIG_FILE,
               help="Configuration file. Defaults to '" + CONFIG_FILE + "'", metavar="CONFIG_FILE")
(options, args) = opt_parser.parse_args()

## Configuration setup
from ConfigParser import RawConfigParser
config = RawConfigParser()
config.read(options.config)
LOG_FILENAME = config.get('WxLogger','LOG_FILENAME')
LOG_LEVEL = config.get('WxLogger','LOG_LEVEL')
WEATHER_STATION = config.get('WxLogger','WEATHER_STATION')
LOG_SIZE = config.get('WxLogger','LOG_SIZE')
LOG_BACKUPS = config.get('WxLogger','LOG_BACKUPS')

## Logging setup
import logging, logging.handlers
logger = logging.getLogger('WxLogger')
handler = logging.handlers.RotatingFileHandler(
                      filename=LOG_FILENAME,  maxBytes=int(LOG_SIZE), backupCount=int(LOG_BACKUPS))
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)
levels = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}
logger.setLevel(levels.get(LOG_LEVEL.lower(), logging.WARNING))
logger.info("WxLogger INIT")

## Main
if WEATHER_STATION == 'WMR928NX':
    from WMR928NXParser import WMR928NXParser
    from WMR928NXReader import WMR928NXReader
    ## Shared objects
    data = WMR928NXParser(config)
    ## Driver Thread
    r = WMR928NXReader(data, config)
    r.setName('WxReader')
    r.setDaemon(True)
    r.start()
    
elif WEATHER_STATION == 'WMRS200':
    from WMRS200Parser import WMRS200Parser
    from WMRS200Reader import WMRS200Reader
    ## Shared objects
    data = WMRS200Parser(config)
    ## Driver thread
    r = WMRS200Reader(data, config)
    r.setName('WxReader')
    r.setDaemon(True)
    r.start()
    
else:
    logger.critical('Unsupported station "%s"' % WEATHER_STATION)
    print 'Unsupported station "%s"' % WEATHER_STATION
    exit(1)

## Logger thread
from WxProcess import WxProcess 
p = WxProcess(data, config)
p.setName('WxProcess')
p.setDaemon(True)
p.start()

## Wait to exit
raw_input("Press a key to exit")

## Log
logger.info("WxLogger EXIT")
