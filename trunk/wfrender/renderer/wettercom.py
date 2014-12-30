## Copyright 2011 Robin Kluth <commi1993gmail.com>
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

import math
import logging
import sys
import time
import hashlib
import json
from wfcommon.formula.base import LastFormula
from httplib import HTTPConnection
from urllib import urlencode

try:
    from wfrender.datasource.accumulator import AccumulatorDatasource
except ImportError, e:
    from datasource.accumulator import AccumulatorDatasource

class WetterComPublisher(object):
    """
    Render and publisher for wetter.com.

    [ Properties ]

    stationId [string]:
        Your wetter.com station-ID.

    password [string]:
        Your station password

    period [numeric]:
        The update period in seconds.

    storage: 
        The storage service.

    test: 
        true if test-publishing
    """

    stationId = None
    password = None
    publisher = None
    storage = None
    alive = False
    test = False

    logger = logging.getLogger("renderer.wettercom")

    def render(self, data={}, context={}):
        try:
            assert self.stationId is not None, "'wettercom.stationId' must be set"
            assert self.password is not None, "'wettercom.password' must be set"
            assert self.period is not None, "'wettercom.period' must be set"

            self.logger.info("Initializing Wetter.com (stationID %s)" % self.stationId)

            self.alive = True

            accu = AccumulatorDatasource()
            accu.slice = 'hour'
            accu.span = 1
            accu.storage = self.storage

            accu.formulas =     {'current': {
                 'temp'         : LastFormula('temp'),
                 'hum'          : LastFormula('hum'),
                 'hum2'         : LastFormula('hum2'),
                 'pressure'     : LastFormula('pressure'),
                 'wind'         : LastFormula('wind'),
                 'wind_deg'     : LastFormula('wind_dir'),
                 'rain'         : LastFormula('rain'),
                 'localtime'    : LastFormula('localtime'),
                 'utctime'      : LastFormula('utctime'),
                 'dew_point'    : LastFormula('dew_point') } }

            while self.alive:
                try:
                    data = accu.execute()['current']['series']
                    self.logger.debug("Got data from accumulator: %s" % data)
                    index = len(data['lbl'])-1

                    try:
                        # If date is NoneType (see except for this try), we need to wait for a new value in wfrog.csv

                        args = {
                            'sid'                   : 'wfrog',
                            'id'                    : str(self.stationId),
                            'pwd'                   : str(self.password),
                            'dt'                    : data['localtime'][index].strftime('%Y%m%d%H%M'),
                            'dtutc'                 : data['utctime'][index].strftime('%Y%m%d%H%M'), # we need both, dt (date) and dtutc (date in UTC).
                            'hu'                    : int(round(data['hum'][index])),
                            'te'                    : str(data['temp'][index]),
                            'dp'                    : str(data['dew_point'][index]),
                            'wd'                    : int(round(data['wind_deg'][index])),
                            'ws'                    : str(data['wind'][index]),
                            'pr'                    : str(data['pressure'][index]),
                            'pa'                    : str(data['rain'][index])
                            }
                            
                        if self.test:
                            args["test"] = "true"
                            self.logger.info('#!#!#!#!#!#!#!#!#!#! >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Running in test-mode!! The data wont be stored. #!#!#!#!#!#!#!#!#!#!')

                        self.logger.debug("Publishing wettercom data: %s " % args)
                        rawResponse = self._publish(args, 'interface.wetterarchiv.de', '/weather/')
                        self.logger.debug('Server response: Code: %s Status: %s API-Answer: %s' % rawResponse)
                        
                        # Ok, now create an JSON-object
                        response = json.loads(rawResponse[2])
                        
                        # With the new API, checking for any error is very easy!
                        if (response["status"] == "success"):
                            self.logger.info('Data published successfully!')
                        else:
                            self.logger.error('Data publishing fails! Code: %s | Description: %s' % response["errorcode"], response["errormessage"])

                    except Exception, e:
                        if (str(e) == "'NoneType' object has no attribute 'strftime'") or (str(e) == "a float is required"):
                            self.logger.error('Could not publish: no valid values at this time. Retry next run...')
                        else:
                            self.logger.error('Got unexpected error. Retry next run. Error: %s' % e)
                            raise
                except Exception, e:
                    self.logger.exception(e)

                time.sleep(self.period)

        except Exception, e:
            self.logger.exception(e)
            raise

    def close(self):
        self.alive = False

    def _publish(self, args, server, uri):
      
      self.logger.debug('Connect to: http://%s' % server)
      self.logger.debug('POST %s' % uri)
      self.logger.debug('... and the following data: %s' % urlencode(args))

      conn = HTTPConnection(server)
      if not conn:
         raise Exception, 'Remote server connection timeout!'
     
      headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}

      conn.request("POST", uri, urlencode(args), headers)
      conn.sock.settimeout(5.0)

      http = conn.getresponse()
      self.logger.debug("Header: %s" % http.getheaders())
      data = (http.status, http.reason, http.read())
      conn.close()
      if not (data[0] == 200 and data[1] == 'OK'):
         raise Exception, 'Server returned invalid status: %d %s %s' % data
      return data