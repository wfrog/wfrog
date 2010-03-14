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

import httplib
import urlparse
import logging

class HttpOutput(object):
    '''
    Sends the events using HTTP post according to WESTEP HTTP transport.

    [ Properties ]

    url:
        Endpoint the events are sent to.
    '''

    connection = None

    logger = logging.getLogger('output.http')

    def send_event(self, event):
        if self.connection == None:
            parts = urlparse.urlsplit(self.url)
            self.connection = httplib.HTTPConnection(parts.netloc)
            self.path = parts.path
            if parts.query:
                self.path = self.path + '?' + parts.query

        try:
            self.connection.request('POST', self.url, str(event))
            response = self.connection.getresponse()
            response.read()
        except Exception, e:
            self.connection = None
            self.logger.critical(self.url+": "+str(e))
            return
        
        if response.status != 200:
            self.logger.critical('HTTP '+response.status+' '+response.reason)
            self.connection = None
