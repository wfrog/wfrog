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


from pyquickchart import Chart
#from pyquickchart import _check_colour
#from pyquickchart import Axis
from pyquickchart import RadarChart
from pyquickchart import PolarChart
from pyquickchart import SimpleLineChart
from pyquickchart import SimpleBarChart
from pyquickchart import HorizontalBarChart
from pyquickchart import StackedVerticalBarChart
from pyquickchart import StackedHorizontalBarChart
from pyquickchart import SimplePieChart
from pyquickchart import SimpleDoughnutChart
from pyquickchart import QRChart
from math import log
import math
import wfcommon.units
import webcolors
import re
import copy
import logging
import sys

# Limit of the text density on x-axis to start removing label
#LABEL_DENSITY_THRESHOLD = 1.78

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

def _valid_color(color):
    if color == None or color == "None":
        return "000000"
    if not re.search("[^a-fA-F0-9]+", color):
        return color
    else:
        return webcolors.name_to_hex(color)[1:]

def _valid_rgba_color(color, intensity):
    if color == None or color == "None":
        return "00000000"
    if intensity < 0 or intensity > 1:
        intensity = 1
    intensity = "%02x" % int(intensity*255)    
    if not re.search("[^a-fA-F0-9]+", color):
        return color+intensity
    else:
        return webcolors.name_to_hex(color)[1:]+intensity
        
def hex_rgb(color):
    if color == None or color == "None":
        return "#000000"
    return "#"+_valid_color(color)
    
def hex_rgba(color,intensity):
    if color == None or color == "None" or color == "00000000":
        return "#00000000"
    return "#"+_valid_rgba_color(color,intensity)


# Default configuration
class ChartConfig(object):
    # Graph attributes
    width = 250 #333
    height = 150 #200
    bgcolor = '00000000'
    ymargin = [ 1, 1 ]
    axes = True
    ticks = True
    legend = None
    legend_pos = 'b'
    nval = 100

    # Drawing
    color = '008000'
    thickness = 2
    text = '8d7641'
    size = 10 # for text and markers
    fill = None # fill color of the arrow
    style = 'v' # for markers
    dash = None
    accumulate = False  # draw accumulated values
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

def dumpChartConfig(o):
    t = []
    # Graph attributes
    t.append(o.width)       # = 250
    t.append(o.height)      # = 150
    t.append(o.bgcolor)     # = '00000000'
    t.append(o.ymargin)     # = [ 1, 1 ]
    t.append(o.axes)        # = True
    t.append(o.ticks)       # = True
    t.append(o.legend)      # = None
    t.append(o.legend_pos)  # = 'b'
    t.append(o.nval)        # = 100

    # Drawing
    t.append(o.color)       # = '008000'
    t.append(o.thickness)   # = 1.5
    t.append(o.text)        # = '8d7641'
    t.append(o.size)        # = 10 # for text and markers
    t.append(o.fill)        # = None # fill color of the arrow
    t.append(o.style)       # = 'v' # for markers
    t.append(o.dash)        # = None
    t.append(o.accumulate)  # = False  # draw accumulated values
    t.append(o.interpolate) # = False # line series interpolation of missing values.

    # Series
    t.append(o.area)        # = None
    t.append(o.zero)        # = None
    t.append(o.max)         # = None
    t.append(o.min)         # = None
    t.append(o.last)        # = None
    t.append(o.marks)       # = None
    t.append(o.space)       # = 1.5 # Spacing between marks

    # Drawing order
    t.append(o.order)       # = 0

    # Wind Radar
    t.append(o.radius)      # = 18 # max value for logarithmic scaling
    t.append(o.median)      # = 2.5  # value in the middle of the graph

    t.append(o.intensity)   # = 0.5 # ratio of intensity for wind radar charts
    t.append(o.tail)        # = None
    t.append(o.arrow)       # = { }
    t.append(o.trace)       # = None
    t.append(o.ratio)       # = 3  # Size i
    t.append(o.length)      # = 5 # Number of traces

    t.append(o.sectors)     # = None

    t.append(o.gust)        # = None
    t.append(o.bars)        # = None
    t.append(o.lines)       # = None
    t.append(o.areas)       # = None
    t.append(o.beaufort)    # = None
    return tuple(t)

class TestChartRenderer(object):

    logger = logging.getLogger("renderer.test")

    def render(self,data={}, context={}):
        assert self.series is not None, "'chart.series' must be set"
        #self.logger.info("Hello World!")
        #self.logger.info("data:          "+str(data))
        #self.logger.info("series:        "+str(self.series))
        #self.logger.info("context:       "+str(context))
        
        chart = self.qrchart(data,context)
        try:
            import uuid
