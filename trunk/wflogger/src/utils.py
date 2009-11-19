## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <lbovet@windmaster.ch>
##
##  This file is part of WFrog
##
##  WFrog is free software: you can redistribute it and/or modify
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

from xml.etree import ElementTree
from time import struct_time, strftime
from datetime import datetime

def format(obj, time_format):
    if isinstance(obj, int):
        return str(obj)
    elif isinstance(obj, float):
        return str(round(obj,1))
    elif isinstance(obj, struct_time):
        return strftime(time_format, obj)
    elif isinstance(obj, (str, unicode)):
        return obj.strip()
    elif isinstance(obj, datetime):
        return obj.strftime(time_format)
    else:
        return "unknown"

def extract_units(tag):
    i = tag.find('(') 
    if i == -1:
        return (tag, None)
    j = tag.find(')') 
    if j == -1:
        return (tag[:i], tag[i+1:j])
    return (tag[:i], tag[i+1:j])

def write2xml(dictionary, root_tag, filename, time_format='%Y-%m-%d %H:%M:%S'):
    root = ElementTree.Element(root_tag)
    doc = ElementTree.ElementTree(root)
    if dictionary != None:
        ks = dictionary.keys()
        ks.sort()
        for k in ks:
            ele = root
            for (t,u) in map(extract_units, k.split('.')):
                aux = ele.find(t)
                if aux == None:
                    if u == None:
                        aux = ElementTree.Element(t)
                    else:
                        aux = ElementTree.Element(t, {'units': u})
                    ele.append(aux)
                    ele = aux
                else:
                    ele = aux
            ele.text = format(dictionary[k], time_format)
    f = open(filename, 'w')
    doc.write(f)
    f.close()    
