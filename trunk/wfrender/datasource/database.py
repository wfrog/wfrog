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

kinterbasdb.init(type_conv=0)

class DatabaseDataSource(object):
    """
    Queries a database for consolidated data.
    """

    timestamp_field = "TIMESTAMP_LOCAL"

    separator = '.'
    switch = True #False

    BEFORE=1
    AFTER=2

    lpad_function="DECLARE EXTERNAL FUNCTION lpad \
           CSTRING(255) NULL, INTEGER, CSTRING(1) NULL \
           RETURNS CSTRING(255) FREE_IT \
           ENTRY_POINT 'IB_UDF_lpad' MODULE_NAME 'ib_udf'"

    lpa="lpad("
    lpz =")"

    YEAR=[
        "EXTRACT(YEAR FROM "+timestamp_field+")",
        '',
        sys.maxint,
        None, None]

    MONTH=[
        "EXTRACT(MONTH FROM "+timestamp_field+")&'"+separator+"'&EXTRACT(YEAR FROM "+timestamp_field+")",
        '',
        sys.maxint,
        None, BEFORE]

    DAY=[
        "EXTRACT(" + ("DAY" if not switch else "MONTH")+" FROM "+timestamp_field+")&'.'&EXTRACT("+("MONTH" if not switch else "DAY")+" FROM "+timestamp_field+")",
        "&'"+separator+"'&",
        365,
        YEAR, BEFORE if not switch else AFTER]

    HOUR=[
        "EXTRACT(HOUR FROM "+timestamp_field+")&':00'",
        "&' '&",
        24,
        DAY, AFTER]

    MINUTE=[
        "EXTRACT(HOUR FROM "+timestamp_field+")&':'&EXTRACT(MINUTE FROM "+timestamp_field+")",
        "&' '&",
        60*24,
        DAY, AFTER]

    periods = {
        'minute': MINUTE,
        'hour': HOUR,
        'day': DAY,
        'month': MONTH,
        'year': YEAR }

    TEMP= ['avg(temp) as temp_avg, min(temp) as temp_min, max(temp) as temp_max)']
    HUM= ['avg(hum) as hum_avg']
    DEW= ['avg(dew) as dew_avg']
    WIND= ['avg(wind) as wind_avg, max(wind_gust) as wind_gust']
    PRESSURE= ['avg(pressure) as pressure_avg']
    RAIN= ['sum(rain) as rain_sum, avg(rain_rate) as rain_rate']
    UV= ['avg(uv) as uv_avg']

    measure_list = (TEMP, HUM, DEW, WIND, PRESSURE, RAIN, UV)

    url = None
    username = 'sysdba'
    password = 'masterkey'
    table = 'METEO'
    period = 'hour'
    span = 24*366
    measures = [ TEMP, HUM, DEW, WIND, PRESSURE, RAIN, UV ]

    def get_key(self, p, span, key):
        (sql, sep, max_span, next, pos) = (p[0], p[1], p[2], p[3], p[4])

        actual_sep = ''
        if span > max_span:
            key = self.get_key(next, span / max_span, key)
            actual_sep=sep
        if pos == self.AFTER:
            key = key + actual_sep + sql
        else:
            key = sql + actual_sep + key
        return key

    def execute(self,data={}, context={}):

        start = False
        stop = False

        key = self.get_key(self.periods[self.period], self.span, "")

        select = StringIO()
        select.write("SELECT "+key+" AS key")

        for measure in self.measures:
            select.write(", ")
            select.write(measure[0])

        select.write(" FROM "+self.table+" WHERE ... ")
        select.write("GROUP BY "+key)

        print select.getvalue()

    def create_column_sql(measure, period, span):
        return

DatabaseDataSource().execute()


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