#            url = chart.get_url()
#            self.logger.info('URL: %s', url)
            filename = uuid.uuid1().hex+'.png'
            url = '/'+str(self.static)+'/'+filename
            #self.logger.info('URL:      %s', url)
            filepath = str(self.docroot)+'/'+filename
            #self.logger.info('filepath: %s', filepath)
            chart.download(filepath)
            return url
        except Exception as e:
            self.logger.exception("Could not render chart: %s",e)
            return 'img_cache/fixed/status_503-t.png'
            
        #chart = self.float_bar(data,context)
        #chart = self.horiz_bar(data,context)
        #chart = self.mixed_bar(data,context)
        #chart = self.pie(data,context)
        
        try:
            url = chart.get_json(self.docroot)
            if url != '500':
                url='/'+str(self.static)+'/'+url
                self.logger.debug('PNG URL: '+url)
                return url
        except:
            self.logger.exception("Could not render chart")
            return "Could not render chart"

    def qrchart(self,data={}, context={}):    

        config = ChartConfig()
        if context.has_key('test'):
            config.__dict__.update(context['test'])
        config.__dict__.update(self.__dict__)
        self.logger.debug("self.__dict__: "+str(self.__dict__))
        
        chart = QRChart(config.width,config.height)
        chart.set_ec('H')
        chart.set_margin(4)
        chart.set_colours('ff0','8D7641')
        chart.set_encoding('png')
        chart.add_data("Oh freddled gruntbuggly,\n\
Thy micturations are to me\n\
As plurdled gabbleblotchits on a lurgid bee.\n\
Groop, I implore thee, my foonting turlingdromes,\n\
And hooptiously drangle me with crinkly bindlewurdles,\n\
Or I will rend thee in the gobberwarts\n\
With my blurglecruncheon, see if I don't!")
        return chart
        

    def pie(self,data={}, context={}):
        
        config = ChartConfig()
        if context.has_key('test'):
            config.__dict__.update(context['test'])
        config.__dict__.update(self.__dict__)
        self.logger.debug("self.__dict__: "+str(self.__dict__))
        
        chart = SimpleDoughnutChart(config.width, config.height, 2)
        chart.set_rotation(-11.25) # rotate 11.25 degrees anticlockwise from N
        #chart.set_circumference(90) # 90 degrees
        
        chart.set_title(False)
        chart.set_title_text(['Hello','World!'])
        #chart.set_title_text('Hello World!')
        chart.set_title_position('top')
        chart.set_title_style(fontSize=20, fontFamily='Times New Roman', fontColor='red', fontStyle='italic')
        
        chart.set_legend(False)
        chart.set_legend_style(fontSize=8, fontFamily='Times New Roman',fontColor='red',fontStyle='bold italic')
        
        chart.set_datalabels(True)
        chart.set_datalabels_style(fontSize=8, fontFamily='Arial', fontColor='#666', fontStyle='bold')
        chart.set_datalabels_border(borderRadius=20, borderWidth=1, borderColor='black', backgroundColor='black')
        chart.set_datalabels_align('center')

        chart.set_cutoutPercentage(25)
        
        serie_data = copy.copy(data['temp']['series']['avg'])
        self.logger.debug("Data: %s", str(serie_data))
        self.logger.debug("dataset index: %s", chart.add_dataset(0,serie_data))

        serie_data = [2,6,4,8,9,3]
        self.logger.debug("Data: %s", str(serie_data))
        self.logger.debug("dataset index: %s", chart.add_dataset(1,serie_data))

        chart.set_dataset_backgroundcolour(1,['red','green','blue','magenta','yellow','cyan'])
        chart.set_dataset_borderwidth(1,1)
        chart.set_dataset_bordercolour(1,'black')
        #chart.set_dataset_weight(1,[1,1,1,1,4,1])

        if self.labels:
            self.logger.debug("labels: %s",str(self.labels))
            labels_data = copy.copy(data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]])
            chart.set_legend_data(labels_data)
            
        self.logger.debug('Chart JSON: '+chart.dump_chart())

        return chart
         
    def mixed_bar(self,data={}, context={}):
        
        config = ChartConfig()
        if context.has_key('test'):
            config.__dict__.update(context['test'])
        config.__dict__.update(self.__dict__)
        self.logger.debug("self.__dict__: "+str(self.__dict__))
         
        chart = StackedVerticalBarChart(config.width, config.height, 2)

        x_axis_id = 'x-axis-0'
        y_axis_id = 'y-axis-0'
        x_axis = (chart.get_axis(x_axis_id))
        y_axis = (chart.get_axis(y_axis_id))
        chart.set_axis_style(x_axis_id,9)
        chart.set_axis_style(y_axis_id,9)
        chart.set_axis_gridlines(x_axis_id,False)
        chart.set_axis_gridlines(y_axis_id,True)
        #chart.set_axis_gridline_width(y_axis_id,2)
        self.logger.debug("Add Y-Axis: %s", str(chart.add_axis('right')))
        self.logger.debug("Y-Axis: %s", str(chart.get_axis('y-axis-1')))
        chart.set_axis_gridlines('y-axis-1',False)
        
        #chart.set_chartbackground(hex_rgba('red',0.01))
        chart.set_title(False)
        #chart.set_title_text(['Hello','World!'])
        chart.set_title_text('Hello World!')
        chart.set_title_position('top')
        chart.set_title_style(20,'Times New Roman','red','italic')
        #chart.set_legend(True)
        #chart.set_legend_position('left')
        #chart.set_legend_style(8,'Times New Roman','red','italic')

        #chart.set_stacked(True)
        serie_data = copy.copy(data['temp']['series']['avg'])
        self.logger.debug("Data: %s", str(serie_data))
        self.logger.debug("dataset index: %s", chart.add_dataset(0,serie_data))

        serie_data = copy.copy(data['wind']['series']['avg'])
        self.logger.debug("Data: %s", str(serie_data))
        self.logger.debug("dataset index: %s", chart.add_dataset(1,serie_data))

        serie_data = copy.copy(data['press']['series']['avg'])
        self.logger.debug("Data: %s", str(serie_data))
        press_idx = chart.add_dataset(2,serie_data,'y-axis-1','line')
        self.logger.debug("dataset index: %s", press_idx)
        chart.set_dataset_fillstyle(press_idx,False)
        chart.set_dataset_linestyle(press_idx,[4,2])
        chart.set_dataset_linecolour(press_idx,'black')
        chart.set_dataset_pointsize(press_idx,0)

        if self.labels:
            self.logger.debug("labels: %s",str(self.labels))
            labels_data = copy.copy(data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]])
            chart.set_axis_labels(x_axis_id, labels_data)
        
        self.logger.debug('Chart JSON: '+chart.dump_chart())
        
        return chart        

    def horiz_bar(self,data={}, context={}):
        
        config = ChartConfig()
        if context.has_key('test'):
            config.__dict__.update(context['test'])
        config.__dict__.update(self.__dict__)
        self.logger.debug("self.__dict__: "+str(self.__dict__))
         
        chart = StackedHorizontalBarChart(config.width, config.height, 2)

        x_axis_id = 'x-axis-0'
        y_axis_id = 'y-axis-0'
        x_axis = (chart.get_axis(x_axis_id))
        y_axis = (chart.get_axis(y_axis_id))
        chart.set_axis_style(x_axis_id,9)
        chart.set_axis_style(y_axis_id,9)
        chart.set_axis_gridlines(x_axis_id,True)
        chart.set_axis_gridlines(y_axis_id,True)
        #chart.set_axis_gridline_width(y_axis_id,2)
        
        #chart.set_chartbackground(hex_rgba('red',0.01))
        chart.set_title(False)
        #chart.set_title_text(['Hello','World!'])
        chart.set_title_text('Hello World!')
        chart.set_title_position('top')
        chart.set_title_style(20,'Times New Roman','red','italic')
        #chart.set_legend(True)
        #chart.set_legend_position('left')
        #chart.set_legend_style(8,'Times New Roman','red','italic')

        #chart.set_stacked(True)
        serie_data = copy.copy(data['temp']['series']['avg'])
        self.logger.debug("Data: %s", str(serie_data))
        temp_idx = chart.add_dataset(0,serie_data,'y-axis-0')
        self.logger.debug("dataset index: %s", temp_idx)
        chart.set_dataset_fillcolour(temp_idx,hex_rgba("red",0.2))
        
        serie_data = copy.copy(data['wind']['series']['avg'])
        self.logger.debug("Data: %s", str(serie_data))
        wind_idx = chart.add_dataset(1,serie_data,'y-axis-0')
        self.logger.debug("dataset index: %s", wind_idx)
        chart.set_dataset_fillcolour(wind_idx,hex_rgba("green",0.2))

        if self.labels:
            self.logger.debug("labels: %s",str(self.labels))
            labels_data = copy.copy(data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]])
            chart.set_axis_labels(y_axis_id, labels_data)
        
        self.logger.debug('Chart JSON: '+chart.dump_chart())
        
        return chart        

    def float_bar(self,data={}, context={}):
        
        config = ChartConfig()
        if context.has_key('test'):
            config.__dict__.update(context['test'])

        config.__dict__.update(self.__dict__)
        self.logger.debug("config.__dict__: "+str(config.__dict__))
        self.logger.debug("interpolate:  "+str(config.interpolate))
         
        chart = SimpleBarChart(config.width, config.height)

        x_axis_id = 'x-axis-0'
        y_axis_id = 'y-axis-0'
        #x_axis = (chart.get_axis(x_axis_id))
        #y_axis = (chart.get_axis(y_axis_id))
        #chart.set_axis_gridlines(x_axis_id,False)
        #chart.set_axis_gridlines(y_axis_id,False)
