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
import wrapper
from os import path

from Cheetah.Template import Template

class IncludeElement(wrapper.ElementWrapper):
    """
    Includes another yaml configuration file.
    The included file must define only one root element.  

    [ Properties ]

    path:
        A path to the file to include relative to the main config file.
    """

    path = None
    target = None
    variables = None

    logger = logging.getLogger("generic.include")

    def _call(self, attr, *args, **keywords):        
        
        config_file = keywords['context']['_yaml_config_file']
        
        if not self.target:
            dir_name = path.dirname(config_file)
            abs_path=path.join(dir_name, self.path)

            if self.variables:
                conf_str = str(Template(file=file(abs_path, "r"), searchList=[self.variables]))
            else:
                conf_str = file(abs_path, "r").read()
            config = yaml.load(conf_str)
            self.target = config.values()[0]

        self.logger.debug('Calling '+attr+' on ' + str(self.target))
        return self.target.__getattribute__(attr).__call__(*args, **keywords)
