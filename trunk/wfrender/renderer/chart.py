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
from math import log
import renderer
import webcolors
import re
import copy
import logging
import sys

# Limit of the text density on x-axis to start removing label
LABEL_DENSITY_THRESHOLD = 1.78

# Make min robust to None
def rmin(a,b):
    result = min(a,b)
    if result == None:
        result = max(a,b)
        if result == None:
            result = 0
    return result

def amin(a):
    m=sys.maxint
    for i in a:
        if i and i < m:
            m=i
    return m

# Default configuration
class ChartConfig(object):
    # Graph attributes
    width = 200
    height = 125
    bgcolor = '00000000'
    y_margin = [ 2, 2 ]
    axes = 'on'
    ticks = 'on'
    legend = None
    legend_pos = 'b'
    nval = 100

    # Drawing
    color = '008000'
    thickness = 1.5
    text = '8d7641'
    size = 10 # for text and markers
    fill = None
    style = 'v' # for markers
    dash = None
    intensity = 0.5
    interpolate = False

    # Series
    area = None
    zero = None
    max = None
    min = None
    last = None
    marks = None
    space = 1.5 # Spacing between marks

    # Drawing order
    order = 0

    # Wind Radar
    radius = 16 # max value for logarithmic scaling
    median = 2  # value in the middle of the graph

    tail = None
    arrow = { }
    trace = None
    ratio = 3  # Size i
    length = 5 # Number of traces

    sectors = None

    gust = None
    bars = None
    lines = None
    areas = None
    beaufort = None

    def __missing__(item):
        return None # avoid exception when item is missing

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

        # create the chart
        chart = SimpleLineChart(config.width, config.height)

        colors = []
        legend_set = False
        legend = []

        chart_min = sys.maxint
        chart_max = -sys.maxint

        # Prepare series config
        ordered_series = []
        for key, serie in self.series.iteritems():
            serie_config = ChartConfig()
            serie_config.__dict__.update(config.__dict__)
            serie_config.__dict__.update(serie)
            ordered_series.append( (serie_config.order, key, serie) )

        ordered_series.sort( cmp=lambda x,y: cmp(x[0],y[0]) )

        ordered_keys = []
        for order, key, serie in ordered_series:
            ordered_keys.append(key)

        # Draws for each serie
        index=0
        for order, key, serie in ordered_series:
            serie_config = ChartConfig()
            serie_config.__dict__.update(config.__dict__)
            serie_config.__dict__.update(serie)
            serie_data = data[key.split('.')[0]]['series'][key.split('.')[1]]
                          
            if serie_config.interpolate:
                serie_data = interpolate(serie_data)

            # Compute min and max value for the serie and the whole chart
            min_data = amin(serie_data)
            chart_min = rmin(chart_min, min_data)
            if serie_data.__contains__(min_data):
                min_index = serie_data.index(min_data)
            else:
                min_index = None
            max_data = max(serie_data)
            chart_max = max(chart_max, max_data)
            if serie_data.__contains__(max_data):
                max_index = serie_data.index(max_data)
            else:
                max_index = None

            serie_data = compress_to(serie_data, config.nval, min_index, max_index)

            chart.add_data(serie_data)
            colors.append(_valid_color(serie_config.color))

            if serie_config.max and max_index :
                max_config = ChartConfig()
                max_config.__dict__.update(serie_config.__dict__)
                max_config.__dict__.update(serie_config.max)
                chart.add_marker(index, max_index, 't'+str(max_data), _valid_color(max_config.text), max_config.size)
                chart.add_marker(index, max_index, max_config.style, _valid_color(max_config.color), max_config.thickness)

            if serie_config.min and min_index:
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
                if last_data:
                    chart.add_marker(index, last_index, 't'+str(last_data), _valid_color(last_config.text), last_config.size)
                    chart.add_marker(index, last_index, last_config.style, _valid_color(last_config.color), last_config.thickness)

            if serie_config.area:
                fill_config = ChartConfig()
                fill_config.__dict__.update(serie_config.__dict__)
                fill_config.__dict__.update(serie_config.area)
                to = ordered_keys.index(fill_config.to)
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
                mark_data = copy.copy(data[mark_config.serie.split('.')[0]]['series'][mark_config.serie.split('.')[1]])
                mark_data = compress_to(mark_data, config.nval, min_index, max_index)
                for i, m in enumerate(mark_data):
                    if not m:
                        mark_data[i] = " "
                density = max(1.0, 1.0 * mark_config.space * len("".join(mark_data))*mark_config.size  / config.width)

                for i, v in enumerate(mark_data):
                    if (i +1) % round(density) == 0:
                        if serie_data[i] != 0:
                            text = str(mark_data[i])
                        else:
                            text = " "
                        chart.add_marker(index, i, 't'+text, _valid_color(mark_config.color), mark_config.size)

            index = index + 1

        # Compute vertical range
        chart.y_range=[chart_min-config.y_margin[0], chart_max+config.y_margin[1]]
        if config.axes:
            chart.set_axis_range(Axis.LEFT, chart_min-config.y_margin[0], chart_max+config.y_margin[1])
            chart.set_axis_style(0, _valid_color(config.text), config.size, 0, Axis.BOTH if config.ticks else Axis.AXIS_LINES)
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
            labels_data = data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]]
            labels_data = compress_to(labels_data, config.nval, None, None)
            if config.axes == 'on':
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

        return chart.get_url()+"&chma=10,10,10,10" # add a margin

