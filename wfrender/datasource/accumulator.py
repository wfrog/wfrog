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

import copy
import datetime
import threading

class AccumulatorDatasource(object):
    '''
    Calculates data from a storage in an iterative fashion by traversing
    only recently added data.

    [ Properties ]

    storage [storage]:
        The underlying storage to get samples.
    '''

    storage = None
    slice = 'hour'
    span = 23

    formats = { 'month': '%m',
                'day': '%d',
                'hour': '%H:00',
                'minute': '%H:%M' ]

    period = 120

    default_formulas = {
        'temp': { 'avg' : AverageFormula('temp'), 'min' : MinFormula('temp'), 'max' : MaxFormula('temp') },
        'hum' : { 'avg' : AverageFormula('hum') },
        'press' : { 'avg' : AverageFormula('pressure') },
        'rain' : { 'rate' : AverageFormula('rain_rate'), 'fall' : SumFormula('rain') },
        'uv' : { 'index' : MaxFormula('uv_index') }
    }

    formulas = default_formulas

    logger = logging.getLogger("datasource.accumulator")

    last_timestamp = datetime.datetime.fromtimestamp(0)
    cached_slices = []

    lock = threading.Lock()

    class Slice(object):
        def __init__(self, formulas, from_time, to_time):
            self.formulas = copy.deepcopy(formulas)
            self.from_time = from_time
            self.to_time = to_time

        def add_sample(self, sample):
            for serie in self.formulas.values():
                for formula in serie.values():
                    formula.append(sample)

    def get_slice_duration(self):
        if self.slice == 'minute':
            return datetime.timedelta(0, 60)
        elif self.slice == 'hour':
            return datetime.timedelta(0, 3600)
        elif self.slice == 'day':
            return datetime.timedelta(1)
        elif self.slice == 'month':
            return datetime.timedelta(30)

    def get_slice_start(self, time):
        if self.slice == 'minute':
            return datetime.datetime(time.year, time.month, time.day, time.hour, time.minute)
        elif self.slice == 'hour':
            return datetime.datetime(time.year, time.month, time.day, time.hour)
        elif self.slice == 'day':
            return datetime.datetime(time.year, time.month, time.day)
        elif self.slice == 'month':
            return datetime.datetime(time.year, time.month, 1)

    def get_next_slice_start(self, time):
        if self.slice == 'minute':
            return time+datetime.timedelta(0,60)
        elif self.slice == 'hour':
            return time+datetime.timedelta(0,3600)
        elif self.slice == 'day':
            return time+datetime.timedelta(1,0)
        elif self.slice == 'month':
            return datetime.datetime(time.year, time.month+1 % 13, 1)

    def create_slices(self, from_time, to_time):
        t = self.get_slice_start(from_time)
        while t < to_time:
            end = self.get_next_slice_start(t)
            self.logger.debug("Creating slice %s - %s", t, end)
            slice = self.Slice(self.formulas, t, end)
            self.cached_slices.append(slice)
            t = end

    def get_labels(self):
        format = self.formats[self.slice]

    def execute(self,data={}, context={}):
        to_time = parse(data['time_end']) if data.has_key('time_end') else datetime.datetime.now()
        from_time = to_time - (self.get_slice_duration() * (self.span - 1) )

        self.logger.debug("Last timestamp: %s", self.last_timestamp)

        if self.last_timestamp < to_time - datetime.timedelta(0,self.period):
            self.lock.acquire()
            try:
                if len(self.cached_slices) > 0:
                    slice_from_time = self.cached_slices[-1].to_time
                else:
                    slice_from_time = from_time

                self.create_slices(slice_from_time, to_time)

                update_from_time = max(self.last_timestamp, from_time)
                self.logger.debug("Update from %s ", update_from_time)
                s = 0
                for sample in self.storage.samples(update_from_time, to_time):
                    # find the first slice receiving the samples
                    while self.cached_slices[s].to_time < sample['localtime']:
                        s = s + 1
                    self.cached_slices[s].add_sample(sample)
                    self.last_timestamp = sample['localtime']
                self.logger.debug("Last timestamp: %s", self.last_timestamp)
            finally:
                self.lock.release()

        result = {}

        for k,v in self.formulas.iteritems():
            result[k]={}
            result[k]['series']={}
            for key in v.keys():
                result[k]['series'][key]=[]
                result[k]['series'][key]=self.get_labels()

        for slice in self.cached_slices:
            for k,v in slice.formulas.iteritems():
                for key,formula in v.iteritems():
                    result[k]['series'][key].append(formula.value())

        return result

def parse(isodate):
    if len(isodate) == 10:
        return datetime.datetime.strptime(isodate, "%Y-%m-%d")
    else:
        return datetime.datetime.strptime(isodate, "%Y-%m-%d"+isodate[10]+"%H:%M:%S")
