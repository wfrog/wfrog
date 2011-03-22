#!/usr/bin/python
## Copyright 2010 Laurent Bovet <laurent.bovet@windmaster.ch>
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

import os.path
import sys
import shutil

class Customizer(object):

    '''Prepares the user directory for customization. Does not override existing
    custom config.'''

    config_subdirs = [ '/config/', '/templates/' ]

    def customize(self, source_dir, target_dir, modules, output=sys.stdout):
        for module in modules:
            for subdir in self.config_subdirs:
                source_config_dir = source_dir+module+subdir
                target_config_dir = target_dir+module+subdir
                if os.path.exists(source_config_dir):
                    if os.path.exists(target_config_dir):
                        output.write('Config for '+module+' was already customized in '+target_config_dir+'. Skipping')
                    else:
                        output.write('Copying config of '+module+' for customization in '+target_config_dir+'.')
                        shutil.copytree(source_config_dir, target_config_dir)
                    output.write('\n')
