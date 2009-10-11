import yaml

import database
import xmlquery
import simulator

# YAML mappings

class YamlSimulatorQuery(simulator.SimulatorQuery, yaml.YAMLObject):
    yaml_tag = u'!simulator'

class YamlWxDataXmlQuery(xmlquery.WxDataXmlQuery, yaml.YAMLObject):
    yaml_tag = u'!wxdataxml'
