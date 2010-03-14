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

# Protocol information obtained from:
# http://www.ejeklint.se/development/wmr100n-driver-for-mac-os-x/wmr100n-usb-protocol/
# http://wmrx00.sourceforge.net/  (WMR100 weather logger project)

## TODO: DOCUMENT MESSAGES' PROTOCOL
##       Implement calibration parameter for rain sensor
##       WMRS100 projects implement a calibration for humidity sensor to obtain 100% value (necessary?)
##       GENERATE CRITICAL LOG ENTRIES FOR LOW BATTERY LEVEL (ONE ALARM PER DAY!)
##       ALLOW CONFIG TO SPECIFY WHICH temp/hum SENSOR(S) SHOULD BE USED

# Attention!
# In individual measures wind avg. value can be higher than wind gust.
# This might be due to the fact that wind gust is an instantaneous measure
# whereas wind avg has been calculated over a period of --probably-- several
# minutes.

from base import BaseStation
import time
import logging
import logging
import threading
import sys

forecastMap = { 0:'PartlyCloudy', 1:'Rainy', 2:'Cloudy', 3:'Sunny', 4:'Snowy' }
comfortLevelMap = { 0:'-', 1:'Good',  2:'Poor', 3:'Fair' }
trendMap = { 0:'Steady', 1:'Falling', 2:'Rising'}
windDirMap = { 0:"N", 1:"NNE", 2:"NE", 3:"ENE", 4:"E", 5:"ESE", 6:"SE", 7:"SSE",
              8:"S", 9:"SSW", 10:"SW", 11:"WSW", 12:"W", 13:"WNW", 14:"NW", 15:"NWN" }
thSensors = { 0:'thInt', 1:'th1', 2:'th2', 3:'th3', 4:'th4',
              5:'th5', 6:'th6', 7:'th7', 8:'th8', 9:'th9' }
mainThExtSensor = 'th1'

vendor_id  = 0xfde
product_id = 0xca01

