## Copyright 2011 Jordi Puigsegur <jordi.puigsegur@gmail.com>
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


class StaticFileRenderer(object):
    """
    Passes an existing static file to the renderer

    render result [string]:
        The path to the generated file.

    [ Properties ]

    path [string]:
        The absolute or relative path to the file to create.
    """

    path = None

    def render(self, data={}, context={}):
        assert self.path is not None, "'staticfile.path' must be set"
        return self.path
