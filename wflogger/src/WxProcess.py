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
##       Add aggregates support for UV sensor (current value already showing)
##       Prepare por null windchill and heatindex values
##       Control errors & retries writting xml file (not necessary if this feature is move to a renderer)
##       Support for other DBMS (should be easy <== no special features used)
##       Prepare a station simulator driver

import sys, time, kinterbasdb, logging
from threading import Thread
from utils import write2xml

# Remove the dependency to mx.DateTime
try:
    kinterbasdb.init(type_conv=0)
except:
    pass

## Firebird database driver
class FbDB():
    def __init__(self, bdd, user='sysdba', password='masterkey', charset='ISO8859_1'):
        self._bdd = bdd
        self._user = user
        self._password = password
        self._charset = charset
    
    def connect(self):
        self._db = kinterbasdb.connect(dsn=self._bdd, 
                                       user=self._user,
                                       password=self._password, 
                                       charset=self._charset)

    def select(self, sql):
        cursor = self._db.cursor()
        cursor.execute(sql)
        l = []
        for e in cursor.fetchall():
            l.append(e)
        cursor.close()
        self._db.commit()
        return l

    def execute(self, sql):
        cursor = self._db.cursor()
        cursor.execute(sql)
        cursor.close()
        self._db.commit()

    def disconnect(self):
        try:
            self._db.close()
        except:
            pass

