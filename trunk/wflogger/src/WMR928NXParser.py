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

# Protocol information obtained from from:
# - http://www.netsky.org/WMR/Protocol.htm
# - http://www.cs.stir.ac.uk/~kjt/software/comms/wmr928.html
# - http://www.castro.aus.net/~maurice/weather/

## TODO: DOCUMENT MESSAGES' PROTOCOL
##       GENERATE CRITICAL LOG ENTRIES FOR LOW BATTERY LEVEL

import time, logging
from uWxUtils import StationToSeaLevelPressure
from WxParser import WxParser
from utils import write2xml

CURRENT_CONDITIONS_UPDATE = 10
CURRENT_CONDITIONS_FILENAME = "WMR928NX_current_conditions.xml"
CURRENT_CONDITIONS_ROOT = "WMR928NX"

WxWeatherStatus = {0xc: 'Sunny', 0x6: 'Half cloudy', 0x2: 'Cloudy', 0x3: 'rainy'}

class WMR928NXParser (WxParser):
    """
    """
    def __init__(self, config):
        WxParser.__init__(self, config)
        self._logger = logging.getLogger('WxLogger.WMR928NXParser')
        ## Configuration
        self.CURRENT_CONDITIONS_UPDATE = config.getint('WMR928NX', 'CURRENT_CONDITIONS_UPDATE')
        self.CURRENT_CONDITIONS_FILENAME = config.get('WMR928NX', 'CURRENT_CONDITIONS_FILENAME')
        self.CURRENT_CONDITIONS_ROOT = config.get('WMR928NX', 'CURRENT_CONDITIONS_ROOT')
        self.TIME_FORMAT = config.get('WxLogger', 'TIME_FORMAT')
        ## Initialize internal data
        self._WMR928NX_record_types = {
            0x00: (9, 'Wind', self._parse_wind_record),
            0x01: (14, 'Rain', self._parse_rain_record),
            0x03: (7, 'Temperature', self._parse_temperature_record),
            0x06: (12, 'Console', self._parse_console_record),            
            0x0e: (3, 'Minute', self._parse_minute_record),
            0x0f: (7, 'Clock', self._parse_clock_record)}
        self._WxCurrent = {}  # Wx Current conditions
        self._message_count = 0

    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def _decode_bcd(self, bcd):
        return(bcd & 0xf) + ((bcd & 0xf0) >> 4) * 10

    def _parse_clock_record(self, record):
        """
        """
        batteryOK = (record[1] & 0x80) == 0
       
        minute = self._decode_bcd(record[1] & 0x7f)
        hour = self._decode_bcd(record[2])
        day = self._decode_bcd(record[3])
        month = self._decode_bcd(record[4])
        year = 2000 + self._decode_bcd(record[5]) 
        consoleClock = "%d/%d/%d %d:%d" % (day, month, year, hour, minute)
        
        # Wx Current conditions
        self._WxCurrent['console.batteryOK'] = batteryOK
        self._WxCurrent['console.clock'] = consoleClock
        
        # Log
        self._logger.info("Clock %s, batteryOK: %s", consoleClock, batteryOK)

    def _parse_minute_record(self, record):
        """
        """
        batteryOK = (record[1] & 0x80) == 0
        minute = self._decode_bcd(record[1] & 0x7f)
        
        # Current data
        self._WxCurrent['console.batteryOK'] = batteryOK
        if 'console.clock' in self._WxCurrent:
            consoleClock = self._WxCurrent['console.clock']
            pos = consoleClock.find(':')
            if pos != -1:
                consoleClock = consoleClock[:pos+1] + str(minute)
                self._WxCurrent['console.clock'] = consoleClock
            
        # Log
        self._logger.info("Minute %d, batteryOK: %s" , minute, batteryOK)
        
    def _parse_rain_record(self, record):
        """
        """
        batteryOk = (record[1] & 0x40) == 0

        # TODO: investigate meaning of over bits  & include in xml file if necessary      
        rateOver = not ((record[1] & 0x10) == 0) 
        totalOver = not ((record[1] & 0x20) == 0)
        yesterdayOver = not ((record[1] & 0x80) == 0)

        # results come in inches
        rate = self._decode_bcd(record[2]) + self._decode_bcd(record[3] & 0xf) * 100.0
        yesterday = self._decode_bcd(record[6]) + self._decode_bcd(record[7]) * 100.0
        total = ((self._decode_bcd(record[3] & 0xf0)) / 100.0) + \
                       self._decode_bcd(record[4]) + \
                       self._decode_bcd(record[5]) * 100.0

        minuteT = self._decode_bcd(record[8])
        hourT = self._decode_bcd(record[9])
        dayT = self._decode_bcd(record[10])
        monthT = self._decode_bcd(record[11])
        yearT = 2000 + self._decode_bcd(record[12])
        
        # Wx Current conditions
        self._WxCurrent['rain.batteryOk'] = batteryOk
        self._WxCurrent['rain.yesterday'] = yesterday
        self._WxCurrent['rain.total'] = total
        self._WxCurrent['rain.rate'] = rate
        self._WxCurrent['rain.totalSince'] = "%d/%d/%d %d:%d" % (yearT, monthT, dayT, hourT, minuteT)

        # Report data
        self._report_rain(total, rate)

        # Log
        self._logger.info("Rain batteryOK Ok: %s, Rate %g, Yesterday %g, Total %g since %d/%d/%d %d:%d",
                          batteryOk, rate, yesterday, total, yearT, monthT, dayT, hourT, minuteT)

    def _parse_wind_record(self, record):
        """
        """
        # TODO: investigate meaning over variables
        avrgOver = not ((record[1] & 0x20) == 0)
        gustOver = not ((record[1] & 0x10) == 0)
        batteryOK = ((record[1] & 0x40) == 0)
        
        dirDeg = self._decode_bcd(record[2]) + self._decode_bcd(record[3] & 0xf) * 100
        gustSpeed = self._decode_bcd(record[3] & 0xf0) / 100.0 + self._decode_bcd(record[4])
        avgSpeed = self._decode_bcd(record[5]) / 10.0 + self._decode_bcd(record[6] & 0xf) * 10.0

        chillNoData = not ((record[6] & 0x20) == 0)
        chillOver = not ((record[6] & 0x40) == 0)

        windChill = self._decode_bcd(record[7])
        if not ((record[6] & 0x80) == 0):
            chillsign *= -1.0
        
        # Current Data
        self._WxCurrent['wind.batteryOK'] = batteryOK
        self._WxCurrent['wind.dirDeg'] = dirDeg
        if not avrgOver:
            self._WxCurrent['wind.avgSpeed'] = avgSpeed
        if not gustOver:
            self._WxCurrent['wind.gustSpeed'] = gustSpeed
        if not chillNoData and not chillOver:
            self._WxCurrent['wind.windChill'] = windChill

        # Report Data
        if not avrgOver and not gustOver:
            self._report_wind(dirDeg, avgSpeed, gustSpeed)

        # Log
        self._logger.info("Wind batteryOk: %s, direction: %d, gust: %g m/s, avg. speed: %g m/s, WindChill %g C",
                          batteryOK, dirDeg, gustSpeed, avgSpeed, windChill)

    def _parse_console_record(self, record):
        """
        Pressure = real pressure - 600
        Offset - 600 = offset to add to real pressure
        """
        batteryOK = (record[1] & 0x40) == 0

        temperature = self._decode_bcd(record[2]) * 0.1 + self._decode_bcd(record[3] & 0x3f) * 10.0
        if record[3] & 0x80 == 0x80:
            temperature *= -1
        humidity = self._decode_bcd(record[4])
        dewPoint = None
        if record[1] & 0x10 == 0x10:
            dewPoint = self._decode_bcd(record[45])

        pressure = 600 + record[6] + ((0x1 & record[7]) << 8)
        offset = (((record[8] & 0xf0) >> 4) / 10.0) + self._decode_bcd(record[9]) + \
                 (self._decode_bcd(record[10]) * 100.0) - 600
        seaLevelPressure = pressure + offset

        # Calculate seaLevelPressure by software
        if 'thext.temp' in self._WxCurrent:
            seaLevelPressure = round(StationToSeaLevelPressure(
                                                   pressure,
                                                   self.ALTITUDE, self._WxCurrent['thext.temp'], 
                                                   self.MEAN_TEMP, 
                                                   self._WxCurrent['thext.humidity'], 'paDavisVP'),1)
        
        weatherStatus = (record[7] & 0xf0) >> 4
        weatherStatusTxt = WxWeatherStatus.get(weatherStatus, str(weatherStatus))
        
        # Current Data
        self._WxCurrent['console.batteryOK'] = batteryOK
        self._WxCurrent['console.temperature'] = temperature
        self._WxCurrent['console.humidity'] = humidity
        if dewPoint != None:
            self._WxCurrent['console.dewPoint'] = dewPoint
        self._WxCurrent['console.pressure'] = pressure
        self._WxCurrent['console.seaLevelPressure'] = seaLevelPressure
        self._WxCurrent['console.weatherStatus'] = weatherStatus
        self._WxCurrent['console.weatherStatusTxt'] = weatherStatusTxt

        # Report data
        self._report_barometer(seaLevelPressure)

        # Log
        if dewPoint == None:
            self._logger.info("Console batteryOK: %s, Temp.: %g C, Humidity: %d %%, Pressure: %g, SeaLevelPressure: %g, WeatherStatus: %d, WeatherStatusTxt: %s",
                              batteryOK, temperature, humidity, pressure, seaLevelPressure, weatherStatus, weatherStatusTxt)
        else:
            self._logger.info("Console batteryOK: %s, Temp.: %g C, Humidity: %d %%, DewPoint: %g, Pressure: %g, SeaLevelPressure: %g, WeatherStatus: %d, WeatherStatusTxt: %s",
                              batteryOK, temperature, humidity, dewPoint, pressure, seaLevelPressure, weatherStatus, weatherStatusTxt)

    def _parse_temperature_record(self, record):
        """
        """
        batteryOk = (record[1] & 0x40) == 0

        overUnder = not((record[3] & 0x40) == 0)
        dewUnder = not ((record[1] & 0x10) == 0)

        # Temperature
        temp = self._decode_bcd(record[2]) * 0.1 + self._decode_bcd(record[3] & 0x3f) * 10.0;
        if not ((record[3] & 0x80) == 0):
            temp *= -1
        
        # Humidity
        humidity = self._decode_bcd(record[4])
        
        # Station Dew Point
        dewPoint = self._decode_bcd(record[5])
        
        # Current Data
        if not overUnder:
            self._WxCurrent['thext.temp'] = temp
        self._WxCurrent['thext.humidity'] = humidity
        if not dewUnder:
            self._WxCurrent['thext.dewPoint'] = dewPoint
        
        # Report data
        if not overUnder:
            self._report_temperature(temp, humidity)

        # Log
        self._logger.info("Temperature  Temp.: %g C, Humidity: %d %%, Dew Point: %g C",
                          temp, humidity, dewPoint)



    def parse_record(self, record):
        # 1 - ID byte (record type)
        # <record bytes>
        # n-1 - checksum

        length = len(record)
        if length < 3:
            self._logger.warning("Record: %s - bad checksum + wrong size", self._list2bytes(record))
        else:
            computedChecksum = (reduce(lambda x,y: x + y, record[:-1]) - 2) & 0xff
            recordChecksum = record[length - 1]
            
            if recordChecksum != computedChecksum:
                self._logger.warning("Record: %s - bad checksum", self._list2bytes(record))
            elif record[0] in self._WMR928NX_record_types:
                (expected_length, record_type, record_parser) = self._WMR928NX_record_types.get(record[0])
                if expected_length != length:
                    self._logger.warning("%s Record: %s - wrong length (expected %d, received %d)",
                                         record_type, self._list2bytes(record), expected_length, length)
                    return
                else:
                    self._logger.debug("%s Record: %s", record_type, self._list2bytes(record))
                    #if record_type in ["Minute", "Clock", "Console", "Wind", "Temperature"]:
                    record_parser(record)
                    if self.CURRENT_CONDITIONS_UPDATE != 0:
                        self._message_count += 1
                        ## Save current condition to xml file
                        if self._message_count  >= self.CURRENT_CONDITIONS_UPDATE:
                            try:
                                self._WxCurrent['timestampt'] = time.strftime(self.TIME_FORMAT, time.localtime())
                                write2xml(self._WxCurrent, self.CURRENT_CONDITIONS_ROOT, self.CURRENT_CONDITIONS_FILENAME)
                                self._message_count = 0
                            except:
                                self._logger.exception("Error writting WMRS200 current conditions file (%s)", 
                                                  self.CURRENT_CONDITIONS_FILENAME)
            else:
                self._logger.warning("Unknown record type: %s", self._list2bytes(record))