#        chart.add_marker('horizontal', \
#                         '', \
#                         0, \
#                         'centre', \
#                         0, \
#                         0, \
#                         0, \
#                         '#aaa', \
#                         3)
#        chart.add_marker('vertical', \
#                         '', \
#                         0, \
#                         'centre', \
#                         0, \
#                         0, \
#                         0, \
#                         '#aaa', \
#                         3)
        #chart.set_axis_style(x_axis_id,9)
        #chart.set_axis_style(y_axis_id,9)
        chart.set_axis_zeroline_width(x_axis_id,1)
        chart.set_axis_zeroline_width(y_axis_id,1)
        chart.set_axis_gridline_width(x_axis_id,0)
        chart.set_axis_gridline_width(y_axis_id,0)
        
        #chart.set_chartbackground(hex_rgba('red',0.01))
        #chart.set_title(False)
        #chart.set_title_text(['Hello','World!'])
        #chart.set_title_text('Hello World!')
        #chart.set_title_position('top')
        #chart.set_title_style(20,'Times New Roman','red','italic')
        #chart.set_legend(True)
        #chart.set_legend_position('left')
        #chart.set_legend_style(8,'Times New Roman','red','italic')

        #chart.set_stacked(True)
        serie_data = []
        min_data = copy.copy(data['temp']['series']['min'])
        max_data = copy.copy(data['temp']['series']['max'])
        avg_data = copy.copy(data['temp']['series']['avg'])
        for datum in range(0,len(min_data)):
            #serie_data.append([min_data[datum]])
            #serie_data[datum].append(max_data[datum])
            serie_data.append([max_data[datum],min_data[datum]])
            #serie_data.append({'min':min_data[datum],'max':max_data[datum]})
            #serie_data.append({'l':9,'h':10})

        self.logger.debug("Data: %s", str(serie_data))
        serie_idx = chart.add_dataset(1,serie_data)
        self.logger.debug("dataset index: %s", serie_idx)
        chart.set_dataset_maxbarthickness(serie_idx, 10)
        chart.set_dataset_fillcolour(serie_idx,hex_rgba('wheat',0.8))
        avgl_idx = chart.add_dataset(2,avg_data,mix_type='line')
        self.logger.debug("dataset index: %s", avgl_idx)
        chart.set_dataset_fillstyle(avgl_idx,False)
        chart.set_dataset_pointsize(avgl_idx,0)
        chart.set_dataset_linecolour(avgl_idx,hex_rgb(config.color))

        if config.interpolate:
            chart.set_dataset_spangaps(avgl_idx,True)
            #chart.set_dataset_spangaps(maxl_idx,True)
        
        if self.labels:
            self.logger.debug("labels: %s",str(self.labels))
            labels_data = copy.copy(data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]])
            chart.set_axis_labels(x_axis_id,labels_data)
            chart.set_axis_style(x_axis_id,fontColor='#8D7641')
            chart.set_axis_style(y_axis_id,fontColor='#8D7641')
            
            
        self.logger.debug('Chart JSON: '+chart.dump_chart())
        self.logger.debug('Chart JSON: '+chart.chart_json())
        
        return chart        



