import renderer
import string,cgi,time
import threading
import socket
import select
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import logging

_HttpRendererSingleton = None

class HttpRenderer(object):
    """
    Renderer starting an embedded HTTP server and serves the content results from the wrapped renderers.
    The URL corresponds to the wrapped renderer names.
    Only one such renderer must be configured in one process.

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

    def close(self):
        self.logger.debug('Close requested')
        self.server.shutdown()

class HttpRendererHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global _HttpRendererSingleton
        renderers = _HttpRendererSingleton.renderers
        root = _HttpRendererSingleton.root
        content = None

        name = self.path.strip('/')

        if name == "":
            if not root:
                mime = "text/html"
                content = "<html><head><title>wfrender</title><body>"
                for renderer in renderers.keys():
                    content += "<a href='"+renderer+"'>"+renderer+"</a><br>"
                content += "</body></html>"
            else:
                [ mime, content ] = root.render()
        else:
            if renderers is not None and renderers.has_key(name):
                [ mime, content ] = renderers[name].render()

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

    def serve_forever(self, poll_interval=0.5):
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
