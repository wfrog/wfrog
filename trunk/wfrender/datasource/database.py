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

import kinterbasdb
from StringIO import StringIO
import sys
import logging
import datetime

class DatabaseDataSource(object):
    """
    Queries a database for consolidated data.
    """

    logger = logging.getLogger("datasource.database")

    timestamp_field = "TIMESTAMP_LOCAL"

    separator = '.'
    switch = False
    conc = chr(124)*2

    BEFORE=1
    AFTER=2

    lpa="lpad("
    lpz=",2,'0')"

    TEMP= ['avg(temp) as temp_avg, min(temp) as temp_min, max(temp) as temp_max', 3]
    HUM= ['avg(hum) as hum_avg', 1]
    DEW= ['avg(dew_point) as dew_avg', 1]
    WIND= ['avg(wind) as wind_avg, max(wind_gust) as wind_gust', 2]
    PRESS = ['avg(pressure) as press_avg', 1]
    RAIN= ['sum(rain) as rain_sum, avg(rain_rate) as rain_rate', 2]
    UV= ['avg(uv_index) as uv_avg', 1]

    measure_map = {
        'temp': TEMP,
        'hum': HUM,
        'dew': DEW,
        'wind': WIND,
        'press': PRESS,
        'rain': RAIN,
        'uv': UV
    }    

    url = None
    username = 'sysdba'
    password = 'masterkey'
    table = 'METEO'
    slice = 'hour'
    span = 24
    measures = [ 'temp', 'hum', 'dew', 'wind', 'sector', 'press', 'rain', 'uv' ]
    holes = True

    def get_key(self, p, span, key='', date_format=''):
        (sql, sep, max_span, next, pos, df) = (p[0], p[1], p[2], p[3], p[4], p[5])

        actual_sep = ''
        if span > max_span:
            (key, date_format) = self.get_key(next, span / max_span, key, date_format)
            actual_sep=sep            
        if not actual_sep == '':
            db_sep = self.conc+"'"+actual_sep+"'"+self.conc
        else:
            db_sep=''
                                 
        if pos == self.AFTER:
            key = key + db_sep + sql
            date_format = date_format + actual_sep + df
        else:
            key = sql + db_sep + key
            date_format = df + actual_sep + date_format
        return (key, date_format)

    def execute(self,data={}, context={}):

        conc = self.conc
        lpa = self.lpa
        lpz = self.lpz
        separator = self.separator
        timestamp_field = self.timestamp_field
        switch = self.switch
        holes = self.holes
        
        begin = parse(data['time_begin']) if data.has_key('time_begin') else None
        end = parse(data['time_end']) if data.has_key('time_end') else None
        span = data['time_span'] if data.has_key('time_span') else self.span
        slice = data['time_slice'] if data.has_key('time_slice') else self.slice

        YEAR=[
            "EXTRACT(YEAR FROM "+timestamp_field+")",
            '',
            sys.maxint,
            None, None, "%Y"]

        MONTH=[
            lpa+"EXTRACT(MONTH FROM "+timestamp_field+")"+lpz+conc+"'"+separator+"'"+conc+"EXTRACT(YEAR FROM "+timestamp_field+")",
            '',
            sys.maxint,
            None, self.BEFORE, "%m"+separator+"%Y"]

        DAY=[
            lpa+"EXTRACT(" + ("DAY" if not switch else "MONTH")+" FROM "+timestamp_field+")"+lpz+conc+"'.'"+conc+lpa+"EXTRACT("+("MONTH" if not switch else "DAY")+" FROM "+timestamp_field+")"+lpz,
            separator,
            365,
            YEAR, self.BEFORE if not switch else self.AFTER, "%d"+separator+"%m"]

        HOUR=[
            lpa+"EXTRACT(HOUR FROM "+timestamp_field+")"+lpz+conc+"':00'",
            ' ',
            24,
            DAY, self.AFTER, "%H:00"]

        MINUTE=[
            lpa+"EXTRACT(HOUR FROM "+timestamp_field+")"+lpz+conc+"':'"+conc+lpa+"EXTRACT(MINUTE FROM "+timestamp_field+")"+lpz,
            ' ',
            60*24,
            DAY, self.AFTER, "%H:%M"]

        slices = {
            'minute': MINUTE,
            'hour': HOUR,
            'day': DAY,
            'month': MONTH,
            'year': YEAR }

        if begin:
            where_clause = " WHERE " + timestamp_field + ">='" + format(begin) + "'"
            if end:
                where_clause = where_clause + " AND " + timestamp_field + "<='" + format(end) + "'"
                span=sys.maxint # TODO: calculate exact span
            else:                
                if span:
                    end=delta(begin, span, slice)
                    where_clause = where_clause + " AND " + timestamp_field + "<='" + format(end) + "'"
                else:
                    end=datetime.datetime.now()
                    span=sys.maxint # TODO: calculate exact span
        else:
            if end:
                if span:
                    begin = delta(end, -span, slice)
                    where_clause = " WHERE "+timestamp_field + ">='" + format(begin) + " AND " 
                    where_clause = where_clause + timestamp_field + "<='" + format(end) + "'"
                else:
                    span=sys.maxint # TODO: calculate exact span
            else:                
                end=datetime.datetime.now()
                begin=delta(datetime.datetime.now(), -span, slice)
                if span:
                    where_clause = " WHERE "+timestamp_field + ">='" + format(begin) + "'"         
                else:
                    span=sys.maxint # TODO: calculate exact span

        (key, date_format) = self.get_key(slices[slice], span)

        select = StringIO()
                
        select.write("SELECT "+key+" AS slice")

        row_length=1
        for measure in self.measures:
            if self.measure_map.has_key(measure):
                select.write(", ")
                select.write(self.measure_map[measure][0])         
                row_length = row_length + self.measure_map[measure][1]    

        select.write(" FROM "+self.table + where_clause )
        
        if not slice == "sample":
            select.write(" GROUP BY slice")
        
        select.write(" ORDER BY MIN("+self.timestamp_field+")")
        
        db = FirebirdDB(self.url)
        db.connect()
        try:
            result = db.select(select.getvalue())   
        finally:
            db.disconnect()
        
        if holes:
            map = {}
            for row in result:
                map[row[0]]=row
                          
            result = []
            d = begin
            while d <= end:
                df = d.strftime(date_format)
                if map.has_key(df):
                    result.append(map[df])
                else:
                    r = tuple([df]+([None]*(row_length-1)))
                    result.append(r)
                d = delta(d, 1, slice)
        
        for row in result:
            print repr(row)

        self.logger.debug(select.getvalue())