class ChartRenderer(object):
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
        Display or not the tick along the axes. Defaults to 'true'.

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

    accumulate (G, S) [true|false]:
        If 'true' the data is transformed to write its accumulated 
        value. Useful when drawing accumulated rain.

    interpolate (G, S) [true|false]:
        If 'true', draw a continuous line instead of blank for missing
        values. This is useful when the chart resolution is finer than
        the sampling period. Ignored when accumulate = 'true'.

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
    docroot = '/var/www'
    static = None

    logger = logging.getLogger("renderer.chart")

    def render(self,data={}, context={}):

        assert self.series is not None, "'chart.series' must be set"

        converter = wfcommon.units.Converter(context["units"])
        #self.logger.info("context: "+str(context["units"]))
        
        # merge builtin defaults, context and renderer config
        config = ChartConfig()
        if context.has_key('chart'):
            config.__dict__.update(context['chart'])
        config.__dict__.update(self.__dict__)

        if self.series.has_key('wind.avg'):
            self.logger.debug("chart.series:  "+str(self.series))
            self.logger.debug("config:        "+str(dumpChartConfig(config)))
            self.logger.debug("self.__dict__: "+str(self.__dict__))
            self.logger.debug("data:          "+str(data["wind"]))

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

        self.logger.debug("measure: %s", str(key.split('.')[0]))
        self.logger.debug("interpolate: %s", str(serie_config.interpolate))

        ordered_series.sort( cmp=lambda x,y: cmp(x[0],y[0]) )

        ordered_keys = []
        for order, key, serie in ordered_series:
            ordered_keys.append(key)

        # create the chart
        self.logger.debug("measure: %s", str(key.split('.')[0]))

        chart = SimpleLineChart(config.width, config.height)
        x_axis_id = chart.add_axis('x', True)
        y_axis_id = chart.add_axis('y', True)
        #y_axis_id = 'y-axis-0'
        x_axis = (chart.get_axis(x_axis_id))
        y_axis = (chart.get_axis(y_axis_id))

        chart.set_axis_visible('x-axis-0',False)
        chart.set_axis_visible('y-axis-0',False)
        chart.set_axis_zeroline_width(x_axis_id,1)
        chart.set_axis_zeroline_width(y_axis_id,1)
        chart.set_axis_gridline_width(x_axis_id,0)
        chart.set_axis_gridline_width(y_axis_id,0)
#        chart.set_axis_visible(x_axis_id,True)
#        chart.set_axis_visible(y_axis_id,True)
#        chart.set_axis_gridlines(x_axis_id,False)
#        chart.set_axis_gridlines(y_axis_id,False)
        #chart.set_axis_style(x_axis_id,11)
        #chart.set_axis_style(y_axis_id,11)
        chart.set_axis_style(x_axis_id,fontColor='#8D7641')
        chart.set_axis_style(y_axis_id,fontColor='#8D7641')
        
        self.logger.debug('Chart JSON: '+chart.dump_chart())

        # Draws for each serie
        index=0
        for order, key, serie in ordered_series:
            serie_config = ChartConfig()
            serie_config.__dict__.update(config.__dict__)
            serie_config.__dict__.update(serie)
            serie_data = copy.copy(data[key.split('.')[0]]['series'][key.split('.')[1]])
            #self.logger.info("Data copy: [%s]['series'][%s]",key.split('.')[0],key.split('.')[1]) 
            measure = key.split('.')[0]
            self.logger.debug("key: %s", key)
            self.logger.debug("measure: %s", measure)

            if self.flat(serie_data):  # Series with all data = None
                continue

            if serie_config.accumulate:
                serie_data = self._accumulate(serie_data)
            elif serie_config.interpolate:
                serie_data = self._interpolate(serie_data)

            #convert the data values according to current context
            if measure == "dew":
                for i in range(len(serie_data)):
                    serie_data[i]=converter.convert('temp',serie_data[i])
            elif key != "wind.deg":
                for i in range(len(serie_data)):
                    serie_data[i]=converter.convert(measure,serie_data[i])
            else:
                for i in range(len(serie_data)):
                    if serie_data[i] != None:
                        serie_data[i]=180-serie_data[i]
            
            if key == "wind.deg":
                self.logger.debug("Deg: %s", repr(serie_data))
                y_axis_id = chart.add_axis('y', True)
                chart.set_axis_visible(y_axis_id, False)
                #chart.set_axis_labels(y_axis_id, ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW', 'S'], True)
                chart.set_axis_gridlines(y_axis_id, True)

                #continue
                
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
                
            #self.logger.info("Chart range: min: %s max: %s",str(chart_min),str(chart_max))
            #self.logger.info("Data  range: min: %s max: %s",str(min_data),str(max_data))
            #self.logger.info("Index      : min: %s max: %s",str(min_index),str(max_index))
            
            #(serie_data, min_index, max_index) = self.compress_to(serie_data, config.nval, min_index, max_index)

            #serie_config.color=_valid_color(serie_config.color)
            #chart.add_data(serie_data,serie_config)
#aaaaaaaaaaaaaa
#       dataset = {'order':index,
#                   #'pointStyle':'rectRot',
#                   #'pointRadius':0,
#                   #'borderColor':'#'+config.color,
#                   #'borderWidth':config.thickness,
#                   #'borderDash':dash,
#                   #'backgroundColor':'#'+fillcolour+"AA",
#                   #'fill':fill,
#                   #'data':data
#                  }

            chart.add_dataset(index,serie_data,y_axis_id) # create new dataset
            chart.set_dataset_label(index,key)
            chart.set_dataset_linecolour(index,hex_rgb(serie_config.color))
            chart.set_dataset_linewidth(index,serie_config.thickness)
            chart.set_dataset_linestyle(index,[])
            if key == 'rain.fall':
                chart.set_dataset_linetension(index,0)
            chart.set_dataset_fillcolour(index,hex_rgba(serie_config.bgcolor,0.7))
            chart.set_dataset_fillstyle(index,False)
            chart.set_dataset_pointsize(index,0)
