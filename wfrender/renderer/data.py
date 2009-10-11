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

class DataRenderer(object):
    """
    Executes a data query and pass the result to a wrapped renderer.

    [ Properties ]

    source:
        A data source performing the query and returning a data structure.

    renderer:
        A renderer called after the query was performed.
        The data structure is passed as parameter.
    """

    source=None
    renderer=None

    def render(self,data={}, context={}):
        assert self.source is not None, "'data.source' must be set"
        assert self.renderer is not None, "'data.renderer' must be set"
        assert renderer.is_renderer(self.renderer), "'data.renderer' must be a renderer"
        new_data = self.source.execute(data, context)
        new_data.update(data)
        return self.renderer.render(new_data, context)
