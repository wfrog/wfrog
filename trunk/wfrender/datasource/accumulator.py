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


import logging
from wfcommon.formula.base import AverageFormula
from wfcommon.formula.base import MinFormula
from wfcommon.formula.base import MaxFormula
from wfcommon.formula.base import SumFormula

class AccumulatorDatasource(object):
    '''
    Calculates data from a storage in an iterative fashion by traversing
    only recently added data.

    [ Properties ]

    storage [storage]:
        The underlying storage to get samples.
    '''    
        
    storage: None
    slice: 'hour'    
    span: 23
    
    last_timestamp = time.
    
    default_formulas = {
        'temp': { 'avg' : AverageFormula('temp'), 'min' : MinFormula('temp'), 'max' : MaxFormula('temp') },
        'hum' : { 'avg' : AverageFormula('hum') },
        'press' : { 'avg' : AverageFormula('pressure') },
        'rain' : { 'rate' : AverageFormula('rain_rate'), 'fall' : SumFormula('rain') },
        'uv' : { 'index' : MaxFormula('uv_index') }
    }
            
    logger = logging.getLogger("datasource.accumulator")
    
    def execute(self,data={}, context={}):
        