def parse(isodate):
    if len(isodate) == 10:
        return datetime.datetime.strptime(isodate, "%Y-%m-%d")
    else:
        return datetime.datetime.strptime(isodate, "%Y-%m-%d"+isodate[10]+"%H:%M:%S")

def format(d):
    return d.isoformat(' ')

def delta(d, n, slice):
    d2=d.replace(microsecond=0)
    if slice == 'minute':
        return d2+datetime.timedelta(0,n*60)
    if slice == 'hour':
        return d2+datetime.timedelta(0,n*3600)
    if slice == 'day':
        return d2+datetime.timedelta(n)
    if slice == 'month':
        return d2+datetime.timedelta(n*31) # TODO: calculate exact start of month
    if slice == 'year':
        return d2+datetime.timedelta(n*365) # TODO: calculate exact start of year

kinterbasdb.init(type_conv=0)

class FirebirdDB():
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
        try:
            self._db.cursor().execute("DECLARE EXTERNAL FUNCTION lpad \
               CSTRING(255) NULL, INTEGER, CSTRING(1) NULL \
               RETURNS CSTRING(255) FREE_IT \
               ENTRY_POINT 'IB_UDF_lpad' MODULE_NAME 'ib_udf'")
        except:
            pass

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ds = DatabaseDataSource()
    ds.url = 'localhost:/var/lib/firebird/2.0/data/wfrog.db'
    ds.slice = 'hour'
    ds.span = 10
    data = {}
    data['time_begin'] = '2009-10-27 14:00:00'
    ds.execute(data)
