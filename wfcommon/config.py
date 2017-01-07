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
import log
import yaml
import inspect
import sys
import os.path
import copy
from Cheetah.Template import Template

wfrog_version = "0.8.2.99-git"

class Configurer(object):

    default_filename = None
    module_map = None

    log_configurer = log.LogConfigurer()
    logger = logging.getLogger('config')

    def __init__(self, module_map):
        self.module_map = module_map
        self.extensions = {}

    def add_options(self, opt_parser):
        opt_parser.add_option("-f", "--config", dest="config",
                  help="Configuration file (in yaml)", metavar="CONFIG_FILE")
        opt_parser.add_option("-s", "--settings", dest="settings",
                  help="Settings file (in yaml)", metavar="SETTINGS_FILE")
        opt_parser.add_option("-H", action="store_true", dest="help_list", help="Gives help on the configuration file and the list of possible config !elements in the yaml config file")
        opt_parser.add_option("-E", dest="help_element", metavar="ELEMENT", help="Gives help about a config !element")
        opt_parser.add_option("-e", "--extensions", dest="extension_names", metavar="MODULE1,MODULE2,...", help="Comma-separated list of modules containing custom configuration elements")
        self.log_configurer.add_options(opt_parser)

    def configure(self, options, component, config_file, settings_file=None, embedded=False):
        self.config_file = config_file
        self.settings_file = settings_file
        if options.extension_names:
            for ext in options.extension_names.split(","):
                self.logger.debug("Loading extension module '"+ext+"'")
                self.extensions[ext]=__import__(ext)
        if options.help_list:
            if component.__doc__ is not None:
                print component.__doc__
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
            # Adds logger documentation
            print self.log_configurer.__doc__
            print " Use option -H ELEMENT for help on a particular !element"
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
                print element + " [" + desc[element][1] +"]"
                print "    " + desc[element][0]
                print
            else:
                print "Element "+element+" not found or not documented"
            sys.exit()

        if not embedded and options.config:
            self.config_file = options.config

        settings_warning=False
        if self.settings_file is None:
            if options.settings is not None:
                self.settings_file = options.settings
            else:
                settings_warning=True
                self.settings_file = os.path.dirname(self.config_file)+'/../../wfcommon/config/default-settings.yaml'
        settings = yaml.load( file(self.settings_file, 'r') )

        variables = {}
        variables['settings']=settings
        config = yaml.load( str(Template(file=file(self.config_file, "r"), searchList=[variables])))

        if settings is not None:
            context = copy.deepcopy(settings)
        else:
            context = {}

        context['_yaml_config_file'] = self.config_file
        context['os']=sys.platform

        if not embedded:
            self.log_configurer.configure(options, config, context)

        self.logger.info("Starting wfrog " + wfrog_version)
        if settings_warning:
            self.logger.warn('User settings are missing. Loading default ones. Run \'wfrog -S\' for user settings setup.')
        self.logger.info("Loaded settings file " + os.path.normpath(self.settings_file))
        self.logger.debug('Loaded settings %s', repr(settings))
        self.logger.debug("Loaded config file " + os.path.normpath(self.config_file))
        
        if config.has_key('init'):
            for k,v in config['init'].iteritems():
                self.logger.debug("Initializing "+k)
                try:
                    v.init(context=context)
                except AttributeError:
                    pass # In case the element has not init method

        return ( config, context )

    def print_help(self, module):
        desc = self.get_help_desc(module, summary=True)
        sorted = desc.keys()
        sorted.sort()
        for k in sorted:
            print k
            print "    " + desc[k][0]
            print

    def get_help_desc(self, module, summary=False):
        self.logger.debug("Getting info on module '"+module.__name__+"'")
        elements = inspect.getmembers(module, lambda l : inspect.isclass(l) and yaml.YAMLObject in inspect.getmro(l))
        desc={}
        for element in elements:
            self.logger.debug("Getting doc of "+element[0])
            # Gets the documentation of the first superclass
            superclass = inspect.getmro(element[1])[1]
            fulldoc=superclass.__doc__

            # Add the doc of the super-super-class if _element_doc is
            if hasattr(inspect.getmro(superclass)[1], "_element_doc") and inspect.getmro(superclass)[1].__doc__  is not None:
                fulldoc = fulldoc + inspect.getmro(superclass)[1].__doc__

            firstline=fulldoc.split(".")[0]
            self.logger.debug(firstline)

            module_name = module.__name__.split('.')[-1]

            if summary:
                desc[element[1].yaml_tag] = [ firstline, module_name ]
            else:
                desc[element[1].yaml_tag] = [ fulldoc, module_name ]
        return desc
