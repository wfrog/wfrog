# -*- coding: latin-1 -*-

## Copyright 2012 Jordi Puigsegur <jordi.puigsegur@gmail.com>
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
import wfcommon.database
from wfcommon.formula.base import LastFormula
from wfcommon.formula.base import SumFormula
from wfcommon.formula.base import MinFormula
from wfcommon.formula.base import MaxFormula
try:
    from wfrender.datasource.accumulator import AccumulatorDatasource
except ImportError, e:
    from datasource.accumulator import AccumulatorDatasource
from wfcommon.units import MpsToKmh
import Image
import ImageDraw
import ImageColor

class StickerRenderer(object):
    """
    Renders a wfrog sticker, to be served via http or uploaded with ftp.
    (currently beta version and only using metric units)

    render result [string]:
        The path to the generated file.

    [ Properties ]

    filename [optional]:
        Sticker temporal filename. By default "/tmp/sticker.png".

    station_name [optional]:
        The name of the station (to appear in sticker). By default "wfrog weather station".

    storage: 
        The storage service.

    logo_file [optional]:
        Location and name of the logo file. By default "/etc/wfrog/wfrender/config/logo.png".
    """

    id = None
    storage = None
    accuY = None
    accuM = None
    accuD = None
    filename = "/tmp/sticker.png"
    station_name = "wfrog weather station"
    logo_file = "/etc/wfrog/wfrender/config/logo.png"
    
    logger = logging.getLogger("renderer.sticker")

    def render(self, data={}, context={}):
        try:
            assert self.storage is not None, "'sticker.storage' must be set"

            # Initialize accumulators

            if self.accuD == None:
                self.logger.info("Initializing accumulators")

                # Accumulator for yearly data
                self.accuY = AccumulatorDatasource()
                self.accuY.slice = 'year'
                self.accuY.span = 1
                self.accuY.caching = True
                self.accuY.storage = self.storage
                self.accuY.formulas = {'data': {
                     'max_temp' : MaxFormula('temp'),
                     'min_temp' : MinFormula('temp'),
                     'max_gust' : MaxFormula('wind_gust'),
                     'rain_fall' : SumFormula('rain') } }

                # Accumulator for monthly data
                self.accuM = AccumulatorDatasource()
                self.accuM.slice = 'month'
                self.accuM.span = 1
                self.accuM.storage = self.storage
                self.accuM.caching = True
                self.accuM.formulas = {'data': {
                     'max_temp' : MaxFormula('temp'),
                     'min_temp' : MinFormula('temp'),
                     'max_gust' : MaxFormula('wind_gust'),
                     'rain_fall' : SumFormula('rain') } }

                # Accumulator for daily and current data
                self.accuD = AccumulatorDatasource()
                self.accuD.slice = 'day'
                self.accuD.span = 1
                self.accuD.storage = self.storage
                self.accuD.caching = True
                self.accuD.formulas = {
                     'data': {
                         'max_temp' : MaxFormula('temp'),
                         'min_temp' : MinFormula('temp'),
                         'max_gust' : MaxFormula('wind_gust'),
                         'rain_fall' : SumFormula('rain') },
                     'current': {
                         'temp' : LastFormula('temp'),
                         'hum' : LastFormula('hum'),
                         'pressure' : LastFormula('pressure'),
                         'gust' : LastFormula('wind_gust'),
                         'wind_deg' : LastFormula('wind_dir'),
                         'time' : LastFormula('localtime') } }

            # Calculate data

            self.logger.info("Calculating ...")
            current = self._calculateCurrentData(self.accuD)
   
            # Create Sticker

            green = ImageColor.getrgb("#007000")
            wheat = ImageColor.getrgb("#F5DEB3")
            dark_wheat = ImageColor.getrgb("#8D7641")
            black =  ImageColor.getrgb("#000000")
            width = 260
            height = 100
            corner = 10

            im = Image.new('RGBA', (width, height), wheat)
            draw = ImageDraw.Draw(im)

            # 1) Transparency
            mask=Image.new('L', im.size, color=0)
            mdraw=ImageDraw.Draw(mask) 
            mdraw.rectangle((corner, 0, width-corner, height), fill=255)
            mdraw.rectangle((0, corner, width, height-corner), fill=255)
            mdraw.chord((0, 0, corner*2, corner*2), 0, 360, fill=255)
            mdraw.chord((0, height-corner*2-1, corner*2, height-1), 0, 360, fill=255)
            mdraw.chord((width-corner*2-1, 0, width-1, corner*2), 0, 360, fill=255)
            mdraw.chord((width-corner*2-1, height-corner*2-1, width-1, height-1), 0, 360, fill=255)
            im.putalpha(mask)

            # 2) Borders
            draw.arc((0, 0, corner*2, corner*2), 180, 270, fill=dark_wheat)
            draw.arc((0, height-corner*2-1, corner*2, height-1), 90, 180, fill=dark_wheat)
            draw.arc((width-corner*2-1, 0, width, corner*2), 270, 360, fill=dark_wheat)
            draw.arc((width-corner*2-1, height-corner*2-1, width-1, height-1), 0, 90, fill=dark_wheat)
            draw.line((corner, 0, width-corner-1,0), fill=dark_wheat)
            draw.line((corner, height-1, width-corner-1, height-1), fill=dark_wheat)
            draw.line((0, corner, 0, height-corner-1), fill=dark_wheat)
            draw.line((width-1, corner, width-1, height-corner-1), fill=dark_wheat)

            # 3) Logo
            logo = Image.open(self.logo_file)
            im.paste(logo, (4, 3), logo) # using the same image with transparencies as mask 

            # 4) Current data
            draw.text((65,5), self.station_name, fill=green)
            draw.text((65,25), "%0.1fC  %d%%  %0.1fKm/h  %dmb" % current[0], fill=black)
            draw.text((65,38), current[1], fill=dark_wheat)

            draw.text((6,60), 
                      " Today:   %4.1fC-%4.1fC  %4.1fKm/h  %5.1fl." % self._calculateAggregData(self.accuD), 
                      fill=dark_wheat) 
            draw.text((6,72), 
                      " Monthly: %4.1fC-%4.1fC  %4.1fKm/h  %5.1fl." % self._calculateAggregData(self.accuM), 
                      fill=dark_wheat) 
            draw.text((6,84), 
                      " Yearly:  %4.1fC-%4.1fC  %4.1fKm/h  %5.1fl." % self._calculateAggregData(self.accuY), 
                      fill=dark_wheat) 

            # Save sticker
            im.save(self.filename)
            self.logger.info("Sticker generated")

            f = open(self.filename, "rb")
            d = f.read()
            f.close()

            return ['image/png', d]

        except Exception, e:
            self.logger.warning("Error rendering sticker: %s" % str(e))
            return None

    def _calculateCurrentData(self, accu):
        data = accu.execute()['current']['series']
        index = len(data['lbl'])-1
        return ( ( self._format(data['temp'][index]),
                   self._format(data['hum'][index]),
                   self._format(MpsToKmh(data['gust'][index])),
                   #'wind_deg': self._format(data['wind_deg'][index])
                   self._format(data['pressure'][index])  ),

                 self._format(data['time'][index].strftime("%d/%m/%Y %H:%M")) )

    def _calculateAggregData(self, accu):
        data = accu.execute()['data']['series']
        index = len(data['lbl'])-1
        return (self._format(data['min_temp'][index]), 
                self._format(data['max_temp'][index]),
                self._format(MpsToKmh(data['max_gust'][index])),  
                self._format(data['rain_fall'][index]) )

    def _format(self, value, default='-'):
        return value if value != None else default



