#!/usr/bin/python
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
import os
import os.path
import yaml
import logging
import inspect
import wfcommon.config
import wfdriver.station

class SetupClient(object):
    '''Interactive setup for user settings'''

    logger = logging.getLogger('setup')

    def setup_settings(self, settings_def_file, source_file, target_file):
        self.logger.debug('Current settings file: '+str(source_file))
        self.logger.debug('New settings file:'+target_file)
        defs = yaml.load( file(settings_def_file, 'r') )
        if source_file is not None:
            source = yaml.load( file(source_file, 'r') )
        else:
            source = {}
        target = {}
        try:
            os.makedirs(os.path.dirname(target_file))
        except:
            pass
            
        # First question is about the station
        section = {}
        section['name'] = "station"
        section['description'] = "Station information"
        section['type'] = 'dict'
        question = {}
        question['name'] = "driver"
        question['description'] = "the driver for your station model"
        question['type'] = 'choice'
        question['default'] = 'none'
        question['choices'] = {}
        section['children'] =[question]
        
        stations = inspect.getmembers(wfdriver.station, lambda l : inspect.isclass(l) and yaml.YAMLObject in inspect.getmro(l))
        for station in stations:
            station_class = station[1]
            if hasattr(station_class,('name')):
                question['choices'][str(station_class.yaml_tag)[1:]] = station_class.name
        
        defs.insert(0,section)        
            
        self.welcome(target_file)
        self.recurse_create(defs, source, target)
        yaml.dump(target, file(target_file, 'w'), default_flow_style=False)
        self.bye()
        return target_file

    def recurse_create(self, defs, source_node, target_node):
        for v in defs:
            k=v['name']
            if v['type'] == 'dict':
                target_node[k] = {}
                if source_node.has_key(k):
                    new_source_node = source_node[k]
                else:
                    new_source_node = {}
                self.recurse_create(v['children'], new_source_node, target_node[k])
            else:
                if source_node.has_key(k):
                    default = source_node[k]
                else:
                    if v.has_key('default') and v['default'] == 'none':
                        default = 'none'
                    else:
                        default = None
                value = None
                while value == None:
                    value = self.create_value(v, default)
                target_node[k] = value

    def create_value(self, node, default):
        question = 'Please enter '+node['description']+':'
        if node['type'] == 'number':
            if default is None:
                default = node['default']
            answer = self.ask_question(question, default, default)
            try:
                return int(answer)
            except:
                return None
        if node['type'] == 'choice':
            choices_collection = node['choices']
            if type(choices_collection) == dict:
                choices=sorted(choices_collection.keys())
            else:
                choices=choices_collection            
            
            if default != 'none':                
                if default is not None and choices.count(default) > 0:
                    default = str(choices.index(default)+1)
                else:
                    default = '1'
                prompt = choices[int(default)-1]
            else:
                prompt = None
            for i in range(len(choices)):
                if type(choices_collection) == dict:
                    value = choices[i] + ' - ' + choices_collection[choices[i]]
                else:
                    value = choices[i]
                question = question+'\n '+ str(i+1) +') '+ value
            answer = self.ask_question(question, default, prompt)
            try:
                return choices[int(answer)-1]
            except:
                if choices.count(answer) > 0:
                    return answer
                else:
                    return None

    def ask_question(self, question, default, prompt):
        print '\n'+question
        if prompt is not None:
            sys.stdout.write('['+str(prompt)+'] ')    
        sys.stdout.write('> ')
        line=sys.stdin.readline()
        if line is None or line.strip() == '':
            return default
        else:
            return line.strip()

    def welcome(self, settings_file):
        print 'This is the setup of wfrog '+wfcommon.config.wfrog_version+' user settings that will be written in '+settings_file

    def bye(self):
        print
        print 'Thanks.'
