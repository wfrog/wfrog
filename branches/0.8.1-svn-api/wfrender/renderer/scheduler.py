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

import time
import logging

class SchedulerRenderer(object):
    """
    Schedules a renderer to be called periodically.
    This renderer runs indefinitely until 'close()' is called.

    render result [none]:
        Nothing is returned by this renderer.

    [ Properties ]

    renderer [renderer]:
        The renderer to call periodically.

    period [numeric]:
        The period in seconds.

    delay [numeric] (optional):
        Delay before first execution. By default 60 seconds.
    """

    renderers = None
    period = None
    delay = 60

    alive = True

    logger = logging.getLogger("renderer.scheduler")

    def render(self, data={}, context={}):
        assert self.period is not None, "'scheduler.period' must be set"

        time.sleep(self.delay)
        self.logger.info("Started scheduler")
        while self.alive:
            self.logger.debug("Rendering.")
            try:
                self.renderer.render(data=data, context=context)
            except Exception, e:
                self.logger.exception(e)
            time.sleep(self.period)

    def close(self):
        self.alive = False
