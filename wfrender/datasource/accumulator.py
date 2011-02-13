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
from wfcommon.formula.wind import PredominantWindFormula
from wfcommon.formula.wind import WindSectorAverageFormula
from wfcommon.formula.wind import WindSectorMaxFormula
from wfcommon.formula.wind import WindSectorFrequencyFormula
from wfcommon.formula.temp import WindChillMinFormula
from wfcommon.formula.temp import HeatIndexMaxFormula

import copy
import datetime
import threading

class AccumulatorDatasource(object):
    '''
    Calculates data from a storage in an iterative way by traversing
    only recently added data.

    [ Properties ]

    storage [storage]:
        The underlying storage to get samples.

    slice [year|month|week|day|hour|minute] (optional):
        The unit of grouping for the calculated series.
        Defaults to 'hour''

    span [numeric] (optional):
        Number of slices in the resulting series.
        Defaults to 24.

    period [numeric] (optional):
        Number of seconds between two refreshes of the calculated data.
        DEfaults to 120.

    format [string] (optional):
        Date/time format string for labels.
        See Python strftime function.

    formulas [dict] (optional):
        Specify what and how to calculate. Defines the structure of the
        resulting data.
        Dictionary keyed by the measure names ('temp', 'hum', ...). Values
        are dictionaries keyed by the serie names ('avg', 'min', ...) and
        containing 'formula' objects.

    caching [true|false] (optional):
        Enable/disable caching for normal requests. Defaults to true.
    '''

    storage = None
    slice = 'hour'
    span = 23

    format = None

    formats = { 'year': '%y',
                'month': '%m',
                'week': '%d/%m', 
                'day': '%d/%m',
                'hour': '%H',
                'minute': '%H:%M' }

    period = 120

    default_formulas = {
        'temp': { 'avg' : AverageFormula('temp'),
                   'min' : MinFormula('temp'),
                   'max' : MaxFormula('temp') },
        'dew' : { 'avg': AverageFormula('dew_point')},
        'hum' : { 'avg' : AverageFormula('hum') },
        'press' : { 'avg' : AverageFormula('pressure') },
        'wind' : { 'avg' : AverageFormula('wind'),
                   'max' : MaxFormula('wind_gust'),
                   'deg,dir' : PredominantWindFormula('wind')  },
        'sectors' : { 'avg' : WindSectorAverageFormula('wind'),
                      'max' : WindSectorMaxFormula('wind_gust'),
                      'freq' : WindSectorFrequencyFormula('wind') },
        'rain' : { 'rate' : AverageFormula('rain_rate'),
                   'fall' : SumFormula('rain') },
        'uv' : { 'index' : MaxFormula('uv_index') }
    }

    formulas = default_formulas

    caching = True

    logger = logging.getLogger("datasource.accumulator")

    last_timestamp = datetime.datetime.fromtimestamp(0)
    cached_slices = None
    cached_series = None

    lock = threading.Lock()

    class Slice(object):
        def __init__(self, formulas, from_time, to_time, keys):
            self.formulas = copy.deepcopy(formulas)
            self.from_time = from_time
            self.to_time = to_time

            # replace string keys with index for performance
            for serie in self.formulas.values():
                for formula in serie.values():
                    if type(formula.index)==str:
                        formula.index = keys.index(formula.index)
                    # Index can be a list of indexes (e.g. heatIndex or WindChill)
                    elif type(formula.index)==list:
                        formula.index = map(lambda x: keys.index(x), formula.index)

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
        elif self.slice == 'week':
            return datetime.timedelta(7)
        elif self.slice == 'month':
            return datetime.timedelta(30)
        elif self.slice == 'year':
            return datetime.timedelta(365)

    def get_slice_start(self, time):
        if self.slice == 'minute':
            return datetime.datetime(time.year, time.month, time.day, time.hour, time.minute)
        elif self.slice == 'hour':
            return datetime.datetime(time.year, time.month, time.day, time.hour)
        elif self.slice == 'day':
            return datetime.datetime(time.year, time.month, time.day)
        elif self.slice == 'week':
            (year, week, dayweek) = time.isocalendar()
            return iso_to_gregorian(year, week, 1)
        elif self.slice == 'month':
            return datetime.datetime(time.year, time.month, 1)
        elif self.slice == 'year':
            return datetime.datetime(time.year, 1, 1)

    def get_next_slice_start(self, time):
        if self.slice == 'minute':
            return time+datetime.timedelta(0,60)
        elif self.slice == 'hour':
            return time+datetime.timedelta(0,3600)
        elif self.slice == 'day':
            return time+datetime.timedelta(1,0)
        elif self.slice == 'week':
            (year, week, dayweek) = time.isocalendar()
            return iso_to_gregorian(year, week, 1)+datetime.timedelta(7)
        elif self.slice == 'month':
            if time.month == 12:
                return datetime.datetime(time.year + 1, 1, 1)
            else:
                return datetime.datetime(time.year, time.month + 1, 1)
        elif self.slice == 'year':
            return datetime.datetime(time.year + 1, 1, 1)

    def get_labels(self, slices):
        if self.format is not None:
            format = self.format
        else:
            format = self.formats[self.slice]
        return list(slice.from_time.strftime(format) for slice in slices)

    def update_slices(self, slices, from_time, to_time, context, last_timestamp=None):
        if len(slices) > 0:
            slice_from_time = slices[-1].to_time
        else:
            slice_from_time = from_time

        # Create the necessary slices
        t = self.get_slice_start(slice_from_time)
        keys = self.storage.keys(context=context)
        while t < to_time:
            end = self.get_next_slice_start(t)
            self.logger.debug("Creating slice %s - %s", t, end)
            slice = self.Slice(self.formulas, t, end, keys)
            slices.append(slice)
            t = end

        # Fill them with samples
        if last_timestamp:
            update_from_time = max(last_timestamp + datetime.timedelta(seconds=1), from_time)
            # Add 1 sec to last_timestamp so that the same sample is not retrieved twice
        else:
            update_from_time = from_time
        self.logger.debug("Update from %s ", update_from_time)
        s = 0
        to_delete = 0
        localtime_index = keys.index('localtime')
        for sample in self.storage.samples(update_from_time, to_time, context=context):
            # find the first slice receiving the samples
            sample_localtime = sample[localtime_index]
            while slices[s].to_time < sample_localtime:
                if slices[s].to_time < from_time:
                    # count of obsolete slices to delete
                    to_delete=s
                s = s + 1
            slices[s].add_sample(sample)
            last_timestamp = sample_localtime
        return last_timestamp, to_delete

    def get_series(self, slices):

        result = {}

        for k,v in self.formulas.iteritems():
            result[k]={}
            result[k]['series']={}
            for key in v.keys():
                subkeys = key.split(',')
                for subkey in subkeys:
                    result[k]['series'][subkey]=[]
                result[k]['series']['lbl']=self.get_labels(slices)

        for slice in slices:
            for k,v in slice.formulas.iteritems():
                for key,formula in v.iteritems():
                    value = formula.value()
                    subkeys = key.split(',')
                    if len(subkeys) == 1:
                        value = [ value ]
                    for i in range(len(subkeys)):
                        result[k]['series'][subkeys[i]].append(value[i])

        return result

    def execute(self,data={}, context={}):
        if data.has_key('time_end'):
            to_time = parse(data['time_end'])
            use_cache = False
        else:
            to_time = datetime.datetime.now()
            use_cache = self.caching

        duration = self.get_slice_duration()
        times = (self.span - 1)
        delta= duration * times
        from_time = self.get_slice_start(to_time - delta)

        if use_cache:
            self.logger.debug("Last timestamp: %s", self.last_timestamp)

            self.lock.acquire()
            try:
                if self.last_timestamp < to_time - datetime.timedelta(0,self.period) or self.cached_series is None:
                    if self.cached_slices is None: 
                        self.cached_slices = []

                    last_timestamp, to_delete = self.update_slices(self.cached_slices, from_time, to_time, context, self.last_timestamp)

                    self.cached_slices = self.cached_slices[to_delete:]
                    self.logger.debug('Deleted %s slices', to_delete)
                    self.logger.debug("Last timestamp: %s", self.last_timestamp)

                    self.last_timestamp = last_timestamp

                    self.cached_series = self.get_series(self.cached_slices)
            finally:
                self.lock.release()

            return self.cached_series

        else: # use_cache == False
            slices = []
            self.update_slices(slices, from_time, to_time, context)
            return self.get_series(slices)

def parse(isodate):
    if len(isodate) == 10:
        return datetime.datetime.strptime(isodate, "%Y-%m-%d")
    else:
        return datetime.datetime.strptime(isodate, "%Y-%m-%d"+isodate[10]+"%H:%M:%S")

def iso_year_start(iso_year):
    "The gregorian calendar date of the first day of the given ISO year"
    fourth_jan = datetime.datetime(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta 

def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"
    year_start = iso_year_start(iso_year)
    return year_start + datetime.timedelta(iso_day-1, 0, 0, 0, 0, 0, iso_week-1)


