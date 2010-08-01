## Copyright 2010 Chris Schlaeger <cschlaeger@gmail.com>
##
## This WMR200 driver was modeled after the WMRS200 driver. It contains
## some code fragment from the original WMRS200 file. There portions are
##
## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <laurent.bovet@windmaster.ch>
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

# Protocol information obtained from:
# http://aguilmard.com/phpBB3/viewtopic.php?f=2&t=508&st=0&sk=t&sd=a&start=75

from base import BaseStation
import time
import logging
import threading
import sys

windDirMap = { 0:"N", 1:"NNE", 2:"NE", 3:"ENE", 4:"E", 5:"ESE", 6:"SE", 7:"SSE",
              8:"S", 9:"SSW", 10:"SW", 11:"WSW", 12:"W", 13:"WNW", 14:"NW", 15:"NWN" }
forecastMap = { 0:"Partly Cloudy", 1:"Rainy", 2:"Cloudy", 3:"Sunny", 4:"Snowy" }

vendor_id  = 0xfde
product_id = 0xca01

name = "Oregon Scientific WMR 200"

def detect():
    station = WMR200Station()
    if station._search_device(vendor_id, product_id) is not None:
        return station

class WMR200Station(BaseStation):
    logger = logging.getLogger('station.wmr200')

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def _search_device(self, vendor_id, product_id):
        try:
            import usb
        except Exception, e:
            self.logger.warning(e)
            return None
        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idVendor == vendor_id and dev.idProduct == product_id:
                    return dev

    def run(self, generate_event, send_event):
      import usb

      # Initialize injected functions used by BaseStation
      self.generate_event = generate_event
      self.send_event = send_event
      self.logger.info("Thread started")
      while True:
        try:
          self.logger.info("USB initialization")
          dev = self._search_device(vendor_id, product_id)

          if dev == None:
            raise Exception("USB WMR200 not found (%04X %04X)" % (vendor_id, product_id))

          self.logger.info("USB WMR200 found")
          devh = dev.open()
          self.logger.info("USB WMR200 open")

          if sys.platform in ['linux2']:
            try:
              devh.claimInterface(0)
            except usb.USBError:
              devh.detachKernelDriver(0)
              devh.claimInterface(0)
          elif sys.platform in ['win32']:
            #devh.claimInterface(0)
            self.logger.critical('Windows is not yet supported: devh.claimInterface() fails')
            print 'Windows is not yet supported: devh.claimInterface() fails'
            exit(1)
          else:
            self.logger.critical('Platform "%s" not yet supported' % sys.platform)
            print 'Platform "%s" not yet supported' % sys.platform
            exit(1)

          tbuf = devh.getDescriptor(1, 0, 0x12)
          tbuf = devh.getDescriptor(2, 0, 0x09)
          tbuf = devh.getDescriptor(2, 0, 0x22)
          devh.releaseInterface()
          devh.setConfiguration(1)
          devh.claimInterface(0)
          devh.setAltInterface(0)
          time.sleep(1)

          # WMR200 Init sequence
          devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                          0x000000A, [], 0x0000000, 0x0000000, 1000)
          devh.getDescriptor(0x22, 0, 0x62)
          #devh.interruptRead(0x81, 8, 1000)
          #devh.interruptRead(0x81, 8, 1000)
          devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                          0x0000009,
                          [0x20,0x00,0x08,0x01,0x00,0x00,0x00,0x00],
                          0x0000200, 0x0000000, 1000)

          ## Do the actual work
          self.sendCommand(usb, devh, 0xDB)
          self.logger.info("USB WMR200 initialized")
          self._run(devh)

        except Exception, e:
            self.logger.exception("WMR200 exception: %s" % str(e))

        self.logger.critical("USB WMR200 connection failure")

        ## Wait 2 seconds
        time.sleep(2)

    def _run(self, devh):
      import usb
      inputRecord = []
      outstandingBytes = 0
      state = 0
      errors = 0

      while True:
        try:
          try:
              packet = devh.interruptRead(usb.ENDPOINT_IN + 1,
                                          0x0000008, 5000)
              errors = 0
          except usb.USBError, e:
              if e.args == ('No error',):
                packet = None
              else:
                self.logger.debug("Args: %s" % e.args)
                raise e
        except Exception, e:
          self.logger.exception("Exception reading interrupt: "+ str(e))
          errors = errors + 1
          packet = None
          if errors > 3: break   ## Maximum 3 consecutive errors before reconnection
          time.sleep(3)

        if packet == None:
          # No more data to read. Send a control message to signal that
          # we are ready for more.
          self.sendCommand(usb, devh, 0xD0)
        elif packet[0] > 7:
          # Ignore records with a size larger than 7.
          self.logger.debug("Bad Record: %s" % self._list2bytes(packet))
        else:
          if state == 0:
            # Looking for 0x10 0xD? packets
            inputRecord = []
            if packet[0] == 0x01 and packet[1] == 0xD1:
              self.logger.debug("D1 Record: %s" % self._list2bytes(packet))
            elif packet[0] == 0x01 and packet[1] & 0xF0 == 0xD0:
              self.logger.debug("New Record: %s" % self._list2bytes(packet))
              inputRecord = [ packet[1] ]
              state = 1
            else:
              self.logger.critical("Unknown: %s" % self._list2bytes(packet))
          elif state == 1:
            if packet[1] >= 0xD0:
              self.logger.critical("Record too large: %s" % self._list2bytes(packet))
              inputRecord = [ packet[1] ]
              state = 0
            else:
              self.logger.debug("Length: %s" % self._list2bytes(packet))
              inputRecord += packet[1:packet[0] + 1]
              outstandingBytes = packet[1] - 1 - packet[0]
              if outstandingBytes > 0:
                state = 2
              else:
                state = 0
          elif state == 2:
            self.logger.debug("Data: %s" % self._list2bytes(packet))
            inputRecord += packet[1:packet[0] + 1]
            outstandingBytes -= packet[0]
            if outstandingBytes <= 0:
              self.decodeRecord(inputRecord)
              state = 0
              #if 0xD3 <= inputRecord[0] <= 0xD7:
              #self.requestData(usb, devh)
          else:
            self.logger.critical("Unknown state: %d", state)
            state = 0

    def decodeRecord(self, record):
      type = record[0]
      if type == 0xD3:
        self.decodeTimeStamp(record[2:7])
        dirDeg = record[7] * 22.5
        gustSpeed = record[9] / 3.6
        avgSpeed = (((record[10] & 0xF0) >> 4) | (record[11] & 0xF0)) / 3.6
        self.logger.info("Wind Dir: %s" % windDirMap[record[7]])
        self.logger.info("Gust: %.1f km/h" % gustSpeed)
        self.logger.info("Wind: %.1f km/h" % avgSpeed)
        self._report_wind(dirDeg, avgSpeed, gustSpeed)
      elif type == 0xD4:
        self.decodeTimeStamp(record[2:7])
        rate = record[8] 
        self.logger.info("Rain Rate: %d mm/hr" % rate)
        self.logger.info("Rain Hour: %d mm" % (record[9] * 256 + record[10]))
        self.logger.info("Rain 24h: %.1f mm" % ((record[11] * 256 + record[12]) / 1000.0))
        total = (record[13] * 256 + record[14]) / 1000.0 
        self.logger.info("Rain Total: %.1f mm" % total)
        self.decodeTimeStamp(record[15:20]) 
        self._report_rain(total, rate)
      elif type == 0xD5:
        # Untested. I don't have a UV sensor.
        uv = record[7]
        self.logger.info("UV Index: %d" % uv)
        self._report_uv(uv)
      elif type == 0xD6:
        self.decodeTimeStamp(record[2:7])
        pressure = (record[8] & 0xF) * 256 + record[7]
        self.logger.info("Forecast1: %s" % forecastMap[(record[8] & 0xF0) >> 4])
        self.logger.info("Pressure1: %d hPa" % pressure)
        self.logger.info("Forecast1: %s" % forecastMap[(record[10] & 0xF0) >> 4])
        self.logger.info("Pressure2: %d hPa" % ((record[10] & 0xF) * 256 + record[9]))
        self._report_barometer_absolute(pressure)
      elif type == 0xD7:
        self.decodeTimeStamp(record[2:7])
        offset = 7
        rSize = 7
        records = (record[1] - offset + 1) / rSize
        for i in xrange(records):
          sensor = record[offset + i * rSize] & 0xF
          temp = ((record[offset + i * rSize + 2] & 0x0F) * 256 +
                  record[offset + i * rSize + 1]) * 0.1
          if record[offset + i * rSize + 2] & 0x80:
            temp = -temp
          humidity = record[offset + i * rSize + 3]
          self.logger.info("Sensor: %d" % sensor)
          self.logger.info("Temp: %.1f C" % temp)
          self.logger.info("Humidity: %d%%" % humidity) 
          dewPoint = (record[12] * 256 + record[11]) * 0.1
          self.logger.info("Dew point: %.1f C" % dewPoint)
          self._report_temperature(temp, humidity, sensor)

    def sendCommand(self, usb, devh, command):
      try:
        devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                        0x000009,
                        [0x01,command,0x00,0x00,0x00,0x00,0x00,0x00],
                        0x000200, timeout=100)
      except Exception, e:
        if e.args != ('No error',):
          self.logger.exception("Can't write request record: "+ str(e))
        else:
          self.logger.debug("Timeout: "+ str(e))

    def decodeTimeStamp(self, record):
      minutes = record[0]
      hours = record[1]
      day = record[2]
      month = record[3]
      year = record[4]
      date = "20%02d-%02d-%02d %d:%02d" % (year, month, day, hours, minutes)
      self.logger.info("Date: %s", date)