#            chart.set_dataset_pointstyle(index,'star')
#            chart.set_dataset_pointwidth(index,4)
#            chart.set_dataset_pointcolour(index,hex_rgba('darkblue',0.5))
#            chart.set_dataset_pointfillcolour(index,hex_rgba('darkred',0.2))
            
            if serie_config.dash:
                chart.set_dataset_linestyle(index,[4,2])

            if serie_config.area is not None:
                chart.set_dataset_fillcolour(index,hex_rgba(serie_config.color,0.7))
                chart.set_dataset_fillstyle(index,'+1')
           
            self.logger.debug("Dataset: %s\n%s", str(index), chart.get_dataset(index))

            serie_length = len(serie_data)
            serie_edge = int(round(serie_length * 0.1))+1

            if serie_config.max and not max_index == None:
                max_config = ChartConfig()
                max_config.__dict__.update(serie_config.__dict__)
                max_config.__dict__.update(serie_config.max)
                #self.logger.info("max_config: "+str(max_config.max))
                near_edge = (max_index < serie_edge or serie_length - max_index < serie_edge)
                if near_edge and max_index < serie_edge:
                    offset = -4
                elif near_edge:
                    offset = 4
                else:
                    offset = 0
                if max_data or measure == 'temp':
                    max_adjust = len(str(round(max_data,1))) * offset
                    #self.logger.info("Max: %s %s %s %s %s %s %s", str(round(max_data,1)), str(max_index), str(serie_length), str(serie_edge), \
                    #                                                str(near_edge), str(max_adjust), hex_rgba(max_config.color,0.4))
                    #chart.add_marker('max',str(round(max_data,1)),max_index, max_adjust)
                    chart.add_marker('x', \
                                     str(round(max_data,1)), \
                                     max_index, \
                                     'top', \
                                     max_adjust, \
                                     hex_rgb(max_config.text), \
                                     hex_rgba(max_config.color,0.4), \
                                     hex_rgba(max_config.color,0.2), \
                                     max_config.thickness)
                                  
            if serie_config.min and not min_index == None:
                min_config = ChartConfig()
                min_config.__dict__.update(serie_config.__dict__)
                min_config.__dict__.update(serie_config.min)
                #self.logger.info("min_config: "+str(min_config.max))
                near_edge = (min_index < serie_edge or serie_length - min_index < serie_edge)
                if near_edge and min_index < serie_edge:
                    offset = -4
                elif near_edge:
                    offset = 4
                else:
                    offset = 0
                if min_data or measure == 'temp':
                    min_adjust = len(str(round(min_data,1))) * offset
                    #self.logger.info("Max: %s %s %s %s %s %s %s", str(round(min_data,1)), str(min_index), str(serie_length), str(serie_edge), \
                    #                                                str(near_edge), str(min_adjust), hex_rgba(min_config.color,0.4))
                    #chart.add_marker('min',str(round(min_data,1)),min_index, min_adjust)
                    chart.add_marker('v', \
                                     str(round(min_data,1)), \
                                     min_index, \
                                     'bottom', \
                                     min_adjust, \
                                     hex_rgb(min_config.text), \
                                     hex_rgba(min_config.color,0.4), \
                                     hex_rgba(min_config.color,0.2), \
                                     min_config.thickness)

            if serie_config.last:
                last_config = ChartConfig()
                last_config.__dict__.update(serie_config.__dict__)
                last_config.__dict__.update(serie_config.last)
                last_index = len(serie_data)-1
                last_data = serie_data[last_index]
                if last_data:
                    last_adjust = len(str(round(last_data,1))) * 4
                    #self.logger.info("Last: %s %s %s %s", str(round(last_data,1)), str(last_index), str(last_adjust), \
                    #                                      hex_rgba(last_config.color,0.4))
                    #chart.add_marker('last',str(round(last_data,1)),last_index, last_adjust)
                    chart.add_marker('vertical', \
                                     str(round(last_data,1)), \
                                     last_index, \
                                     'top', \
                                     last_adjust, \
                                     hex_rgb(last_config.text), \
                                     hex_rgba(last_config.color,0.4), \
                                     hex_rgba(last_config.color,0.2), \
                                     last_config.thickness)

            index = index + 1
        
#        for i in range(0,index):        
#            self.logger.info("Dataset: %s\n%s", str(i), chart.get_dataset(i))



       
        # Peg rain yaxis to 0 origin
        if measure == 'rain' or (measure == 'wind' and key != "wind.deg"):
            chart.set_axis_range(y_axis_id, 0, None, True)
        elif key == "wind.deg":
            chart.set_axis_range(y_axis_id, -180, 180)
        else:
            chart.set_axis_range(y_axis_id, chart_min, chart_max)
        
        # Draw a horizontal line through 'zero'
        
        chart.add_marker('horizontal', \
                          '', \
                          0, \
                          'centre', \
                          0, \
                          0, \
                          0, \
                          '#aaa', \
                          1)
                
                
        # Draw a horizontal line through 'zero'
#        if config.zero and config.axes and chart_min < 0 and chart_max > 0:
#            zero_config = ChartConfig()
#            zero_config.__dict__.update(config.__dict__)
#            zero_config.__dict__.update(config.zero)
#            chart.add_marker('horizontal', \
#                              '', \
#                              0, \
#                              'centre', \
#                              0, \
#                              0, \
#                              0, \
#                              hex_rgb(zero_config.color), \
#                              zero_config.thickness)

        if self.labels:
            labels_data = copy.copy(data[self.labels.split('.')[0]]['series'][self.labels.split('.')[1]])
            #labels_data = self.compress_to(labels_data, config.nval, None, None)[0]
            if config.axes:
                chart.set_axis_labels(x_axis_id, labels_data, True)
            else:
                chart.set_axis_labels(x_axis_id, [])



        if measure == 'hum':
        #if index == 4:
            self.logger.debug('JSON Dump:\n'+chart.dump_chart())

        try:
            url = chart.get_json(self.docroot)
            if url != '500':
                url='/'+str(self.static)+'/'+url
                self.logger.debug('PNG URL: '+url)
                return url
        except:
            self.logger.exception("Could not render chart")
            return "http://chart.apis.google.com/chart?cht=lc&chs="+str(config.width)+"x"+str(config.height)

#        try:
#            url = chart.get_url()+"&chma=10,10,10,10" # add a margin
#            url = chart.get_url()
#            if measure == 'temp':
#                self.logger.debug("url:   "+url)
#            self.logger.info("Serie: "+str(measure))
#            self.logger.info("lenurl: "+str(len(url)))
#            return url
#        except:
#            self.logger.exception("Could not render chart")
#            return "http://chart.apis.google.com/chart?cht=lc&chs="+str(config.width)+"x"+str(config.height)

    def _interpolate(self, data):
        result = copy.copy(data)
        (last, index, count) = (None, None, 0)
        for i,val in enumerate(data):
            if val is None:
                if last is not None:             # ignore leading None(s)
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

    def _accumulate(self, data):
        result = []
        acc = None
        for d in data:
            if d is not None:
                if acc is None:
                    acc = 0
                else:
                    acc += d
            result.append(acc)
        return result

    def compress_to(self, data, n, min_index, max_index):
        new_min_index = min_index
        new_max_index = max_index
        while len(data) > n:
            l = len(data)
            d = l-n        # how many values to remove
            r = l / d      # each r-th must be removed
            #print "compress "+str(l)+" to "+str(n)+" by "+str(r)
            if r < 2:
                r = 2
            (data, new_min_index, new_max_index) = self._compress(data, r, new_min_index, new_max_index)
            #print "compressed to "+str(len(data))
        return (data, new_min_index, new_max_index)

    def _compress(self, data, ratio, min_index, max_index):
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
            if v is not None:
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
                    result.append(v if v is not None else last)
                last=None
        return (result, new_min_index, new_max_index)

    def flat(self, data):
        if len(data)==0:
            return True
        for d in data:
            if d != None:
                return False
        return True

