import kinterbasdb
import time
from random import random
import logging

kinterbasdb.init(type_conv=0)

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def main():
    db = FirebirdDB("localhost:/var/lib/firebird/2.0/data/test.fdb")
    now = time.time()
    for i in range (0, 10000):
        writeDB(db, time.localtime(now+(600*i)))
        print i

def writeDB(db, t):
    sql = """
INSERT INTO METEO (TIMESTAMP_UTC, TIMESTAMP_LOCAL, TEMP, TEMP_MIN, TEMP_MIN_TIME, TEMP_MAX,
               TEMP_MAX_TIME, HUM, WIND, WIND_DIR, WIND_GUST, WIND_GUST_DIR, WIND_GUST_TIME,
               DEW_POINT, RAIN, RAIN_RATE, RAIN_RATE_TIME, PRESSURE, UV_INDEX)
VALUES (%s, %s, %g, %g, %s, %g, %s, %g, %g, %s, %g, %s, %s, %g, %g, %g, %s, %g, %s)
""" % ("'%s'" % time.strftime(TIME_FORMAT, t),
   "'%s'" % time.strftime(TIME_FORMAT, t),
   random()*20-5,
   random()*10-10,
   "'%s'" % time.strftime(TIME_FORMAT, t),
   random()*30+10,
   "'%s'" % time.strftime(TIME_FORMAT, t),
   random()*100,
   random()*10,
   int(random()*360),
   random()*20,
   int(random()*360),
   "'%s'" % time.strftime(TIME_FORMAT, t),
   random()*20,
   random()*1000,
   random()*5,
   "'%s'" % time.strftime(TIME_FORMAT, t),
   random()*100+950,
   random()*5)
    try:
        bdd = db
        bdd.connect()
        bdd.execute(sql)
        bdd.disconnect()
        logging.debug("SQL executed: %s", sql)
    except:
        logging.exception("Error writting current data to database")
        return False
    return True

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


if __name__ == "__main__":
    main()
