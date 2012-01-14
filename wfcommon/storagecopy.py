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

        configurer = wfcommon.config.Configurer(module_map)

        # Initialize the option parser
        opt_parser = optparse.OptionParser()
        configurer.add_options(opt_parser)

        # Parse the options and create object trees from configuration
        (options, args) = opt_parser.parse_args()

        (config, context) = configurer.configure(options, self, config_file)

        self.from_storage = config['from']
        self.to_storage = config['to']
        try:
            self.from_storage.init(context=context)
        except AttributeError:
            pass # In case the element has not init method

        try:
            self.to_storage.init(context=context)
        except AttributeError:
            pass # In case the element has not init method

    def run(self):

        keys = self.from_storage.keys()
        n = 0

        for sample in self.from_storage.samples():
            if n % 500 == 0: 
                self.logger.info("Processed %d samples" % n)
            sample_to_write = {}
            for i in range(len(keys)):
                sample_to_write[keys[i]] = sample[i]
            self.to_storage.write_sample(sample_to_write)
            n += 1

if __name__ == "__main__":
    driver = StorageCopy()
    driver.logger.debug("Started main()")
    try:
        driver.run()
    except:
        driver.logger.exception("An unexpected error has ocurred while copying storages:")
    driver.logger.debug("Finished main()")
