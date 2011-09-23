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

    username [string]:
        Your wetter.com username.

    password [string]:
        password - wfrog ALWAYS send your password md5-decrypted to wetter.com!

    period [numeric]:
        The update period in seconds.

    storage: 
        The storage service.

    test: 
        true if test-publishing
    """

    username = None
    password = None
    publisher = None
    storage = None
    alive = False
    test = False

    logger = logging.getLogger("renderer.wettercom")

    def render(self, data={}, context={}):
        try:
            assert self.username is not None, "'wettercom.id' must be set"
            assert self.password is not None, "'wettercom.password' must be set"
            assert self.period is not None, "'wettercom.period' must be set"

            self.logger.info("Initializing Wetter.com (user %s)" % self.username)

            self.alive = True

            accu = AccumulatorDatasource()
            accu.slice = 'hour'
            accu.span = 1
            accu.storage = self.storage

            accu.formulas =     {'current': {
                 'temp'         : LastFormula('temp'),
                 'hum'          : LastFormula('hum'),
                 'pressure'     : LastFormula('pressure'),
                 'wind'         : LastFormula('wind'),
                 'wind_deg'     : LastFormula('wind_dir'),
                 'rain'         : LastFormula('rain'),
                 'localtime'    : LastFormula('localtime') } }

            while self.alive:
                try:
                    data = accu.execute()['current']['series']
                    index = len(data['lbl'])-1

                    try:
                        # try, if date is NoneType, if yes, we need to wait for a new value in wfrog.csv

                        args = {
                            'benutzername':         str(self.username),
                            'passwortmd5':          hashlib.md5(str(self.password)).hexdigest(),
                            'datum':                data['localtime'][index].strftime('%Y%m%d%H%M'),
                            'feuchtigkeit':         int(round(data['hum'][index])),
                            'temperatur':           str(data['temp'][index]).replace('.', ','),
                            'windrichtung':         int(round(data['wind_deg'][index])),
                            'windstaerke':          str(data['wind'][index]).replace('.', ','),
                            'luftdruck':            str(data['pressure'][index]).replace('.', ','),
                            'niederschlagsmenge':   str(data['rain'][index]).replace('.', ',')
                            }

                        if self.test:
                            args['test'] = "true"
                            self.logger.info('Running in test-mode!! The data wont be stored.')
                        else:
                            # If test is not true, we must send &test=false. If the GET string ends with rain-value, wetter.com returns an error
                            args['test'] = "false"

                        self.logger.debug("Publishing wettercom data: %s " % urlencode(args))

                        response = self._publish(args, 'www.wetterarchiv.de', '/interface/http/input.php')
                        # Split response to determine if the request was ok or not.
                        answer = response[2].split('=')

                        if (answer[1] == 'SUCCESS&') or (answer[5] == 'SUCCESS&'):
                            self.logger.info('Data published successfully')
                        else:
                            self.logger.error('Data publishing fails! Response: %s' % answer[5])

                        self.logger.debug('Publish-data: %s Status: %s Answer: %s' % response)

                    except Exception, e:
                        if str(e) == "'NoneType' object has no attribute 'strftime'":
                            self.logger.error('Could not publish to wetter.com: no valid values at this time. Retry next run...')
                        else:
                            self.logger.exception(e)

                except Exception, e:
                    self.logger.exception(e)

                time.sleep(self.period)

        except Exception, e:
            self.logger.exception(e)
            raise

    def close(self):
        self.alive = False

    def _publish(self, args, server, uri):

      uri = uri + "?" + urlencode(args)
      
      self.logger.debug('Connect to: http://%s' % server)
      self.logger.debug('GET %s' % uri)

      conn = HTTPConnection(server)
      if not conn:
         raise Exception, 'Remote server connection timeout!'

      conn.request("GET", uri)
      conn.sock.settimeout(5.0)

      http = conn.getresponse()
      data = (http.status, http.reason, http.read())
      conn.close()
      if not (data[0] == 200 and data[1] == 'OK'):
         raise Exception, 'Server returned invalid status: %d %s %s' % data
      return data