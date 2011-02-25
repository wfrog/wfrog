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

import sys
import logging

stations = []

class AutoDetectStation(object):

    '''
    Auto detect station. Station driver class must implement the unbound
    boolean method 'detect' and must be register in the 'stations' list
    in order to be detected.

    [ Properties ]

    debug [true|false] (optional):
        If true also detects debug stations like simulators. Defaults to 'true'.
        Set it to 'false' in productive installation to ensure having only
        meaningful data even if the station fails.
    '''

    logger = logging.getLogger('station.auto')

    debug = True

    def run(self, generate_event, send_event):
        detected_station = None
        self.logger.info("Discovering stations...")

        for station in stations:
            if hasattr(station, 'name'):
                name = station.name
            else:
                name = '<unknown>'
            if hasattr(station, 'detect'):
                detected_result = station.detect()
                if self.detected(detected_result):
                    self.logger.info("Detected station "+name)
                    detected_station = detected_result
                    break
        if detected_station is None:
            self.logger.error("Could not detect any station connected to this computer")
            sys.exit(1)
        detected_station.run(generate_event, send_event)

    def detected(self, detected_result):
        # If level is debug and debug station are not excluded
        if detected_result and \
            hasattr(detected_result, 'debug_station') and \
            detected_result.debug_station and \
            not (self.logger.isEnabledFor(logging.DEBUG) and \
            self.debug):
            return False
        else:
            return detected_result
