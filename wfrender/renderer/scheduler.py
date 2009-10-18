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

import renderer
import time
import logging

class SchedulerRenderer(object):
    """
    Schedules a renderer to be repeatly called every X seconds.
    This renderer runs indefinitely until close() is called.

    [ Properties ]

    renderer
        The renderer to call periodically.

    periodicity:
        The repeat period in seconds.

    """

    renderers = None
    periodicity = None

    alive = True

    logger = logging.getLogger("renderer.scheduler")

    def render(self, data={}, context={}):
        assert renderer.is_renderer(self.renderer), "'scheduler.renderer' must be set to a renderer"
        assert self.periodicity is not None, "'scheduler.periodicity' must be set"

        while self.alive:
            self.logger.debug("Rendering.")
            self.renderer.render(data, context)
            time.sleep(self.periodicity)

    def close(self):
        self.alive = False
