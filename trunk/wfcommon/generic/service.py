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
import wrapper

# The global service registry
services = {}

class ServiceElement(wrapper.ElementWrapper):
    """
    Provides a dictionary of objects global to the python process.
    Objects are called if they are registered under a name.

    [ Properties ]

    name [string]:
        Name under which an object is registered.
        
    instance [object] (optional):
        Object to register as a service. If absent, this element
        makes a lookup of the service. If not found, it behaves silently
        and does not fail on method calls.
        
    """

    name = None
    instance = None

    logger = logging.getLogger("generic.service")

    def _call(self, attr, *args, **keywords):        
    
        assert self.name is not None, "'service.name' must be set"
        
        global services
        
        if self.instance:
            if not services.__contains__(self.name):
                self.logger.debug('Registering service '+str(self.instance)+" under '" + self.name +"'")
                services[self.name] = self.instance

        if services.__contains__(self.name):
            self.logger.debug('Calling '+attr+' on ' + str(services[self.name]))
            return services[self.name].__getattribute__(attr).__call__(*args, **keywords)
        else:
            self.logger.debug("No service registered under '" + self.name +"'. Ignoring call to '" +attr+"'")
