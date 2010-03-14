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

## TODO:  DOCUMENT WMRS928NX serial protocol

## TODO: DOCUMENT MESSAGES' PROTOCOL
##       GENERATE CRITICAL LOG ENTRIES FOR LOW BATTERY LEVEL (ONE ALARM PER DAY!)
##       ALLOW CONFIG TO SPECIFY WHICH temp/hum SENSOR(S) SHOULD BE USED

import wfcommon.utils 
import serial
import logging
import time
import threading
from base import BaseStation

class WMR928NXStation(BaseStation):
    '''
    Station driver for the Oregon Scientific WMR928NX.
    
    [ Properties ]
    
    port [numeric] (optional):
        Serial port number where the station is connected. Defaults to 1.
    '''
    
    port = 1
    
    logger = logging.getLogger('station.wmr928nx')
    
    weatherStatusMap = {0xc: 'Sunny', 0x6: 'Half cloudy', 0x2: 'Cloudy', 0x3: 'rainy'}
    
    def _list2bytes(self, d):
        return reduce(lambda a, b: a + b, map(lambda a: "%02X " % a, d))

    def _decode_bcd(self, bcd):
        return(bcd & 0xf) + ((bcd & 0xf0) >> 4) * 10

    def run(self):
        # Initialize injected functions used by BaseStation
        self.generate_event = generate_event
        self.send_event = send_event        
        self.logger.info("Thread started")
        while True:
            try:
                self.logger.info("Opening serial port")
                ## Open Serial port
                ser = serial.Serial()
                ser.setBaudrate(9600)
                ser.setParity(serial.PARITY_NONE)
                ser.setByteSize(serial.EIGHTBITS)
                ser.setStopbits(serial.STOPBITS_ONE)
                ser.setPort(self.port)
                ser.setTimeout(60)  # 60s timeout
                ser.open()
                ser.setRTS(True)
                ## Do the actual work
                self.logger.info("Serial port open")
                self._run(ser)
            except:
                self.logger.exception("WMR928NX reader exception")

            ## Close serial port connection
            self.logger.critical("Serial port WMR928NX connection failure")
            try:
                ser.close()
                ser = None
            except:
                pass
            ## Wait 10 seconds
            time.sleep(10)

    def _run(self, ser):
        
        self._WMR928NX_record_types = {
            0x00: (9, 'Wind', self._parse_wind_record),
            0x01: (14, 'Rain', self._parse_rain_record),
            0x03: (7, 'Temperature', self._parse_temperature_record),
            0x06: (12, 'Console', self._parse_console_record),            
            0x0e: (3, 'Minute', self._parse_minute_record),
            0x0f: (7, 'Clock', self._parse_clock_record)}    
            
        input_buffer = []
        while True:
            buffer = ser.read(10) # Read next 10 bytes and return
            
            if len(buffer)== 0:
                # 60s timeout expired without data received
                self.logger.warning("No data received - reinitializing serial port")
                try:
                    ser.close()
                    input_buffer = []
                    time.sleep(10)
                    ser.open()
                    ser.setRTS(True)
                    self.logger.warning("Serial port reinitialized")
                except:
                    pass
            else:
                # data received and added to input buffer
                n_buffer = map(lambda x: ord(x), buffer)
                self.logger.debug("Serial RAW DATA: %s" % self._list2bytes(n_buffer))
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
                            self.logger.debug("Ignored %d bytes in input", startSep)

                        length = endSep - startSep - 2
                        if length == 0:
                            self.logger.debug("Warning: zero length message in input")
                        else:
                            # Parse the message
                            self.parse_record(input_buffer[startSep + 2 : endSep])

                        # remove this message from the input queue
                        input_buffer = input_buffer[endSep:]


    def parse_record(self, record):
        # 1 - ID byte (record type)
        # <record bytes>
        # n-1 - checksum

        length = len(record)
        if length < 3:
            self.logger.warning("Record: %s - bad checksum + wrong size", self._list2bytes(record))
        else:
            computedChecksum = (reduce(lambda x,y: x + y, record[:-1]) - 2) & 0xff
            recordChecksum = record[length - 1]
            
            if recordChecksum != computedChecksum:
                self.logger.warning("Record: %s - bad checksum", self._list2bytes(record))
            elif record[0] in self._WMR928NX_record_types:
                (expected_length, record_type, record_parser) = self._WMR928NX_record_types.get(record[0])
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

        batteryOK = (record[1] & 0x80) == 0
       
        minute = self._decode_bcd(record[1] & 0x7f)
        hour = self._decode_bcd(record[2])
        day = self._decode_bcd(record[3])
        month = self._decode_bcd(record[4])
        year = 2000 + self._decode_bcd(record[5]) 
        consoleClock = "%d/%d/%d %d:%d" % (day, month, year, hour, minute)

        self.logger.info("Clock %s, batteryOK: %s", consoleClock, batteryOK)

    def _parse_minute_record(self, record):
        batteryOK = (record[1] & 0x80) == 0
        minute = self._decode_bcd(record[1] & 0x7f)
        
        self.logger.info("Minute %d, batteryOK: %s" , minute, batteryOK)
        
    def _parse_rain_record(self, record):
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

        self._report_rain(total, rate)

        self.logger.info("Rain batteryOK Ok: %s, Rate %g, Yesterday %g, Total %g since %d/%d/%d %d:%d",
                          batteryOk, rate, yesterday, total, yearT, monthT, dayT, hourT, minuteT)

    def _parse_wind_record(self, record):
        # TODO: investigate meaning other variables
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
            windChill *= -1.0

        if not avrgOver and not gustOver:
            self._report_wind(dirDeg, avgSpeed, gustSpeed)

        self.logger.info("Wind batteryOk: %s, direction: %d, gust: %g m/s, avg. speed: %g m/s, WindChill %g C",
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
        
        weatherStatus = (record[7] & 0xf0) >> 4
        weatherStatusTxt = weatherStatusMap.get(weatherStatus, str(weatherStatus))
    
        self._report_barometer_absolute(pressure)
        self._report_temperature(0, temperature, humidity)        

        # Log
        if dewPoint == None:
            self.logger.info("Console batteryOK: %s, Temp.: %g C, Humidity: %d %%, Pressure: %g, SeaLevelPressure: %g, WeatherStatus: %d, WeatherStatusTxt: %s",
                              batteryOK, temperature, humidity, pressure, seaLevelPressure, weatherStatus, weatherStatusTxt)
        else:
            self.logger.info("Console batteryOK: %s, Temp.: %g C, Humidity: %d %%, DewPoint: %g, Pressure: %g, SeaLevelPressure: %g, WeatherStatus: %d, WeatherStatusTxt: %s",
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
        
        # Report data
        if not overUnder:
            self._report_temperature(1, temp, humidity)

        # Log
        self.logger.info("Temperature  Temp.: %g C, Humidity: %d %%, Dew Point: %g C",
                          temp, humidity, dewPoint)
