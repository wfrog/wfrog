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
import wfcommon.base
import wfcommon.database

class MysqlStorage(wfcommon.base.DatabaseStorage):
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
    '''

    database = 'wfrog'
    host = 'localhost'
    port = 3306
    user = 'root'
    password = 'root'

    logger = logging.getLogger('storage.mysql')

    def init(self):
        self.db = wfcommon.database.MySQLDB(self.database, self.host, self.port, self.user, self.password)
