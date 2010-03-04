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

import yaml
import logging
from os import path

from functools import partial

from Cheetah.Template import Template

class IncludeRenderer(object):
    """
    Includes another yaml configuration file.
    The included file must define only one root renderer.

    [ Properties ]

    path:
        A path to the file to include relative to the main config file.
    """

    path = None
    renderer = None
    variables = None

    logger = logging.getLogger("renderer.include")

    def _call(self, data={}, context={}):
        if not self.renderer:
            dir_name = path.dirname(context['_yaml_config_file'])
            abs_path=path.join(dir_name, self.path)

            if self.variables:
                conf_str = str(Template(file=file(abs_path, "r"), searchList=[self.variables]))
            else:
                conf_str = file(abs_path, "r").read()
            config = yaml.load(conf_str)
            self.renderer = config["renderer"]

        return self.renderer.render(data,context)

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr.startswith('__'):
                raise AttributeError()
            else:
                return partial(object.__getattribute__(self,'_call'))
