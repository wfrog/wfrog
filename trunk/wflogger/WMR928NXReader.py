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

## TODO:  DOCUMENT WMRS928NX serial protocol


import serial
import logging
import time
import threading

class WMR928NXReader (threading.Thread):
    def __init__(self, wxData, config):
        threading.Thread.__init__(self)
        self._wxData = wxData
        self._logger = logging.getLogger('WxLogger.WMR928NXReader')
        ## Configuration
        self.PORT_NUMBER = int(config.get('WMR928NX', 'PORT_NUMBER'))

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def run(self):
        self._logger.info("Thread started")
        while True:
            try:
                self._logger.info("Opening serial port")
                ## Open Serial port
                ser = serial.Serial()
                ser.setBaudrate(9600)
                ser.setParity(serial.PARITY_NONE)
                ser.setByteSize(serial.EIGHTBITS)
                ser.setStopbits(serial.STOPBITS_ONE)
                ser.setPort(self.PORT_NUMBER)
                ser.setTimeout(60)  # 60s timeout
                ser.open()
                ser.setRTS(True)
                ## Do the actual work
                self._logger.info("Serial port open")
                self._run(ser)
            except:
                self._logger.exception("WMR928NX reader exception")

            ## Close serial port connection
            self._logger.critical("Serial port WMR928NX connection failure")
            try:
                ser.close()
                ser = None
            except:
                pass
            ## Wait 10 seconds
            time.sleep(10)

    def _run(self, ser):
        input_buffer = []
        while True:
            buffer = ser.read(10) # Read next 10 bytes and return
            
            if len(buffer)== 0:
                # 60s timeout expired without data received
                self._logger.warning("No data received - reinitializing serial port")
                try:
                    ser.close()
                    input_buffer = []
                    time.sleep(10)
                    ser.open()
                    ser.setRTS(True)
                    self._logger.warning("Serial port reinitialized")
                except:
                    pass
            else:
                # data received and added to input buffer
                n_buffer = map(lambda x: ord(x), buffer)
                self._logger.debug("Serial RAW DATA: %s" % self._list2bytes(n_buffer))
                input_buffer += n_buffer

                # obtain new messages when input_buffer contains at least 20 bytes to process 
                if len(input_buffer) > 20:
                    # Using two bytes of 0xFF as record separators, extract as many
                    # full messages as possible and add them to the message queue.
                    while True:
                        # start by finding the first record separator in the input 
                        startSep = -1
                        for i in range(len(input_buffer)):
                            if input_buffer[i] == 0xff and input_buffer[i + 1] == 0xff:
                                startSep = i
                                break
                        if startSep == -1: 
                            break

                        # find the next most right separator (FF FF), 
                        # which will indicate the end of the record
                        endSep = -1
                        for i in range(startSep + 2, len(input_buffer) - 2):
                            if input_buffer[i] == 0xff and input_buffer[i + 1] == 0xff:
                                endSep = i
                            elif endSep != -1:                                  
                                break
                        if endSep == -1: 
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

