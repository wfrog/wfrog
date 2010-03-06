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
import yaml
import inspect
import sys
import copy

class Configurer(object):

    default_filename = None
    module_map = None

    logger = logging.getLogger('config')

    def __init__(self, default_filename, module_map):
        self.default_filename = default_filename
        self.module_map = module_map
        
    def add_options(self, opt_parser):
        opt_parser.add_option("-f", "--file", dest="config", default=self.default_filename,
                  help="Configuration file (in yaml). Defaults to '" + self.default_filename + "'", metavar="CONFIG_FILE")
        opt_parser.add_option("-L", action="store_true", dest="help_list", help="Gives the list of possible config !elements in the yaml config file")
        opt_parser.add_option("-H", dest="help_element", metavar="ELEMENT", help="Gives help about a config !element")
        opt_parser.add_option("-e", "--extensions", dest="extension_names", metavar="MODULE1,MODULE2,...", help="Comma-separated list of modules containing custom configuration elements")

    def configure(self, options):
        
        if options.extension_names:
            for ext in options.extension_names.split(","):
                self.logger.debug("Loading extension module '"+ext+"'")
                self.extensions[ext]=__import__(ext)
        if options.help_list:
            print "\n Elements you can use in the yaml config file:\n"
            for (k,v) in self.module_map:
                print k
                print "-"*len(k) +"\n"
                self.print_help(v)
            if options.extension_names:
                print "Extensions"
                print "----------\n"
                for ext in self.extensions:
                    print "[" + ext + "]"
                    print
                    self.print_help(self.extensions[ext])
            print " Use option -H ELEMENT for help on a particular element"
            sys.exit()
        if options.help_element:
            element = options.help_element
            if element[0] is not '!':
                element = '!' + element
            desc = {}
            for(k,v) in self.module_map:
                desc.update(self.get_help_desc(v))
            if len(desc) == 0:
                for ext in self.extensions:
                    desc.update(self.get_help_desc(self.extensions[ext]))
            if desc.has_key(element):
                print
                print element
                print "    " + desc[element]
                print
            else:
                print "Element "+element+" not found or not documented"
            sys.exit()

        config = yaml.load( file(options.config, "r") )

        if config.has_key('context'):            
            context = copy.deepcopy(config['context'])
        else:
            context = {}
        
        context['_yaml_config_file'] = options.config

        return ( config, context )

    def print_help(self, module):
        desc = self.get_help_desc(module, summary=True)
        sorted = desc.keys()
        sorted.sort()
        for k in sorted:
            print k
            print "    " + desc[k]
            print

    def get_help_desc(self, module, summary=False):
        self.logger.debug("Getting info on module '"+module.__name__+"'")
        elements = inspect.getmembers(module, lambda l : inspect.isclass(l) and yaml.YAMLObject in inspect.getmro(l))
        desc={}
        for element in elements:
            self.logger.debug("Getting doc of "+element[0])
            # Gets the documentation of the first superclass
            fulldoc=inspect.getmro(element[1])[1].__doc__
            firstline=fulldoc.split(".")[0]
            self.logger.debug(firstline)
            if summary:
                desc[element[1].yaml_tag] = firstline
            else:
                desc[element[1].yaml_tag] = fulldoc
        return desc
