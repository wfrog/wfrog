## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <laurent.bovet@windmaster.ch>
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

## TODO:  DOCUMENT WMRS200 usb protocol
##        CONTROL DISCONNECTION AND RECONNECTION OF WEATHER STATION
##        GENERATE CRITICAL LOG ENTRIES FOR LOW BATTERY

import serial, logging
from threading import Thread

# So far only tested on windows. 

class WMR928NXReader (Thread):
    def __init__(self, wxData, config):
        Thread.__init__(self)
        self._wxData = wxData
        self._logger = logging.getLogger('WxLogger.WMR928NXReader')
        ## Configuration
        self.PORT_NUMBER = config.get('WMR928NX', 'PORT_NUMBER')

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def run(self):
        self._logger.info("Thread started")

        ser = serial.Serial()
        ser.baudrate = 9600
        ser.port = self.PORT_NUMBER
        ser.timeout = 5
        try:
            ser.open()
        except:
            self._logger.critical("Cannot open port %d" % self.PORT_NUMBER)
        ser.setRTS(True)                     

        input_buffer = []
        while True:
            buffer = ser.read(100)
            
            #logging.debug("USB RAW DATA: %s" % self._list2bytes(packet))
            if len(buffer) > 0:
                input_buffer += map(lambda x: ord(x), buffer)

                if len(input_buffer) > 20:
                    # Using two bytes of 0xFF as record separators, extract as many
                    # full messages as possible and add them to the message queue.
                    while True:
                        # start by finding the first record separator in the input 
                        startSep = -1
                        for i in range(len(input_buffer) - 2):
                            if input_buffer[i] == 0xff and input_buffer[i + 1] == 0xff:
                                startSep = i
                                break
                        if startSep < 0: 
                            break

                        # find the next separator, which will indicate the end of the 1st record
                        endSep = -1
                        for i in range(startSep + 2, len(input_buffer) - 2):
                            if input_buffer[i] == 0xff and input_buffer[i + 1] == 0xff:
                                endSep = i;
                                break
                        if endSep < 0: 
                            break
                        if startSep > 0: 
                            self._logger.debug("Ignored %d bytes in input", startSep)

                        length = endSep - startSep - 2
                        if length == 0:
                            self._logger.debug("Warning: zero length message in input")
                        else:
                            # Parse the message
                            self._wxData.parse_record(input_buffer[startSep + 2 : endSep])

                        # remove this message from the input queue
                        input_buffer = input_buffer[endSep:]
