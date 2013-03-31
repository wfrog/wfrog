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

    time_format = '%Y-%m-%d %H:%M:%S'

    tablename = 'METEO'

    
    mandatory_storage_fields = ['TEMP', 'HUM', 'DEW_POINT', 'WIND', 'WIND_DIR', 'WIND_GUST', 
                                'WIND_GUST_DIR', 'RAIN', 'RAIN_RATE', 'PRESSURE']
    optional_storage_fields = ['UV_INDEX', 'SOLAR_RAD', 'TEMPINT', 'HUMINT', 'TEMP2', 'HUM2', 
                               'TEMP3', 'HUM3', 'TEMP4', 'HUM4', 'TEMP5', 'HUM5', 
                               'TEMP6', 'HUM6', 'TEMP7', 'HUM7', 'TEMP8', 'HUM8', 
                               'TEMP9', 'HUM9']

    # Database storages should rewrite the storage_fields variable with the actual available fields
    storage_fields = mandatory_storage_fields


    def write_sample(self, sample, context={}):

        timestamp = time.mktime(sample['localtime'].timetuple())
        utc_time = datetime.utcfromtimestamp(timestamp)
        sql =  "INSERT INTO %s (TIMESTAMP_UTC, TIMESTAMP_LOCAL, %s) VALUES (%s, %s, %s)" % (
                  self.tablename,
                  ', '.join(self.storage_fields), 
                  "'%s'" % utc_time.strftime(self.time_format),
                  "'%s'" % sample['localtime'].strftime(self.time_format),
                  ', '.join(map(lambda x: self.format(sample[x.lower()] if x.lower() in sample else None), self.storage_fields)))
        try:
            self.db.connect()
            self.db.execute(sql)
            self.logger.debug("SQL executed: %s", sql)
        except:
            self.logger.exception("Error writting current data to database")
        finally:
            self.db.disconnect()


    def keys(self, context={}):
        return ['utctime', 'localtime'] + map(str.lower ,self.storage_fields) 


    def samples(self, from_time=datetime.fromtimestamp(0), to_time=datetime.now(), context={}):

        self.logger.debug("Getting samples for range: %s to %s", from_time, to_time)

        sql = ( "SELECT TIMESTAMP_UTC, TIMESTAMP_LOCAL, %s FROM %s " + \
                " WHERE TIMESTAMP_LOCAL >= '%s' AND TIMESTAMP_LOCAL < '%s' "+ \
                " ORDER BY TIMESTAMP_LOCAL ASC" ) % (
                    ', '.join(self.storage_fields), 
                    self.tablename, 
                    from_time.strftime(self.time_format),
                    to_time.strftime(self.time_format))

        try:
            self.db.connect()
            for row in self.db.select(sql):
                if not isinstance(row[0], datetime):
                       row = list(row)
                       row[0] = datetime.strptime(row[0], self.time_format)
                yield row
        finally:
            self.db.disconnect()

    def format(self, value):
        if value is None:
            return 'NULL'
        else:
            return str(value)  # rounds up values to 1 decimal, which is OK. 

