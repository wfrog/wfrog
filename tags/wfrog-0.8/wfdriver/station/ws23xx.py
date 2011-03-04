## Copyright 2010 Laurent Bovet <laurent.bovet@windmaster.ch>
##                derived from ws2300 by Russell Stuart
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

import time
import logging
from wfcommon import units

class WS2300Station(object):

    '''
    Station driver for LaCrosse 2300.
      
    This driver is a wrapper around ws2300 (http://ace-host.stuart.id.au/russell/files/ws2300/), 
    thus needs this package installed on your system.    
    
    [Properties]
    
    port [string] (optional):
        The serial port the station is attached to. Defaults to /dev/ttyS0.
    
    period [numeric] (optional):
        Polling interval in seconds. Defaults to 60.    
    '''

    port = "/dev/ttyS0"

    period=60

    logger = logging.getLogger('station.ws2300')
    

    def run(self, generate_event, send_event, context={}):
    
        import ws2300   
        print(dir(ws2300))
        
        while True:
            serialPort = ws2300.LinuxSerialPort(self.port)
            serialPort.open()
            try:
                ws = ws2300.Ws2300(serialPort)
                measures = [
                    ws2300.Measure.IDS["pa"],
                    ws2300.Measure.IDS["it"],
                    ws2300.Measure.IDS["ih"],
                    ws2300.Measure.IDS["ot"],
                    ws2300.Measure.IDS["oh"],
                    ws2300.Measure.IDS["rh"],
                    ws2300.Measure.IDS["rt"],
                    ws2300.Measure.IDS["ws"],
                    ws2300.Measure.IDS["wsm"],
                    ws2300.Measure.IDS["w0"],
                    ]
                raw_data = ws2300.read_measurements(ws, measures)
                
                data = [ m.conv.binary2value(d) for m, d in zip(measures, data)]
                
            finally:
              serialPort.close()

            try:                
                e = generate_event('press')
                e.value = data[0]
                send_event(e)

                e = generate_event('temp')
                e.sensor = 0
                e.value = data[1]
                send_event(e)
                
                e = generate_event('hum')
                e.sensor = 0
                e.value = data[2]
                send_event(e)
                                
                e = generate_event('temp')
                e.sensor = 1
                e.value = data[3]
                send_event(e)
                
                e = generate_event('hum')
                e.sensor = 1
                e.value = data[4]
                send_event(e)
                
                e = generate_event('rain')                
                e.rate = data[5]
                e.total = data[6]
                send_event(e)
                
                e = generate_event('wind')
                e.create_child('mean')
                e.mean.speed = units.MphToMps(data[7])
                e.mean.dir = data[9]
                e.create_child('gust')
                e.gust.speed = units.MphToMps(data[8])
                e.gust.dir = data[9]
                send_event(e)                        
                
            except Exception, e:
                self.logger.error(e)
                
            # pause until next update time
            next_update = self.period - (time.time() % self.period)
            time.sleep(next_update)                
