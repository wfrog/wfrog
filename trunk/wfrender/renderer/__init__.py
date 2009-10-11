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

import chart
import data
import file
import http
import multi
import template
import value

# Assert functions
def is_renderer(obj):
    return obj is not None and dir(obj).__contains__('render')

def is_dict(obj):
    return obj is not None and dir(obj).__contains__('has_key')

def assert_renderer_dict(name, obj):
    assert isDict(obj), "'"+name+"' is not a key/value dictionary"
    for r in obj.keys():
        assert isRenderer(obj[r]), "'"+name+"."+r+"' is not a renderer"

# YAML mappings

class YamlGoogleChartRenderer(chart.GoogleChartRenderer, yaml.YAMLObject):
    yaml_tag = u'!chart'

class YamlGoogleWindRadarChartRenderer(chart.GoogleChartWindRadarRenderer, yaml.YAMLObject):
    yaml_tag = u'!windradar'

class YamlDataRenderer(data.DataRenderer, yaml.YAMLObject):
    yaml_tag = u'!data'

class YamlFileRenderer(file.FileRenderer, yaml.YAMLObject):
    yaml_tag = u'!file'

class YamlHttpRenderer(http.HttpRenderer, yaml.YAMLObject):
    yaml_tag = u'!http'

class YamlMultiRenderer(multi.MultiRenderer, yaml.YAMLObject):
    yaml_tag = u'!multi'

class YamlTemplateRenderer(template.TemplateRenderer, yaml.YAMLObject):
    yaml_tag = u'!template'

class YamlValueRenderer(value.ValueRenderer, yaml.YAMLObject):
    yaml_tag = u'!value'
