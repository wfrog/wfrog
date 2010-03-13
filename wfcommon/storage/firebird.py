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

class FirebirdStorage(wfcommon.base.DatabaseStorage):
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
    '''
    
    database = 'localhost:/var/lib/firebird/2.0/data/wfrog.db'
    user = 'sysdba'
    password = 'masterkey'
    charset = 'ISO8859_1'
    
    logger = logging.getLogger('storage.firebird')
    
    def init(self):
        self.db = wfcommon.database.FirebirdDB(self.database, self.user, self.password, self.charset)