class WxProcess (Thread):
    def __init__(self, wxData, config):
        Thread.__init__(self)
        self._wxData = wxData
        self._logger = logging.getLogger('WxLogger.WxProcess')
        ##Configuration
        self.DATABASE = config.get('WxProcess', 'DATABASE')
        self.SAMPLE_PERIOD = config.getint('WxProcess', 'SAMPLE_PERIOD')  
        self.WxDATA_FILENAME = config.get('WxProcess', 'WxDATA_FILENAME')
        self.WxDATA_ROOT = config.get('WxProcess', 'WxDATA_ROOT')
        self.TIME_FORMAT = config.get('WxLogger', 'TIME_FORMAT')

    def _get_rain_rate_time(self, data):
        if data['rain_rate_time'] == None:
            return 'NULL'
        else:
            return "'%s'" % time.strftime(self.TIME_FORMAT, data['rain_rate_time'])

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

    def _get_wind_gust_time(self, data):
        if data['wind_gust_time'] == None:
            return 'NULL'
        else:
            return "'%s'" % time.strftime(self.TIME_FORMAT, data['wind_gust_time'])

    def _get_uv_index(self, data):
        if 'uv_index' in data:
            return '%g' % data['uv_index']
        else:
            return 'NULL'

    def _writeDB(self, data):
        sql = """
INSERT INTO METEO (TIMESTAMP_UTC, TIMESTAMP_LOCAL, TEMP, TEMP_MIN, TEMP_MIN_TIME, TEMP_MAX, 
                   TEMP_MAX_TIME, HUM, WIND, WIND_DIR, WIND_GUST, WIND_GUST_DIR, WIND_GUST_TIME, 
                   DEW_POINT, RAIN, RAIN_RATE, RAIN_RATE_TIME, PRESSURE, UV_INDEX)               
VALUES (%s, %s, %g, %g, %s, %g, %s, %g, %g, %s, %g, %s, %s, %g, %g, %g, %s, %g, %s)
""" % ("'%s'" % time.strftime(self.TIME_FORMAT, time.gmtime()), 
       "'%s'" % time.strftime(self.TIME_FORMAT, time.localtime()),
       data['temp'], 
       data['temp_min'], 
       "'%s'" % time.strftime(self.TIME_FORMAT, data['temp_min_time']), 
       data['temp_max'], 
       "'%s'" % time.strftime(self.TIME_FORMAT, data['temp_max_time']),
       data['hum'], 
       data['wind'],
       self._get_wind_dir(data), 
       data['wind_gust'], 
       self._get_wind_gust_dir(data), 
       self._get_wind_gust_time(data), 
       data['dew_point'],
       data['rain'], 
       data['rain_rate'], 
       self._get_rain_rate_time(data), 
       data['sea_level_pressure'],
       self._get_uv_index(data))
        try:
            bdd = FbDB(self.DATABASE)
            bdd.connect()
            bdd.execute(sql)
            bdd.disconnect()
            self._logger.debug("SQL executed: %s", sql)
        except:
            logging.exception("Error writting current data to database")
            return False
        return True

    def _calculateData(self, tag, initial_date, final_date=None):
        sql = """
SELECT TIMESTAMP_LOCAL, TEMP_MIN, TEMP_MIN_TIME, TEMP_MAX, TEMP_MAX_TIME, 
       HUM, WIND_GUST, WIND_GUST_DIR, WIND_GUST_TIME, RAIN, 
       RAIN_RATE, RAIN_RATE_TIME, PRESSURE
FROM METEO
WHERE TIMESTAMP_LOCAL >= '%s'""" % initial_date
        if final_date != None:
            sql += " AND TIMESTAMP_LOCAL <= '%s' " % final_date
        
        try:
            bdd = FbDB(self.DATABASE)
            bdd.connect()
            result = bdd.select(sql)
            bdd.disconnect()
        except:
            logging.exception("Error calculating data")
            return {}
        
        A_tmin = None 
        A_tmin_tm = None 
        A_tmax = None
        A_tmax_tm = None 
        A_hmin = None
        A_hmin_tm = None
        A_hmax = None
        A_hmax_tm = None
        A_gust = None
        A_gust_d = None 
        A_gust_tm = None 
        A_rain = 0
        A_rrt = None 
        A_rrt_tm = None
        A_pmin = None
        A_pmin_tm = None
        A_pmax = None
        A_pmax_tm = None
        
        for (tm, tmin, tmin_tm, tmax, tmax_tm, hum, gust, gust_d, gust_tm, rain, rrt, rrt_tm, press) in result:
            if A_tmin == None or A_tmin > tmin:
                A_tmin = tmin
                A_tmin_tm = tmin_tm
            if A_tmax == None or A_tmax < tmax:
                A_tmax = tmax
                A_tmax_tm = tmax_tm
            if A_hmin == None or A_hmin > hum:
                A_hmin = hum
                A_hmin_tm = tm
            if A_hmax == None or A_hmax < hum:
                A_hmax = hum
                A_hmax_tm = tm                
            if gust > 0 and (A_gust == None or A_gust < gust):
                A_gust = gust
                A_gust_d = gust_d
                A_gust_tm = gust_tm
            A_rain += rain
            if rrt > 0 and (A_rrt == None or A_rrt < rrt):
                A_rrt = rrt
                A_rrt_tm = rrt_tm
            if A_pmin == None or A_pmin > press:
                A_pmin = press
                A_pmin_tm = tm
            if A_pmax == None or A_pmax < press:
                A_pmax = press
                A_pmax_tm = tm
        if A_tmin != None:
            data = {tag + '.rain_fall.value(mm)': A_rain,
                    tag + '.temperature.max.value(C)': A_tmax,
                    tag + '.temperature.max.time': A_tmax_tm,
                    tag + '.humidity.max.value(%)': A_hmax,
                    tag + '.humidity.max.time': A_hmax_tm,
                    tag + '.pressure.max.value(mb)': A_pmax,
                    tag + '.pressure.max.time': A_pmax_tm,                
                    tag + '.temperature.min.value(C)': A_tmin,
                    tag + '.temperature.min.time': A_tmin_tm,
                    tag + '.humidity.min.value(%)': A_hmin,
                    tag + '.humidity.min.time': A_hmin_tm,
                    tag + '.pressure.min.value(mb)': A_pmin,
                    tag + '.pressure.min.time': A_pmin_tm}
        if A_rrt != None:
            data[tag + '.rain_rate.max.value(mm/h)'] = A_rrt
            data[tag + '.rain_rate.max.time'] = A_rrt_tm
        if A_gust != None:
            data[tag + '.wind_gust.max.speed(m/s)'] = A_gust
            data[tag +'.wind_gust.max.dir(deg)'] = A_gust_d
            data[tag + '.wind_gust.max.time'] = A_gust_tm                
        return data
        
    def _writeXML(self, data):
        WxData = {'time': time.strftime(self.TIME_FORMAT, time.localtime())}
        ## Current data
        WxData['current.temperature(C)'] = data['temp']
        WxData['current.humidity(%)'] = data['hum']
        WxData['current.pressure(mb)'] = data['sea_level_pressure']
        WxData['current.dew_point(C)'] = data['dew_point']
        WxData['current.wind_chill(C)'] = data['wind_chill']
        WxData['current.heat_index(C)'] = data['heat_index']
        WxData['current.rain_rate(mm/s)'] = data['rain_rate']
        WxData['current.wind_avg.speed(m/s)'] = data['wind']
        if data['wind'] != 0.0:
            WxData['current.wind_avg.dir(deg)'] = data['wind_dir']
        WxData['current.wind_gust.speed(m/s)'] = data['wind_gust']
        if data['wind_gust'] != 0.0:
            WxData['current.wind_gust.dir(deg)'] = data['wind_gust_dir']
        if 'uv_index' in data:
            WxData['current.uv_index'] = data['uv_index']
        
        now = time.localtime()
        ## Today data
        d = self._calculateData('today','%s.%s.%s'%(now.tm_year, now.tm_mon, now.tm_mday))
        for k in d.keys(): 
            WxData[k] = d[k]
        ## Monthly data
        d = self._calculateData('month','%s.%s.1'%(now.tm_year, now.tm_mon))
        for k in d.keys(): 
            WxData[k] = d[k]
        ## Yearly data
        d = self._calculateData('year','%s.1.1'%(now.tm_year))
        for k in d.keys(): 
            WxData[k] = d[k]

        try:
            write2xml(WxData, self.WxDATA_ROOT, self.WxDATA_FILENAME)
        except:
            logging.exception("Error writting xml file (%s)", self.WxDATA_FILENAME)
            return False
        return True
        
    def run(self):
        self._logger.info("Thread started")
        bdd = FbDB(self.DATABASE)
        while True:
            time.sleep(self.SAMPLE_PERIOD)
            data = self._wxData.get_data()
            if data == None:
                self._logger.warning("No data received")
            else:
                rc = self._writeDB(data)
                rc = self._writeXML(data)
