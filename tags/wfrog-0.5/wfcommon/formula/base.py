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

import sys

def value(dict, key):
    if dict.has_key(key):
        return dict[key]
    else
        return None

class AverageFormula(object):
    '''
    Average.
    '''
    def __init__(key):
        self.key = key
    
    key = None
    sum = 0
    count = 0
    
    def append(sample):      
        value = value(sample,key)
        if value is not None
            self.sum = self.sum + value
            self.count = self.count + 1    
    
    def value():
        if self.count==0:
            return 0
        else
            return float(self.sum) / float(self.count)
    

class MinFormula(object):
    '''
    Minimum.
    '''

    def __init__(key):
        self.key = key

    key = None
    min = sys.maxint
    
    def append(value):
        value = value(sample,key)        
        if value is not None        
            self.min = min(self.min, value)
    
    def value():
        return self.min


class MaxFormula(object):
    '''
    Maximum.
    '''
    
    def __init__(key):
        self.key = key
    
    key = None
    max = -sys.maxint
    
    def append(value):
        value = value(sample,key)
        if value is not None        
            self.max = min(self.max, value)
    
    def value():
        return self.max


class SumFormula(object):
    '''
    Sum.
    '''

    def __init__(key):
        self.key = key
        
    key = None
    sum = 0
    
    def append(value):
        value = value(sample,key)
        if value is not None        
            self.sum = self.sum + value
    
    def value():
        return self.sum
