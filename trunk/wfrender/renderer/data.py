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
        merge_dictionary(new_data, data)
        return self.renderer.render(new_data, context)

def merge_dictionary(dst, src):
    stack = [(dst, src)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) and isinstance(current_dst[key], dict) :
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst
