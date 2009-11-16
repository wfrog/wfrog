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

# USB connection to WMRS200 has been possible thanks to:
# - help from libusb and libhid distribution lists
# - reference to Oregon WMR200 Driver (Under Dev.)
#      http://www.sdic.ch/innovation/contributions    
#      http://www.sdic.ch/public/downloads/wmr200.zip

## TODO:  DOCUMENT WMRS200 usb protocol
##        CONTROL DISCONNECTION AND RECONNECTION OF WEATHER STATION
##        GENERATE CRITICAL LOG ENTRIES FOR LOW BATTERY

import sys, usb, logging
from WMRS200Parser import WMRS200Parser
from threading import Thread
import time
import sys

vendor_id  = 0xfde
product_id = 0xca01

class WMRS200Reader (Thread):
    def __init__(self, wxData, config):
        Thread.__init__(self)
        self._wxData = wxData
        self._logger = logging.getLogger('WxLogger.WMRS200Reader')

    def _search_device(self, vendor_id, product_id): 
        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idVendor == vendor_id and dev.idProduct == product_id:
                    return dev

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def run(self):
        self._logger.info("Thread started")
        dev = self._search_device(vendor_id, product_id)
        if dev == None:
            self._logger.critical("WMRS200 not found (%04X %04X), Connected devices:" % (vendor_id, product_id))
            for bus in usb.busses():
                for dev in bus.devices:
                    logging.critical("- %04X:%04X" % (dev.idVendor, dev.idProduct))
            exit(1)

        devh = dev.open()

        if sys.platform in ['linux2']:
            try:
                devh.claimInterface(0)
            except usb.USBError:
                devh.detachKernelDriver(0)
                devh.claimInterface(0)
        elif sys.platform in ['win32']:
            #devh.claimInterface(0)
            self._logger.critical('Windows is not yet supported: devh.claimInterface() fails')
            print 'Windows is not yet supported: devh.claimInterface() fails'
            exit(1)            
        else:
            self._logger.critical('Platform "%s" not yet supported' % sys.platform)
            print 'Platform "%s" not yet supported' % sys.platform
            exit(1)
            

        # WMRS200 Init sequence
        devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,       # requestType
                        0x0000009,                                  # request
                        [0x20,0x00,0x08,0x01,0x00,0x00,0x00,0x00],  # buffer
                        0x0000200,                                  # value
                        0x0000000,                                  # index 
                        1000)                                       # timeout


        input_buffer = []

        errors = 0
        while True:
            try:
                packet = devh.interruptRead(usb.ENDPOINT_IN + 1,  # endpoint number 
                                            0x0000008,            # bytes to read
                                            10000)                # timeout
            except Exception, e:
                self._logger.error("Exception reading interrupt: "+ str(e))
                self._logger.error(repr(sys.exc_info()[2]))
                errors = errors + 1
                time.sleep(3)
                if errors > 10:
                    exit(1)
                
            input_buffer += packet[1:packet[0]+1]

            if packet != None:
                if len(packet) > 0:
                    input_buffer += packet[1:packet[0]+1]
                    #logging.debug("USB RAW DATA: %s" % self._list2bytes(packet))

            if len(input_buffer) > 20:
                errors = 0
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
