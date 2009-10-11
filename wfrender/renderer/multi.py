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

class MultiRenderer(object):
    """
    Wraps a list of renderers and delegates the rendering to them.
    The result is a dictionary containing the result of each rende-
    rer indexed by names.

    Properties

    renderers:
        A dictionary in which keys are names and values are the renderer
        objects the rendering is delegated to.

        If the key name contains an underscore, that means that the data
        passed to
    """

    renderers={}

    def render(self,data,context={}):
        result = {}
        for name, r in self.renderers.iteritems():
            parts = name.split("_")
            if len(parts) > 1 and data.has_key(parts[0]):
                data_to_render = data[parts[0]]
            else:
                data_to_render = data

            result[name] = r.render(data_to_render, context)
        return result
