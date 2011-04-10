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

import wfcommon.units
import logging

class ValueRenderer(object):
    """
    Returns the main value as a string in the right units according to the context.

    render result [numeric]:
        The selected value.

    [ Properties ]

    key [string]:
        Refers to the dictionary key of the data part to render, e.g. 'temp'.

    select [value|last] (optional):
        Chooses what to render:
        - value: the 'value' item under the data part. Default.
        - last: the last element of the chosen serie (see the 'serie'
          property).

    serie [string] (optional):
        The chosen serie name (e.g. 'avg') if 'select' is set to 'last'.
    """

    key = None
    select = 'value'
    value = None
    serie = None

    logger = logging.getLogger('renderer.value')

    def render(self,data,context={}):
        if self.select == "last": 
            return data[self.key]['series'][self.serie][len(data[self.key]['series'][self.serie])-1]
        elif self.select == "value":
            val_key = self.value if self.value else 'value'
            self.logger.debug("Getting value for '"+self.key+"."+val_key+"'")
            return wfcommon.units.Converter(context["units"]).convert(self.key, data[self.key][val_key])

