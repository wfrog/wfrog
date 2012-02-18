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

import aggregator
import flush
import xmlfile
import buffer

# YAML mappings

class YamlAggregatorCollector(aggregator.AggregatorCollector, yaml.YAMLObject):
    yaml_tag = u'!aggregator'

class YamlFlushCollector(flush.FlushCollector, yaml.YAMLObject):
    yaml_tag = u'!flush'

class YamlBufferCollector(buffer.BufferCollector, yaml.YAMLObject):
    yaml_tag = u'!buffer'

class YamlXmlFileCollector(xmlfile.XmlFileCollector, yaml.YAMLObject):
    yaml_tag = u'!xmlfile'