class ChartWindRadarRenderer(object):
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

    logger = logging.getLogger("renderer.chart")

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

        sectors_config.color=hex_rgb(sectors_config.color)
        sectors_config.bgcolor=hex_rgb(sectors_config.bgcolor)
        lines_config.color=hex_rgb(lines_config.color)
        lines_config.bgcolor=hex_rgb(lines_config.bgcolor)

        self.logger.debug('arrow: True') if config.arrow else self.logger.debug('arrow: False')
        self.logger.debug('tail: True') if config.tail else self.logger.debug('tail: False')
        self.logger.debug('trace: True') if config.trace else self.logger.debug('trace: False')
        self.logger.debug('sectors: True') if config.sectors else self.logger.debug('sectors: False')
        self.logger.debug('bars: True') if config.bars else self.logger.debug('bars: False')
        self.logger.debug('lines: True') if config.lines else self.logger.debug('lines: False')
        self.logger.debug('areas: True') if config.areas else self.logger.debug('areas: False')
        self.logger.debug('beaufort: True') if config.beaufort else self.logger.debug('beaufort: False')

        # Prepare data

        max = config.median * 2
        
        if data[self.key].has_key('sectors'):
            sector_data = data[self.key]['sectors'] # 'old' sector from db datasource
            self.logger.debug("sector_data from db")

        else:
            if data.has_key(self.sector_key): # 'new' sector data from accumulator
                sector_data = self.calculate_accumulated_sector_data(data[self.sector_key]['series'])
                self.logger.debug("sector_data from accumulator")
            else:
                if data[self.key].has_key('series'):
                    sector_data = self.calculate_cheap_sector_data(data[self.key]['series'])
                    self.logger.debug("sector_data from cheap")
                else:
                    sector_data = None

        
#        if not config.arrow:
#            #self.logger.info("data: "+str(data['sectors']))
#            self.logger.debug("data lbl: %s",str(data['sectors']['series']['lbl']))
#            for i in range(len(data['sectors']['series']['lbl'])):
#                self.logger.debug("data avg[%s]: %s",str(i),str(data['sectors']['series']['avg'][i]))
#            #for i in range(len(data['sectors']['series']['lbl'])):
#            #    self.logger.info("data max[%s]: %s",str(i),str(data['sectors']['series']['max'][i]))
#            #for i in range(len(data['sectors']['series']['lbl'])):
#            #    self.logger.info("data frq[%s]: %s",str(i),str(data['sectors']['series']['freq'][i]))
#            #self.logger.info("sector_data asm: "+str(sector_data['asum']))
#            #self.logger.info("sector_data gsm: "+str(sector_data['gsum']))

#            #self.logger.info("sector_data lbl: %s",str(sector_data['lbl']))
#            #self.logger.info("sector_data avg: %s",str(sector_data['avg']))
#            #self.logger.info("sector_data max: %s",str(sector_data['max']))
#            #self.logger.info("sector_data frq: %s %s",str(sector_data['freq']),str(sum(sector_data['freq'])))
#            #self.logger.info("sector_data asm: %s",str(sector_data['asum']))
#            #self.logger.info("sector_data gsm: %s",str(sector_data['gsum']))
#        else:
#            self.logger.debug("wind value: %s",str(data['wind']['value']))
#            self.logger.debug("wind max: %s",str(data['wind']['max']))
#            self.logger.debug("wind dir: %s",str(data['wind']['dir']))
#            self.logger.debug("wind deg: %s",str(data['wind']['deg']))

        
               
        if data[self.key].has_key('value'):
            current_noscale = data[self.key]['value']
            last_gust_noscale = data[self.key]['max']
            pos = int(round(data[self.key]['deg'] * 16 / 360.0))
            if pos > 15: pos = 0
            current = self.scale(current_noscale, config.median, config.radius)
            last_gust_scaled = self.scale(last_gust_noscale, config.median, config.radius)
            arrow_thickness = 0.3+3.0*arrow_config.thickness*current/max

        if config.bars or config.areas or config.sectors:
            avg = []
            for val in sector_data['avg']:
                avg.append(int(self.scale(val, config.median, config.radius)))
            #avg.append(avg[0])
            gust = []
            for val in sector_data['max']:
                gust.append(int(self.scale(val, config.median, config.radius)))
            #gust.append(gust[0])
            asm = []
            #for val in sector_data['asum']:
            for val in sector_data['freq']:
                asm.append(int(val*100))
            gsm = []
            for val in sector_data['gsum']:
                gsm.append(int(val))
        else:
            avg = [0] * 16
            gust = [0] * 16

        line = [0] * 16
        crown = [int(max)] * 16
        tail = [0] * 16
        last_gust = [0] * 16
        head = [0] * 16
#aaaaaaaaaaaaaa        
        if data[self.key].has_key('value'):
#            self.logger.info("pos: %s",str(pos))
#            self.logger.info("max: %s",str(max))
#            self.logger.info("current: %s",str(current)+" "+str(current_noscale)+" "+str(int(round(current_noscale))))
#            self.logger.info("beaufort: %s", str(int(round(wfcommon.units.MpsToBft(current_noscale)))))
            current=int(round(current_noscale))
            line[pos] = int(max) if current > 0 else 0
            tail[pos] = int(current)
            last_gust[pos] = int(last_gust_scaled)
