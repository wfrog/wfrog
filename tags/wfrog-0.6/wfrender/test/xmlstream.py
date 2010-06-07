import sys
import optparse
from StringIO import StringIO
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from Queue import Queue
from threading import Thread

# The event queue decoupling the logger thread and the listener receiving events
# from the driver
event_queue = Queue(500)

def main():

    # Configure the example
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("-s", "--source", dest="source", default="stdin", help="Where to read the events from. \
        Can be 'local' (simulates an embedded driver), \
        'http' (listening to XML events submitted by HTTP POST) or \
        'stdin' (reading events on the standard output, separated by an empty line). Defaults to 'stdin'")
    opt_parser.add_option("-p", "--port", dest="port", default="8080",
        help="If source is HTTP, listen on this port for HTTP POST events. Defaults to 8080")
    (options, args) = opt_parser.parse_args()

    # Start the logger thread
    logger_thread = Thread(target=logger_loop)
    logger_thread.setDaemon(True)
    logger_thread.start()

    # Start the chosen listener
    if options.source == 'http':
        listen_http(int(options.port))

    if options.source == 'stdin':
        listen_stdin()

    if options.source == 'local':
        listen_local()

    # Wait
    logger_thread.join()

# The logger thread body, picking events from the queue and "logging" them to the console
def logger_loop():
    while True:
        event = event_queue.get(block=True)
        if(event == "stop"):
            break
        print event.__dict__

##############################################
# Example listening on stdin, e.g. for pipe communication

def listen_stdin():
    end = False
    buffer = StringIO()
    while not end:
        line = sys.stdin.readline()

        if line.strip() == "":
            message = buffer.getvalue().strip()
            if not message == "": # skip additional emtpy lines
                process_message(buffer.getvalue())
            buffer.close()
            buffer = StringIO()
        else:
            buffer.write(line)

        end = (line == "")
    enqueue_event("stop") # special event to stop the logger

##############################################
# Example listening on HTTP, good for remote communication

class HTTPEventHandler(BaseHTTPRequestHandler):

    protocol_version = 'HTTP/1.1'

    def do_POST(self):
        clen = self.headers.getheader('content-length')
        if clen:
            clen = int(clen)
        else:
            self.send_error(411)

        message = self.rfile.read(clen)
        process_message(message)

        self.send_response(200)
        self.send_header('Content-length', 0)
        self.end_headers()

def listen_http(port):
    HTTPServer(('', port), HTTPEventHandler).serve_forever()

##############################################
# Example simulating the case where the driver runs in the same python process

class empty_event(object):
       pass

def listen_local():
    event = empty_event() # create "native" events
    event.type = "temp"
    event.sensor = 2
    event.value = 24

    enqueue_event(event)

    event = empty_event()
    event.type = "temp"
    event.sensor = 3
    event.value = 25

    enqueue_event(event)
    enqueue_event("stop")

##############################################
# Transform XML messages to events
def process_message(message):
    from lxml import objectify
    event = objectify.XML(message)
    event.type = event.tag
    enqueue_event(event)

# Put an event on the queue
def enqueue_event(event):
    event_queue.put(event, block=True, timeout=60)

main()
