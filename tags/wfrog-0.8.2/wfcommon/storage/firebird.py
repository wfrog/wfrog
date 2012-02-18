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

class FirebirdStorage(base.DatabaseStorage):
    '''
    Stores sample data in a Firebird database table.
    
    [ Properties ]
    
    database [string] (optional):
        Path to the database. Defaults 
        to 'localhost:/var/lib/firebird/2.0/data/wfrog.db'
        
    user [string] (optional):
        Database user. Defaults to 'sysdba'.
        
    password [string] (optional):
        Database user password. Defaults to 'masterkey'.
        
    charset [string] (optional):
        Character encoding in the database. Defaults to 'ISO8859_1'.

    tablename [string] (optional):
        Table name. Defaults to 'METEO'.   
    '''
    
    database = 'localhost:/var/lib/firebird/2.0/data/wfrog.db'
    user = 'sysdba'
    password = 'masterkey'
    charset = 'ISO8859_1'

    logger = logging.getLogger('storage.firebird')
    
    def init(self, context=None):
        self.db = wfcommon.database.FirebirdDB(self.database, self.user, self.password, self.charset)

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
        sql = "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = '%s'" % self.tablename
        fields = []

        try:
            self.db.connect()
            for row in self.db.select(sql):
                fields.append(str(row[0].strip()))
        finally:
            self.db.disconnect()

        return fields

