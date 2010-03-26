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
import urllib

class XmlInput(object):
    '''
    validate [true|false] (optional):
        Whether to validate or not the events against the WESTEP XML schema.
        Validation errors are reported using the log system but do not discard
        the event.
        
    namespace [string] (optional):
        If validation is activated, specifie the default namespace of events.
        Defaults to 'http://www.westep.org/2010/westep'.
        
    location [url] (optional):
        If validation is activated, location of the WESTEP XML schema.
        Defaults to 'http://wfrog.googlecode.com/svn/trunk/xsd/westep.xsd'.
    '''
    _element_doc=True
    
    send_event = None
    
    logger = logging.getLogger("input.xml")
    
    validate = False
    schema = None
    namespace = 'http://www.westep.org/2010/westep'
    location = 'http://wfrog.googlecode.com/svn/trunk/xsd/westep.xsd'
    
    def run(self, send_event):
        self.send_event = send_event
        self.do_run()
    
    def process_message(self, message):        
        from lxml import objectify
        self.logger.debug("Received: %s ", message)
        if self.validate:
            from lxml import etree
            if self.schema is None:                
                self.schema = etree.XMLSchema(file=urllib.urlopen(self.location))
            parsed_message = etree.fromstring(message)
            if not parsed_message.nsmap.has_key(None): #if no default namespace specified, set it
                new_element = etree.Element(parsed_message.tag, attrib=parsed_message.attrib, nsmap={ None: self.namespace })
                new_element.extend(parsed_message.getchildren())
                parsed_message = etree.fromstring(etree.tostring(new_element))
            if not self.schema.validate(parsed_message):
                log = self.schema.error_log
                error = log.last_error
                self.logger.error("XML validation error: %s", error)

        event = objectify.XML(message)
        event._type = event.tag.replace('{'+self.namespace+'}','')
        self.send_event(event)
