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

if __name__=="__main__":
    import os.path
    import sys
    sys.path.append(os.path.abspath(sys.path[0] + '/../..'))


from pygooglechart import Chart
from pygooglechart import _check_colour
from pygooglechart import Axis
from pygooglechart import RadarChart
from pygooglechart import SimpleLineChart
from math import log
import math
import wfcommon.units
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
        if not i == None and i < m:
            m=i
    return m

# Default configuration
class ChartConfig(object):
    # Graph attributes
    width = 250
    height = 150
    bgcolor = '00000000'
    ymargin = [ 1, 1 ]
    axes = True
    ticks = True
    legend = None
    legend_pos = 'b'
    nval = 100

    # Drawing
    color = '008000'
    thickness = 1.5
    text = '8d7641'
    size = 10 # for text and markers
    fill = None # fill color of the arrow
    style = 'v' # for markers
    dash = None
    interpolate = False # line series interpolation of missing values.

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
    radius = 18 # max value for logarithmic scaling
    median = 2.5  # value in the middle of the graph

    intensity = 0.5 # ratio of intensity for wind radar charts
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
    Renders the data as a google chart.

    render result [string]:
        The google chart URL.

    [ Properties ]

    series [dict]:
        Defines which series data are rendered on the chart and
        their options. Keys follow the format 'measure.serie', e.g.
        'temp.avg'. Value contains a dictionary of rendering options. See
        below the available options and their scope.

    axes [true|false] (optional):
        Display or not the axes. Defaults to 'true'.

    height [numeric] (optional):
        Height in pixels of the generated graph image. Defaults to 125.

    labels [string] (optional):
        Defines which data must be used to render the chart labels on
        the X axis. The value has the format 'measure.lbl', e.g.
        'temp.label' to specify which data to use.

    nval [numeric] (optional):
        Maximum resolution of the graph, in order to avoid too much
        values in the Google Chart URL. Defaults to 100.

    ticks [true|false] (optional):
        Display or not the tick alon the axes. Defaults to 'true'.

    width [numeric] (optional):
        Width in pixels of the generated graph image. Defaults to 250.

    ymargin [pair of numeric] (optional):
        Space to keep above and below the graph extreme values, in
        graph units. Defaults to [1, 1].

    zero [dict] (optional):
        Draw an horizontal line at y=0. Makes sense when graph values
        can be negative. Contains rendering options. For default
        rendering (a thin gray line), specify an empty dictionary '{}'.


    [ Markers ]

    In the scope of a data serie, one can specify markers highlighting
    some data points:

    min [dict] (optional):
        The minimum value of the serie.

    max [dict] (optional):
        The maximum value of the serie.

    last [dict] (optional):
        The last value of the serie.


    [ Rendering Options ]

    Some options are of type 'color'. They can take either
        - an hexadecimal triplet string, e.g A3F500 (without dash and
          in upper case.
        - or a named color defined in the CSS specification, e.g 'blue',
          'red', 'wheat', ...

    Rendering options are always optional and can be used in
    different scope:
        - (G) the whole graph
        - (S) a given data serie
        - (M) a marker

    bgcolor (G) [color]:
        Background color of the graph.

    color (G, S, M) [color]:
        Foreground color of the line or bar.

    dash (G, S) [pair of numeric]:
        If present, write a dashed line for the serie. The first value
        represents the length of dash elements, the second the space
        between them.

    interpolate (G, S) [true|false]:
        If 'true', draw a continuous line instead of blank for missing
        values. This is useful when the chart resolution is finer than
        the sampling period.

    order (S) [numeric]:
        Defines in which orders series are drawn on the graph.

    size (G, S, M) [numeric]:
        Text size. Defaults to 10.

    text (G, S, M) [color]:
        Foreground color of the text.

    thickness (G, S, M) [numeric]:
        Pixel thickness of the line.
    """

    series = None
    labels = None

    logger = logging.getLogger("renderer.chart")

    def render(self,data={}, context={}):

        assert self.series is not None, "'chart.series' must be set"

        converter = wfcommon.units.Converter(context["units"])

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
            measure = key.split('.')[0]

            if flat(serie_data):
                continue

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

            (serie_data, min_index, max_index) = compress_to(serie_data, config.nval, min_index, max_index)

            chart.add_data(serie_data)
            colors.append(_valid_color(serie_config.color))

            if serie_config.max and not max_index == None :
                max_config = ChartConfig()
                max_config.__dict__.update(serie_config.__dict__)
                max_config.__dict__.update(serie_config.max)
                str_max_data = str(round(converter.convert(measure, max_data), 1))
                chart.add_marker(index, max_index, 't'+str_max_data, _valid_color(max_config.text), max_config.size)
                chart.add_marker(index, max_index, max_config.style, _valid_color(max_config.color), max_config.thickness)

            if serie_config.min and not min_index == None:
                min_config = ChartConfig()
                min_config.__dict__.update(serie_config.__dict__)
                min_config.__dict__.update(serie_config.min)
                str_min_data = str(round(converter.convert(measure, min_data), 1))
                chart.add_marker(index, min_index, 't'+str_min_data, _valid_color(min_config.text), min_config.size)
                chart.add_marker(index, min_index, min_config.style, _valid_color(min_config.color), min_config.thickness)

            if serie_config.last:
                last_config = ChartConfig()
                last_config.__dict__.update(serie_config.__dict__)
                last_config.__dict__.update(serie_config.last)
                last_index=len(serie_data)-1
                last_data = serie_data[last_index]
                if last_data:
                    str_last_data = str(round(converter.convert(measure, last_data), 1))
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
                mark_data = compress_to(mark_data, config.nval, min_index, max_index)[0]
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

        if config.axes:
            range_min_ref_units = 0
            if not chart_min == sys.maxint and not chart_max == -sys.maxint:
                range_min = chart_min-config.ymargin[0]
                range_max = chart_max+config.ymargin[1]
                range_min_target_units = math.floor(converter.convert(measure, range_min))
                range_max_target_units = math.ceil(converter.convert(measure, range_max))
                range_min_ref_units = converter.convert_back(measure, range_min_target_units)
                range_max_ref_units = converter.convert_back(measure, range_max_target_units)
                self.logger.debug("Y range: "+str(range_min_target_units) +" "+str(range_max_target_units))
                chart.set_axis_range(Axis.LEFT, range_min_target_units, range_max_target_units+1)
                chart.add_data([range_min_ref_units, range_max_ref_units])
                colors.append("00000000")
            else:
                chart.set_axis_range(Axis.LEFT, 0, 100)
            chart.set_axis_style(0, _valid_color(config.text), config.size, 0, Axis.BOTH if config.ticks else Axis.AXIS_LINES)
        else:
            chart.set_axis_labels(Axis.LEFT, [])
            chart.set_axis_style(0, _valid_color(config.text), config.size, 0, Axis.TICK_MARKS, _valid_color(config.bgcolor))

        if config.zero and config.axes and range_min_ref_units < 0:
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
            labels_data = compress_to(labels_data, config.nval, None, None)[0]
            if config.axes:
                density = 1.0 * len("".join(labels_data))*config.size  / config.width

                if density > LABEL_DENSITY_THRESHOLD:
                    for i, v in enumerate(labels_data):
                        if i % round(density) != 0:
                            labels_data[i] = ' '
                chart.set_axis_labels(Axis.BOTTOM, labels_data)
                chart.set_axis_style(1, _valid_color(config.text), config.size, 0, Axis.BOTH if config.ticks else Axis.AXIS_LINES)
            else:
                chart.set_axis_labels(Axis.BOTTOM, [])
                chart.set_axis_style(1, _valid_color(config.text), config.size, 0, Axis.TICK_MARKS, _valid_color(config.bgcolor))

        try:
            return chart.get_url()+"&chma=10,10,10,10" # add a margin
        except:
            self.logger.exception("Could not render chart")
            return "http://chart.apis.google.com/chart?cht=lc&chs="+str(config.width)+"x"+str(config.height)

class GoogleChartWindRadarRenderer(object):
    """
    Renders wind data as a radar google chart URL.

    render result [string]:
        The google chart URL.

    [ Properties ]

    height [numeric] (optional):
        Height in pixels of the generated graph image. Defaults to 125.

    width [numeric] (optional):
        Width in pixels of the generated graph image. Defaults to 250.


    [ Rendering Options ]

    Roughly, the same rendering options as !chart are available.
    Additionally, the following options are specific to this renderer:

    sectors [dict] (optional):
        If present, shows pie sectors shaded according to the frequency
        of wind in each direction. The dict contain the rendering options
        for the sector painting, i.e. 'color' and 'intensity'.
        Default to None.

    radius [numeric] (optional):
        Asymptotic limit value corresponding to maximum wind. This value
        is used to compute the logarithmic scale.

    median [numeric] (optional):
        Value of wind speed that will be represented as a being in the
        middle of the radar chart range. Together with 'radius', this
        value defines the logarithmic scale for the wind speed.

    arrow [dict] (optional):
        If present, draws the wind direction arrow. The dict can contain
        options 'color', 'thickness' and 'text'. The 'text' options, is
        set to a color, shows the current wind value on the graph.

    tail [dict] (optional):
        Rendering options for the arrow tail. The dict can contain
        options 'color' and 'thickness'.

    trace [dict] (optional):
        If present, draws crown bullets showing the last direction of
        the wind. The dict can contain options 'color', 'size', 'length'
        and 'ratio'. The length corresponds to the number of trace bullets
        to draw. The ratio is proportional to the way bullet size fades out.

    bars [dict] (optional):
        Show bars for the wind values. The dict can contain 'color',
        'gust' and 'thickness'.
        The value 'color' is for average wind values and 'gust' is
        the color for maximum wind values.

    lines [dict] (optional):
        Show lines for the wind values. The dict can contain 'color',
        'gust' and 'thickness'.
        The value 'color' is for average wind values and 'gust' is
        the color for maximum wind values.

    areas [dict] (optional):
        Show shaded area for the wind values. The dict can contain 'color',
        'gust'.
        The value 'color' is for average wind values and 'gust' is
        the color for maximum wind values.

    beaufort [dict] (optional):
        Show a the beaufort value in the radar chart as a large digit.
        Options are 'color' and 'intensity'.

    max [dict] (optional):
        Show a marker for the maximum wind value on the chart. Options
        are 'color', 'thickness', 'text' and 'size'.
    """

    key = 'wind'
    sector_key = 'sectors' # 'new' sector calculation from accumulator

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

        if data[self.key].has_key('sectors'):
            sector_data = data[self.key]['sectors'] # 'old' sector from db datasource
        else:
            if data.has_key(self.sector_key): # 'new' sector data from accumulator
                sector_data = self.calculate_accumulated_sector_data(data[self.sector_key]['series'])
            else:
                sector_data = self.calculate_cheap_sector_data(data[self.key]['series'])

        if data[self.key].has_key('value'):
            current_noscale = data[self.key]['value']
            last_gust_noscale = data[self.key]['max']
            pos = int(round(data[self.key]['deg'] * 16 / 360.0))
            if pos == 16: pos = 0
            current = self.scale(current_noscale, config.median, config.radius)
            last_gust_scaled = self.scale(last_gust_noscale, config.median, config.radius)
            arrow_thickness = 0.3+3.0*arrow_config.thickness*current/max

        if config.bars or config.areas or config.sectors:
            avg = []
            for val in sector_data['avg']:
                avg.append(self.scale(val, config.median, config.radius))
            avg.append(avg[0])
            gust = []
            for val in sector_data['max']:
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
            chart.add_marker(0, "220:0.9", "@t"+str(int(round(wfcommon.units.MpsToBft(current_noscale)))), _valid_color(beaufort_config.color) + "%02x" % (beaufort_config.intensity*255), rmin(config.height, config.width)-config.size*5, -1)

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
                avg = self.scale(sector_data['avg'][i], config.median, config.radius)
                freq_value = sector_data['freq'][i]*255
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

    def calculate_cheap_sector_data(self, serie_data):
        sector_data = {}
        sector_data['lbl'] = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        sector_data['avg'] = 16 * [ 0.0 ]
        sector_data['freq'] = 16 * [ 0.0 ]
        sector_data['max'] = 16 * [ 0.0 ]

        total_count=0
        for i in range(len(serie_data['avg'])):
            avg = serie_data['avg'][i]
            max = serie_data['max'][i]
            dir = serie_data['dir'][i]
            if avg > 0 and dir is not None:
                index = sector_data['lbl'].index(dir)
                sector_data['freq'][index] = sector_data['freq'][index] + 1
                total_count = total_count + 1
                sector_data['avg'][index] = sector_data['avg'][index] + avg
                if max > sector_data['max'][index]:
                    sector_data['max'][index] = max

        # divide sums to calculate averages
        for i in range(len(sector_data['avg'])):
            if sector_data['freq'][i] > 0:
                sector_data['avg'][i] = sector_data['avg'][i] / sector_data['freq'][i]

        # normalize frequencies
        if total_count > 0:
            for i in range(len(sector_data['freq'])):
                   sector_data['freq'][i] = sector_data['freq'][i] / total_count

        return sector_data

    def calculate_accumulated_sector_data(self, serie_data):
        sector_data = {}
        sector_data['lbl'] = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        d_avg = sector_data['avg'] = 16 * [ 0.0 ]
        d_freq = sector_data['freq'] = 16 * [ 0.0 ]
        d_max = sector_data['max'] = 16 * [ 0.0 ]
        avg_counts = 16 * [0.0]        
        
        count = len(serie_data['avg'])
    
        s_avg=serie_data['avg']
        s_max=serie_data['max']
        s_freq=serie_data['freq']
        
        for i in range(count):
            for j in range(16):                  
                if s_avg[i][j] > 0:
                    d_avg[j] = d_avg[j]+s_avg[i][j]
                    avg_counts[j] = avg_counts[j] + 1
                if s_max[i][j] > d_max[j]:
                    d_max[j] = s_max[i][j] 
                d_freq[j] = d_freq[j] + s_freq[i][j] 

        for i in range(16):
            if avg_counts[i] > 0:
                d_avg[i] = float(d_avg[i]) / avg_counts[i]
            
        sum_freq = sum(d_freq)
        
        if sum_freq > 0:
            for i in range(16):
                d_freq[i] = d_freq[i] / sum_freq
            
        return sector_data
                

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

def flat(data):
    if len(data)==0:
        return true
    for d in data:
        if d and not d==0:
            return False
    return True

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
    new_min_index = min_index
    new_max_index = max_index
    while len(data) > n:
        l = len(data)
        d = l-n        # how many values to remove
        r = l / d      # each r-th must be removed
        #print "compress "+str(l)+" to "+str(n)+" by "+str(r)
        if r < 2:
            r = 2
        (data, new_min_index, new_max_index) = compress(data, r, min_index, max_index)
        #print "compressed to "+str(len(data))

    return (data, new_min_index, new_max_index)

def compress(data, ratio, min_index, max_index):
    result = []
    r = ratio
    last=None
    new_min_index=0
    new_max_index=0
    min = None
    max = None
    for i, v in enumerate(data):
        if i == max_index:
            max=v
        if i == min_index:
            min=v
        if v:
            last=v
        if not i % r == 0:
            if not min == None:
                new_min_index = len(result)
                result.append(min)
                min = None
            elif not max == None:
                new_max_index = len(result)
                result.append(max)
                max = None
            else:
                result.append(v if v else last)
            last=None
    return (result, new_min_index, new_max_index)


if __name__=="__main__":

    serie_data = {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "avg" : [ 4, 3.8, None, 1, 1.2, .3, 0.2, 0, 1 , 1],
                    "max" : [ 5, 6, None, 1.3, 1.3, .4, 0.2, 0, 1.2 , 1],
                    "deg" : [ 318, None, 300, 310, 300, 300, 300, 345, 12, 60 ],
                    "dir": [ 'NNW', None, 'NW', 'NW', 'NW', 'NW', 'N', 'NNE', 'NE', 'NE']
                    }

    r = GoogleChartWindRadarRenderer()
    print r.calculate_cheap_sector_data(serie_data)
