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
import base
from StringIO import StringIO
import sys

class StdioInput(base.XmlInput):
    """
    Receives events on standard input according to WESTEP STDIO transport.
    """

    logger = logging.getLogger('input.stdio')

    def do_run(self):
        self.logger.debug('Starting')
        
        end = False
        buffer = StringIO()
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            self.logger.debug('Got line: '+line)

            if line.strip() == "":
                message = buffer.getvalue().strip()
                if not message == "": # skip additional emtpy lines
                    self.process_message(buffer.getvalue())
                buffer.close()
                buffer = StringIO()
            else:
                buffer.write(line)        
