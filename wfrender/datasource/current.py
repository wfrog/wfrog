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

class CurrentConditionsDataSource(object):
    """
    Reads data from a !current-collector or a yaml file created by it.

    [ Properties ]

    path [string] (optional):
        The location of the yaml file.

    collector: [current-collector] (optional):
        The !current collector.
    """

    logger = logging.getLogger('data.current')

    path = None
    collector = None

    def execute(self,data={}, context={}):
        if self.collector is not None:
            result = self.collector.get_data(context=context)
            if result is not None:
                return result
        if self.path is not None:
            return yaml.load(file(self.path, 'r'))
        self.logger.error('No collector nor path is defined for current conditions datasource')