#            head[ (pos - 1 + 16) % 16 ] = int(current*0.6)
#            head[ (pos + 16) % 16 ] = int(current*0.6)
#            head[ (pos + 1) % 16 ] = int(current*0.6)
            head[ (pos - 7 + 16) % 16 ] = current
            head[ (pos + 8) % 16 ] = current
            head[ (pos + 7) % 16 ] = current
            head[ (pos) % 16 ] = current
            self.logger.debug("head:  "+str(head))

        if not config.arrow:
            self.logger.debug("avg:  "+str(avg))
            self.logger.debug("gust: "+str(gust))
            self.logger.debug("asm:  "+str(asm))
            self.logger.debug("gsm:  "+str(gsm))



        #return "http://chart.apis.google.com/chart?cht=lc&chs="+str(config.width)+"x"+str(config.height)
        #chart = RadarChart(config.width, config.height, y_range=(0,max) )
        if config.arrow:
            chart = RadarChart(config.width, config.height)
            chart.set_axis_visible('radial',True)
            chart.set_axis_gridlines('radial',False)
            chart.set_axis_gridlines('grid',False)
        else:
            chart = PolarChart(config.width, config.height)
            chart.set_startangle(-11.25) # rotate 11.25 degrees anticlockwise from N
            chart.set_axis_visible('radial',True)
            chart.set_axis_visible('grid',True)
            chart.set_axis_gridlines('radial',False)
            chart.set_axis_gridlines('grid',True)
            chart.set_axis_style('grid',10,'Arial','#8D7641')
            #chart.set_axis_labels_suffix(None,'%')
        
        index = 0
        
#        chart.add_data([0] * 2)
#        chart.add_data(line)
#        chart.add_data(avg,beaufort_config)
#        chart.add_data(gust,beaufort_config)
#        chart.add_data(crown)
#        chart.add_data(tail)
#        chart.add_data(head,config)
#        chart.add_data(last_gust,beaufort_config)

#        if config.bars:
#            chart.add_marker(2, -1, "v", _valid_color(bars_config.gust), bars_config.thickness, -1)
#            chart.add_marker(3, -1, "v", _valid_color(bars_config.color), bars_config.thickness, -1)

#        if config.beaufort:
#            chart.add_marker(0, "220:0.9", "@t"+str(int(round(wfcommon.units.MpsToBft(current_noscale)))), _valid_color(beaufort_config.color) + "%02x" % (beaufort_config.intensity*255), rmin(config.height, config.width)-config.size*5, -1)

#        colors = [
#            "00000000",
#            _valid_color(tail_config.color),
#            _valid_color(lines_config.color),
#            _valid_color(lines_config.gust),
#            "00000000",
#            _valid_color(arrow_config.color),
#            _valid_color(arrow_config.color),
#            "00000000"
#            ]

#        if config.sectors:
#            for i in range(0,16):
#                sec = [0] * 16
#                avg = self.scale(sector_data['avg'][i], config.median, config.radius)
#                freq_value = sector_data['freq'][i]*255
#                freq_value = rmin(255, (1+2*sectors_config.intensity) * freq_value)
#                self.logger.info('freq_value: '+str(freq_value))
#                freq = "%02x" % int(freq_value)
#                start = i-0.5
#                stop = i+0.5
#                chart.add_vertical_range(_valid_color(sectors_config.color)+freq, start, stop)

#        if config.trace:
#            nval = len(data[self.key]['series']['deg'])
#            nbullet = rmin(trace_config.length, nval)
#            minsize = trace_config.size / float(trace_config.ratio)
#            maxsize = trace_config.size
#            size = float(maxsize)
#            inc = (maxsize-minsize) / nbullet
#            n = 0
#            for p in reversed(data[self.key]['series']['deg']):
#                chart.add_marker(4, int(p/22.5), 'o', _valid_color(trace_config.color), size)
#                size = size - inc
#                n = n + 1
#                if n == nbullet:
#                    break

#        if config.areas:
#            chart.add_fill_range(_valid_color(areas_config.gust), 3, 2)
#            chart.add_fill_range(_valid_color(areas_config.color), 3, 0)

#        if config.max:
#            chart.add_marker(7, pos, 'o', _valid_color(gust_config.color), gust_config.thickness)
#            chart.add_marker(7, pos, 't'+str(round(last_gust_noscale,1)), _valid_color(gust_config.text), gust_config.size)

#        if config.arrow:
#            chart.add_marker(0, 0, 'o', _valid_color(arrow_config.color), arrow_thickness)
#            chart.add_marker(5, pos, 't'+str(round(current_noscale,1)), _valid_color(arrow_config.text), arrow_config.size)
#            chart.add_fill_range(_valid_color(arrow_config.fill), 6, 0)

#        chart.set_colours( colors )

        if config.axes:
            chart.set_axis_labels('radial', ['N', '', 'NE', '', 'E', '', 'SE', '', 'S', '', 'SW', '', 'W', '', 'NW', ''])
            chart.set_axis_style('radial',10,'Arial','#8D7641')
            #chart.set_axis_style(0, _valid_color(config.text), config.size, 0, 'l', _valid_color(config.bgcolor));

#        if data[self.key].has_key('value'):
#            chart.set_line_style(1, tail_config.thickness)
#        else:
#            chart.set_line_style(1, 0)
#        chart.set_line_style(2, lines_config.thickness)
#        chart.set_line_style(3, lines_config.thickness)
#        chart.set_line_style(4, 0)
#        if data[self.key].has_key('value'):
#            chart.set_line_style(5, arrow_thickness)
#            chart.set_line_style(6, arrow_thickness)
#        else:
#            chart.set_line_style(5, 0)
#            chart.set_line_style(6, 0)


#        chart.fill_solid(Chart.BACKGROUND, _valid_color(config.bgcolor))




#            chart.set_dataset_label(index,key)
#            chart.set_dataset_linecolour(index,hex_rgb(serie_config.color))
#            chart.set_dataset_linewidth(index,serie_config.thickness)
#            chart.set_dataset_linestyle(index,[])
#            chart.set_dataset_fillcolour(index,hex_rgba(serie_config.bgcolor,0.7))
#            chart.set_dataset_fillstyle(index,False)
#            chart.set_dataset_pointsize(index,0)





        
        if config.sectors:
            sectors_config.color=hex_rgba(sectors_config.sectors['color'],sectors_config.sectors['intensity'])
            sectors_config.bgcolor=sectors_config.color
