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
from base import get
from wfcommon import meteo

class PredominantWindFormula(object):
    '''
    Returns the direction in degrees of predominant wind.
    '''
    def __init__(self, prefix):
        self.prefix = prefix

    prefix = None

    sumX = 0
    sumY = 0

    count = 0

    def append(self, sample):
        speed = get(sample, self.prefix)
        dir = get(sample, self.prefix+"_dir")
        if speed is not None and dir is not None:
            x = meteo.WindX(speed, dir)
            y = meteo.WindY(speed, dir)
            self.sumX = self.sumX + x
            self.sumY = self.sumY + y
            self.count = self.count + 1

    def value(self):
        if self.count==0:
            return None
        else:
            avgX = self.sumX / self.count
            avgY = self.sumY / self.count
            return meteo.WindDir(avgX, avgY)
