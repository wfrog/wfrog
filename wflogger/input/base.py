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

class XmlInput(object):
    '''
    Base class for inputs receiving events as WESTEP XML messages.
    '''
    
    send_event = None
    
    logger = logging.getLogger("input.xml")
    
    def run(self, send_event):
        self.send_event = send_event
        self.do_run()
    
    def process_message(self, message):
        from lxml import objectify
        event = objectify.XML(message)
        event._type = event.tag.replace('{http://www.westep.org/2010/westep}','')
        self.logger.debug("Received: %s ", message)
        self.send_event(event)
