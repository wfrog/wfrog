## Copyright 2009 Laurent Bovet <laurent.bovet@windmaster.ch>
##                Jordi Puigsegur <jordi.puigsegur@gmail.com>
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

import datetime
import decimal

try:
    import kinterbasdb
    if __name__ == '__main__': print "firebird driver present"
except ImportError:
    kinterbasdb = None

if kinterbasdb:
    try:
        kinterbasdb.init(type_conv=199) # Set type conversion (datetime / floats)
        if __name__ == '__main__': print "firebird conversion 199"
        #kinterbasdb.init(type_conv=200) # Set type conversion (datetime / decimal)
    except:
        try:
            kinterbasdb.init(type_conv=0) # Set type conversion (time tuple / floats) old python 2.5
            if __name__ == '__main__': print "firebird conversion 0"
        except:
            pass
try:
    import MySQLdb
    if __name__ == '__main__': print "mysql driver present"
except ImportError:
    MySQLdb = None


# Converts time tuples (old Firebird format) to datetime
# and Decimal into floats.
# Working with Decimal numbers needs to be studied ...

def adjust(obj):
    try:
        if isinstance(obj, tuple):
            if len(obj) == 7 or len(obj) == 6:
                return datetime.datetime(*obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return obj
    except:
        return obj


class DB():
    dbObject = None

    def __init__(self):
        raise Exception("Method cannot be called")

    def connect(self):
        raise Exception("Method cannot be called")

    def select(self, sql):
        if self.dbObject == None:
            raise Exception("Not connected to a Database")
        cursor = self.dbObject.cursor()
        cursor.execute(sql)

        try:
            while True:
                row = cursor.fetchone()
                if row is not None:
                    yield tuple(map(adjust, row))
                else:
                    break
        finally:
            cursor.close()
            self.dbObject.commit()

    def execute(self, sql):
        if self.dbObject == None:
            raise Exception("Not connected to a Database")
        cursor = self.dbObject.cursor()
        cursor.execute(sql)
        cursor.close()
        self.dbObject.commit()

    def disconnect(self):
        try:
            self.dbObject.close()
            self.dbObject = None
        except:
            pass


## Firebird database driver

class FirebirdDB(DB):
    def __init__(self, db, user='sysdba', password='masterkey', charset='ISO8859_1'):

        self.db = db
        self.user = user
        self.password = str(password)
        self.charset = charset

    def connect(self):
        if self.dbObject != None:
            raise Exception("Firebird: already connected to %s" % self.db)
        self.dbObject = kinterbasdb.connect(dsn=self.db,
                                            user=self.user,
                                            password=self.password,
                                            charset=self.charset)

## MySQL database driver

class MySQLDB(DB):
    def __init__(self, db,  host, port=3306, user='root', password='root'):
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = str(password)

    def connect(self):
        if self.dbObject != None:
            raise Exception("MySQL: already connected to %s" % self.db)
        self.dbObject = MySQLdb.connect(host=self.host,
                                        port=self.port,
                                        user=self.user,
                                        passwd=self.password,
                                        db=self.db)

## sqlite3 database driver

try:
    import sqlite3
    if __name__ == '__main__': print "sqlite driver present"
except ImportError:
    sqlite3 = None


class Sqlite3(DB):
    def __init__(self, filename):
        self.filename = filename

    def connect(self):
        if self.dbObject != None:
            raise Exception("MySQL: already connected to %s" % self.db)
        #http://stackoverflow.com/questions/1829872/read-datetime-back-from-sqlite-as-a-datetime-in-python
        self.dbObject = sqlite3.connect(self.filename,  detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)


## Database driver factory
##

def DBFactory(configuration):
    """
    Expects a python dictionary with the database configuration and returns
    its corresponding database object.

    Two types of database are available:
    1) firebird
       {'type' : 'firebird',
        'database' : 'localhost:/var/lib/firebird/2.0/data/wfrog.db',
        'user' : 'sysdba',
        'password' : 'masterkey'}
    2) mysql
       {'type' : 'mysql',
        'database' : 'wfrog',
        'host' : 'localhost',
        'port' : 3306,
        'user' : 'root',
        'password' : 'root'}
    """

    if 'type' not in configuration: raise(Exception('DBFactory: database type not specified'))
    type = configuration['type'].lower()

    if type == 'firebird':
        if not kinterbasdb:
            raise(Exception("DBFactory: kinterbasdb (Firebirds python's database driver) is not installed"))
        if 'database' not in configuration:
            raise(Exception('DBFactory: Firebird database connection string not specified'))
        database = configuration['database']
        if 'user' not in configuration:
            user = 'SYSDBA'
        else:
            user = configuration['user']
        if 'password' not in configuration:
            password = 'masterkey'
        else:
            password = configuration['password']
        if 'charset' not in configuration:
            charset = 'ISO8859_1'
        else:
            charset = configuration['charset']

        return FirebirdDB(database, user, password, charset)

    elif type == 'mysql':
        if not MySQLdb:
            raise(Exception("DBFactory: MySQLdb (mysql python's database driver) is not installed"))
        if 'database' not in configuration:
            raise(Exception('DBFactory: MySql database name not specified'))
        database = configuration['database']
        if 'host' not in configuration:
            raise(Exception('DBFactory: MySql database name not specified'))
        host = configuration['host']
        if 'port' not in configuration:
            port = 3306
        else:
            port = int(configuration['port'])
        if 'user' not in configuration:
            user = 'root'
        else:
            user = configuration['user']
        if 'password' not in configuration:
            password = 'root'
        else:
            password = configuration['password']

        return  MySQLDB(database, host, port, user, password)

    else:
        raise(Exception('database type %s not supported' % configuration))


if __name__ == '__main__':

    if kinterbasdb:
        firebird_test = {'type' : 'firebird',
                         'database' : 'localhost:/var/lib/firebird/2.0/data/wfrog.db',
                         'user' : 'sysdba',
                         'password' : 'masterkey'}
        db = DBFactory(firebird_test)
        db.connect()
        print db.select("SELECT COUNT(*) FROM METEO")
        db.disconnect()
    else:
        print "kinterbasdb (Firebird python's driver) is not installed"

    if MySQLdb:
        mysql_test = {'type' : 'mysql',
                      'database' : 'wfrog',
                      'host' : 'localhost',
                      'port' : 3306,
                      'user' : 'root',
                      'password' : 'root'}
        db = DBFactory(mysql_test)
        db.connect()
        print db.select("SELECT COUNT(*) FROM METEO")
        db.disconnect()
    else:
        print "MySQLdb (mysql python's driver) is not installed"

