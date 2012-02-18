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

import logging
import base
import wfcommon.database

class MysqlStorage(base.DatabaseStorage):
    '''
    Stores sample data in a MySQL database table.
    
    [ Properties ]
    
    database [string] (optional):
        Name of the database. defaults to 'wfrog'.
        
    host [string] (optional):
        Database host. Defaults to 'localhost'.
        
    port [string] (optional):
        Database TCP port.
        
    user [string] (optional):
        Database usename. Defaults to 'root'.
        
    password [string] (optional):
        Database user password. Defaults to 'root'.    

    tablename [string] (optional):
        Table name. Defaults to 'METEO'.   
    '''

    database = 'wfrog'
    host = 'localhost'
    port = 3306
    user = 'root'
    password = 'root'

    logger = logging.getLogger('storage.mysql')

    def init(self, context=None):
        self.db = wfcommon.database.MySQLDB(self.database, self.host, self.port, self.user, self.password)

        table_fields = self._get_table_fields()
        # Verify Mandatory fields
        assert 'TIMESTAMP_UTC' in table_fields
        assert 'TIMESTAMP_LOCAL' in table_fields
        for field in self.mandatory_storage_fields:
            assert field in table_fields
        # Obtain actual storage fields
        self.storage_fields = self.mandatory_storage_fields + \
                              [field for field in self.optional_storage_fields if field in table_fields]
        self.logger.info("Table %s detected with fields: %s" % (self.tablename, ', '.join(self.storage_fields)))


    def _get_table_fields(self):
        sql = "show columns from %s;" % self.tablename
        fields = []

        try:
            self.db.connect()
            for row in self.db.select(sql):
                fields.append(row[0])
        finally:
            self.db.disconnect()

        return fields

