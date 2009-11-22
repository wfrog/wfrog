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

import renderer
import string,cgi,time
import threading
import socket
import select
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import copy
import urlparse, cgi
import logging


class HttpRenderer(object):
    """
    Renderer starting an embedded HTTP server and serves the content
    results from the wrapped renderers.
    The URL corresponds to the wrapped renderer names.
    Only one such renderer must be configured in one process.

    This renderer runs indefinitely until close() is called.

    [ Properties ]

    root: (optional)
        A renderer providing a result served on the base URI.

    renderers: (optional)
        Must be set if root is not set. A key/value dictionary of
        renderers providing a results served on URIs corresponding to
        the key names.

    port: (optional)
        The listening TCP port. Defaults to 8080.
    """

    renderers = None
    port = 8080
    root = None

    logger = logging.getLogger("renderer.http")

    def render(self, data={}, context={}):
        assert renderer.is_dict(self.renderers) or renderer.is_renderer(self.root), \
            "'http.renderers' must be set to a key/value dictionary or 'root' must be set to a renderer"
        if self.renderers:
            renderer.assert_renderer_dict('http.renderers', self.renderers)

        self.context = context
        self.data = data

        try:
            global _HttpRendererSingleton
            _HttpRendererSingleton = self
            self.server = StoppableHTTPServer(('', self.port), HttpRendererHandler)
            self.server.allow_reuse_address
            self.logger.info('Started server on port ' + str(self.port))
            self.server.serve_forever()
            self.server.socket.close()
            self.logger.debug('Stopped listening')
        except KeyboardInterrupt:
            self.logger.info('^C received, shutting down server')
            self.server.shutdown()
            raise KeyboardInterrupt()
        except Exception, e:
            self.logger.exception(e.message)
            raise

    def close(self):
        self.logger.debug('Close requested')
        self.server.shutdown()

class HttpRendererHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global _HttpRendererSingleton
        renderers = _HttpRendererSingleton.renderers
        root = _HttpRendererSingleton.root
        context = _HttpRendererSingleton.context
        
        data = copy.deepcopy(_HttpRendererSingleton.data)
        
        params = cgi.parse_qsl(urlparse.urlsplit(self.path).query)
        for p in params:
            data[p[0]] = p[1]
        
        content = None

        name = urlparse.urlsplit(self.path).path.strip('/')

        if name == "":
            if not root:
                mime = "text/html"
                content = "<html><head><title>wfrender</title><body>"
                for renderer in renderers.keys():
                    content += "<a href='"+renderer+"'>"+renderer+"</a><br>"
                content += "</body></html>"
            else:
                [ mime, content ] = root.render(data, context)
        else:
            if renderers is not None and renderers.has_key(name):
                [ mime, content ] = renderers[name].render(data, context)

        if content:
            self.send_response(200)
            self.send_header('Content-type', mime)
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404,"File Not Found: '%s'" % self.path)

class StoppableHTTPServer(HTTPServer):

    def __init__(self, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.__serving = False
        self.__is_shut_down = threading.Event()

    def serve_forever(self, poll_interval=0.1):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        self.__serving = True
        self.__is_shut_down.clear()
        while self.__serving:
            # XXX: Consider using another file descriptor or
            # connecting to the socket to wake this up instead of
            # polling. Polling reduces our responsiveness to a
            # shutdown request and wastes cpu at all other times.
            r, w, e = select.select([self], [], [], poll_interval)
            if r:
                self._handle_request_noblock()
        self.__is_shut_down.set()

    def shutdown(self):
        """Stops the serve_forever loop.

        Blocks until the loop has finished. This must be called while
        serve_forever() is running in another thread, or it will
        deadlock.
        """
        self.__serving = False

    def _handle_request_noblock(self):
        """Handle one request, without blocking.

        I assume that select.select has returned that the socket is
        readable before this function was called, so there should be
        no risk of blocking in get_request().
        """
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.close_request(request)
