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
import time
from threading import Thread

class MultiElement(wrapper.ElementWrapper):
    """
    Wraps a list of children elements and delegates the method calls to 
    them. The result of a method call is a dictionary containing the 
    result of call to the method on each elements indexed by their names.

    [ Properties ]

    children:
        A dictionary in which keys are names and values are the children
        objects the method calls are delegated to.

    parallel: (optional)
        Boolean value. True if the children must be called in parallel
        i.e. each in a separate thread.
        Useful when using blocking childrens like schedulers or servers.
        When true, this element returns nothing, it just launches the
        threads for children method calls and returns.

    """

    children={}
    threads = []
    parallel = False

    logger = logging.getLogger('generic.multi')

    def _call(self, attr, *args, **keywords):  
        result = {}
        for name, r in self.children.iteritems():
            
            self.logger.debug("Calling "+attr+" on child "+name)
            
            if self.parallel:
                thread = Thread( target=lambda : r.__getattribute__(attr).__call__(*args, **keywords) )
                self.threads.append(thread)
                thread.start()
            else:
                result[name] = r.__getattribute__(attr).__call__(*args, **keywords)

        if self.parallel:
            try:
                while True:
                    time.sleep(2)
            except KeyboardInterrupt:
                self.logger.debug("^C received, closing childrens")
                self.close()
                raise

            for thread in self.threads:
                self.logger.debug("Main thread waiting for thread "+str(thread)+" to finish")
                thread.join()

        else:
            return result

    def close(self):
        for name, r in self.children.iteritems():
            try:
                r.close()
            except:
                pass
