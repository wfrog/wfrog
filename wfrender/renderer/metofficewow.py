## Copyright 2013 Chris Brunt <chris.brunt@gmail.com>
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
import wfcommon.database
from wfcommon.formula.base import LastFormula
from wfcommon.formula.base import SumFormula
from httplib import HTTPConnection
from urllib import urlencode

try:
    from wfrender.datasource.accumulator import AccumulatorDatasource
except ImportError, e:
    from datasource.accumulator import AccumulatorDatasource
from wfcommon.units import HPaToInHg
from wfcommon.units import CToF
from wfcommon.units import MmToIn
from wfcommon.units import MpsToMph

class MetOfficeWowPublisher(object):
    """
    Render and publisher for UK Metoffice WOW (weather Observations Website).

    [ Properties ]

    username [string]:
        Your MetOffice Site ID.

    password [string]:
        Your MetOffice Site Authentication Key

    period [numeric]:
        The update period in seconds. Default value is 900 (15 min.)

    storage:
        The storage service.
    """

    username = None
    password = None
    publisher = None
    storage = None
    period = 900
    alive = False

    logger = logging.getLogger("renderer.metofficeWOW")

    def render(self, data={}, context={}):
        try:
            assert self.username is not None, "'MetofficeWOW.siteid' must be set"
            assert self.password is not None, "'MetofficeWOW.siteAuthenticationKey' must be set"
            assert self.period is not None, "'MetofficeWOW.period' must be set"

            self.logger.info("Initializing MetOffice WOW Upload (user %s)" % self.username)

            self.alive = True

            accu = AccumulatorDatasource()
            accu.slice = 'hour'
            accu.span = 2
            accu.storage = self.storage

            accu.formulas = {'current': {
                 'temp'         : LastFormula('temp'),
                 'hum'          : LastFormula('hum'),
                 'pressure'     : LastFormula('pressure'),
                 'wind'         : LastFormula('wind'),
                 'wind_deg'     : LastFormula('wind_dir'),
                 'rain'         : SumFormula('rain'),
                 'utctime'      : LastFormula('utctime') } }

            while self.alive:
                try:
                    data = accu.execute()['current']['series']
                    index = len(data['lbl'])-1

                    args = {
                        'dateutc':                data['utctime'][index].strftime('%Y-%m-%d %H:%M:%S'),
                        # Some ARGs are hashed out here as Metoffice WOW needs them in the correct order or it will reject the post
                        # I found that if I used the args they are in a random order so define them on the URL encode instead
                        #'siteAuthenticationKey': str(self.password),
                        #'softwaretype':          "Wfrog",
                        'humidity':               int(round(data['hum'][index])),
                        'tempf':                  str(CToF(data['temp'][index])),
                        #'siteid':                str(self.username),
                        'winddir':                int(round(data['wind_deg'][index])),
                        'windspeedmph':           str(MpsToMph(data['wind'][index])),
                        'baromin':                str(HPaToInHg(data['pressure'][index])),
                        'rainin':                 str(MmToIn(data['rain'][index])) }

                    self.logger.info("Publishing Metoffice WOW data: %s " % urlencode(args))
                    self._publish(args, 'wow.metoffice.gov.uk', '/automaticreading')

                except Exception, e:
                    if (str(e) == "'NoneType' object has no attribute 'strftime'") or (str(e) == "a float is required"):
                        self.logger.error('Could not publish: no valid values at this time. Retry next run...')
                    else:
                        self.logger.error('Got unexpected error. Retry next run. Error: %s' % e)
 
                time.sleep(self.period)

        except Exception, e:
            self.logger.exception(e)
            raise

    def close(self):
        self.alive = False

    def _publish(self, args, server, uri):
        uri = uri + "?siteid=" + str(self.username) + "&siteAuthenticationKey=" + str(self.password) + "&" + urlencode(args) + "&softwaretype=Wfrog"

        self.logger.debug('Connect to: http://%s' % server)

        conn = HTTPConnection(server)
        if not conn:
            raise Exception, 'Remote server connection (%s) timeout!' % server

        self.logger.debug('GET %s' % uri)

        conn.request("GET", uri)
        conn.sock.settimeout(5.0)

        http = conn.getresponse()
        data = (http.status, http.reason, http.read())
        conn.close()

        self.logger.debug('Response: %d, %s, %s' % data)

        if not (data[0] == 200 and data[1] == 'OK'):
            raise Exception, 'Server returned invalid status: %d %s %s' % data
        return data

