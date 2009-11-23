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


# Attention! 
# In individual measures wind avg. value can be higher than wind gust.
# This might be due to the fact that wind gust is an instantaneous measure 
# whereas wind avg has been calculated over a period of --probably-- several
# minutes.

import time, logging
from uWxUtils import InToMm, StationToSeaLevelPressure
from WxParser import WxParser
from utils import write2xml

WxForecast = { 0:'PartlyCloudy', 1:'Rainy', 2:'Cloudy', 3:'Sunny', 4:'Snowy' }
WxComfortLevel = { 0:'-', 1:'Good',  2:'Poor', 3:'Fair' }
WxTrend = { 0:'Steady', 1:'Falling', 2:'Rising'}
WxWindDir = { 0:"N", 1:"NNE", 2:"NE", 3:"ENE", 4:"E", 5:"ESE", 6:"SE", 7:"SSE", 
              8:"S", 9:"SSW", 10:"SW", 11:"WSW", 12:"W", 13:"WNW", 14:"NW", 15:"NWN" }
THSensors = { 0:'thInt', 1:'th1', 2:'th2', 3:'th3', 4:'th4', 
              5:'th5', 6:'th6', 7:'th7', 8:'th8', 9:'th9' }
MainTHExtSensor = 'th1'

class WMRS200Parser (WxParser):
    def __init__(self, config):
        WxParser.__init__(self, config)
        self._logger = logging.getLogger('WxLogger.WMRS200Parser')
        ## Configuration
        self.CURRENT_CONDITIONS_UPDATE = config.getint('WMRS200', 'CURRENT_CONDITIONS_UPDATE')
        self.CURRENT_CONDITIONS_FILENAME = config.get('WMRS200', 'CURRENT_CONDITIONS_FILENAME')
        self.CURRENT_CONDITIONS_ROOT = config.get('WMRS200', 'CURRENT_CONDITIONS_ROOT')
        self.TIME_FORMAT = config.get('WxLogger', 'TIME_FORMAT')
        ## Initialize internal data
        self._WMRS200_record_types = {
            0x41: (17, 'Rain', self._parse_rain_record),
            0x42: (12, 'Temperature', self._parse_temperature_record),
            0x46: (8, 'Barometer', self._parse_barometer_record),
            0x47: (6, 'UV', self._parse_uv_record),
            0x48: (11, 'Wind', self._parse_wind_record),
            0x60: (12, 'Clock', self._parse_clock_record)}
        self._WxCurrent = {}  # Wx Current conditions
        self._message_count = 0

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

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
        
        # Wx Current conditions
        self._WxCurrent['console.powered'] = powered
        self._WxCurrent['console.batteryOK'] = batteryOK
        self._WxCurrent['console.clockSync'] = rf
        self._WxCurrent['console.clock'] = consoleDate
        
        # Log
        self._logger.info("Clock %s, power: %s, Powered: %s, Battery: %s, RF: %s",
                          consoleDate, power, powered, batteryOK, rf)

    def _parse_rain_record(self, record):
        """
    Length  16  
    Example: 00 41 ff 02 0c 00 00 00 25 00 00 0c 01 01 06 87
    Byte Data   Comment
    0    00     Battery level in high nibble
    1    41     Identifier
    2-3  ff 02  Rain ratlogging.basicConfig(level=logging.WARNING)
e: byte 3 * 256 + byte 2, in inches/hour (verify time unit)
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
        rate = InToMm((record[2] + record[3] * 256) * 0.01)
        thisHour = InToMm((record[4] + record[5] * 256) * 0.01) 
        thisDay = InToMm((record[6] + record[7] * 256) * 0.01) 
        total = InToMm((record[8] + record[9] * 256) * 0.01)  

        minuteT = record[10]
        hourT = record[11]
        dayT = record[12]
        monthT = record[13]
        yearT = 2000 + record[14]
        
        # Wx Current conditions
        self._WxCurrent['rain.batteryOk'] = batteryOk
        self._WxCurrent['rain.thisHour'] = thisHour
        self._WxCurrent['rain.thisDay'] = thisDay
        self._WxCurrent['rain.total'] = total
        self._WxCurrent['rain.rate'] = rate
        self._WxCurrent['rain.totalSince'] = "%d/%d/%d %d:%d" % (yearT, monthT, dayT, hourT, minuteT)

        # Report data
        self._report_rain(total, rate)

        # Log
        self._logger.info("Rain Battery Ok: %s, Rate %g, This Hr %g, This Day %g, Total %g since %4d/%2d/%2d %2d:%2d",
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
        dirStr = WxWindDir[dir]
        avgSpeed = 0.1 * ((record[6] << 4) + ((record[5]) >> 4))
        gustSpeed = 0.1 * (((record[5] & 0x0F) << 8) + record[4])

        # Current Data
        self._WxCurrent['wind.batteryOk'] = batteryOk
        self._WxCurrent['wind.dir'] = dir
        self._WxCurrent['wind.dirDeg'] = dirDeg
        self._WxCurrent['wind.dirStr'] = dirStr
        self._WxCurrent['wind.avgSpeed'] = avgSpeed
        self._WxCurrent['wind.gustSpeed'] = gustSpeed

        # Report Data
        self._report_wind(dirDeg, avgSpeed, gustSpeed)

        # Log
        self._logger.info("Wind batteryOk: %s, direction: %d (%g/%s), gust: %g m/s, avg. speed: %g m/s",
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
        forecastTxt = WxForecast.get(forecast, str(forecast))
            
        ## Can't use WMRS200 qnhPressure (cannot set altitude)
        #qnhPressure = (record[5] & (0x0f)) * 256 + record[4]
        #qnhForecast = record[5] >> 4
        #qnhForecast_txt = WxForecast.get(forecast, str(qnhForecast))

        if self._WxCurrent.has_key('th1.temp') and self._WxCurrent.has_key('th1.humidity'):
            pressure = round(StationToSeaLevelPressure(
                                                   pressure,
                                                   self.ALTITUDE, self._WxCurrent['th1.temp'], self.MEAN_TEMP, 
                                                   self._WxCurrent['th1.humidity'], 'paDavisVP'),1)
            # Current Data
            self._WxCurrent['barometer.pressure'] = pressure
            self._WxCurrent['barometer.forecast'] = forecast
            self._WxCurrent['barometer.forecastTxt'] = forecastTxt

            # Report data
            self._report_barometer(pressure)

            # Log
            self._logger.info("Barometer Forecast: %s, Pressure: %d mb", forecastTxt, pressure)

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
        sensorName = THSensors[sensor]

        # Confort level and trend
        comfortLevel = record[2] >> 6
        trend = (record[2] >> 4) & 0x03
        comfortLevelTxt = WxComfortLevel.get(comfortLevel,str(comfortLevel))
        trendTxt = WxTrend.get(trend, str(trend))

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
        
        # Current Data
        self._WxCurrent['%s.temp' % sensorName] = temp
        self._WxCurrent['%s.humidity' % sensorName] = humidity
        self._WxCurrent['%s.comfortLevel' % sensorName] = comfortLevel
        self._WxCurrent['%s.comfortLevelTxt' % sensorName] = comfortLevelTxt
        self._WxCurrent['%s.trend' % sensorName] = trend
        self._WxCurrent['%s.trendTxt' % sensorName] = trendTxt
        self._WxCurrent['%s.dewPoint' % sensorName] = dewPoint
        
        # Report data
        if sensorName == MainTHExtSensor:
            self._report_temperature(temp, humidity)

        # Log
        self._logger.info("Temperature %s  Temp.: %g C (%s), Humidity: %d %% (%s), Dew Point: %g C",
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
        
        # Current data
        self._WxCurrent['uv.batteryOk'] = batteryOk
        self._WxCurrent['uv.index'] = uv

        # Report data
        self._report_uv(uv)
        
        # Log
        self._logger.info("UV  Battery Ok: %s  UV Index: %d" % (batteryOk, uv))

    def parse_record(self, record):
        # 0 - Flag
        # 1 - ID byte (record type)
        # <record bytes>
        # n-2 - checksum
        # n-1 - checksum

        length = len(record)
        if length < 3:
            self._logger.warning("Record: %s - bad checksum + wrong size", self._list2bytes(record))
        else:
            computedChecksum = reduce(lambda x,y: x + y, record[:-2])
            recordChecksum = (record[length - 1] << 8) + record[length - 2]
            
            if recordChecksum != computedChecksum:
                self._logger.warning("Record: %s - bad checksum", self._list2bytes(record))
            elif record[1] in self._WMRS200_record_types: 
                (expected_length, record_type, record_parser) = self._WMRS200_record_types[record[1]]
                if expected_length != length:
                    self._logger.warning("%s Record: %s - wrong length (expected %d, received %d)",
                                         record_type, self._list2bytes(record), expected_length, length)
                    return
                else:
                    self._logger.debug("%s Record: %s", record_type, self._list2bytes(record))
                    record_parser(record)
                    if self.CURRENT_CONDITIONS_UPDATE != 0:
                        self._message_count += 1
                        ## Save current condition to xml file
                        if self._message_count >= self.CURRENT_CONDITIONS_UPDATE:
                            try:
                                self._WxCurrent['time'] = time.strftime(self.TIME_FORMAT, time.localtime())
                                write2xml(self._WxCurrent, self.CURRENT_CONDITIONS_ROOT, self.CURRENT_CONDITIONS_FILENAME)
                                self._message_count = 0
                            except:
                                logging.exception("Error writting WMRS200 current conditions file (%s)", 
                                                  self.CURRENT_CONDITIONS_FILENAME)
            else:
                self._logger.warning("Unknown record type: %s", self._list2bytes(record))

