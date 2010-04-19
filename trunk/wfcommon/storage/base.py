## Copyright 2009 Laurent Bovet <laurent.bovet@windmaster.ch>
##                Jordi Puigsegur <jordi.puigsegur@gmail.com>
##
##  This file is part of wfrog
##
##  wfrog is free software: you can redistribute it and/or modify
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

import time
from datetime import datetime

class DatabaseStorage(object):
    '''
    Base class for database storages.
    '''

    initialized = False

    time_format = '%Y-%m-%d %H:%M:%S'

    def write_sample(self, sample, context={}):
        if not self.initialized:
            self.init()
            self.initialized = True

        statement =  "INSERT INTO METEO (TIMESTAMP_UTC, TIMESTAMP_LOCAL," + \
            " TEMP, HUM, WIND, WIND_DIR, WIND_GUST, WIND_GUST_DIR, DEW_POINT,"+ \
            " RAIN, RAIN_RATE, PRESSURE, UV_INDEX) "+ \
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        timestamp = int(time.mktime(sample['localtime']))
        sql = statement % ("'%s'" % datetime.utcfromtimestamp(timestamp).strftime(self.time_format),
       "'%s'" % sample['localtime'].strftime(self.time_format),
       self.format(sample['temp']),
       self.format(sample['hum']),
       self.format(sample['wind']),
       self.format(sample['wind_dir']),
       self.format(sample['wind_gust']),
       self.format(sample['wind_gust_dir']),
       self.format(sample['dew_point']),
       self.format(sample['rain']),
       self.format(sample['rain_rate']),
       self.format(sample['pressure']),
       self.format(sample['uv_index']))
        try:
            self.db.connect()
            self.db.execute(sql)
            self.logger.debug("SQL executed: %s", sql)
        except:
            self.logger.exception("Error writting current data to database")
        finally:
            self.db.disconnect()

    def samples(self, from_time=datetime.fromtimestamp(0), to_time=datetime.now(), context={}):
        if not self.initialized:
            self.init()
            self.initialized = True

        statement = "SELECT TIMESTAMP_LOCAL," + \
            " TEMP, HUM, WIND, WIND_DIR, WIND_GUST, WIND_GUST_DIR, DEW_POINT,"+ \
            " RAIN, RAIN_RATE, PRESSURE, UV_INDEX FROM METEO " + \
            " WHERE TIMESTAMP_LOCAL >= '%s' AND TIMESTAMP_LOCAL < '%s' "+ \
            " ORDER BY TIMESTAMP_LOCAL ASC"

        sql = statement % ( from_time.strftime(self.time_format),
            to_time.strftime(self.time_format))

        mapper = lambda(row) : { 'local_timestamp' : row[0],
            'temp' : row[1],
            'hum' : row[2],
            'wind' : row[3],
            'wind_dir' : row[4],
            'wind_gust' : row[5],
            'wind_gust_dir' : row[6],
            'dew_point' : row[7],
            'rain' : row[8],
            'rain_rate' : row[8],
            'pressure' : row[10],
            'uv_index' : row[11] }

        try:
            self.db.connect()
            for i in self.db.select(sql):
                yield mapper(i)
        finally:
            self.db.disconnect()

    def format(self, value):
        if value is None:
            return 'NULL'
        else:
            return value

