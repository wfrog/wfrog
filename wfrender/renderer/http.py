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

import string,cgi,time
import threading
import socket
import select
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import copy
import urlparse, cgi, Cookie
import logging
import posixpath
import urllib
import os

class HttpRenderer(object):
    """
    Renderer starting an embedded HTTP server and serves the content
    results from the wrapped renderers.
    The URL corresponds to the wrapped renderer names.
    Only one such renderer must be configured in one process.

    This renderer runs indefinitely until close() is called.

    render result [none]:
        Nothing is returned by this renderer.

    [ Properties ]

    root [renderer] (optional):
        A renderer providing a result served on the base URI.

    renderers [dict] (optional):
        Must be set if root is not set. A key/value dictionary of
        renderers providing a results served on URIs corresponding to
        the key names.

    port [numeric] (optional):
        The listening TCP port. Defaults to 7680.

    cookies [list] (optional):
        List of context sections overridable with a cookie using the -set- uri.
        
    static [string] (optional):
        Activates the serving of static files and specify under which URL path they are served. Disabled by default.
        
    docroot [string] (optional):
        Root directory served when static content is enabled. Defaults to /var/wwww.
        
    """

    renderers = None
    port = 7680
    root = None
    cookies = []
    static = None
    docroot = "/var/www"

    logger = logging.getLogger("renderer.http")

    def render(self, data={}, context={}):

        self.context = context
        self.context["http"] = True # Put in the context that we use the http render. It may be useful to know that in templates.
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
            self.logger.exception(e)
            raise

    def close(self):
        self.logger.debug('Close requested')
        self.server.shutdown()

class HttpRendererHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global _HttpRendererSingleton
        renderers = _HttpRendererSingleton.renderers
        root = _HttpRendererSingleton.root
        context = copy.deepcopy(_HttpRendererSingleton.context)
        cookie_sections = _HttpRendererSingleton.cookies

        data = copy.deepcopy(_HttpRendererSingleton.data)

        try:
            params = cgi.parse_qsl(urlparse.urlsplit(self.path).query)
            for p in params:
                data[p[0]] = p[1]

            content = None

            name = urlparse.urlsplit(self.path).path.strip('/')

            if name == "-set-":
                if data.has_key("s") and data.has_key("k") and data.has_key("v"):
                    section = data["s"]
                    key = data["k"]
                    value = data["v"]
                    if not cookie_sections.__contains__(section):
                        self.send_error(403,"Permission Denied")
                        return
                    context[section][key]=value
                    cookie = Cookie.SimpleCookie()

                    cookie[section+"."+key]=value

                    self.send_response(302)
                    self.send_header('Location', self.headers["Referer"] if self.headers.has_key("Referer") else "/")
                    self.wfile.write(cookie)
                    self.end_headers()

                    return
                else:
                    self.send_error(500,"Missing parameters")
                    return

            cookie_str = self.headers.get('Cookie')
            if cookie_str:
                try:
                    cookie = Cookie.SimpleCookie(cookie_str)
                except Exception:
                    cookie = Cookie.SimpleCookie(cookie_str.replace(':', ''))

                 for i in cookie:
                     parts = i.split('.')
                     if len(parts) == 2:
                        section = parts[0]
                        key = parts[1]
                        if cookie_sections.__contains__(section) and context[section].has_key(key):
                            context[section][key]=cookie[i].value

            if _HttpRendererSingleton.static and self.path == "/"+_HttpRendererSingleton.static:
                self.send_response(301);
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return

            if _HttpRendererSingleton.static and self.path.startswith("/"+_HttpRendererSingleton.static+"/"):
                h = StaticFileRequestHandler()             
                h.requestline = self.requestline
                h.request_version = self.request_version
                h.client_address = self.client_address
                h.command = self.command
                h.path = self.path[len(_HttpRendererSingleton.static)+1:]
                h.wfile = self.wfile
                h.rfile = self.rfile
                h.do_GET()
                return

            if name == "":
                if not root:
                    mime = "text/html"
                    content = "<html><head><title>wfrender</title><body>"
                    for renderer in renderers.keys():
                        content += "<a href='"+renderer+"'>"+renderer+"</a><br>"
                    content += "</body></html>"
                else:
                    [ mime, content ] = root.render(data=data, context=context)
            else:
                if renderers is not None and renderers.has_key(name):
                    [ mime, content ] = renderers[name].render(data=data, context=context)
        except Exception, e:
            _HttpRendererSingleton.logger.exception(e)
            self.send_error(500, "Internal Server Error")
            return 

        if content:
            self.send_response(200)
            self.send_header('Content-type', mime)
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404,"File Not Found: '%s'" % self.path)
    
    def log_message(self, format, *args):
        global _HttpRendererSingleton
        _HttpRendererSingleton.logger.info(str(self.client_address[0]) + " - "+ format % args)

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

class StaticFileRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self):
        pass

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        print "IN: "+path
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = _HttpRendererSingleton.docroot
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
