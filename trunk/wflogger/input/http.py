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

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import logging
import base

server_map = {}

class HTTPEventHandler(BaseHTTPRequestHandler):

    protocol_version = 'HTTP/1.1'
    process_message = None

    def __init__(self, request, client_address, server):
        global server_map
        self.input = server_map[server]
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def do_POST(self):
        clen = self.headers.getheader('content-length')
        if clen:
            clen = int(clen)
        else:
            self.send_error(411)

        message = self.rfile.read(clen)
        self.input.process_message(message)

        self.send_response(200)
        self.send_header('Content-length', 0)
        self.end_headers()
        
    def do_GET(self):
        self.send_response(200)
        text="Ready to receive events."
        self.send_header('Content-type', "text/html")
        self.send_header('Content-length', len(text))
        self.end_headers()
        self.wfile.write(text)

class HttpInput(base.XmlInput):
    """
    Listen to HTTP events according to WESTEP HTTP transport.

    [ Properties ]
    
    port [numeric] (optional):
        The TCP port listening to events. Default to 8888.
    """

    port = 8888

    logger = logging.getLogger("input.http")

    def do_run(self):
        self.listen_http(self.port)

    def listen_http(self, port):
        self.logger.info("Starting WESTEP HTTP transport listening on port "+str(port))
        global server_map
        server = HTTPServer(('', port), HTTPEventHandler)
        server_map[server] = self
        server.serve_forever() 
