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

class DatabaseDataSource(object):
    """
    Queries a database for consolidated data.
    """"

    db_url: None


    def execute(self,data={}, context={}):
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

