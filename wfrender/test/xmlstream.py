import sys
import optparse
from StringIO import StringIO
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

def listen_stdin():
    end = False
    buffer = StringIO()
    while not end:
        line = sys.stdin.readline()

        if line.strip() == "":
            process_event(buffer.getvalue())
            buffer.close()
            buffer = StringIO()
        else:
            buffer.write(line)

        end = (line == "")

class HTTPEventHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        process_event(rfile.read())

def listen_http(port):
    HTTPServer(('', port), HTTPEventHandler).serve_forever()

def process_event(message):
    print message

opt_parser = optparse.OptionParser()
opt_parser.add_option("-p", "--port", dest="port", help="If set, listen on this port for HTTP POST events. Otherwise, listen on standard input.")
(options, args) = opt_parser.parse_args()

if options.port is not None:
    listen_http(int(options.port))
else:
    listen_stdin()
