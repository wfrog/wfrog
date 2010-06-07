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

import os
import os.path
import time
import wfcommon.meteo
import copy
import random
import datetime
import sys

class SimulatorStorage(object):
    '''
    Returns random generated samples.

    [ Properties ]

    seed (optional): To change the generated data. Default to 0.
    period (optional): Sampling period in seconds.
    '''

    seed=0
    period=300

    keylist = ['localtime',
                'temp',
                'hum',
                'wind',
                 'wind_dir',
                'wind_gust',
                'wind_gust_dir',
                'dew_point',
                'rain',
                'rain_rate',
                'pressure',
                'uv_index']

    base = [ 0, 20, 65, 2, 45, 0, 0, 0, 0, 2, 1020, 2 ]

    logger = logging.getLogger('storage.random')

    def write_sample(self, sample, context={}):
        pass

    def keys(self):
        return self.keylist

    def samples(self, from_time=datetime.datetime.fromtimestamp(0), to_time=datetime.datetime.now(), context={}):
        from_timestamp = int(time.mktime(from_time.timetuple()))
        to_timestamp = time.mktime(to_time.timetuple())

        sample = copy.copy(self.base)

        t = from_time
        while t < to_time:
            gen = random.Random()
            minutes = int(time.mktime(t.timetuple())/60)
            gen.seed(self.seed+minutes)

            sample[0] = t
            #temp
            sample[1] = self.variate(sample[1], gen, 1, -5, 28)
            #hum
            sample[2] = self.variate(sample[2], gen, 3, 10, 98)
            #wind avg
            sample[3] = self.variate(sample[3], gen, 0.5, 0, 10)
            #avg dir
            sample[4] = self.variate(sample[4], gen, 60, 0, 359)
            #wind gust
            sample[5] = self.variate(sample[3]+4, gen, 2, 0, 15)
            #gust dir
            sample[6] = self.variate(sample[4], gen , 22, 0, 359)
            #rain rate
            sample[9] = self.variate(sample[9], gen, 1, 0, 20)
            #rain fall
            sample[8] = sample[8]+sample[9]*(self.period/3600.0)
            #pressure
            sample[10] = self.variate(sample[10], gen, 5, 980, 1030)
            #uv-index
            sample[11] = round(self.variate(sample[11], gen, 2, 0, 12))
            #dew point
            sample[7] = wfcommon.meteo.DewPoint(sample[1], sample[2])

            yield sample
            t = t+datetime.timedelta(0,self.period)

    def variate(self, value, gen, ratio, vmin, vmax):
        delta = ratio * ( gen.random() - 0.5 )
        if value + delta < vmin or value + delta > vmax:
            delta = -delta
        return value + delta
