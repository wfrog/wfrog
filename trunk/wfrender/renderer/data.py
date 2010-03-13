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

from wfcommon.dict import merge

class DataRenderer(object):
    """
    Executes a data query and pass the result to a wrapped renderer.

    [ Properties ]

    source [datasource]:
        A data source performing the query and returning a data structure.

    renderer [renderer]:
        A renderer called after the query was performed.
        The data structure is passed as parameter.
    """

    source=None
    renderer=None

    def render(self,data={}, context={}):
        assert self.source is not None, "'data.source' must be set"
        assert self.renderer is not None, "'data.renderer' must be set"
        new_data = self.source.execute(data=data, context=context)
        merge(new_data, data)
        return self.renderer.render(data=new_data, context=context)
