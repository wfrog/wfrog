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

from Cheetah.Template import Template
import logging

def rnd(value, dec=0):
    if value == round(value):
        return int(round(value))
    else:
        return round(value, dec)

class TemplateRenderer(object):
    """
    Executes a wrapped renderer and fills a Cheetah template with the
    resulting data. The result of rendering is a list [ mime, document ].

    [ Properties ]

    renderer [renderer]:
        The underlying renderer providing the data to render.

    path [string]:
        Path to the template file.

    mime [string] (optional):
        The mime type of the generated document. Defaults to 'text/plain'.
    """

    path = None
    renderer = None
    mime = "text/plain"

    logger = logging.getLogger("renderer.template")

    def render(self,data={}, context={}):
        content = {}
        if self.renderer:
            content = self.renderer.render(data=data, context=context)
        self.logger.debug("Rendering with template "+self.path)
        content["rnd"]=rnd
        template = Template(file=file(self.path, "r"), searchList=[content, context])
        return [ self.mime, str(template) ]
