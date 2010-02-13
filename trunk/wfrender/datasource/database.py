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

class DatabaseConfig(object):
    url = None
    username = 'sysdba'
    password = 'masterkey'

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

    TEMP= ['avg(temp), min(temp), max(temp) ', ['avg', 'min', 'max'], 'temp, temp, temp', [ 'avg', 'min', 'max' ]]
    HUM= ['avg(hum)', ['avg'], 'hum', ['avg']]
    DEW= ['avg(dew_point)', ['avg'], 'dew_point', ['avg']]
    WIND= ['avg(wind), max(wind_gust)', ['avg', 'max'], 'wind, wind_gust', ['avg', 'max']]
    PRESS = ['avg(pressure)', ['avg'], 'pressure', ['avg']]
    RAIN= ['sum(rain), avg(rain_rate)', ['fall', 'rate'], 'rain, rain_rate', ['fall', 'rate']]
    UV= ['max(uv_index)', ['index'], 'uv_index', ['index']]

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
    username = None
    password = None
    table = 'METEO'
    slice = 'hour'
    span = 23
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

        config = DatabaseConfig()
        if context.has_key('database'):
            config.__dict__.update(context['database'])
        config.__dict__.update(self.__dict__)

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
            363,
            YEAR, self.BEFORE if not switch else self.AFTER, "%d"+separator+"%m"]

        HOUR=[
            lpa+"EXTRACT(HOUR FROM "+timestamp_field+")"+lpz+conc+"''",
            ' ',
            23,
            DAY, self.AFTER, "%H"]

        MINUTE=[
            lpa+"EXTRACT(HOUR FROM "+timestamp_field+")"+lpz+conc+"':'"+conc+lpa+"EXTRACT(MINUTE FROM "+timestamp_field+")"+lpz,
            ' ',
            60*24-1,
            DAY, self.AFTER, "%H:%M"]

        slices = {
            'minute': MINUTE,
            'hour': HOUR,
            'day': DAY,
            'month': MONTH,
            'year': YEAR }

        where_clause=""
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
                    where_clause = " WHERE "+timestamp_field + ">='" + format(begin) + "' AND "
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

        if slice == "minute":
            measure_index = 2
        else:
            measure_index = 0

        row_length=1
        for measure in self.measures:
            if self.measure_map.has_key(measure):
                select.write(", ")
                select.write(self.measure_map[measure][measure_index])
                row_length = row_length + len(self.measure_map[measure][measure_index+1])

        select.write(" FROM "+self.table + where_clause )

        if slice == "minute":
            select.write(" ORDER BY "+self.timestamp_field)
        else:
            select.write(" GROUP BY slice")
            select.write(" ORDER BY MIN("+self.timestamp_field+")")

        if self.measures.__contains__("sector"):
            sector = "22.5*(round(wind_dir/22.5))"
            sector_select = "SELECT "+sector+", avg(wind), count(*) " + \
                " FROM "+self.table + where_clause + \
                " AND wind > 0 GROUP BY "+sector
            sector_gust = "22.5*(round(wind_gust_dir/22.5))"
            sector_gust_select = "SELECT "+sector_gust+", max(wind_gust)" + \
                " FROM "+self.table + where_clause + \
                " AND wind > 0 GROUP BY "+sector_gust

        db = FirebirdDB(config.url, config.username, config.password)
        db.connect()
        try:
            self.logger.debug(select.getvalue())
            result = db.select(select.getvalue())

            if self.measures.__contains__("sector"):
                self.logger.debug(sector_select)
                sector_result = db.select(sector_select)
                self.logger.debug(sector_gust_select)
                sector_gust_result = db.select(sector_gust_select)

        finally:
            db.disconnect()

        if holes and begin and end:
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

        result_data = {}
        result_data.update(data)
        items = []
        labels = []

        for measure in self.measures:
            if self.measure_map.has_key(measure):
                key = measure
                result_data[key]={ 'series': {} }
                for serie in self.measure_map[measure][measure_index+1]:
                    result_data[key]['series'][serie] = []
                    result_data[key]['series']['lbl'] = labels
                    items.append((key, serie))

        for row in result:
            labels.append(row[0])
            for item in range(0, row_length-1):
                result_data[items[item][0]]['series'][items[item][1]].append(row[item+1])

        if self.measures.__contains__("sector"):
            if not result_data.has_key('wind'):
                result_data['wind'] = {}
            result_data['wind']['sectors'] = {
                "lbl" : ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'],
                "freq" : [0]*16,
                "avg" :  [0]*16,
                "max" :  [0]*16
            }

        sector_map = {}
        for (d,v,c) in sector_result:
            sector_map[d]=(v,c)
        sector_gust_map = {}
        for (d,v) in sector_gust_result:
            sector_gust_map[d]=v

            for i in range(0, 16):
                deg = 22.5*i
                if sector_map.has_key(deg % 360):
                    result_data['wind']['sectors']['avg'][i % 16] = result_data['wind']['sectors']['avg'][i % 16] + sector_map[deg % 360][0];
                    result_data['wind']['sectors']['freq'][i % 16] = result_data['wind']['sectors']['freq'][i % 16] + sector_map[deg % 360][1];

                if sector_gust_map.has_key(deg % 360):
                    result_data['wind']['sectors']['max'][i % 16] = result_data['wind']['sectors']['max'][i % 16] + sector_gust_map[deg % 360];

        result_data['wind']['sectors']['freq'] = normalize(result_data['wind']['sectors']['freq'])

        return result_data

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

def normalize(data):
    s = sum(data)
    if s == 0:
        return data
    result = []
    for d in data:
        result.append(float(d)/s)
    return result

try:
    kinterbasdb.init(type_conv=0)
except:
    pass

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
        try:
            self._db.cursor().execute("DECLARE EXTERNAL FUNCTION Round \
                INT BY DESCRIPTOR, INT BY DESCRIPTOR \
                RETURNS PARAMETER 2 \
                ENTRY_POINT 'fbround' MODULE_NAME 'fbudf'")
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
    ds.slice = 'day'
    ds.span = 4
    data = {}
    data['time_begin'] = '2009-11-01'
    ds.execute(data)
