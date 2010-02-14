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

import math
import renderer
import units
import logging
import sys
import time
import wfcommon.database

class MeteoclimaticRenderer(object):
    """
    Renders the data chunk to send to www.meteoclimatic.com.

    Properties
        id: meteoclimatic station ID
    """

    logger = logging.getLogger("renderer.meteoclimatic")

    def render(self, data={}, context={}):
        try:
            now = time.localtime()
            db = wfcommon.database.DBFactory({'type':'firebird', 'database':context['database']['url']})
            db.connect()
            ## Current data
            data_block_1 = self._calculateCurrentData(db)
            ## Today data
            data_block_2 = self._calculateAggregData(db, 'D','%s.%s.%s'%(now.tm_year, now.tm_mon, now.tm_mday))
            ## Current month
            data_block_3 = self._calculateAggregData(db, 'M','%s.%s.1'%(now.tm_year, now.tm_mon))
            ## Current year
            data_block_4 = self._calculateAggregData(db, 'Y','%s.1.1'%(now.tm_year))
            db.disconnect()
            return ['text/plain', "*VER=DATA2*COD=%s%s%s%s%s*EOT*" % (
                    self.id, data_block_1, data_block_2, data_block_3, data_block_4)]
        except Exception, e:
            self.logger.warning("Error rendering meteoclimatic data: %s" % str(e))
            return ['text/plain', "*VER=DATA2*COD=%s*EOT*" % self.id]

    def _calculateCurrentData(self, db):
        sql = """
SELECT FIRST 1 TIMESTAMP_LOCAL, TEMP, WIND_GUST, WIND_GUST_DIR, PRESSURE, HUM
FROM METEO
ORDER BY TIMESTAMP_UTC DESC
        """
        [(UPD, TMP, WND, AZI, BAR, HUM)] = db.select(sql)
        return "*UPD=%s*TMP=%s*WND=%s*AZI=%s*BAR=%s*HUM=%s*SUN=" % (
               UPD.strftime("%d/%m/%Y %H:%M"), TMP,  WND * 3.6, AZI, BAR, HUM)


    def _calculateAggregData(self, db, time_span, date_from):
        sql = """
SELECT MAX(TEMP), MIN(TEMP), MAX(HUM), MIN(HUM), MAX(PRESSURE), MIN(PRESSURE), MAX(WIND_GUST), SUM(RAIN)
FROM METEO
WHERE TIMESTAMP_LOCAL >= '%s'
        """ % date_from
        [(HTM, LTM, HHM, LHM, HBR, LBR, GST, PCP)] = db.select(sql)
        return "*%sHTM=%s*%sLTM=%s*%sHHM=%s*%sLHM=%s*%sHBR=%s*%sLBR=%s*%sGST=%s*%sPCP=%s" % (
               time_span, HTM, time_span, LTM, time_span, HHM, time_span, LHM,
               time_span, HBR, time_span, LBR, time_span, GST * 3.6, time_span, PCP )




