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

from wfcommon.dict import merge
import wfcommon.units

class DataTableRenderer(object):
    """
    Executes a data query and renders the result in a data table.

    render result [any]:
        The data table corresponding to the data query.

    [ Properties ]

    source [datasource]:
        A data source performing the query and returning a data structure.
    """

    source=None

    def render(self,data={}, context={}):
        assert self.source is not None, "'data.source' must be set"
        new_data = self.source.execute(data=data, context=context)
        merge(new_data, data)
        result = {}

        converter = wfcommon.units.Converter(context["units"])

        for measure in new_data.keys():
            lbls = new_data[measure]['series']['lbl']
            for lbl in lbls:
                if not lbl in result:
                    result[lbl] = {}
            for (serie, values) in new_data[measure]['series'].iteritems():
                if serie != 'lbl':
                    for i in range(len(lbls)):
                        if serie != 'count':  # Unit conversion cannot be applied to count formula
                            result[lbls[i]][measure + '_' + serie] = converter.convert(measure, values[i])
                        else:
                            result[lbls[i]][measure + '_' + serie] = values[i]
        return result


