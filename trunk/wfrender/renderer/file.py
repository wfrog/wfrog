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

import os, time
import renderer as renderer_module

class FileRenderer(object):
    """
    Writes the result of the wrapped renderer to a file.
    Currently supports only text output.

    [ Properties ]

    path:
        The absolute or relative path to the file to create.

    suffix: (optional)
        If present, specifies that the filename is generated by the
        path, a generated unique id and the provided suffix. Useful
        for generating temporary files.
    """

    renderer = None
    path = None
    suffix = None

    def render(self, data={}, context={}):
        assert renderer_module.is_renderer(renderer), "'file.renderer' must be set to a renderer"
        assert path is not None, "'file.path' must be set"

        [ mime, content ] = self.renderer.render(data, context)

        if self.suffix:
            filename=self.path+"-"+str(os.getpid())+"-"+ \
            str(int(( time.time() % 1000 ) * 10000))+"." + self.suffix
        else:
            filename=self.path

        f = open(filename, "w")
        try:
            f.write(content)
        finally:
            f.close()

        return "Wrote result to "+filename