class WMRS200Station(BaseStation):
    '''
    Station driver for the Oregon Scientific WMRS200. Reported to work with WMR100.
    '''

    logger = logging.getLogger('station.wmrs200')

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def _search_device(self, vendor_id, product_id):
        import usb
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
                    raise Exception("USB WMRS200 not found (%04X %04X)" % (vendor_id, product_id))

                self.logger.info("USB WMRS200 found")
                devh = dev.open()
                self.logger.info("USB WMRS200 open")

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

                # WMRS200 Init sequence
                devh.controlMsg(usb.TYPE_CLASS + usb.RECIP_INTERFACE,       # requestType
                                0x0000009,                                  # request
                                [0x20,0x00,0x08,0x01,0x00,0x00,0x00,0x00],  # buffer
                                0x0000200,                                  # value
                                0x0000000,                                  # index
                                1000)                                       # timeout

                ## Do the actual work
                self.logger.info("USB WMRS200 initialized")
                self._run(devh)

            except Exception, e:
                self.logger.exception("WMRS200 exception: %s" % str(e))

            self.logger.critical("USB WMRS200 connection failure")

            ## Wait 10 seconds
            time.sleep(10)

    def _run(self, devh):
        import usb
        ## Initialize internal data
        self._WMRS200_record_types = {
            0x41: (17, 'Rain', self._parse_rain_record),
            0x42: (12, 'Temperature', self._parse_temperature_record),
            0x46: (8, 'Barometer', self._parse_barometer_record),
            0x47: (6, 'UV', self._parse_uv_record),
            0x48: (11, 'Wind', self._parse_wind_record),
            0x60: (12, 'Clock', self._parse_clock_record)}
        
        input_buffer = []
        errors = 0
        while True:
            try:
                # Ignore USBError("No error") exceptions http://bugs.debian.org/476796
                try:
                    packet = devh.interruptRead(usb.ENDPOINT_IN + 1,  # endpoint number
                                                0x0000008,            # bytes to read
                                                10000)                # timeout (10 seconds)
                    errors = 0
                except usb.USBError, e:
                    if e.args == ('No error',):
                        self.logger.debug('USBError("No error") exception received. Ignoring...(http://bugs.debian.org/476796)')
                        packet = None
                        time.sleep(1)
                    else:
                        raise e
            except Exception, e:
                self.logger.exception("Exception reading interrupt: "+ str(e))
                errors = errors + 1
                if errors > 3: break   ## Maximum 3 consecutive errors before reconnection
                time.sleep(3)

            if packet != None:
                if len(packet) > 0 and packet[0] >= 1 and packet[0] <= 7:   ## Ignore packets with wrong lengths
                    input_buffer += packet[1:packet[0]+1]
                    self.logger.debug("USB RAW DATA: %s" % self._list2bytes(packet))

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
                        self.logger.debug("Ignored %d bytes in input", startSep)

                    length = endSep - startSep - 2
                    if length == 0:
                        self.logger.debug("Warning: zero length message in input")
                    else:
                        # Parse the message
                        try:
                            self.parse_record(input_buffer[startSep + 2 : endSep])
                        except:
                            self.logger.exception("WMRS200 reader exception")

                    # remove this message from the input queue
                    input_buffer = input_buffer[endSep:]


    def parse_record(self, record):
        # 0 - Flag
        # 1 - ID byte (record type)
        # <record bytes>
        # n-2 - checksum
        # n-1 - checksum

        length = len(record)
        if length < 3:
            self.logger.warning("Record: %s - bad checksum + wrong size", self._list2bytes(record))
        else:
            computedChecksum = reduce(lambda x,y: x + y, record[:-2])
            recordChecksum = (record[length - 1] << 8) + record[length - 2]

            if recordChecksum != computedChecksum:
                self.logger.warning("Record: %s - bad checksum", self._list2bytes(record))
            elif record[1] in self._WMRS200_record_types:
                (expected_length, record_type, record_parser) = self._WMRS200_record_types[record[1]]
                if expected_length != length:
                    self.logger.warning("%s Record: %s - wrong length (expected %d, received %d)",
                                         record_type, self._list2bytes(record), expected_length, length)
                    return
                else:
                    self.logger.debug("%s Record: %s", record_type, self._list2bytes(record))
                    record_parser(record)
            else:
                self.logger.warning("Unknown record type: %s", self._list2bytes(record))

    def _parse_clock_record(self, record):
        """
    Length 11
    Example: 00 60 00 00 14 09 1c 04 09 01 a7

    Byte    Data    Comment
    0   00  Battery data in high nibble, lowest bit 1 if main unit runs only on battery
    1   60  Identifier
    2-3 00 00   Unknown
    4   14  Minutes: 20
    5   09  Hour: 09
    6   1c  Day: 28
    7   04  Month: 04, April
    8   09  Year: 2009 (add 2000)
    9   01  Time Zone: GMT +1 (highest bit 1 if negative)
    10  a7  Checksum: 167
        """
        power = (record[0]) >> 4
        powered = ((power & 0x8) >> 3) == 0    # VERIFIED -- EXTERNAL POWER INDICATOR
        batteryOK = ((power & 0x4) >> 2) == 0  # VERIFIED -- BATTERY LOW FLAG
        rf = ((power & 0x2) >> 1) == 0         # CLOCK SYNCHRONIZED FLAG
        level = (power & 0x1)                  # What is this???

        minute = record[4]
        hour = record[5]
        day = record[6]
        month = record[7]
        year = 2000 + record[8]
        consoleDate = "%d/%d/%d %d:%d" % (day, month, year, hour, minute)

        # Log
        self.logger.info("Clock %s, power: %s, Powered: %s, Battery: %s, RF: %s",
                          consoleDate, power, powered, batteryOK, rf)

    def _parse_rain_record(self, record):
        """
    Length  16
    Example: 00 41 ff 02 0c 00 00 00 25 00 00 0c 01 01 06 87
    Byte Data   Comment
    0    00     Battery level in high nibble
    1    41     Identifier
    2-3  ff 02  Rain rate: byte 3 * 256 + byte 2, in inches/hour
    4-5  0c 00  Rain last hour: byte 5 * 256 + byte 4, in inches
    6-7  00 00  Rain last 24 hours: byte 7 * 256 + byte 6, in inches
    8-9  00 25  Total rain since reset date: byte 9 * 256 + byte 8, in inches
    10   00     Minute of reset date
    11   0c     Hour of reset date
    12   01     Day of reset date
    13   01     Month of reset date
    14   06     Year + 2000 of reset date
    15   4e     Checksum
        """
        batteryOk = (record[0] & 0x40) == 0

        # 1 inch = 25,4 mm
        rate = (record[2] + record[3] * 256) * 0.01 * 25.4
        thisHour = (record[4] + record[5] * 256) * 0.01 * 25.4
        thisDay = (record[6] + record[7] * 256) * 0.01 * 25.4
        total = (record[8] + record[9] * 256) * 0.01 * 25.4

        minuteT = record[10]
        hourT = record[11]
        dayT = record[12]
        monthT = record[13]
        yearT = 2000 + record[14]

        # Report data
        self._report_rain(total, rate)

        # Log
        self.logger.info("Rain Battery Ok: %s, Rate %g, This Hr %g, This Day %g, Total %g since %4d/%2d/%2d %2d:%2d",
                          batteryOk, rate, thisHour, thisDay, total, yearT, monthT, dayT, hourT, minuteT)

    def _parse_wind_record(self, record):
        """
    Length  10
    Example: 00 48 0a 0c 16 e0 02 00 20 76
    Byte Data   Comment
    0    00     Battery level in high nibble
    1    48     Identifier
    2    0a     Wind direction in low nibble, 10 * 360 / 16 = 225 degrees
    3    0c     Unknown
    4-5  16 e0  Wind gust, (low nibble of byte 5 * 256 + byte 4) / 10
    5-6  e0 02  Wind average, (high nibble of byte 5 + byte 6 * 16) / 10
    7    00     ?
    8    20     ?
    9    76     Checksum
        """
        batteryOk = (record[0] & 0x40) == 0
        dir = record[2] & (0x0f)
        if dir == 0:
            dirDeg = 360
        else:
            dirDeg = dir * 360 / 16
        dirStr = windDirMap[dir]
        avgSpeed = 0.1 * ((record[6] << 4) + ((record[5]) >> 4))
        gustSpeed = 0.1 * (((record[5] & 0x0F) << 8) + record[4])

        # Report Data
        self._report_wind(dirDeg, avgSpeed, gustSpeed)

        # Log
        self.logger.info("Wind batteryOk: %s, direction: %d (%g/%s), gust: %g m/s, avg. speed: %g m/s",
                          batteryOk, dir, dirDeg, dirStr, gustSpeed, avgSpeed)

    def _parse_barometer_record(self, record):
        """
    Length  7
    Example: 00 46 ed 03 ed 33 56
    Byte    Data    Comment
    0    00     Unused?
    1    46     Identifier
    2-3  ed 03  Absolute pressure, low nibble of byte 3 * 256 + byte 2
    3    03     High nibble is forecast indicator for absolute pressure
    4-5  ed 03  Relative pressure, low nibble of byte 5 * 256 + byte 4
    5    03     High nibble is forecast indicator for relative pressure
    6    56
        """
        pressure = (record[3] & (0x0f)) * 256 + record[2]
        forecast = record[3] >> 4
        forecastTxt = forecastMap.get(forecast, str(forecast))

        ## Can't use WMRS200 seaLevelPressure (cannot set altitude from wfrog)
        seaLevelPressure = (record[5] & (0x0f)) * 256 + record[4]
        slpForecast = record[5] >> 4
        slpForecastTxt = forecastMap.get(slpForecast, str(slpForecast))

        # Current Data
        self._current['barometer.pressure'] = seaLevelPressure
        self._current['barometer.forecast'] = forecast
        self._current['barometer.forecastTxt'] = forecastTxt
        self._current['barometer.seaLevelPressure'] = seaLevelPressure
        self._current['barometer.slpForecast'] = slpForecast
        self._current['barometer.slpForecastTxt'] = slpForecastTxt

        # Report data
        self._report_barometer_absolute(pressure)

        # Log
        self.logger.info("Barometer Forecast: %s, Absolute pressure: %.1f mb, Sea Level Pressure: %.1f", forecastTxt, pressure, seaLevelPressure)

    def _parse_temperature_record(self, record):
        """
    Length  11
    Example: 20 42 d1 91 00 48 64 00 00 20 90
    Byte    Data    Comment
    0   20  Battery level in high nibble. Temp trend in low nibble?
    1   42  Identifier
    2   d1  Low nibble is device channel number, high nibble humidity trend and smiley code
    3-4 91 00   Temperature: (256 * byte 4 + byte 3) / 10 = 14,5 degrees
    5   48  Humidity: 72%
    6-7 64 00   Dew point: (256 * byte 7 + byte 6) / 10 = 10 degrees
    8   00  ?
    9   20  ?
    10  90
        """
        sensor = record[2] & 0x0f
        sensorName = thSensors[sensor]

        # Confort level and trend
        comfortLevel = record[2] >> 6
        trend = (record[2] >> 4) & 0x03
        comfortLevelTxt = comfortLevelMap.get(comfortLevel,str(comfortLevel))
        trendTxt = trendMap.get(trend, str(trend))

        # Temperature
        temp = (((record[4] & 0x0f) * 255.0) + record[3]) / 10.0
        if ((record[4] >> 4) == 0x08):
            temp = temp * -1

        # Humidity
        humidity = record[5]

        # Station Dew Point
        dewPoint = (((record[7] & 0x0f) * 255.0) + record[6]) / 10.0
        if ((record[7] >> 4) == 0x08):
            dewPoint = dewPoint * -1


        self._report_temperature(sensor, temp, humidity)

        # Log
        self.logger.info("Temperature %s  Temp.: %g C (%s), Humidity: %d %% (%s), Dew Point: %g C",
                          sensorName, temp, trendTxt, humidity, comfortLevelTxt, dewPoint)

    def _parse_uv_record(self, record):
        """
    Length  6
    Example: 00 47 01 00 48 00
    Byte Data  Comment
    0    00    Battery level in high nibble
    1    47    Identifier
    2    01    ???
    3    00    UV Index  (value 0-11)
    4    48    Checksum
    5    00    Checksum
        """
        batteryOk = (record[0] & 0x40) == 0
        uv = record[3]

        # Report data
        self._report_uv(uv)

        # Log
        self.logger.info("UV  Battery Ok: %s  UV Index: %d" % (batteryOk, uv))
