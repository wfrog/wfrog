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
import copy
import logging
import sys

LABEL_DENSITY_THRESHOLD = 1.78

class ChartConfig(object):
    width = 200
    height = 125
    color = 'orange'
    thickness = 1.5
    text = '7F7F7F'
    bgcolor = '00000000'
    y_margin = [ 2, 2 ]
    fill = None
    zero = None
    max = None
    min = None
    last = None
    style = 'v'
    size = 10
    axes = 'on'
    ticks = 'on'
    dash = None
    legend = None
    legend_pos = 'b'
    marks = None
    space = 1.5
    
    def __missing__(item):
        return None

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

        # merge builtin defaults, context and renderer config
        config = ChartConfig()       
        if context.has_key('chart'):
            config.__dict__.update(context['chart'])
        config.__dict__.update(self.__dict__)        

        chart = SimpleLineChart(config.width, config.height)        

        colors = []        
        legend_set = False
        legend = []

        chart_min = sys.maxint
        chart_max = -sys.maxint

        index=0
        for key, serie in self.series.iteritems():
            serie_config = ChartConfig()
            serie_config.__dict__.update(config.__dict__)
            serie_config.__dict__.update(serie)
            serie_data = data[key.split('.')[0]]['series'][key.split('.')[1]]
            chart.add_data(serie_data)
                      
            min_data = min(serie_data)
            chart_min = min(chart_min, min_data)
            min_index = serie_data.index(min_data)
            max_data = max(serie_data)
            chart_max = max(chart_max, max_data)
            max_index = serie_data.index(max_data)
            
            colors.append(_valid_color(serie_config.color))            
            
            if serie_config.max:
                max_config = ChartConfig()
                max_config.__dict__.update(serie_config.__dict__)                
                max_config.__dict__.update(serie_config.max)
                chart.add_marker(index, max_index, 't'+str(max_data), _valid_color(max_config.text), max_config.size)
                chart.add_marker(index, max_index, max_config.style, _valid_color(max_config.color), max_config.thickness)

            if serie_config.min:
                min_config = ChartConfig()
                min_config.__dict__.update(serie_config.__dict__)                
                min_config.__dict__.update(serie_config.min)
                chart.add_marker(index, min_index, 't'+str(min_data), _valid_color(min_config.text), min_config.size)
                chart.add_marker(index, min_index, min_config.style, _valid_color(min_config.color), min_config.thickness)
           
            if serie_config.last:
                last_config = ChartConfig()
                last_config.__dict__.update(serie_config.__dict__)                
                last_config.__dict__.update(serie_config.last)
                last_index=len(serie_data)-1
                last_data = serie_data[last_index]
                chart.add_marker(index, last_index, 't'+str(last_data), _valid_color(last_config.text), last_config.size)
                chart.add_marker(index, last_index, last_config.style, _valid_color(last_config.color), last_config.thickness)
           
            if serie_config.fill:
                fill_config = ChartConfig()
                fill_config.__dict__.update(serie_config.__dict__)
                fill_config.__dict__.update(serie_config.fill)
                to = self.series.keys().index(fill_config.to)
                chart.add_fill_range(_valid_color(fill_config.color), index, to)
            
            if serie_config.dash:
                chart.set_line_style(index, serie_config.thickness, serie_config.dash, serie_config.dash)
            else:
                chart.set_line_style(index, serie_config.thickness)
            
            if serie_config.legend:
                legend.append(serie_config.legend)
                legend_set = True
            else:
                legend.append('')
            
            if serie_config.marks:
                mark_config = ChartConfig()
                mark_config.__dict__.update(serie_config.__dict__)
                mark_config.__dict__.update(serie_config.marks)
                mark_data = data[mark_config.serie.split('.')[0]]['series'][mark_config.serie.split('.')[1]]                
                density = max(1.0, 1.0 * mark_config.space * len("".join(mark_data))*mark_config.size  / config.width)
          
                for i, v in enumerate(mark_data):
                    if (i +1) % round(density) == 0:              
                        chart.add_marker(index, i, 't'+str(mark_data[i]), _valid_color(mark_config.color), mark_config.size)                
        
            index = index + 1

        chart.y_range=[chart_min-config.y_margin[0], chart_max+config.y_margin[1]]     
        if config.axes == 'on':            
            chart.set_axis_range(Axis.LEFT, chart_min-config.y_margin[0], chart_max+config.y_margin[1])        
            chart.set_axis_style(0, _valid_color(config.text), config.size, 0, Axis.BOTH if config.ticks == 'on' else Axis.AXIS_LINES)
        else:
            chart.set_axis_labels(Axis.LEFT, [])
            chart.set_axis_style(0, _valid_color(config.text), config.size, 0, Axis.TICK_MARKS, _valid_color(config.bgcolor))

        if config.zero:
            zero_config = ChartConfig()
            zero_config.__dict__.update(config.__dict__)
            zero_config.__dict__.update(config.zero)
            chart.add_data([0]*2)
            colors.append(_valid_color(zero_config.color))
            chart.set_line_style(index, zero_config.thickness)

        chart.set_colours(colors)
        chart.fill_solid(Chart.BACKGROUND, _valid_color(config.bgcolor))        
        
        if legend_set:
            chart.set_legend(legend)
            chart.set_legend_position(config.legend_pos)

        if self.labels:
            if config.axes == 'on':
                labels_data = data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]]
                density = 1.0 * len("".join(labels_data))*config.size  / config.width
          
                if density > LABEL_DENSITY_THRESHOLD:
                    for i, v in enumerate(labels_data):
                        if i % round(density) != 0:
                            labels_data[i] = ' '
                chart.set_axis_labels(Axis.BOTTOM, labels_data)                
                chart.set_axis_style(1, _valid_color(config.text), config.size, 0, Axis.BOTH if config.ticks == 'on' else Axis.AXIS_LINES)
            else:
                chart.set_axis_labels(Axis.BOTTOM, []) 
                chart.set_axis_style(1, _valid_color(config.text), config.size, 0, Axis.TICK_MARKS, _valid_color(config.bgcolor))
                
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


def _valid_color(color):
    if re.match("[A-F0-9]+", color):
        return color
    else:
        return webcolors.name_to_hex(color)[1:]
