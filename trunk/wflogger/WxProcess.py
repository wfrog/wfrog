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

## TODO: Control errors & retries writting to database
##       Improve unexpected exception control
##       Support for other DBMS (should be easy <== no special features used)
##       Prepare a station simulator driver

import sys
import time
import logging
import threading
import wfcommon.database

class WxProcess (threading.Thread):
    def __init__(self, wxData, config):
        threading.Thread.__init__(self)
        self._wxData = wxData
        self._logger = logging.getLogger('WxLogger.WxProcess')
        ##Configuration
        self.DATABASE = config.get('WxProcess', 'DATABASE')
        self.SAMPLE_PERIOD = config.getint('WxProcess', 'SAMPLE_PERIOD')  
        self.TIME_FORMAT = config.get('WxLogger', 'TIME_FORMAT')

    def _get_wind_dir(self, data):
        if data['wind'] == 0.0:
            return 'NULL'
        else:
            return '%g' % data['wind_dir']
        
    def _get_wind_gust_dir(self, data):
        if data['wind_gust_dir'] == None:
            return 'NULL'
        else:
            return '%g' % data['wind_gust_dir']

    def _get_uv_index(self, data):
        if 'uv_index' in data:
            return '%g' % data['uv_index']
        else:
            return 'NULL'

    def _writeDB(self, data):
        sql = """
INSERT INTO METEO (TIMESTAMP_UTC, TIMESTAMP_LOCAL, TEMP, HUM, WIND, WIND_DIR, WIND_GUST, WIND_GUST_DIR,  
                   DEW_POINT, RAIN, RAIN_RATE, PRESSURE, UV_INDEX)               
VALUES (%s, %s, %g, %g, %g, %s, %g, %s, %g, %g, %g, %g, %s)
""" % ("'%s'" % time.strftime(self.TIME_FORMAT, time.gmtime()), 
       "'%s'" % time.strftime(self.TIME_FORMAT, time.localtime()),
       data['temp'], 
       data['hum'], 
       data['wind'],
       self._get_wind_dir(data), 
       data['wind_gust'], 
       self._get_wind_gust_dir(data), 
       data['dew_point'],
       data['rain'], 
       data['rain_rate'], 
       data['sea_level_pressure'],
       self._get_uv_index(data))
        try:
            bdd = wfcommon.database.FirebirdDB(self.DATABASE)
            bdd.connect()
            bdd.execute(sql)
            bdd.disconnect()
            self._logger.debug("SQL executed: %s", sql)
        except:
            self._logger.exception("Error writting current data to database")
            return False
        return True
        
    def run(self):
        self._logger.info("Thread started")
        while True:
            time.sleep(self.SAMPLE_PERIOD)
            data = self._wxData.get_data()
            if data == None:
                self._logger.warning("No data received")
            else:
                rc = self._writeDB(data)

