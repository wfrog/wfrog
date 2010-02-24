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

import yaml
import time

class RandomSimulator(yaml.YAMLObject):
    yaml_tag = u'!random-simulator'
    
    def run(self, generate_event, consume_event):
        while True:
            e = generate_event('temp')
            e.value = 34
            
            e.create_child('mean')
            e.mean.value = 2
                        
            consume_event(e)
            time.sleep(2) 
           
           
