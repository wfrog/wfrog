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
import renderer
import datasource
import optparse
import sys
import os
from os import path
import time
from threading import Thread
import inspect
import logging
import traceback
import dict

class YamlConfigurer(object):
    """Returns a configuration read from a yaml file (default to wfrender.yaml in cwd)"""

    DEFAULT_CONFIG = "config/wfrender.yaml"

    watcher_running = False
    builtins = [ "renderer", "datasource" ]
    extensions = {}
    logger=logging.getLogger("config")

    def __init__(self, opt_parser):
        opt_parser.add_option("-f", "--file", dest="config", default=self.DEFAULT_CONFIG,
                  help="Configuration file (in yaml). Defaults to '" + self.DEFAULT_CONFIG + "'", metavar="CONFIG_FILE")
        opt_parser.add_option("-L", action="store_true", dest="help_list", help="Gives the list of possible config !elements in the yaml config file")
        opt_parser.add_option("-H", dest="help_element", metavar="ELEMENT", help="Gives help about a config !element")
        opt_parser.add_option("-e", "--extensions", dest="extension_names", metavar="MODULE1,MODULE2,...", help="Comma-separated list of modules containing custom data sources, renderers or new types of application elements")
        opt_parser.add_option("-r", "--reload-config", action="store_true", dest="reload_config", help="Reloads the yaml configuration if it changes during execution")
        opt_parser.add_option("-R", "--reload-modules", action="store_true", dest="reload_mod", help="Reloads the data source, renderer and extension modules if they change during execution")
        opt_parser.add_option("-q", "--quiet", action="store_true", dest="quiet", help="Issues only errors, nothing else")
        opt_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Issues all debug messages")
        opt_parser.add_option("-c", "--command", dest="command", help="A command to execute after automatic reload. Useful to trigger events during development such as browser reload.")

    def configure(self, engine, options, args):
        if not options.quiet:
            if options.debug:
                level=logging.DEBUG
            else:
                level=logging.INFO
            logging.basicConfig(level=level, format="%(levelname)s [%(name)s] %(message)s")

        if options.extension_names:
            for ext in options.extension_names.split(","):
                self.logger.debug("Loading extension module '"+ext+"'")
                self.extensions[ext]=__import__(ext)
        if options.help_list:
            print "\n> Elements you can use in the yaml config file:\n"
            print "Renderers"
            print "---------\n"
            self.print_help(renderer)
            print "Data Sources"
            print "------------\n"
            self.print_help(datasource)
            if options.extension_names:
                print "Extensions"
                print "----------\n"
                for ext in self.extensions:
                    print "[" + ext + "]"
                    print
                    self.print_help(self.extensions[ext])
            print "> Use option -H ELEMENT for help on a particular element"
            sys.exit()
        if options.help_element:
            element = options.help_element
            if element[0] is not '!':
                element = '!' + element
            desc = {}
            desc.update(self.get_help_desc(renderer))
            desc.update(self.get_help_desc(datasource))
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

        engine.root_renderer = config["renderer"]
        if config.has_key("context"):
            config_context = config["context"]
        else:
            config_context = {}
        config_context['_yaml_config_file'] = path.abspath(options.config)
        engine.initial_context = dict.merge(engine.initial_context, config_context)

        if ( options.reload_config or options.reload_mod) and not self.watcher_running:
            self.watcher_running = True
            engine.daemon = True
            modules = []
            modules.extend(self.builtins)
            modules.extend(self.extensions.keys())
            FileWatcher(options, modules, self, engine, options, args).start()

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

class FileWatcher(Thread):

    logger = logging.getLogger("config.watcher")

    def __init__(self, options, modules, configurer, engine, *args, **kwargs):
        Thread.__init__(self)
        self.config_file = options.config
        self.options = options
        self.modules = modules
        self.configurer = configurer
        self.engine = engine
        self.args = args
        self.kwargs = kwargs

    def run(self):
        config_this_modified = time.time()
        templates_this_modified = time.time()

        modules_modified = {}
        for m in self.modules:
            modules_modified[m] = time.time()
        while self.engine.daemon:

            config_last_modified = os.stat(self.config_file).st_mtime
            if config_last_modified > config_this_modified and self.options.reload_config:
                self.logger.debug("Changed detected on "+self.config_file)
                self.reconfigure()
                config_this_modified = config_last_modified
                continue

            templates_last_modified = last_mod('templates')
            if templates_last_modified > templates_this_modified and self.options.reload_config:
                self.logger.debug("Changed detected on templates")
                self.reconfigure()
                templates_this_modified = templates_last_modified
                continue

            if self.options.reload_mod:
                for m in modules_modified.keys():
                    last_modified = last_mod(m)
                    if last_modified > modules_modified[m]:
                        try:
                            reload_modules(m)
                            self.reconfigure()
                        except:
                            traceback.print_exc()
                        modules_modified[m] = last_mod(m)

    def reconfigure(self):
        self.logger.info("Reconfiguring engine...")
        old_root_renderer = self.engine.root_renderer
        self.configurer.configure(self.engine,*self.args, **self.kwargs)
        try:
            old_root_renderer.close()
            time.sleep(0.1)
        except:
            pass
        if self.options.command:
            self.logger.info("Running command: "+self.options.command)
            command_thread = CommandThread()
            command_thread.command = self.options.command
            command_thread.start()

class CommandThread(Thread):
    command = None
    def run(self):
        time.sleep(0.1)
        os.system(self.command)

def reload_modules(parent):
    logger = logging.getLogger("config.loader")
    logger.info("Reloading module '"+parent+"' and direct sub-modules...")
    parent = __import__(parent)
    for m in inspect.getmembers(parent, lambda l: inspect.ismodule(l)):
        logger.debug("Reloading module '"+m[0]+"'.")
        reload(m[1])
    logger.debug("Reloading module '"+parent.__name__+"'.")
    reload(parent)


def last_mod(parent):
    logger = logging.getLogger("config.loader")
    max=0
    for fname in os.listdir(parent):
        mod = os.stat(parent+'/'+fname).st_mtime
        if(mod > max):
            max = mod
    return max

