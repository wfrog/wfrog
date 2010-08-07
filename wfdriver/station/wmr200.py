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

from base import BaseStation
import time
import logging
import threading
import sys

windDirMap = { 0:"N", 1:"NNE", 2:"NE", 3:"ENE",
               4:"E", 5:"ESE", 6:"SE", 7:"SSE",
               8:"S", 9:"SSW", 10:"SW", 11:"WSW",
	       12:"W", 13:"WNW", 14:"NW", 15:"NNW" }
forecastMap = { 0:"Partly Cloudy", 1:"Rainy", 2:"Cloudy", 3:"Sunny",
		4:"Snowy", 5:"Unknown5", 6:"Unknown6", 7:"Unknown7" }

# The USB vendor and product ID of the WMR200. Unfortunately, Oregon
# Scientific is using this combination for several other products as
# well. Checking for it, is not good enough to reliable identify the
# WMR200.
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

    def _search_device(self, vendorId, productId):
      try:
        import usb
      except Exception, e:
        self.logger.warning(e)
        return None
      busses = usb.busses()
      for bus in busses:
        for device in bus.devices:
          if device.idVendor == vendorId and device.idProduct == productId:
               return device 

    def receivePacket(self, devh):
      import usb
      errors = 0
      while True:
        try:
          return devh.interruptRead(usb.ENDPOINT_IN + 1, 0x0000008, 1000)
        except usb.USBError, e:
          if e.args == ('No error',):
            return None
          else:
            self.logger.exception("Exception reading interrupt: "+ str(e))
            errors = errors + 1
            if errors > 3:
              time.sleep(3)
              raise e

    def sendPacket(self, devh, packet):
      import usb
      try:
        devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                        0x000009, packet, 0x000200, timeout=500)
      except Exception, e:
        if e.args != ('No error',):
          self.logger.exception("Can't write request record: "+ str(e))

    def sendCommand(self, devh, command):
      self.sendPacket(devh, [0x01, command, 0x00, 0x00,
	                     0x00, 0x00, 0x00, 0x00])

    def clearReceiver(self, devh):
      while True:
	if self.receivePacket(devh) == None:
	  break

    def run(self, generate_event, send_event):
      import usb

      # Initialize injected functions used by BaseStation
      self.generate_event = generate_event
      self.send_event = send_event
      self.logger.info("Thread started")
      errors = 0
      while True:
        try:
          self.logger.info("USB initialization")
          dev = self._search_device(vendor_id, product_id)

          if dev == None:
            raise Exception("USB WMR200 not found (%04X %04X)" % (vendor_id, product_id))

          devh = dev.open()
          self.logger.info("WMR200 found")

          # Some magic to get the USB connection going. Not sure if all of
          # this is really needed, but I've seen this in the pyUSB
          # documentation.
          devh.claimInterface(0)
          tbuf = devh.getDescriptor(1, 0, 0x12)
          tbuf = devh.getDescriptor(2, 0, 0x09)
          tbuf = devh.getDescriptor(2, 0, 0x22)
          devh.releaseInterface()
          devh.setConfiguration(1)
          devh.claimInterface(0)
          devh.setAltInterface(0)
          time.sleep(0.3)

          # WMR200 Init sequence
          devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                          0x000000A, [], 0x0000000, 0x0000000, 1000)
          devh.getDescriptor(0x22, 0, 0x62)
	  self.clearReceiver(devh)
          self.logger.info("USB WMR200 initialized")
          errors = 0
          self._run(devh)

        except Exception, e:
          self.logger.exception("WMR200 exception: %s" % str(e))

        self.logger.critical("USB WMR200 connection failure")
        errors += 1
        # We we get too frequent errors, bail out.
        if errors >= 3:
          self.logger.fatal("Too many USB errors. Terminating...")
          exit(1)

        # Let's try if we can get the connection going again.
        try:
          devh.reset()
          devh.releaseInterface()
        except Exception, e:
          self.logger.exception("WMR200 USB reset failed: %s" % str(e))
        devh = dev = None

        ## Wait 5 seconds
        time.sleep(5)

    def _run(self, devh):
      frame = []

      while True:
        # Get the next 8 byte packet from the USB device.
	packet = self.receivePacket(devh)

        if packet == None:
          # No more data to read. Send a control message to signal that
          # we are ready for more. If we poll too fast, we get frames
          # with historic data (0xD2 frames).
          time.sleep(5)
          self.sendCommand(devh, 0xD0)
        elif packet[0] > 7:
          # The first octet is always the number of valid octets in the
          # packet. Since a packet can only have 8 bytes, ignore all packets
          # with a larger size value. It must be corrupted.
          self.logger.error("Bad Record: %s" % self._list2bytes(packet))
        else:
          # Append the valid part of the packet to the frame buffer.
          frame += packet[1:packet[0] + 1]
          if frame[0] < 0xD1 or frame[0] > 0xD9:
            # All frames must start with 0xD1 - 0xD9. If the first byte is
            # not within this range, we don't have a proper frame start.
            # Discard all octets and restart with the next packet.
            self.logger.error("Bad frame: %s" % self._list2bytes(frame))
            frame = []
          if frame[0] == 0xD1:
            # Frames starting with 0xD1 are 1 byte frames and contain no
            # further information. Just remove it from the frame buffer.
            frame = frame[1:len(frame) - 1]
          elif len(frame) > 1 and len(frame) >= frame[1]:
            # We have a complete frame. Let's decode it.
            self.logger.debug("Frame: %s" % self._list2bytes(frame))
            self.decodeRecord(frame[0:frame[1]])
            # Put the remainder in the frame. It should be the start of
            # the next frame.
            frame = frame[frame[1]:len(frame)]
          
    def decodeRecord(self, record):
      # The last 2 octets of D2 - D9 frames are always the low and high byte
      # of the checksum. We ignore all frames that don't have a matching
      # checksum.
      if self.checkSum(record[0:len(record)-2],
                       record[len(record) - 2] |
                       (record[len(record) - 1] << 8)) == False:
        return

      type = record[0]
      # We don't care about 0xD2 frames. They only contain historic data.
      if type == 0xD3:
        # 0xD3 frames contain wind related information.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        # Byte 7: Wind direction in steps of 22.5 degrees.
        # 0 is N, 1 is NNE and so on. See windDirMap for complete list.
        dirDeg = (record[7] & 0xF) * 22.5
        # Byte 8: Always 0x0C? Maybe high nible is high byte of gust speed.
        # Byts 9: The low byte of gust speed in 0.1 m/s.
        gustSpeed = (((record[8] >> 4) & 0xF) | record[9]) * 0.36
        # Byte 10: High nibble seems to be low nibble of average speed.
        # Byte 11: Maybe low nibble of high byte and high nibble of low byte
        #          of average speed. Value is in 0.1 m/s
        avgSpeed = ((record[11] << 4) | ((record[10] >> 4) & 0xF)) * 0.36

        self.logger.info("Wind Dir: %s" % windDirMap[record[7]])
        self.logger.info("Gust: %.1f km/h" % gustSpeed)
        self.logger.info("Wind: %.1f km/h" % avgSpeed)

        self._report_wind(dirDeg, avgSpeed, gustSpeed)
      elif type == 0xD4:
        # 0xD4 frames contain rain data
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        # Bytes 7 and 8: high and low byte of the current rainfall rate
        # in 0.1 in/h
        rainRate = ((record[8] << 8) | record[7]) / 3.9370078
        # Bytes 9 and 10: high and low byte of the last hour rainfall in 0.1in
        rainHour = ((record[10] << 8) | record[9]) / 3.9370078
        # Bytes 11 and 12: high and low byte of the last day rainfall in 0.1in
        rainDay = ((record[12] << 8) | record[11]) / 3.9370078
        # Bytes 13 and 14: high and low byte of the total rainfall in 0.1in
        rainTotal = ((record[14] << 8) | record[13]) / 3.9370078

        self.logger.info("Rain Rate: %.1f mm/hr" % rainRate)
        self.logger.info("Rain Hour: %.1f mm" % rainHour)
        self.logger.info("Rain 24h: %.1f mm" % rainDay)
        self.logger.info("Rain Total: %.1f mm" % rainTotal)
        # Bytes 15 - 19 contain the time stamp since the measurement started.
        self.decodeTimeStamp(record[15:20]) 

        self._report_rain(rainTotal, rainRate)
      elif type == 0xD5:
        # 0xD5 frames contain UV data.
        # Untested. I don't have a UV sensor.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        uv = record[7]
        self.logger.info("UV Index: %d" % uv)
        self._report_uv(uv)
      elif type == 0xD6:
        # 0xD6 frames contain forecast and air pressure data.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        # Byte 8: high nibble is probably forecast
        #         low nibble is high byte of pressure.
        # Byte 9: low byte of pressure. Value is in hPa.
        pressure = ((record[8] & 0xF) << 8) | record[7]
        self.logger.info("Forecast1: %s" % forecastMap[(record[8] & 0x70) >> 4])
        self.logger.info("Pressure1: %d hPa" % pressure)
        # Bytes 10 - 11: Similar to bytes 8 and 9, but altitude corrected
        # pressure.
        self.logger.info("Forecast2: %s" % forecastMap[(record[10] & 0x70) >> 4])
        self.logger.info("Pressure2: %d hPa" % ((record[10] & 0xF) * 256 + record[9]))

        self._report_barometer_absolute(pressure)
      elif type == 0xD7:
        # 0xD7 frames contain humidity and temperature data.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        # The historic data can contain data from multiple sensors. I'm not
        # sure if the 0xD7 frames can do too. I've never seen a frame with
        # multiple sensors.
        offset = 7
        rSize = 7
        records = (record[1] - offset + 1) / rSize
        for i in xrange(records):
          # Byte 7: low nibble contains sensor ID. 0 for base station.
          sensor = record[offset + i * rSize] & 0xF
          # Byte 8: probably the high nible contains the sign indicator.
          #         The low nibble is the high byte of the temperature.
          # Byte 9: The low byte of the temperature. The value is in 1/10
          # degrees centigrade.
          temp = (((record[offset + i * rSize + 2] & 0x0F) << 8) +
                  record[offset + i * rSize + 1]) * 0.1
          if record[offset + i * rSize + 2] & 0x80:
            temp = -temp
          # Byte 10: The humidity in percent.
          humidity = record[offset + i * rSize + 3]
          # Bytes 11 and 12: Like bytes 8 and 9 but for dew point.
          dewPoint = (((record[offset + i * rSize + 5] & 0x0F) << 8) +
                      record[offset + i * rSize + 4]) * 0.1
          if record[offset + i * rSize + 5] & 0x80:
            dewPoint = -dewPoint

          self.logger.info("Sensor: %d" % sensor)
          self.logger.info("Temp: %.1f C" % temp)
          self.logger.info("Humidity: %d%%" % humidity) 
          self.logger.info("Dew point: %.1f C" % dewPoint)

          self._report_temperature(temp, humidity, sensor)
        # 0xD8 frames have never been observerd.
        # 0xD9 frames have unknown content.

    def decodeTimeStamp(self, record):
      minutes = record[0]
      hours = record[1]
      day = record[2]
      month = record[3]
      year = record[4]
      date = "20%02d-%02d-%02d %d:%02d" % (year, month, day, hours, minutes)
      self.logger.info("Date: %s", date)

    def checkSum(self, packet, checkSum):
      sum = 0
      for byte in packet:
        sum += byte
      if sum != checkSum:
        self.logger.error("Checksum error: %d instead of %d" % (sum, checkSum))
        return False
      return True