class GoogleChartWindRadarRenderer(object):
    """
    Renders wind data as a radar google chart URL
    """

    key = 'wind'

    def render(self,data={}, context={}):

        # Prepare config
        config = ChartConfig()
        if context.has_key('chart'):
            config.__dict__.update(context['chart'])
        config.__dict__.update(self.__dict__)

        tail_config = ChartConfig()
        tail_config.__dict__.update(config.__dict__)
        if config.tail:
            tail_config.__dict__.update(config.tail)
        else:
            tail_config.color = "00000000"

        arrow_config = ChartConfig()
        arrow_config.__dict__.update(config.__dict__)
        arrow_config.text = "00000000"
        if config.arrow:
            arrow_config.__dict__.update(config.arrow)
        else:
            arrow_config.color = "00000000"

        gust_config = ChartConfig()
        gust_config.__dict__.update(config.__dict__)
        gust_config.text = "00000000"
        if config.max:
            gust_config.__dict__.update(config.max)
        else:
            gust_config.color = "00000000"

        trace_config = ChartConfig()
        trace_config.__dict__.update(config.__dict__)
        if config.trace:
            trace_config.__dict__.update(config.trace)

        sectors_config = ChartConfig()
        sectors_config.__dict__.update(config.__dict__)
        if config.sectors:
            sectors_config.__dict__.update(config.sectors)

        bars_config = ChartConfig()
        bars_config.__dict__.update(config.__dict__)
        if config.bars:
            bars_config.__dict__.update(config.bars)

        lines_config = ChartConfig()
        lines_config.__dict__.update(config.__dict__)
        if config.lines:
            lines_config.__dict__.update(config.lines)
        else:
            lines_config.color = "00000000"
            lines_config.gust = "00000000"

        areas_config = ChartConfig()
        areas_config.__dict__.update(config.__dict__)
        if config.areas:
            areas_config.__dict__.update(config.areas)

        beaufort_config = ChartConfig()
        beaufort_config.__dict__.update(config.__dict__)
        if config.beaufort:
            beaufort_config.__dict__.update(config.beaufort)

        # Prepare data

        max = config.median * 2
        
        if data[self.key].has_key('value'):
            current_noscale = data[self.key]['value']
            last_gust_noscale = data[self.key]['max']
            pos = int(round(data[self.key]['deg'] * 16 / 360.0))        
            current = self.scale(current_noscale, config.median, config.radius)
            last_gust_scaled = self.scale(last_gust_noscale, config.median, config.radius)
            arrow_thickness = 0.3+3.0*arrow_config.thickness*current/max            

        if config.bars or config.areas or config.sectors:
            avg = []
            for val in data[self.key]['sectors']['avg']:
                avg.append(self.scale(val, config.median, config.radius))
            avg.append(avg[0])
            gust = []
            for val in data[self.key]['sectors']['max']:
                gust.append(self.scale(val, config.median, config.radius))
            gust.append(gust[0])
        else:
            avg = [0] * 16
            gust = [0] * 16

        line = [0] * 16
        crown = [max] * 16
        tail = [0] * 16
        last_gust = [0] * 16
        head = [0] * 16

        if data[self.key].has_key('value'):
            line[pos] = max if current > 0 else 0
            tail[pos] = current
            last_gust[pos] = last_gust_scaled
            head[ (pos - 1 + 16) % 16 ] = current*0.6
            head[ (pos + 16) % 16 ] = current*0.3
            head[ (pos + 1) % 16 ] = current*0.6

        chart = RadarChart(config.width, config.height, y_range=(0,max) )
        chart.add_data([0] * 2)
        chart.add_data(line)
        chart.add_data(gust)
        chart.add_data(avg)
        chart.add_data(crown)
        chart.add_data(tail)
        chart.add_data(head)
        chart.add_data(last_gust)

        if config.bars:
            chart.add_marker(2, -1, "v", _valid_color(bars_config.gust), bars_config.thickness, -1)
            chart.add_marker(3, -1, "v", _valid_color(bars_config.color), bars_config.thickness, -1)

        if config.beaufort:
            chart.add_marker(0, "220:0.9", "@t"+str(beaufort(current_noscale)), _valid_color(beaufort_config.color) + "%02x" % (beaufort_config.intensity*255), rmin(config.height, config.width)-config.size*5, -1)

        colors = ["00000000",
            _valid_color(tail_config.color),
            _valid_color(lines_config.gust),
            _valid_color(lines_config.color),
            "00000000",
            _valid_color(arrow_config.color),
            _valid_color(arrow_config.color),
            "00000000"]

        if config.sectors:
            for i in range(0,16):
                sec = [0] * 16
                avg = self.scale(data[self.key]['sectors']['avg'][i], config.median, config.radius)
                freq_value = data[self.key]['sectors']['freq'][i]*255
                freq_value = rmin(255, (1+2*sectors_config.intensity) * freq_value)
                freq = "%02x" % int(freq_value)
                start = i-0.5
                stop = i+0.5
                chart.add_vertical_range(_valid_color(sectors_config.color)+freq, start, stop)

        if config.trace:
            nval = len(data[self.key]['series']['deg'])
            nbullet = rmin(trace_config.length, nval)
            minsize = trace_config.size / float(trace_config.ratio)
            maxsize = trace_config.size
            size = float(maxsize)
            inc = (maxsize-minsize) / nbullet
            n = 0
            for p in reversed(data[self.key]['series']['deg']):
                chart.add_marker(4, int(p/22.5), 'o', _valid_color(trace_config.color), size)
                size = size - inc
                n = n + 1
                if n == nbullet:
                    break

        if config.areas:
            chart.add_fill_range(_valid_color(areas_config.gust), 3, 2)
            chart.add_fill_range(_valid_color(areas_config.color), 3, 0)

        if config.max:
            chart.add_marker(7, pos, 'o', _valid_color(gust_config.color), gust_config.thickness)
            chart.add_marker(7, pos, 't'+str(round(last_gust_noscale,1)), _valid_color(gust_config.text), gust_config.size)

        if config.arrow:
            chart.add_marker(0, 0, 'o', _valid_color(arrow_config.color), arrow_thickness)
            chart.add_marker(5, pos, 't'+str(round(current_noscale,1)), _valid_color(arrow_config.text), arrow_config.size)
            chart.add_fill_range(_valid_color(arrow_config.fill), 6, 0)

        chart.set_colours( colors )
        
        if config.axes:
            chart.set_axis_labels(Axis.BOTTOM, ['N', '', 'NE', '', 'E', '', 'SE', '', 'S', '', 'SW', '', 'W', '', 'NW', ''])
            chart.set_axis_style(0, _valid_color(config.text), config.size, 0, 'l', _valid_color(config.bgcolor));
        if data[self.key].has_key('value'):
            chart.set_line_style(1, tail_config.thickness)
        else:
            chart.set_line_style(1, 0)
        chart.set_line_style(2, lines_config.thickness)
        chart.set_line_style(3, lines_config.thickness)
        chart.set_line_style(4, 0)
        if data[self.key].has_key('value'):
            chart.set_line_style(5, arrow_thickness)
            chart.set_line_style(6, arrow_thickness)
        else:
            chart.set_line_style(5, 0)
            chart.set_line_style(6, 0)
            

        chart.fill_solid(Chart.BACKGROUND, _valid_color(config.bgcolor))

        return chart.get_url()

    def scale(self, value, mean, max):
        if mean == max / 2:
            return value
        else:
            return (mean/log((max/mean-2)+1))*log(((max/mean-2)/mean)*value+1)

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
    if color == None or color == "None":
        return "00000000"
    if re.match("[A-F0-9]+", color):
        return color
    else:
        return webcolors.name_to_hex(color)[1:]

