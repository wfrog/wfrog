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

from pygooglechart import Chart
from pygooglechart import _check_colour
from pygooglechart import Axis
from pygooglechart import RadarChart
from pygooglechart import SimpleLineChart
import renderer
import webcolors
import re
import logging


class GoogleChartRenderer(object):    
    """
    Renders the data as a google chart URL.

    Properties

    series:
        Defines which series data are rendered on the chart and
        their options.

    """
    
    series = None
    labels = None

    logger = logging.getLogger("renderer.chart")

    def render(self,data={}, context={}):

        assert self.series is not None, "'chart.series' must be set"
        assert renderer.is_dict(self.series), "'chart.series' must be a key/value dictionary"

        width = _defaults(context, 'width', 200)
        height =_defaults(context, 'height', 125)
        color = _defaults(context, 'color', 'orange')
        bgcolor = _defaults(context, 'bgcolor', "00000000")

        if context.has_key("chart_defaults"):
            defaults = context["chart_defaults"]
            if defaults.has_key('width'):
                width = defaults['width']
            if defaults.has_key('height'):
                height = defaults['height']                

        chart = SimpleLineChart(width, height)        

        colours = []

        for serie in self.series.keys():
            chart.add_data(data[serie.split('.')[0]]['series'][serie.split('.')[1]])
            colours.append(_valid_color(color))

        chart.set_colours(colours)

        if self.labels:
            chart.set_axis_labels(Axis.BOTTOM, data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]])

        return chart.get_url()

class GoogleChartWindRadarRenderer(object):
    """
    Renders wind data as a radar google chart URL
    """

    key = None

    def render(self,data={}, context={}):
        color = '000000'
        bg = 'FFFFFF'
        size = 20+data[self.key]['value']
        pos = data[self.key]['dir']
        line = [0] * 16
        tail = [0] * 16
        head = [0] * 16

        line[pos] = 100
        tail[pos] = size * 1.5
        head[ (pos - 1 + 16) % 16 ] = size
        head[ (pos + 1) % 16 ] = size

        chart = RadarChart(120, 120, y_range=(0,100) )
        chart.add_data([0] * 2)
        chart.add_data(line)
        chart.add_data(tail)
        chart.add_data(head)
        chart.add_data([100] * 2)

        #chart.add_fill_range(color, 0, 2)
        chart.set_colours( [bg, 'EEEEEE', color, color, bg] )
        chart.set_axis_labels(Axis.BOTTOM, ['N', '', 'NE', '', 'E', '', 'SE', '', 'S', '', 'SW', '', 'W', '', 'NW', ''])
        chart.set_axis_style(0, 'BBBBBB', 10, 0, 'l', bg);
        chart.set_line_style(1, 1)
        chart.set_line_style(2, 1+size/30)
        chart.set_line_style(3, 1+size/30)

        return chart.get_url()


def _axis_set_style(self, colour, font_size=None, alignment=None, drawing_control=None, tick_colour=None):
    _check_colour(colour)
    self.colour = colour
    self.font_size = font_size
    self.alignment = alignment
    self.drawing_control = drawing_control
    self.tick_colour = tick_colour
    if tick_colour is not None:
        _check_colour(tick_colour)
    self.has_style = True

def _axis_style_to_url(self):
    bits = []
    bits.append(str(self.axis_index))
    bits.append(self.colour)
    if self.font_size is not None:
        bits.append(str(self.font_size))
        if self.alignment is not None:
            bits.append(str(self.alignment))
            if self.drawing_control is not None:
                assert(self.drawing_control in Axis.DRAWING_CONTROL)
                bits.append(self.drawing_control)
                if self.tick_colour is not None:
                    bits.append(self.tick_colour)

    return ','.join(bits)

Axis.AXIS_LINES = 'l'
Axis.TICK_MARKS = 't'
Axis.BOTH = 'lt'
Axis.DRAWING_CONTROL = (Axis.AXIS_LINES, Axis.TICK_MARKS, Axis.BOTH)

def _chart_set_axis_style(self, axis_index, colour, font_size=None, \
      alignment=None, drawing_control=None, tick_colour=None):
    try:
        self.axis[axis_index].set_style(colour, font_size, alignment, drawing_control, tick_colour)
    except IndexError:
        raise InvalidParametersException('Axis index %i has not been created' % axis)

Axis.set_style = _axis_set_style
Axis.style_to_url = _axis_style_to_url

Chart.set_axis_style = _chart_set_axis_style

def _defaults(context, property, default):
    result = default
    if context.has_key("chart_defaults"):
        defaults = context["chart_defaults"]
        if defaults.has_key(property):
            result = defaults[property]
    return result

def _valid_color(color):
    if re.match("[0-9]+", color):
        return color
    else:
        return webcolors.name_to_hex(color)[1:]
