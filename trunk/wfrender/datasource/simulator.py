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

class SimulatorDataSource(object):
    """
    Return a simulated harcoded data.
    """

    query=None
    renderer=None

    def __init__(self, query, renderer):
        self.query=query
        self.renderer=renderer

    def execute(self,data={}, context={}):
        return {
            "temp" : {
                "value" : 3,
                "min" : 1,
                "max" : 6,
                "series" : {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "avg" : [ -1, -0.6, 1, 2.5, None, 4.2, 3.5, 1, 3.2, 3 ],
                    "min" : [ -3, -3.2, -2, 1, None, 3, 1, 0.2, 2.4, 2.8 ],
                    "max" : [ 2, 1.4, 3, 2.8, None, 4.5, 4.6, 4.3, 5, 5  ]
                    }
                },

            "dew" : {
                "value" : 3,
                "series" : {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "avg" : [ -4, -3.8, -3.5, -2, None, 1.2, .3, -0.2, 0, 1],
                    }
                },
            "wind" : {
                "value" : 2.2,
                "gust" : 6,
                "deg" : 43,
                "dir" : "NE",
                "series" : {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "speed" : [ 4, 3.8, None, 1, 1.2, .3, 0.2, 0, 1 , 1],
                    "gust" : [ 5, 6, None, 1.3, 1.3, .4, 0.2, 0, 1.2 , 1],
                    "deg" : [ 318, None, 300, 310, 300, 300, 300, 345, 12, 60 ],
                    "dir": [ 'NNW', None, 'NW', 'NW', 'NW', 'NW', 'N', 'NNE', 'NE', 'NE']
                    },
                "sectors" : {
                    "lbl" : ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'],
                    "freq" :  [ 0.2, 0.1, 0.2, 0.05, 0.05, 0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.3 ],
                    "avg" :   [ 0.3, 1, 0.3, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0, 2, 3 ],
                    "gust" :  [ 2.1, 2, 0.3, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0, 2.4, 6 ]
                    }
                    
                }                

            }