def interpolate(data):
    result = copy.copy(data)
    (last, index, count) = (None, None, 0)
    for i,val in enumerate(data):
        if not val:
            if last:                         # ignore leading None(s)
                if not index:                # if first None
                    index = i
                count = count + 1
        else:
            if index:                        # there has been None(s) before
                for j in range(index, i):
                    result[j] = last + (j - index + 1)*(val - last)/float(count+1)
                (index, count) = (None, 0)
            last = val
    return result

def compress_to(data, n, min_index, max_index):
    while len(data) > n:
        l = len(data)
        d = l-n        # how many values to remove
        r = l / d      # each r-th must be removed
        #print "compress "+str(l)+" to "+str(n)+" by "+str(r)
        if r < 2:
            r = 2
        data = compress(data, r, min_index, max_index)
        #print "compressed to "+str(len(data))
        
    # Also set a value to 0 if all data is None
    v = None
    for i in data:
        if i:
            v = i
    if not v:
        data[0]=0

    return data

def compress(data, ratio, min_index, max_index):
    result = []
    r = ratio
    ext=None
    last=None
    for i, v in enumerate(data):
        if i == max_index or i == min_index:
            ext=v
        if v:
            last=v
        if not i % r == 0:
            if ext:
                result.append(ext)
                ext=None
            else:
                result.append(v if v else last)
            last=None
    return result


def beaufort(mps):
    if mps < 0.3:
        return 0
    if mps < 1.5:
        return 1
    if mps < 3.4:
        return 2
    if mps < 5.4:
        return 3
    if mps < 7.9:
        return 4
    if mps < 10.7:
        return 5
    if mps < 13.8:
        return 6
    if mps < 17.1:
        return 7
    if mps < 20.7:
        return 8
    if mps < 24.4:
        return 9
    if mps < 28.4:
        return 10
    if mps < 32.6:
        return 11
    return 12

