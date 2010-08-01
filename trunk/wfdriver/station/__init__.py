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

import simulator
import wmrs200
import wmr928nx
import wmr200
import auto

# YAML mappings and registration for auto-detect

class YamlAutoDetectStation(auto.AutoDetectStation, yaml.YAMLObject):
    yaml_tag = u'!auto'

class YamlWMRS200Station(wmrs200.WMRS200Station, yaml.YAMLObject):
    yaml_tag = u'!wmrs200'
auto.stations.append(wmrs200)

class YamlWMR928NXStation(wmr928nx.WMR928NXStation, yaml.YAMLObject):
    yaml_tag = u'!wmr928nx'
auto.stations.append(wmr928nx)

class YamlWMR200Station(wmr200.WMR200Station, yaml.YAMLObject):
    yaml_tag = u'!wmr200'
auto.stations.append(wmr200)

class YamlRandomSimulator(simulator.RandomSimulator, yaml.YAMLObject):
    yaml_tag = u'!random-simulator'
auto.stations.append(simulator)

