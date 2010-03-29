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

import include
import multi
import service
import stopwatch

# YAML mappings

class YamlIncludeElement(include.IncludeElement, yaml.YAMLObject):
    yaml_tag = u'!include'

class YamlMultiElement(multi.MultiElement, yaml.YAMLObject):
    yaml_tag = u'!multi'

class YamlServiceElement(service.ServiceElement, yaml.YAMLObject):
    yaml_tag = u'!service'

class YamlStopWatchElement(stopwatch.StopWatchElement, yaml.YAMLObject):
    yaml_tag = u'!stopwatch'
