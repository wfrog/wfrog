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
                4:"Clear Night", 5:"Snowy",
                6:"Partly Cloudy Night", 7:"Unknown7" }
climateSmileys = { 0:"-", 1:":-)", 2:":-(", 3:":-|" }
humidityTrend = { 0:"Stable", 1:"Rising", 2:"Falling", 3:"Undefined" }

usbWait = 0.5

# The USB vendor and product ID of the WMR200. Unfortunately, Oregon
# Scientific is using this combination for several other products as
# well. Checking for it, is not good enough to reliable identify the
# WMR200.
vendor_id  = 0xfde
product_id = 0xca01

name = "Oregon Scientific WMR200"

def detect():
  station = WMR200Station()
  if station.connectDevice(silent_fail=True) is not None:
    return station

class WMR200Station(BaseStation):
    '''
    Station driver for the Oregon Scientific WMR200.
    '''    
    
    logger = logging.getLogger('station.wmr200')

    def __init__(self):
      # The timeout and delay for USB reads and writes in seconds.
      # Should be between 3 and 5
      self.usbTimeout = 3
      # Initialize some statistic counters.
      # The total number of packets.
      self.totalPackets = 0
      # The number of correctly received USB packets.
      self.packets = 0
      # The total number of received data frames.
      self.frames = 0
      # The number of corrupted packets.
      self.badPackets = 0
      # The number of corrupted frames
      self.badFrames = 0
      # The number of checksum errors
      self.checkSumErrors = 0
      # The number of sent requests for data frames
      self.requests = 0
      # The number of USB connection resyncs
      self.resyncs = 0
      # The time when the program was started
      self.start = time.time()
      # The time of the last resync start or end
      self.lastResync = time.time()
      # True if we are (re-)synching with the station
      self.syncing = True
      # The accumulated time in logging mode
      self.loggedTime = 0
      # The accumulated time in (re-)sync mode
      self.resyncTime = 0
      # Counters for each of the differnt data record types (0xD1 -
      # 0xD9)
      self.recordCounters = [ 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
      self.devh = None

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def searchDevice(self, vendorId, productId):
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

    def receivePacket(self):
      import usb
      errors = 0
      while True:
        try:
          time.sleep(0.1)
          packet = self.devh.interruptRead(usb.ENDPOINT_IN + 1, 8, 
                                           self.usbTimeout * 1000)
          self.totalPackets += 1

          # Provide some statistics on the USB connection every 1000
          # packets.
          if self.totalPackets > 0 and self.totalPackets % 1000 == 0:
            self.logStats()

          if len(packet) != 8:
            # Valid packets must always have 8 octets.
            self.badPackets += 1
            self.logger.error("Wrong packet size: %s" %
                              self._list2bytes(packet))
          elif packet[0] > 7:
            # The first octet is always the number of valid octets in the
            # packet. Since a packet can only have 8 bytes, ignore all packets
            # with a larger size value. It must be corrupted.
            self.badPackets += 1
            self.logger.error("Bad packet: %s" % self._list2bytes(packet))
          else:
            # We've received a new packet.
            self.packets += 1
	    errors = 0
            return packet

        except usb.USBError, e:
          if e.args == ('No error',):
	    # Return None in case we hit a timeout or other error.
	    # This will trigger another request for new packets, so we
	    # don't run dry in this method waiting for new packets.
	    return None
          elif e.args == ('error sending control message: Connection timed out',):
            # Seems to be a common problem. We just retry the read.
            self.logger.debug("Hit sender timeout. Retrying.")
            errors += 1
          else:
            self.logger.exception("Exception reading interrupt: "+ str(e))
            self.devh.resetEndpoint(usb.ENDPOINT_IN + 1)
            errors += 1

          if errors > 3:
            raise e
          return None

    def sendPacket(self, packet):
      import usb
      try:
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                             0x000009, packet, 0x000200,
                             timeout = self.usbTimeout * 1000)
      except Exception, e:
        if e.args != ('No error',):
          self.logger.exception("Can't write request record: "+ str(e))

    def sendCommand(self, command):
      self.sendPacket([0x01, command, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    def clearReceiver(self):
      while True:
        if self.receivePacket() == None:
          break

    def connectDevice(self, silent_fail=False):
      import usb

      if silent_fail:
        self.logger.debug("USB initialization")
      else:
        self.logger.info("USB initialization")
      self.syncMode(True)
      self.resyncs += 1
      try:
        dev = self.searchDevice(vendor_id, product_id)

        if dev == None:
          raise Exception("USB WMR200 not found (%04X %04X)" %
                          (vendor_id, product_id))

        self.devh = dev.open()
        self.logger.info("Oregon Scientific weather station found")
        self.logger.info("Manufacturer: %s" % dev.iManufacturer)
        self.logger.info("Product: %s" % dev.iProduct)
        self.logger.info("Device version: %s" % dev.deviceVersion)
        self.logger.info("USB version: %s" % dev.usbVersion)

        self.devh.claimInterface(0)
        time.sleep(usbWait)
        self.devh.setAltInterface(0)
        time.sleep(usbWait)

        # WMR200 Init sequence
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                             0xA, [], 0, 0, self.usbTimeout * 1000)
        time.sleep(usbWait)
        self.devh.getDescriptor(0x22, 0, 0x62)
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                             0x9,
                             [0x20, 0x00, 0x08, 0x01, 0x00, 0x00, 0x00, 0x00],
                             0x200, 0, self.usbTimeout * 1000)

        time.sleep(self.usbTimeout)
        # This command is supposed to clear the WMR200 history
        # memory. We do this to prevent 0xD2 frames.
        self.sendCommand(0xDB)
        # This command is supposed to stop the communication between
        # PC and the station.
        self.sendCommand(0xDF)
        # Ignore any response packets the commands might have generated.
        self.clearReceiver()
        # This command is probably a 'hello' command. The station
        # usually respons with a 0x01 0xD1 packet.
        self.sendCommand(0xDA)
        time.sleep(self.usbTimeout)
        packet = self.receivePacket()
        if packet == None:
          raise Exception("WMR200 did not respond to ping")
        elif packet[0] == 0x01 and packet[1] == 0xD1:
          self.logger.info("Orgon Scientific WMR200 found")
        else:
          raise Exception("Ping answer doesn't match: %s" %
                          self._list2bytes(packet))

        self.clearReceiver()
        self.logger.info("USB connection established")

        return self.devh
      except Exception, e:
        if silent_fail:
           self.logger.debug("WMR200 connect failed: %s" % str(e))
        else:
            self.logger.exception("WMR200 connect failed: %s" % str(e)) 
        self.disconnectDevice()
        return None

    def disconnectDevice(self):
      if self.devh == None:
        return

      try:
        # Tell console the session is finished.
        self.sendCommand(0xDF)
        self.devh.releaseInterface()
        self.logger.info("USB connection closed")
        time.sleep(self.usbTimeout)
      except Exception, e:
        self.logger.exception("WMR200 disconnect failed: %s" % str(e))
      self.devh = None

    def run(self, generate_event, send_event):
      # Initialize injected functions used by BaseStation
      self.generate_event = generate_event
      self.send_event = send_event
      self.logger.info("Thread started")

      while True:
        try:
          if self.devh == None:
            self.connectDevice()
          self.logData()
        except:
          self.logger.error("Re-syncing USB connection")
        self.disconnectDevice()

        if self.usbTimeout < 5:
          self.usbTimeout += 1
        self.logStats()
        # The more often we resync, the less likely we get back in
        # sync. To prevent useless retries, we wait longer the more
        # often we've tried.
        time.sleep(self.resyncs)

    def receiveFrames(self):
      packets = []
      # Wait a bit so the station can generate the data frames.
      time.sleep(self.usbTimeout)
      # Collect packets until we get no more data. By then we should have
      # received one or more frames.
      while True:
        packet = self.receivePacket()
        if packet == None:
          break
        self.logger.debug("Packet: %s" % self._list2bytes(packet))
        # The first octet is the length. Only length octets are valid data.
        packets += packet[1:packet[0] + 1]

      frames = []
      while True:
        self.frames += 1
        if len(packets) == 0:
          # There should be at least one frame.
          if len(frames) == 0:
            self.logger.error("Received empty frame")
            self.badFrames += 1
            return None
          # We've found all the frames in the packets.
          break
        if packets[0] < 0xD1 or packets[0] > 0xD9:
          # All frames must start with 0xD1 - 0xD9. If the first byte is
          # not within this range, we don't have a proper frame start.
          # Discard all octets and restart with the next packet.
          self.logger.error("Bad frame: %s" % self._list2bytes(packets))
          self.badFrames += 1
          break
        if packets[0] == 0xD1 and len(packets) == 1:
          # 0xD1 frames have only 1 octet.
          return packets
        if len(packets) < 2 or len(packets) < packets[1]:
          # 0xD2 - 0xD9 frames use the 2nd octet to specifiy the length of the
          # frame. The length includes the type and length octet.
          self.logger.error("Short frame: %s" % self._list2bytes(packets))
          self.badFrames += 1
          break

        frame = packets[0:packets[1]]
        packets = packets[packets[1]:len(packets)]

        # The last 2 octets of D2 - D9 frames are always the low and high byte
        # of the checksum. We ignore all frames that don't have a matching
        # checksum.
        if self.checkSum(frame[0:len(frame)-2],
                         frame[len(frame) - 2] |
                         (frame[len(frame) - 1] << 8)) == False:
          self.checkSumErrors += 1
          break

        frames.append(frame)

      if len(frames) > 0:
        return frames
      else:
        return None

    def logData(self):
      while True:
        # Requesting the next set of data frames.
        self.sendCommand(0xD0)
        self.requests += 1
        # Get the frames.
        frames = self.receiveFrames()
        if frames == None:
          # This should normally not happen. A request should always generate
          # an answer.
          time.sleep(self.usbTimeout)
        else:
          # Send the received frames to the decoder.
          for frame in frames:
            self.decodeFrame(frame)

    def decodeFrame(self, record):
      self.syncMode(False)
      self.logger.debug("Frame: %s" % self._list2bytes(record))
      type = record[0]
      self.recordCounters[type - 0xD1] += 1
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
        gustSpeed = (((record[8] >> 4) & 0xF) | record[9]) * 0.1
        # Byte 10: High nibble seems to be low nibble of average speed.
        # Byte 11: Maybe low nibble of high byte and high nibble of low byte
        #          of average speed. Value is in 0.1 m/s
        avgSpeed = ((record[11] << 4) | ((record[10] >> 4) & 0xF)) * 0.1

        self.logger.info("Wind Dir: %s" % windDirMap[record[7]])
        self.logger.info("Gust: %.1f m/s" % gustSpeed)
        self.logger.info("Wind: %.1f m/s" % avgSpeed)

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
        self.logger.info("Forecast2: %s" %
                        forecastMap[(record[10] & 0x70) >> 4])
        self.logger.info("Pressure2: %d hPa" %
                        ((record[10] & 0xF) * 256 + record[9]))

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
          smiley = (record[offset + i * rSize] >> 6) & 0x3
          trend = (record[offset + i * rSize] >> 4) & 0x3
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
          self.logger.info("Humidity: %d%%   Trend: %s   Climate: %s" %
                           (humidity, humidityTrend[trend],
                            climateSmileys[smiley]))
          self.logger.info("Dew point: %.1f C" % dewPoint)

          self._report_temperature(temp, humidity, sensor)
      elif type == 0xD8:
        # 0xD8 frames have never been observerd.
        self.logger.info("TODO: 0xD8 frame found: %s" %
                         self._list2bytes(record))
      elif type == 0xD9:
        # 0xD9 frames have unknown content. Maybe we can find out
        # what the bits mean.
        if record[2] != 0 or record[3] != 0 or record[4] != 0 or record[5] != 0:
          self.logger.info("TODO: 0xD9 frame found: %s" %
                           self._list2bytes(record[2:6]))

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

    def logStats(self):
      now = time.time()
      uptime = now - self.start
      self.logger.info("Uptime: %s" % self.durationToStr(uptime))
      if self.totalPackets > 0:
        self.logger.info("Total packets: %d" % self.totalPackets)
        self.logger.info("Good packets: %d (%.1f%%)" %
                          (self.packets,
                          self.packets * 100.0 / self.totalPackets))
        self.logger.info("Bad packets: %d (%.1f%%)" %
                         (self.badPackets,
                          self.badPackets * 100.0 / self.totalPackets))
      if self.frames > 0:
        self.logger.info("Frames: %d" % self.frames)
        self.logger.info("Bad frames: %d (%.1f%%)" %
                         (self.badFrames,
                          self.badFrames * 100.0 / self.frames))
        self.logger.info("Checksum errors: %d (%.1f%%)" %
                         (self.checkSumErrors,
                          self.checkSumErrors * 100.0 / self.frames))
        self.logger.info("Requests: %d" % self.requests)
      self.logger.info("USB timeout: %d" % self.usbTimeout)
      self.logger.info("USB resyncs: %d" % self.resyncs)

      loggedTime = self.loggedTime
      resyncTime = self.resyncTime
      if not self.syncing:
        loggedTime += now - self.lastResync
      else:
        resyncTime += now - self.lastResync
      self.logger.info("Logged time: %s (%.1f%%)" %
                       (self.durationToStr(loggedTime),
                        loggedTime * 100.0 / uptime))
      self.logger.info("Resync time: %s (%.1f%%)" %
                       (self.durationToStr(resyncTime),
                        resyncTime * 100.0 / uptime))
      for i in xrange(9):
        self.logger.info("0x%X records: %8d (%2d%%)" %
                         (0xD1 + i, self.recordCounters[i],
                          self.recordCounters[i] * 100.0 / self.frames))

    def durationToStr(self, sec):
      seconds = sec % 60
      minutes = (sec / 60) % 60
      hours = (sec / (60 * 60)) % 24
      days = (sec / (60 * 60 * 24))
      return ("%d days, %d hours, %d minutes, %d seconds" %
              (days, hours, minutes, seconds))

    def syncMode(self, on):
      now = time.time()
      if self.syncing:
        if not on:
          self.logger.info("*** Switching to log mode ***")
          # We are in sync mode and need to switch to log mode now.
          self.resyncTime += now - self.lastResync
          self.lastResync = now
          self.syncing = False
      else:
        if on:
          self.logger.info("*** Switching to sync mode ***")
          # We are in log mode and need to switch to sync mode now.
          self.loggedTime += now - self.lastResync
          self.lastResync = now
          self.syncing = True

