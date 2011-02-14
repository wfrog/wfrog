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

    source [datasource] (optional):
        A data source performing the query and returning a data structure. When using
        !datatable inside a !data it is not necessary to inform (by default it 
        takes the datasource of the !data element).

    label [integer] (optional):
        Label to be used when creating the table. By default "1".
    """

    source=None
    label=1

    def render(self,data={}, context={}):
        if self.source != None:
	    new_data = self.source.execute(data=data, context=context)
        else:
           new_data = data
        result = {}

        converter = wfcommon.units.Converter(context["units"])

        label_key = 'lbl' + str(self.label) if self.label > 1 else 'lbl'
        for measure in new_data.keys():
            if measure != 'sectors':
                lbls = new_data[measure]['series'][label_key]
                for lbl in lbls:
                    if not lbl in result:
                        result[lbl] = {}
                for (serie, values) in new_data[measure]['series'].iteritems():
                    if serie[:3] != 'lbl':
                        for i in range(len(lbls)):
                            if serie == 'count':  # Unit conversion cannot be applied to count formula
                                result[lbls[i]][measure + '_' + serie] = values[i]
                            else:
                                result[lbls[i]][measure + '_' + serie] = converter.convert(measure, values[i])
        return result


