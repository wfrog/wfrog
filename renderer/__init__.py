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
