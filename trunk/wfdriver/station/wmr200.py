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

# There is no known official documentation for the USB protocol that
# the WMR200 uses to exchange weather data with a PC. Too bad that
# Oregon Scientific does not understand the benefits of open
# protocols. The code in this WMR200 driver is based on a collective
# reverse engineering effort. Most of the decoding is probably
# accurate, but minor bugs cannot be ruled out. Please submit a bug
# report at http://code.google.com/p/wfrog/issues/list in case you see
# odd behaviour. The report must include the full debug output of
# the logger.
#
#    cd wflogger
#    ./wflogger -d 2> wmr200.log
#
# Attach the wmr200.log file and include the corresponding actual
# readings from your WMR200 display. I'd like to thank the folks at
# http://aguilmard.com/phpBB3/viewtopic.php?f=2&t=508&st=0&sk=t&sd=a&sid=4f64fc06860272367eb6c9e408acabe1
# for their previous work. Also, the work from Denis Ducret
# <info@windspots.com> was very helpful to write this driver. His data
# logger can be found at http://www.sdic.ch/innovation/contributions.

from base import BaseStation
import time
import datetime
import logging
import threading
import platform
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
usbTimeout = 3.0

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

class WMR200Error(IOError):
  "Used to signal an error condition"

class WMR200Station(BaseStation):
    '''
    Station driver for the Oregon Scientific WMR200.
    '''

    logger = logging.getLogger('station.wmr200')

    def __init__(self):
      # The delay between data requests. This value will be adjusted
      # automatically.
      self.pollDelay = 2.5
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
      # Difference between the PC clock and the station clock in
      # minutes.
      self.clockDelta = 0
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

    # After each 0xD0 command, the station will provide a set of data
    # packets. The first byte of each packet indicates the number of
    # valid octects in the packet. The length octect is not counted,
    # so the maximum value for the first octet is 7. The remaining
    # octets to fill the 8 octests are invalid. The actual weather
    # data is contained in data frames that may spread over several
    # packets. If the read times-out, we have received the final
    # packet of the last frame.
    def receivePacket(self):
      import usb
      errors = 0
      while True:
        try:
          packet = self.devh.interruptRead(usb.ENDPOINT_IN + 1, 8,
                                           int(self.pollDelay * 1000))
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
            self.logger.debug("Packet: %s" % self._list2bytes(packet))
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
            raise WRM200Error("Resync required")
          return None

    def sendPacket(self, packet):
      import usb
      try:
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                             0x9, packet, 0x200,
                             timeout = int(usbTimeout * 1000))
      except usb.USBError, e:
        if e.args != ('No error',):
          self.logger.exception("Can't write request record: "+ str(e))

    # The WMR200 is known to support the following commands:
    # 0xD0: Request next set of data frames.
    # 0xDA: Check if station is ready.
    # 0xDB: Clear historic data from station memory.
    # 0xDF: Not really known. Maybe to signal end of data transfer.
    def sendCommand(self, command):
      # All commands are only 1 octect long.
      self.sendPacket([0x01, command, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
      self.logger.debug("Command: %02X" % command)

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
          raise WMR200Error("USB WMR200 not found (%04X %04X)" %
                            (vendor_id, product_id))

        self.devh = dev.open()
        self.logger.info("Oregon Scientific weather station found")
        self.logger.info("Manufacturer: %s" % dev.iManufacturer)
        self.logger.info("Product: %s" % dev.iProduct)
        self.logger.info("Device version: %s" % dev.deviceVersion)
        self.logger.info("USB version: %s" % dev.usbVersion)

        # The following init sequence was adapted from Denis Ducret's
        # wmr200log program.
        if platform.system() is 'Windows':
            self.devh.setConfiguration(1)
        self.devh.claimInterface(0)
        time.sleep(usbWait)
        self.devh.setAltInterface(0)
        time.sleep(usbWait)

        self.devh.getDescriptor(1, 0, 0x12)
        self.devh.getDescriptor(2, 0, 0x9)
        self.devh.getDescriptor(2, 0, 0x22)
        time.sleep(usbWait)

        self.devh.releaseInterface()
        self.devh.setConfiguration(1)
        self.devh.claimInterface(0)
        self.devh.setAltInterface(0)
        time.sleep(usbWait)

        # WMR200 Init sequence
        self.logger.debug("Sending 0xA message")
        self.devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,
                             0xA, [], 0, 0, int(usbTimeout * 1000))
        time.sleep(usbWait)
        self.devh.getDescriptor(0x22, 0, 0x62)
        # Ignore any response packets the commands might have generated.
        self.clearReceiver()

        self.logger.debug("Sending init message")
        self.sendPacket([0x20, 0x00, 0x08, 0x01, 0x00, 0x00, 0x00, 0x00])
        # Ignore any response packets the commands might have generated.
        self.clearReceiver()


        # This command clears the WMR200 history memory. We can use it
        # if we don't care about old data that has been logged to the
        # station memory.
        # self.sendCommand(0xDB)
        # self.clearReceiver()

        # This command is supposed to stop the communication between
        # PC and the station.
        self.sendCommand(0xDF)
        # Ignore any response packets the commands might have generated.
        self.clearReceiver()

        # This command is a 'hello' command. The station respons with
        # a 0x01 0xD1 packet.
        self.sendCommand(0xDA)
        packet = self.receivePacket()
        if packet == None:
          self.logger.error("Station did not respond properly to WMR200 ping")
          return None
        elif packet[0] == 0x01 and packet[1] == 0xD1:
          self.logger.info("Station identified as WMR200")
        else:
          self.logger.error("Ping answer doesn't match: %s" %
                            self._list2bytes(packet))
          return None

        self.clearReceiver()
        self.logger.info("USB connection established")

        return self.devh
      except usb.USBError, e:
        if silent_fail:
           self.logger.debug("WMR200 connect failed: %s" % str(e))
        else:
            self.logger.exception("WMR200 connect failed: %s" % str(e))
        self.disconnectDevice()
        return None

    def disconnectDevice(self):
      import usb

      if self.devh == None:
        return

      try:
        # Tell console the session is finished.
        self.sendCommand(0xDF)
        try:
          self.devh.releaseInterface()
        except ValueError:
          None
        self.logger.info("USB connection closed")
        time.sleep(usbTimeout)
      except usb.USBError, e:
        self.logger.exception("WMR200 disconnect failed: %s" % str(e))
      self.devh = None

    def increasePollDelay(self):
      if self.pollDelay < 5.0:
        self.pollDelay += 0.1
        self.logger.debug("Polling delay increased: %.1f" % self.pollDelay)

    def decreasePollDelay(self):
      if self.pollDelay > 0.5:
        self.pollDelay -= 0.1
        self.logger.debug("Polling delay decreased: %.1f" % self.pollDelay)

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
        except WMR200Error, e:
          self.logger.error("Re-syncing USB connection")
        self.disconnectDevice()

        self.logStats()
        # The more often we resync, the less likely we get back in
        # sync. To prevent useless retries, we wait longer the more
        # often we've tried.
        time.sleep(self.resyncs)

    # The weather data is contained in frames of variable length. The
    # first octet of each frame indicates the type of the frame. Valid
    # types are 0xD1 to 0xD9. The 0xD1 frame is only 1 octet long. It
    # is sent as a response to a 0xDA command. The 0xD2 - 0xD9 frames
    # are responses to a 0xD0 command. 0xD8 frames are probably not
    # used. The meaning of 0xD9 frames is currently unknown.
    def receiveFrames(self):
      packets = []
      # Collect packets until we get no more data. By then we should have
      # received one or more frames.
      while True:
        packet = self.receivePacket()
        if packet == None:
          break
        # The first octet is the length. Only length octets are valid data.
        packets += packet[1:packet[0] + 1]

      frames = []
      while True:
        if len(packets) == 0:
          # There should be at least one frame.
          if len(frames) == 0:
            # If we get empty frames we increase the polling delay a
            # bit.
            self.increasePollDelay()
            return None
          # We've found all the frames in the packets.
          break

        self.frames += 1

        if packets[0] < 0xD1 or packets[0] > 0xD9:
          # All frames must start with 0xD1 - 0xD9. If the first byte is
          # not within this range, we don't have a proper frame start.
          # Discard all octets and restart with the next packet.
          self.logger.error("Bad frame: %s" % self._list2bytes(packets))
          self.badFrames += 1
          break

        if packets[0] == 0xD1 and len(packets) == 1:
          # 0xD1 frames have only 1 octet.
          frame = packets[0:1]
          packets = packets[1:len(packets)]
          frames.append(frame)
        elif len(packets) < 2 or len(packets) < packets[1]:
          # 0xD2 - 0xD9 frames use the 2nd octet to specifiy the length of the
          # frame. The length includes the type and length octet.
          self.logger.error("Short frame: %s" % self._list2bytes(packets))
          self.badFrames += 1
          break
        else:
          # This is for all frames with length byte and checksum.
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
        if len(frames) > 2:
          # If we get more than 2 frames at a time we increase the
          # polling frequency again.
          self.decreasePollDelay()
        return frames
      else:
        return None

    def logData(self):
      while True:
        # Requesting the next set of data frames by sending a D0
        # command.
        self.sendCommand(0xD0)
        self.requests += 1
        # Get the frames.
        frames = self.receiveFrames()
        if frames == None:
          # The station does not have any data right now. Just wait a
          # bit and ask again.
          time.sleep(usbTimeout)
        else:
          # Send the received frames to the decoder.
          for frame in frames:
            self.decodeFrame(frame)

    def decodeFrame(self, record):
      self.syncMode(False)
      self.logger.debug("Frame: %s" % self._list2bytes(record))
      type = record[0]
      self.recordCounters[type - 0xD1] += 1
      if type == 0xD2:
        self.logger.info(">>>>> Historic Data Record >>>>>")
        # We ignore 0xD2 frames for now. They only contain historic data.
        # Byte 2 - 6 contains the time stamp.
        timeStamp = self.decodeTimeStamp(record[2:7], '@Time', False)
        # Bytes 7 - 19 contain rain data
        rainTotal, rainRate = self.decodeRain(record[7:20])
        # Bytes 20 - 26 contain wind data
        dirDeg, avgSpeed, gustSpeed, windchill = self.decodeWind(record[20:27])
        # Byte 27 contains UV data
        uv = self.decodeUV(record[27])
        # Bytes 28 - 32 contain pressure data
        pressure = self.decodePressure(record[28:32])
        # Byte 32: Unknown
        if record[32] != 1:
          self.logger.info("TODO: History byte 32: %02X" % record[32])
        # Bytes 33 - end contain temperature and humidity data
        data = self.decodeTempHumid(record[33:len(record) - 2])
        self.logger.info("<<<<< End Historic Record <<<<<")

        # TODO: Find out how "no wind data" is encoded and ignore it.
        self._report_wind(dirDeg, avgSpeed, gustSpeed, timeStamp)
        # TODO: Find out how "no rain data" is encoded and ignore it.
        self._report_rain(rainTotal, rainRate, timeStamp)
        # If no UV data is present, the value is 0xFF.
        if uv != 0xFF:
          self._report_uv(uv, timeStamp)
        self._report_barometer_absolute(pressure, timeStamp)
        for d in data:
          temp, humidity, sensor = d
          self._report_temperature(temp, humidity, sensor, timeStamp)
      elif type == 0xD3:
        # 0xD3 frames contain wind related information.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        dirDeg, avgSpeed, gustSpeed, windchill = self.decodeWind(record[7:15])
        self._report_wind(dirDeg, avgSpeed, gustSpeed)
      elif type == 0xD4:
        # 0xD4 frames contain rain data
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        rainTotal, rainRate = self.decodeRain(record[7:21])
        self._report_rain(rainTotal, rainRate)
      elif type == 0xD5:
        # 0xD5 frames contain UV data.
        # Untested. I don't have a UV sensor.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        uv = self.decodeUV(record[7])
        self._report_uv(uv)
      elif type == 0xD6:
        # 0xD6 frames contain forecast and air pressure data.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        pressure = self.decodePressure(record[7:11])
        self._report_barometer_absolute(pressure)
      elif type == 0xD7:
        # 0xD7 frames contain humidity and temperature data.
        # Byte 2 - 6 contains the time stamp.
        self.decodeTimeStamp(record[2:7])
        data = self.decodeTempHumid(record[7:14])
        temp, humidity, sensor = data[0]
        self._report_temperature(temp, humidity, sensor)
      elif type == 0xD8:
        # 0xD8 frames have never been observed.
        self.logger.info("TODO: 0xD8 frame found: %s" %
                         self._list2bytes(record))
      elif type == 0xD9:
        # 0xD9 frames have unknown content. Maybe we can find out
        # what the bits mean.
        if record[2] != 0 or record[3] != 0 or record[4] != 0 or record[5] != 0:
          self.logger.info("TODO: 0xD9 frame found: %s" %
                           self._list2bytes(record[2:6]))

    def decodeTimeStamp(self, record, label = 'Time', check = True):
      minutes = record[0]
      hours = record[1]
      day = record[2]
      month = record[3]
      year = 2000 + record[4]
      date = "%04d-%02d-%02d %d:%02d" % (year, month, day, hours, minutes)
      self.logger.info("%s: %s" % (label, date))
      ts = time.mktime((year, month, day, hours, minutes, 0, -1, -1, -1))

      if check:
        self.clockDelta = int(time.time() / 60) - int(ts / 60)
        # Generate a warning if PC and station clocks are more than 2
        # minutes out of sync.
        if abs(self.clockDelta) > 2:
          self.logger.warning("PC and station clocks are out of sync")

      return datetime.datetime(year, month, day, hours, minutes)

    def decodeWind(self, record):
      # Byte 0: Wind direction in steps of 22.5 degrees.
      # 0 is N, 1 is NNE and so on. See windDirMap for complete list.
      dirDeg = (record[0] & 0xF) * 22.5
      # Byte 1: Always 0x0C? Maybe high nible is high byte of gust speed.
      # Byts 2: The low byte of gust speed in 0.1 m/s.
      gustSpeed = (((record[1] >> 4) & 0xF) | record[2]) * 0.1
      if record[1] != 0x0C:
        self.logger.info("TODO: Wind byte 1: %02X" % record[1])
      # Byte 3: High nibble seems to be low nibble of average speed.
      # Byte 4: Maybe low nibble of high byte and high nibble of low byte
      #          of average speed. Value is in 0.1 m/s
      avgSpeed = ((record[4] << 4) | ((record[3] >> 4) & 0xF)) * 0.1
      if (record[3] & 0x0F) != 0:
        self.logger.info("TODO: Wind byte 3: %02X" % record[3])
      # Byte 5 and 6: Low and high byte of windchill temperature. The value is
      # in 0.1F. If no windchill is available byte 5 is 0 and byte 6 0x20.
      # Looks like OS hasn't had their Mars Climate Orbiter experience yet.
      if record[5] != 0 or record[6] != 0x20:
        windchill = (((record[6] << 8) | record[5]) - 320) * (5.0 / 90.0)
      else:
        windchill = None

      self.logger.info("Wind Dir: %s" % windDirMap[record[0]])
      self.logger.info("Gust: %.1f m/s" % gustSpeed)
      self.logger.info("Wind: %.1f m/s" % avgSpeed)
      if windchill != None:
        self.logger.info("Windchill: %.1f C" % windchill)

      return (dirDeg, avgSpeed, gustSpeed, windchill)

    def decodeRain(self, record):
      # Bytes 0 and 1: high and low byte of the current rainfall rate
      # in 0.1 in/h
      rainRate = ((record[1] << 8) | record[0]) / 3.9370078
      # Bytes 2 and 3: high and low byte of the last hour rainfall in 0.1in
      rainHour = ((record[3] << 8) | record[2]) / 3.9370078
      # Bytes 4 and 5: high and low byte of the last day rainfall in 0.1in
      rainDay = ((record[5] << 8) | record[4]) / 3.9370078
      # Bytes 6 and 7: high and low byte of the total rainfall in 0.1in
      rainTotal = ((record[7] << 8) | record[6]) / 3.9370078

      self.logger.info("Rain Rate: %.1f mm/hr" % rainRate)
      self.logger.info("Rain Hour: %.1f mm" % rainHour)
      self.logger.info("Rain 24h: %.1f mm" % rainDay)
      self.logger.info("Rain Total: %.1f mm" % rainTotal)
      # Bytes 8 - 12 contain the time stamp since the measurement started.
      self.decodeTimeStamp(record[8:13], 'Since', False)
      return (rainTotal, rainRate)

    def decodeUV(self, uv):
      self.logger.info("UV Index: %d" % uv)
      return uv

    def decodePressure(self, record):
      # Byte 0: low byte of pressure. Value is in hPa.
      # Byte 1: high nibble is probably forecast
      #         low nibble is high byte of pressure.
      pressure = ((record[1] & 0xF) << 8) | record[0]
      forecast = forecastMap[(record[1] & 0x70) >> 4]
      # Bytes 2 - 3: Similar to bytes 0 and 1, but altitude corrected
      # pressure. Upper nibble of byte 3 is still unknown. Seems to
      # be always 3.
      altPressure = (record[3] & 0xF) * 256 + record[2]
      unknownNibble = (record[3] & 0x70) >> 4

      self.logger.info("Forecast: %s" % forecast)
      self.logger.info("Measured Pressure: %d hPa" % pressure)
      if unknownNibble != 3:
        self.logger.info("TODO: Pressure unknown nibble: %d" % unknownNibble)
      self.logger.info("Altitude corrected Pressure: %d hPa" % altPressure)
      return pressure

    def decodeTempHumid(self, record):
      data = []
      # The historic data can contain data from multiple sensors. I'm not
      # sure if the 0xD7 frames can do too. I've never seen a frame with
      # multiple sensors. But historic data bundles data for multiple
      # sensors.
      rSize = 7
      for i in xrange(len(record) / rSize):
        # Byte 0: low nibble contains sensor ID. 0 for base station.
        sensor = record[i * rSize] & 0xF
        smiley = (record[i * rSize] >> 6) & 0x3
        trend = (record[i * rSize] >> 4) & 0x3
        # Byte 1: probably the high nible contains the sign indicator.
        #         The low nibble is the high byte of the temperature.
        # Byte 2: The low byte of the temperature. The value is in 1/10
        # degrees centigrade.
        temp = (((record[i * rSize + 2] & 0x0F) << 8) +
                record[i * rSize + 1]) * 0.1
        if record[i * rSize + 2] & 0x80:
          temp = -temp
        # Byte 3: The humidity in percent.
        humidity = record[i * rSize + 3]
        # Bytes 4 and 5: Like bytes 1 and 2 but for dew point.
        dewPoint = (((record[i * rSize + 5] & 0x0F) << 8) +
                    record[i * rSize + 4]) * 0.1
        if record[i * rSize + 5] & 0x80:
          dewPoint = -dewPoint
        if record[i * rSize + 6] != 0:
          self.logger.info("TODO: Sensor %d byte 6: %02X" %
                           (sensor, record[i * rSize + 6]))

        self.logger.info("Temperature %d: %.1f C" % (sensor, temp))
        self.logger.info("Humidity %d: %d%%   Trend: %s   Climate: %s" %
                         (sensor, humidity, humidityTrend[trend],
                          climateSmileys[smiley]))
        self.logger.info("Dew point %d: %.1f C" % (sensor, dewPoint))

        data.append((temp, humidity, sensor))

      return data

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
      self.logger.info("Clock delta: %d" % self.clockDelta)
      self.logger.info("Polling delay: %.1f" % self.pollDelay)
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

