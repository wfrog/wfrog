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

# Before loading other modules add wfrog directory to sys.path to be able to use wfcommon
import os.path
import sys
if __name__ == "__main__": sys.path.append(os.path.abspath(sys.path[0] + '/..'))

import wfcommon.storage
import optparse
import logging
import wfcommon.config

class StorageCopy(object):

    logger = logging.getLogger('storagecopy')

    def __init__(self, config_file=None):

        # Prepare the configurer
        module_map = (
            ( "Storages", wfcommon.storage)
        )

        if config_file is None:
            config_file = "config/storagecopy.yaml"

        configurer = wfcommon.config.Configurer(config_file, module_map)

        # Initialize the option parser
        opt_parser = optparse.OptionParser()
        configurer.add_options(opt_parser)

        # Parse the options and create object trees from configuration
        (options, args) = opt_parser.parse_args()

        (config, context) = configurer.configure(options, self)

        self.from_storage = config['from']
        self.to_storage = config['to']

    def run(self):

        for sample in self.from_storage.samples():
            self.to_storage.write_sample(sample)

if __name__ == "__main__":
    driver = StorageCopy()
    driver.logger.debug("Started main()")
    driver.run()
    driver.logger.debug("Finished main()")
