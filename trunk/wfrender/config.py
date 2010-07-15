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
import wfcommon.generic
import wfcommon.config
import wfcommon.storage
import optparse
import sys
import os
from os import path
import time
from threading import Thread
import inspect
import logging
import traceback
import wfcommon.dict

class RendererConfigurer(wfcommon.config.Configurer):
    """Returns a configuration read from a yaml file (default to wfrender.yaml in cwd)"""

    watcher_running = False
    builtins = [ "renderer", "datasource" ]
    extensions = {}
    logger=logging.getLogger("config")

    embedded = False

    def __init__(self, opt_parser):
        # Prepare the configurer
        module_map = (
            ( "Renderers" , renderer),
            ( "Data Sources" , datasource ),
            ( "Storages" , wfcommon.storage ),
            ( "Generic Elements", wfcommon.generic)
        )

        wfcommon.config.Configurer.__init__(self, module_map)
        self.add_options(opt_parser)
        opt_parser.add_option("-r", "--reload-config", action="store_true", dest="reload_config", help="Reloads the yaml configuration if it changes during execution")
        opt_parser.add_option("-R", "--reload-modules", action="store_true", dest="reload_mod", help="Reloads the data source, renderer and extension modules if they change during execution")
        opt_parser.add_option("-c", "--command", dest="command", help="A command to execute after automatic reload. Useful to trigger events during development such as browser reload.")

    def configure_engine(self, engine, options, args, init, config_file):
        (config, config_context) = self.configure(options, engine, config_file, embedded=(self.embedded or not init))

        engine.root_renderer = config["renderer"]

        engine.initial_context = wfcommon.dict.merge(engine.initial_context, config_context)

        if ( options.reload_config or options.reload_mod) and not self.watcher_running:
            self.watcher_running = True
            engine.daemon = True
            modules = []
            modules.extend(self.builtins)
            modules.extend(self.extensions.keys())
            FileWatcher(options, modules, self, engine, options, args).start()

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

