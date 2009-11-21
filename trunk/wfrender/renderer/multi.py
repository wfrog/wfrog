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
import time
from threading import Thread

class MultiRenderer(object):
    """
    Wraps a list of renderers and delegates the rendering to them.
    The result is a dictionary containing the result of each rende-
    rer indexed by names.

    This renderer is closable and will call close on each wrapped
    renderer.

    [ Properties ]

    renderers:
        A dictionary in which keys are names and values are the renderer
        objects the rendering is delegated to.

    parallel: (optional)
        Boolean value. True if the renderers must be called in parallel
        i.e. each in a separate thread.
        Useful when using blocking renderers like schedulers or http.
        When true, this renderer returns nothing, it just launches the
        renderer threads and returns.

    """

    renderers={}
    threads = []
    parallel = False

    logger = logging.getLogger('renderer.multi')

    def render(self,data,context={}):
        result = {}
        for name, r in self.renderers.iteritems():
            
            logger.debug("Rendering "+name)
            
            if self.parallel:
                thread = Thread( target=lambda : r.render(data, context) )
                self.threads.append(thread)
                thread.start()
            else:
                result[name] = r.render(data, context)

        if self.parallel:
            try:
                while True:
                    time.sleep(2)
            except KeyboardInterrupt:
                self.logger.debug("^C received, closing renderers")
                self.close()
                raise

            for thread in self.threads:
                self.logger.debug("Main thread waiting for thread "+str(thread)+" to finish")
                thread.join()

        else:
            return result

    def close(self):
        for name, r in self.renderers.iteritems():
            try:
                r.close()
            except:
                pass
