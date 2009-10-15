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

class SimulatorQuery(object):
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
                "unit" : "C",
                "series" : {
                    "lbl" : [ "12:00", "13:00", "14:00", "15:00" ],
                    "avg" : [ 3, 5, 6, 8 ],
                    "min" : [ 1, 4, 3, 3 ],
                    "max" : [ 5, 6, 8, 12 ]
                    }
                },
            "dew" : {
                "value" : 3,
                "unit" : "C",
                "series" : {
                    "lbl" : [ "12:00", "13:00", "14:00", "15:00" ],
                    "avg" : [ 3, 5, 6, 6 ],
                    }
                }
                
            }        