#            chart.add_data(asm,sectors_config)
            #self.logger.info('color:     %s',str(sectors_config.color))
            #self.logger.info('bgcolor:   %s',str(sectors_config.bgcolor))
            #self.logger.info('thickness: %s',str(sectors_config.thickness))
            chart.add_dataset(index, asm)
            chart.set_dataset_linecolour(index,sectors_config.color)
            chart.set_dataset_linewidth(index,sectors_config.thickness)
            chart.set_dataset_fillcolour(index,sectors_config.bgcolor)
            chart.set_dataset_pointsize(index,0)
            chart.set_dataset_borderalign(index,'inner')
            index = index + 1
            
#bbbbbbbbbbbbbbbbbbb
#        if config.sectors:
#            sectors_config.color=hex_rgba(sectors_config.sectors['gust'],sectors_config.sectors['intensity'])
#            #sectors_config.color=hex_rgba(sectors_config.sectors['gust'],.75)
#            sectors_config.bgcolor=sectors_config.color
#            #chart.add_data(gsm,sectors_config)
#            chart.add_dataset(index, gsm)
#            chart.set_dataset_linecolour(index,sectors_config.color)
#            chart.set_dataset_linewidth(index,sectors_config.thickness)
#            chart.set_dataset_fillcolour(index,sectors_config.bgcolor)
#            chart.set_dataset_pointsize(index,0)
#            index = index + 1

        if config.arrow:
            arrow_config.color=hex_rgba(arrow_config.color,.66)
            arrow_config.bgcolor=arrow_config.color
            #self.logger.info(str(head))
            #chart.add_data(head,arrow_config)
            chart.add_dataset(index, head)
            chart.set_dataset_linecolour(index,arrow_config.color)
            chart.set_dataset_linewidth(index,arrow_config.thickness)
            chart.set_dataset_fillcolour(index,arrow_config.bgcolor)
            chart.set_dataset_pointsize(index,0)
            index = index + 1

        try:
            self.logger.debug('JSON Dump:\n'+chart.dump_chart())
            url = chart.get_json(self.docroot)
            if url != '500':
                url='/'+str(self.static)+'/'+url
                self.logger.debug('PNG URL: '+url)
                return url
        except:
            self.logger.exception("Could not render chart")
            return "http://chart.apis.google.com/chart?cht=lc&chs="+str(config.width)+"x"+str(config.height)

#        try:
#            url = chart.get_url()
#            self.logger.debug("url:   "+url)
#            return url
#        except:
#            self.logger.exception("Could not render chart")
#            return "http://chart.apis.google.com/chart?cht=lc&chs="+str(config.width)+"x"+str(config.height)

    def scale(self, value, mean, max):
        if value < 0:
            value=0
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
        #avg_counts = 16 * [0.0]        
        avg_counts = sector_data['asum'] = 16 * [0.0]        
        gst_counts = sector_data['gsum'] = 16 * [0.0]        

        count = len(serie_data['avg'])
    
        s_avg=serie_data['avg']
        s_max=serie_data['max']
        s_freq=serie_data['freq']
        
        for i in range(count):
            for j in range(16):     
                if s_max[i][j] > 0:
                    gst_counts[j] = gst_counts[j] + 1
                if s_avg[i][j] > 0:
                    d_avg[j] = d_avg[j]+s_avg[i][j]
                    avg_counts[j] = avg_counts[j] + 1
                if s_max[i][j] > d_max[j]:
                    d_max[j] = s_max[i][j] 
        #        d_freq[j] = d_freq[j] + s_freq[i][j] 

        for i in range(16):
            if avg_counts[i] > 0:
                d_avg[i] = float(d_avg[i]) / avg_counts[i]
            
        #sum_freq = sum(d_freq)
        
        #if sum_freq > 0:
        #    for i in range(16):
        #        d_freq[i] = d_freq[i] / sum_freq
                
        sector_data['freq'] = []
        avgsum = sum(d_avg)
        for i in range(16):
            #d_freq.append(d_avg[i] / avgsum)
            if avgsum != 0:
                sector_data['freq'].append(d_avg[i] / avgsum)
            else:
                sector_data['freq'].append(d_avg[i])

            
        return sector_data
                

#def _axis_set_style(self, colour, font_size=None, alignment=None, drawing_control=None, tick_colour=None):
#    _check_colour(colour)
#    self.colour = colour
#    self.font_size = font_size
#    self.alignment = alignment
#    self.drawing_control = drawing_control
#    self.tick_colour = tick_colour
#    if tick_colour is not None:
#        _check_colour(tick_colour)
#    self.has_style = True

#def _axis_style_to_url(self):
#    bits = []
#    bits.append(str(self.axis_index))
#    bits.append(self.colour)
#    if self.font_size is not None:
#        bits.append(str(self.font_size))
#        if self.alignment is not None:
#            bits.append(str(self.alignment))
#            if self.drawing_control is not None:
#                assert(self.drawing_control in Axis.DRAWING_CONTROL)
#                bits.append(self.drawing_control)
#                if self.tick_colour is not None:
#                    bits.append(self.tick_colour)
#
#    return ','.join(bits)

#Axis.AXIS_LINES = 'l'
#Axis.TICK_MARKS = 't'
#Axis.BOTH = 'lt'
#Axis.DRAWING_CONTROL = (Axis.AXIS_LINES, Axis.TICK_MARKS, Axis.BOTH)

#def _chart_set_axis_style(self, axis_index, colour, font_size=None, \
#      alignment=None, drawing_control=None, tick_colour=None):
#    try:
#        self.axis[axis_index].set_style(colour, font_size, alignment, drawing_control, tick_colour)
#    except IndexError:
#        raise InvalidParametersException('Axis index %i has not been created' % axis)

#Axis.set_style = _axis_set_style
#Axis.style_to_url = _axis_style_to_url

#Chart.set_axis_style_old = _chart_set_axis_style



if __name__=="__main__":

    serie_data = {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "avg" : [ 4, 3.8, None, 1, 1.2, .3, 0.2, 0, 1 , 1],
                    "max" : [ 5, 6, None, 1.3, 1.3, .4, 0.2, 0, 1.2 , 1],
                    "deg" : [ 318, None, 300, 310, 300, 300, 300, 345, 12, 60 ],
                    "dir": [ 'NNW', None, 'NW', 'NW', 'NW', 'NW', 'N', 'NNE', 'NE', 'NE']
                    }

    r = ChartWindRadarRenderer()
    print r.calculate_cheap_sector_data(serie_data)
