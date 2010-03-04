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

import ftplib
import renderer
import logging
import time

class FtpRenderer(object):
    """
    Send rendered files by FTP. Typically used with TemplateRenderer.

    [ Properties ]

    renderers:
        Renderers providing the filenames to upload.

    host:
        FTP site hostname.

    port: (optional)
        FTP site port. Defaults to 21.

    directory: (optional)
        Location on the FTP site where the files will be uploaded.

    username:
        FTP site username.

    password:
        FTP site password.
    """

    renderers = None
    host = None
    port = 21
    directory = None
    username = None
    password = None

    logger = logging.getLogger("renderer.ftp")

    def render(self, data={}, context={}):
        renderer.assert_renderer_dict('renderers', self.renderers)
        assert self.host is not None, "'ftp.host' must be set"
        assert self.username is not None, "'ftp.username' must be set"
        assert self.password is not None, "'ftp.password' must be set"

        files= {}        

        for key in self.renderers.keys():
            files[key] = self.renderers[key].render(data=data, context=context)

        errors = 0
        while True:
            try:
                ftp = ftplib.FTP()
                self.logger.debug("Connecting to %s:%d" % (self.host, self.port))
                ftp.connect(self.host, self.port)
                self.logger.debug("Authenticating...")
                ftp.login(self.username, self.password)
                if self.directory is not None:
                    self.logger.debug("Moving to directory %s" % self.directory)
                    ftp.cwd(self.directory)
                for remote_file, local_file in files.iteritems():
                    self.logger.debug("Sending %s to %s" % (local_file, remote_file))
                    f = open(local_file, 'r')
                    ftp.storbinary("STOR %s" % remote_file, f)
                    f.close()
                ftp.close()
                break
            except Exception, e:
                errors += 1
                if errors < 3:
                    self.logger.warning("Error sending files by FTP (retrying in 5 secs.): %s" % str(e))
                    time.sleep(5)
                else: 
                    self.logger.error("Error sending files by FTP (aborting): %s" % str(e))
                    break
                    


