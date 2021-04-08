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

import os, glob, time
import logging

class HousekeepRenderer(object):
    """
    Runs on a schedule to remove used png files from
    the chart cache folder.
    
    render result [string]:
        The path to the generated file.

    [ Properties ]

    docroot [string]:
        The absolute path to the cache folder.

    suffix [string] (optional):
        If present, specifies that the filetype to be removed
        defaults to png
    """

    renderer = None
    docroot = None
    suffix = 'png'

    logger = logging.getLogger("renderer.housekeeper")

    def render(self, data={}, context={}):
        assert self.docroot is not None, "'housekeeper.docroot' must be set"
        self.logger.info("Houskeeping task is running")
        self.logger.debug("docroot: "+str(self.docroot))
        self.logger.debug("suffix: "+str(self.suffix))
        self._purge(self.docroot, "*."+self.suffix)


    def _purge(self, dir, pattern):
        fpath = dir+'/'+pattern
        self.logger.info("Purging :"+fpath)
        flist=glob.glob(fpath)
        for f in flist:
            self.logger.debug("Deleting: "+str(f))
            try:
                os.remove(f)
            except:
                continue

