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

from base import AverageFormula
from wfcommon import meteo

class PredominantWindFormula(object):
    '''
    Returns the direction in degrees of predominant wind.
    '''
    def __init__(self, index):
        self.index = index

    index = None
    sumX = 0
    sumY = 0
    count = 0


    def append(self, sample):
        speed_index = self.index
        dir_index = self.index+1
        speed = sample[speed_index]
        dir = sample[dir_index]
        if speed is not None and dir is not None:
            x = meteo.WindX(speed, dir)
            y = meteo.WindY(speed, dir)
            self.sumX = self.sumX + x
            self.sumY = self.sumY + y
            self.count = self.count + 1

    def value(self):
        if self.count==0:
            return (None, None)
        else:
            avgX = self.sumX / self.count
            avgY = self.sumY / self.count
            dir = meteo.WindDir(avgX, avgY)
            return ( dir, meteo.WindDirTxt(dir) )

class WindSectorAverageFormula(object):
    '''
    Returns wind average histogram per sector as a sequence.
    '''
    def __init__(self, index):
        self.index = index

    index = None
    sums = None
    counts = [0]*16

    def append(self, sample):
        if self.sums is None:
            self.sums = [0]*16
            self.counts = [0]*16
        speed_index = self.index
        dir_index = self.index+1
        speed = sample[speed_index]
        dir = sample[dir_index]
        if speed is not None and speed > 0 and dir is not None:
            i = int(round(dir/22.5)) % 16
            self.sums[i] = self.sums[i] + speed
            self.counts[i] = self.counts[i]+1

    def value(self):
        averages = [0]*16
        for i in range(16):
            if self.counts[i] > 0:
                averages[i] = float(self.sums[i]) / self.counts[i]
        return averages

class WindSectorMaxFormula(object):
    '''
    Returns wind maximum histogram per sector as a sequence.
    '''
    def __init__(self, index):
        self.index = index

    index = None
    values = None

    def append(self, sample):
        if self.values is None:
            self.values = [0]*16
        speed_index = self.index
        dir_index = self.index+1
        speed = sample[speed_index]
        dir = sample[dir_index]
        if speed is not None and speed > 0 and dir is not None:
            i = int(round(dir/22.5)) % 16
            if speed >  self.values[i]:
                self.values[i] = speed

    def value(self):
        if self.values is not None:
            return self.values
        else:
            return [0]*16

class WindSectorFrequencyFormula(object):
    '''
    Returns wind frequency histogram per sector as a sequence.
    '''
    def __init__(self, index):
        self.index = index

    index = None
    sums = None
    count = 0

    def append(self, sample):
        if self.sums is None:
            self.sums = [0]*16
            self.count = 0
        speed_index = self.index
        dir_index = self.index+1
        speed = sample[speed_index]
        dir = sample[dir_index]
        if speed is not None and speed > 0 and dir is not None:
            i = int(round(dir/22.5)) % 16
            self.sums[i] = self.sums[i] + 1.0
            self.count = self.count + 1

    def value(self):
        freqs = [0]*16
        if self.count > 0:
            for i in range(16):
                freqs[i] = self.sums[i] / self.count
        return freqs
