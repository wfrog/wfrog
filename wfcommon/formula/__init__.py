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
import base
import wind

class YamlAverageFormula(base.AverageFormula, yaml.YAMLObject):
    yaml_tag = u'!avg'

class YamlMinFormula(base.MinFormula, yaml.YAMLObject):
    yaml_tag = u'!min'

class YamlMaxFormula(base.MaxFormula, yaml.YAMLObject):
    yaml_tag = u'!max'

class YamlSumFormula(base.SumFormula, yaml.YAMLObject):
    yaml_tag = u'!sum'

class YamlPredominantWindFormula(wind.PredominantWindFormula, yaml.YAMLObject):
    yaml_tag = u'!predominant'

class YamlWindSectorAverageFormula(wind.WindSectorAverageFormula, yaml.YAMLObject):
    yaml_tag = u'!sector-avg'

class YamlWindSectorMaxFormula(wind.WindSectorMaxFormula, yaml.YAMLObject):
    yaml_tag = u'!sector-max'

class YamlWindSectorFrequencyFormula(wind.WindSectorFrequencyFormula, yaml.YAMLObject):
    yaml_tag = u'!sector-freq'
