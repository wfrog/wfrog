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

import time
import random
import copy

class RandomSimulator(object):

    '''
    Simulates a station. Issues events randomly with random variations.
    '''

    types = [ 'temp', 'press', 'hum', 'rain', 'wind', 'uv', 'rad' ]
    init_values = [ 10, 1020, 65, 10, [ 3, 180], 5, 2 ]
    range = [ 30, 100, 40, 20, [6, 360], 10, 4 ]

    rain_total = 55

    def new_value(self, current, init, range):
        step = random.random()*(range/8.0) - range/16.0
        dev = current-init # deviation from init
        delta = round(step-dev/16.0,1) # encourage keeping around init
        new = current + delta
        # keep in range
        if new < init -range/2.0:
            new = init - range/2.0
        if new > init + range/2.0:
            new = init + range/2.0
        return new

    def run(self, generate_event, send_event):
        current_values = copy.copy(self.init_values)

        while True:
            t = random.randint(0,len(self.types)-1)
            type = self.types[t]
            e = generate_event(type)

            if type == 'temp' or type=='hum':
                e.sensor = random.randint(0,1)
            if type == 'wind':
                current_values[t][0] = self.new_value(current_values[t][0], self.init_values[t][0], self.range[t][0])
                current_values[t][1] = self.new_value(current_values[t][1], self.init_values[t][1], self.range[t][1])
                e.create_child('mean')
                e.mean.speed=current_values[t][0]
                e.mean.dir=current_values[t][1]
                e.create_child('gust')
                e.gust.speed=current_values[t][0] + random.randint(0,2)
                e.gust.dir=current_values[t][1]                
            else:
                current_values[t] = self.new_value(current_values[t], self.init_values[t], self.range[t])
                if type == 'rain':
                    e.rate = current_values[t]
                    e.total = self.rain_total
                    self.rain_total = self.rain_total + random.randint(0,2)
                else:
                    e.value = current_values[t]

            send_event(e)
            time.sleep(2)
