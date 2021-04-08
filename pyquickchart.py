#!/usr/bin/env python
"""
pyquickchart - An incomplete Python wrapper for the QuickChart
replacement for the Google Chart API

Copyright 2019 Mark Blinkhorn

Big chunks stolen from Gerald Kaszuba (PyGoogleChart)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# unnecessary on Python3, but harmless
from __future__ import division

import os
import math
import random
import re
import warnings
import copy
import json

try:
    # we're on Python3
    from urllib.request import urlopen
    from urllib.parse import quote

except ImportError:
    # we're on Python2.x
    from urllib2 import urlopen
    from urllib import quote


# Helper variables and functions
# -----------------------------------------------------------------------------

__version__ = '0.1.0'
__author__ = 'Mark Blinkhorn'

#reo_colour = re.compile('^([A-Fa-f0-9]{2,2}){3,4}$')


#def _check_colour(colour):
#    if not reo_colour.match(colour):
#        raise InvalidParametersException('Colours need to be in ' \
#            'RRGGBB or RRGGBBAA format. One of your colours has %s' % \
#            colour)


#def _reset_warnings():
#    """Helper function to reset all warnings. Used by the unit tests."""
#    globals()['__warningregistry__'] = None


# Exception Classes
# -----------------------------------------------------------------------------


class PyGoogleChartException(Exception):
    pass


class DataOutOfRangeException(PyGoogleChartException):
    pass


class UnknownDataTypeException(PyGoogleChartException):
    pass


class NoDataGivenException(PyGoogleChartException):
    pass


class InvalidParametersException(PyGoogleChartException):
    pass


class BadContentTypeException(PyGoogleChartException):
    pass


class AbstractClassException(PyGoogleChartException):
    pass


class UnknownChartType(PyGoogleChartException):
    pass

class UnknownCountryCodeException(PyGoogleChartException):
    pass

class IndexOutOfRangeException(PyGoogleChartException):
    pass
      
class JsonPostException(PyGoogleChartException):
    print(repr(PyGoogleChartException))

      
# Data Classes
# -----------------------------------------------------------------------------

"""
class Data(object):

    def __init__(self, data):
        if type(self) == Data:
            raise AbstractClassException('This is an abstract class')
        self.data = data

    @classmethod
    def float_scale_value(cls, value, range):
        lower, upper = range
        assert(upper > lower)
        scaled = (value - lower) * (cls.max_value / (upper - lower))
        return scaled

    @classmethod
    def clip_value(cls, value):
        return max(0, min(value, cls.max_value))

    @classmethod
    def int_scale_value(cls, value, range):
        return int(round(cls.float_scale_value(value, range)))

    @classmethod
    def scale_value(cls, value, range):
        scaled = cls.int_scale_value(value, range)
        clipped = cls.clip_value(scaled)
        Data.check_clip(scaled, clipped)
        return clipped

    @staticmethod
    def check_clip(scaled, clipped):
        if clipped != scaled:
            warnings.warn('One or more of of your data points has been '
                'clipped because it is out of range.')


class SimpleData(Data):

    max_value = 61
    enc_map = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

    def __repr__(self):
        encoded_data = []
        for data in self.data:
            sub_data = []
            for value in data:
                if value is None:
                    sub_data.append('_')
                elif value >= 0 and value <= self.max_value:
                    sub_data.append(SimpleData.enc_map[value])
                else:
                    raise DataOutOfRangeException('cannot encode value: %d'
                                                  % value)
            encoded_data.append(''.join(sub_data))
        return 'chd=s:' + ','.join(encoded_data)


class TextData(Data):

    max_value = 100

    def __repr__(self):
        encoded_data = []
        for data in self.data:
            sub_data = []
            for value in data:
                if value is None:
                    sub_data.append(-1)
                elif value >= 0 and value <= self.max_value:
                    sub_data.append("%.1f" % float(value))
                else:
                    raise DataOutOfRangeException()
            encoded_data.append(','.join(sub_data))
        return 'chd=t:' + '%7c'.join(encoded_data)

    @classmethod
    def scale_value(cls, value, range):
        # use float values instead of integers because we don't need an encode
        # map index
        scaled = cls.float_scale_value(value, range)
        clipped = cls.clip_value(scaled)
        Data.check_clip(scaled, clipped)
        return clipped


class ExtendedData(Data):

    max_value = 4095
    enc_map = \
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-.'

    def __repr__(self):
        encoded_data = []
        enc_size = len(ExtendedData.enc_map)
        for data in self.data:
            sub_data = []
            for value in data:
                if value is None:
                    sub_data.append('__')
                elif value >= 0 and value <= self.max_value:
                    first, second = divmod(int(value), enc_size)
                    sub_data.append('%s%s' % (
                        ExtendedData.enc_map[first],
                        ExtendedData.enc_map[second]))
                else:
                    raise DataOutOfRangeException( \
                        'Item #%i "%s" is out of range' % (data.index(value), \
                        value))
            encoded_data.append(''.join(sub_data))
        return 'chd=e:' + ','.join(encoded_data)

class AwesomeData(Data):

    max_value = 4095
    
    def __repr__(self):
        encoded_data = []
        for data in self.data:
            sub_data = []
            for value in data:
                if value is None:
                    sub_data.append('_')
                else:    
                    sub_data.append("%.1f" % float(value))
            encoded_data.append(','.join(sub_data))
        return 'chd=a:' + '%7c'.join(encoded_data)
#            encoded_data.append(''.join(sub_data))
#        return 'chd=a:' + ','.join(encoded_data)            
#                raise DataOutOfRangeException( \
#                        'Item #%i "%s" is out of range' % (data.index(value), value))
"""
# Axis Classes
# -----------------------------------------------------------------------------


"""
class Axis(object):

    BOTTOM = 'x'
    TOP = 't'
    LEFT = 'y'
    RIGHT = 'r'
    TYPES = (BOTTOM, TOP, LEFT, RIGHT)

    def __init__(self, axis_index, axis_type, **kw):
        assert(axis_type in Axis.TYPES)
        self.has_style = False
        self.axis_index = axis_index
        self.axis_type = axis_type
        self.positions = None

    def set_index(self, axis_index):
        self.axis_index = axis_index

    def set_positions(self, positions):
        self.positions = positions

    def set_style(self, colour, font_size=None, alignment=None):
        _check_colour(colour)
        self.colour = colour
        self.font_size = font_size
        self.alignment = alignment
        self.has_style = True

    def style_to_url(self):
        bits = []
        bits.append(str(self.axis_index))
        bits.append(self.colour)
        if self.font_size is not None:
            bits.append(str(self.font_size))
            if self.alignment is not None:
                bits.append(str(self.alignment))
        return ','.join(bits)

    def positions_to_url(self):
        bits = []
        bits.append(str(self.axis_index))
        bits += [str(a) for a in self.positions]
        return ','.join(bits)


class LabelAxis(Axis):

    def __init__(self, axis_index, axis_type, values, **kwargs):
        Axis.__init__(self, axis_index, axis_type, **kwargs)
        self.values = [str(a) for a in values]

    def __repr__(self):
        return '%i:%%7c%s' % (self.axis_index, '%7c'.join(self.values))


class RangeAxis(Axis):

    def __init__(self, axis_index, axis_type, low, high, **kwargs):
        Axis.__init__(self, axis_index, axis_type, **kwargs)
        self.low = low
        self.high = high

    def __repr__(self):
        return '%i,%s,%s' % (self.axis_index, self.low, self.high)
"""
# Chart Classes
# -----------------------------------------------------------------------------


class Chart(object):
    """Abstract class for all chart types.

    width are height specify the dimensions of the image. title sets the title
    of the chart. legend requires a list that corresponds to datasets.
    """

    #BASE_URL = 'https://chart.googleapis.com/chart'
    #BASE_URL = 'https://image-charts.com/chart'
    #BASE_URL = 'http://chart.apis.google.com/chart'
    BASE_URL = 'http://localhost:8080/chart'
    #BASE_URL = 'http://weatherpidev.smbconsult.local:8080/chart'
    #BASE_URL = 'https://quickchart.io/chart'
#    BACKGROUND = 'bg'
#    CHART = 'c'
#    ALPHA = 'a'
#    VALID_SOLID_FILL_TYPES = (BACKGROUND, CHART, ALPHA)
#    SOLID = 's'
#    LINEAR_GRADIENT = 'lg'
#    LINEAR_STRIPES = 'ls'

    def __init__(self, width, height, pixelratio=1, title=None, legend=None, colours=None,
            auto_scale=False, x_range=None, y_range=None,
            colours_within_series=None):
        if type(self) == Chart:
            raise AbstractClassException('This is an abstract class')
        assert(isinstance(width, int))
        assert(isinstance(height, int))
        self.width = width
        self.height = height
        self.Cartesian = False
        self.Radial = False
        #self.data = []
        #self.set_title(title)
        #self.set_title_style(None, None)
        #self.set_legend(legend)
        #self.set_legend_position(None)
        #self.set_colours(colours)
        #self.set_colours_within_series(colours_within_series)

        # Data for scaling.
        #self.auto_scale = auto_scale  # Whether to automatically scale data
        #self.x_range = x_range  # (min, max) x-axis range for scaling
        #self.y_range = y_range  # (min, max) y-axis range for scaling
        #self.scaled_data_class = None
        #self.scaled_x_range = None
        #self.scaled_y_range = None

        #self.fill_types = {
        #    Chart.BACKGROUND: None,
        #    Chart.CHART: None,
        #    Chart.ALPHA: None,
        #}
        #self.fill_area = {
        #    Chart.BACKGROUND: None,
        #    Chart.CHART: None,
        #    Chart.ALPHA: None,
        #}
        #self.axis = []
        #self.markers = []
        #self.line_styles = {}
        #self.grid = None
        #self.title_colour = None
        #self.title_font_size = None

        self.POSTBody = {
                           "backgroundColor": "transparent",
                           "devicePixelRatio": pixelratio,
                           "width": None,
                           "height": None,
                           "format": "png",
                           "chart": None
                        }
                        

        self.chart={
                      'type': '',
                      'options': {
                        'legend': {
                          'labels': {},
                          'display': False
                        },
                      'title': {
                          'display': False
                        }
                      },
                      'data': {
                        'datasets': []
                        }
                    }

        Cartesion=  {
                      'scales': {
                        'xAxes': [
                          {
                            'id':'x-axis-0',
                            'gridLines':{
#                              'lineWidth': 1,
#                              'zeroLineWidth': 3,
#                              'display':False
                            },
                            'labels':[],
#                            'display':False
                            'ticks': {
#                              'display': True,
                              'autoSkipPadding': 2,
                            }
                          }
                        ],
                        'yAxes': [
                          {
                            'id':'y-axis-0',
                            'gridLines': {
#                              'lineWidth': 1,
#                              'zeroLineWidth': 3,
#                              'display':False
                            },
                            'labels':[],
                            'ticks': {
#                              'display': True,
#                              'autoSkipPadding': 2,
                            }
                          }
                        ]
                      }
                    }

        Radial=     {
                      'scale':{
                        'angleLines': {
  #                        'display': False
                        },
                        'gridLines': {
  #                        'display': False,
  #                        'circular': True
                        },
                        'pointLabels': {},
                        'ticks': {
                          'display': False,
#                          "fontColor": "#8D7641",
#                          "fontFamily": "Arial",
#                          "fontSize": 10,
#                          "fontStyle": "normal"
                        }
                      }
                    }
                    
#        Plugin =    {
#                      'annotation': {
#                        'annotations': [{
#                          'type': 'line',
#                          'mode': 'vertical',
#                          'scaleID': 'x-axis-0',
#                          'value': '22',
#                          'borderColor': 'red',
#                          'borderWidth': 2,
#                          'label': {
#                            'position':'top',
#                            'fontStyle':'normal',
#                            'enabled': True,
#                            'content': '999'
#                          }
#                        }, {
#                          'type': 'line',
#                          'mode': 'vertical',
#                          'scaleID': 'x-axis-0',
#                          'value': '08',
#                          'borderColor': 'blue',
#                          'borderWidth': 2,
#                          'label': {
#                            'position':'bottom',
#                            'fontStyle':'normal',
#                            'enabled': True,
#                            'content': '666'
#                          },
#                          'type': 'box',
#                          'xScaleID': 'x-axis-0',
#                          'yScaleID': 'y-axis-0',
#                          'xMin': '00',
#                          'xMax': '02',
#                          'backgroundColor': 'rgba(200, 200, 200, 0.2)',
#                          'borderColor': '#ccc',
#                        }]
#                      } #,
#                      'plugins': {
#                        'datalabels': {
#                          'display': False,
#                          'align': 'bottom',
#                          'backgroundColor': '#ccc',
#                          'borderRadius': 3
#                        }
#                      }
#                    }

        Annotations={
                      'annotation': {
                        'annotations': []
                      }
                    }

        Plugins =   {    
                      'plugins': {
                        'datalabels': {
                          'display': False
                        }
                      }
                    }

#        AnnMax =    {
#                      'type': 'line',
#                      'mode': 'vertical',
#                      'scaleID': 'x-axis-idx',
#                      'value': 4,
#                      'borderColor': 'rgba(128,0,0,0.2)',
#                      'borderWidth': 1,
#                      'label': {
#                        'position':'top',
#                        'fontColor': "#fff",
#                        #'fontSize': 10,
#                        'fontStyle':'normal',
#                        'backgroundColor': 'rgba(128,0,0,0.4)',
#		                    'xPadding': 3,
#		                    'yPadding': 3,
#		                    'cornerRadius': 3,
#                        'enabled': True,
#                        'content': '999'
#                      }
#                    }
#
#        AnnMin =    {
#                      'type': 'line',
#                      'mode': 'vertical',
#                      'scaleID': 'x-axis-idx',
#                      'value': 10,
#                      'borderColor': 'rgba(0,0,128,0.2)',
#                      'borderWidth': 1,
#                      'label': {
#                        'position':'bottom',
#                        'fontColor': "#fff",
#                        'fontStyle':'normal',
#                        'backgroundColor': 'rgba(0,0,128,0.4)',
#		                    'xPadding': 3,
#		                    'yPadding': 3,
#		                    'cornerRadius': 3,
#                        'enabled': True,
#                        'content': '666'
#                      }
#                    }
#        AnnBox =    {
#                      'type': 'box',
#                      'xScaleID': 'x-axis-idx',
#                      'yScaleID': 'y-axis-0',
#                      'xMin': 2,
#                      'xMax': 6,
#                      'backgroundColor': 'rgba(200, 200, 200, 0.2)',
#                      'borderColor': '#ccc'
#                    }
        
        if type(self) in [SimpleLineChart, SimpleBarChart, HorizontalBarChart, \
                           StackedHorizontalBarChart, StackedVerticalBarChart, ScatterChart]:
            self.Cartesian = True            
            self.chart['options'].update(Cartesion)            
            self.chart['options'].update(Annotations)
            #self.add_xaxis()
            #self.add_yaxis()
            # try out modifications
            #self.set_axis_gridlines('x',True)
            #self.set_axis_gridlines('y',True)
            #self.set_axis_gridline_width('x',3)
            #self.set_axis_gridline_width('y',3)
            #self.set_axis_style('x',10)
            #self.set_axis_style('y',10)
            #self.chart['options']['scales']['xAxes'][0]['ticks'].update({'fontSize':10})
            #self.chart['options']['scales']['yAxes'][0]['ticks'].update({'fontSize':10})
            #self.chart['options']['annotation']['annotations'].append(AnnMax)            
            #self.chart['options']['annotation']['annotations'].append(AnnMin)            
            #self.chart['options']['annotation']['annotations'].append(AnnBox)            
 
        if type(self) in [RadarChart, PolarChart]:
            self.Radial = True        
            self.chart['options'].update(Radial)
            # try out modifications
            #self.set_axis_style('x',14,'Arial','red')
            #self.set_axis_gridlines('grid',True)
            #self.set_axis_gridlines('radial',True)
            #self.set_axis_gridline_width('grid',3)
            #self.set_axis_gridline_width('radial',3)
            #self.chart['options'].update({'spanGaps':True})
            
        if type(self) in [SimplePieChart, SimpleDoughnutChart]:
            self.chart['options'].update(Plugins)

        #self.chart['options'].update({'fontSize':6})
        self.chart['type']=self.type_to_url()


        #labels=['Jan','Feb', 'Mar','Apr', 'May','Jan','Feb', 'Mar','Apr', 'May']
        #self.chart['options']['scales']['xAxes'][0]['labels']=labels

    # Inspect chart JSON
    # -------------------------------------------------------------------------
        
    def dump_chart(self, data_class=None):
        return json.dumps(self.chart, indent=2, sort_keys=True)

    # Global options
    # -------------------------------------------------------------------------

    def set_chartpixelratio(self,ratio):
        self.POSTBody.update({'devicePixelRatio':ratio})

    def set_chartsize(self, width, height):
        self.POSTBody.update({'width':width})
        self.POSTBody.update({'height':height})
        
    def set_chartbackground(self,colour):
        self.POSTBody.update({'backgroundColor':colour})

    # URL Generation
    # -------------------------------------------------------------------------
        
    def get_json(self, docroot, data_class=None):
        import requests
        import uuid
        import shutil
         
#        x = {
#              "backgroundColor": "transparent",
#              "devicePixelRatio": 1,
#              "width": self.width,
#              "height": self.height,
#              "format": "png",
#              "chart": json.dumps(self.chart)
#            }
        x = self.POSTBody
        x.update({"width":self.width})
        x.update({"height":self.height})
        x.update({"chart": json.dumps(self.chart)})
        
            
        h = {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Accept': 'application/json'
            }
            
        guid=uuid.uuid1().hex
        filename = guid+'.png'
        pathname = docroot+'/'+guid+'.png'
#        uri = '/img_cache/'+guid+'.png'
        try:
            chart_data = requests.post(self.BASE_URL, data=x, headers=h, stream=True)
        except requests.exceptions.RequestException as e:
            raise JsonPostException(e)
            
# The following code works, but is too slow - keeps timing out. The COPYFILEOBJ method is better        
#        if chart_data.status_code == 200:
#            with open(filename, "wb") as f:
#                for chunk in chart_data:
#                    f.write(chunk)
#                f.close()
        if chart_data.status_code == 200:
            with open(pathname, "wb") as f:
                chart_data.raw.decode_content = True
                shutil.copyfileobj(chart_data.raw, f)
            f.close()
            return filename
        else:
            return str(chart_data.status_code)

        
#    def get_url(self, data_class=None):
        #g_url = self.BASE_URL + "?"
        #g_url = g_url + "w=%i&h=%i" % (self.width, self.height)
        #g_url = g_url + "&devicePixelRatio=1"
        #g_url = g_url + "&c=" + self.chart_json()
        #return g_url
#        return self.BASE_URL + '?' + self.get_url_extension(data_class)# + quote(self.chart_json())
    
#    def get_url_extension(self, data_class=None):
#        url_bits = self.get_url_bits(data_class=data_class)
#        return '&'.join(url_bits)

#    def get_url_bits(self, data_class=None):
#        url_bits = []
        # required arguments
#        url_bits.append("w=%i" % (self.width))
#        url_bits.append("h=%i" % (self.height))
        # optional arguments
#        url_bits.append("devicePixelRatio=1")
        # encode the chart dict
#        url_bits.append("c=" + quote(json.dumps(self.chart)))
#        return url_bits



        
#        # required arguments
#        url_bits.append(self.type_to_url())
#        url_bits.append('chs=%ix%i' % (self.width, self.height))
#        url_bits.append(self.data_to_url(data_class=data_class))
#        # optional arguments
#        if self.title:
#            url_bits.append('chtt=%s' % self.title)
#        if self.title_colour and self.title_font_size:
#            url_bits.append('chts=%s,%s' % (self.title_colour, \
#                self.title_font_size))
#        if self.legend:
#            url_bits.append('chdl=%s' % '%7c'.join(self.legend))
#        if self.legend_position:
#            url_bits.append('chdlp=%s' % (self.legend_position))
#        if self.colours:
#            url_bits.append('chco=%s' % ','.join(self.colours))
#        if self.colours_within_series:
#            url_bits.append('chco=%s' % '%7c'.join(self.colours_within_series))
#        ret = self.fill_to_url()
#        if ret:
#            url_bits.append(ret)
#        ret = self.axis_to_url()
#        if ret:
#            url_bits.append(ret)                    
#        if self.markers:
#            url_bits.append(self.markers_to_url())        
#        if self.line_styles:
#            style = []
#            for index in range(max(self.line_styles) + 1):
#                if index in self.line_styles:
#                    values = self.line_styles[index]
#                else:
#                    values = ('1', )
#                style.append(','.join(values))
#            url_bits.append('chls=%s' % '%7c'.join(style))
#        if self.grid:
#            url_bits.append('chg=%s' % self.grid)
#        return url_bits

    def chart_json(self):
        y=json.dumps(self.chart)
        parsed_json=json.loads(y)
        return json.dumps(self.chart)


    # Downloading
    # -------------------------------------------------------------------------

#    def download(self, file_name=False, use_post=True):
#        if use_post:
#            opener = urlopen(self.BASE_URL, self.get_url_extension().encode('utf-8'))
#        else:
#            opener = urlopen(self.get_url())

#        if opener.headers['content-type'] != 'image/png':
#            raise BadContentTypeException('Server responded with a ' \
#                'content-type of %s' % opener.headers['content-type'])
#        if file_name:
#            open(file_name, 'wb').write(opener.read())
#        else:
#            return opener.read()

    # Generic settings
    # -------------------------------------------------------------------------

    def set_title(self, title):
        """ Enable/Disable the title

        title - boolean    
        """
        self.chart['options']['title'].update({'display':title})
        
    def set_title_text(self, title):
        """ Set the title text

        title - string/array of strings
                array elements are displayed on a new line
        """
        self.chart['options']['title'].update({'text':title})
        
    def set_title_position(self, position):
        """Sets title position. Default is 'top'.

        bottom - At the bottom of the chart
        top    - At the top of the chart
        right  - To the right of the chart
        left   - To the left of the chart
        """
        positions = ['top','left','bottom','right']
        assert (position in positions), "Unknown position"
        
        self.chart['options']['title'].update({'position':position})

    def set_title_style(self, fontSize=12, fontFamily='Arial', fontColor='#666', fontStyle='bold'):
        self.chart['options']['title'].update({'fontSize':fontSize})
        self.chart['options']['title'].update({'fontFamily':fontFamily})
        self.chart['options']['title'].update({'fontColor':fontColor})
        self.chart['options']['title'].update({'fontStyle':fontStyle})

    def set_legend(self, legend):
        """ Enable/Disable the legend

        title - boolean    
        """
        self.chart['options']['legend'].update({'display':legend})
        
    def set_legend_position(self, legend_position):
        """Sets legend position. Default is 'top'.

        bottom - At the bottom of the chart
        top    - At the top of the chart
        right  - To the right of the chart
        left   - To the left of the chart
        """
        positions = ['top','left','bottom','right']
        assert (legend_position in positions), "Unknown position"
        
        self.chart['options']['legend'].update({'position':legend_position})

    def set_legend_style(self, fontSize=12, fontFamily='Arial', fontColor='#666', fontStyle='bold'):
        self.chart['options']['legend']['labels'].update({'fontSize':fontSize})
        self.chart['options']['legend']['labels'].update({'fontFamily':fontFamily})
        self.chart['options']['legend']['labels'].update({'fontColor':fontColor})
        self.chart['options']['legend']['labels'].update({'fontStyle':fontStyle})

           
    # Chart colours
    # -------------------------------------------------------------------------

#    def set_colours(self, colours):
#        # colours needs to be a list, tuple or None
#        assert(isinstance(colours, list) or isinstance(colours, tuple) or
#            colours is None)
#        # make sure the colours are in the right format
#        if colours:
#            for col in colours:
#                _check_colour(col)
#        self.colours = colours

#    def set_colours_within_series(self, colours):
#        # colours needs to be a list, tuple or None
#        assert(isinstance(colours, list) or isinstance(colours, tuple) or
#            colours is None)
#        # make sure the colours are in the right format
#        if colours:
#            for col in colours:
#                _check_colour(col)
#        self.colours_within_series = colours        

    # Background/Chart colours
    # -------------------------------------------------------------------------

#    def fill_solid(self, area, colour):
#        assert(area in Chart.VALID_SOLID_FILL_TYPES)
#        _check_colour(colour)
#        self.fill_area[area] = colour
#        self.fill_types[area] = Chart.SOLID

#    def _check_fill_linear(self, angle, *args):
#        assert(isinstance(args, list) or isinstance(args, tuple))
#        assert(angle >= 0 and angle <= 90)
#        assert(len(args) % 2 == 0)
#        args = list(args)  # args is probably a tuple and we need to mutate
#        for a in range(int(len(args) / 2)):
#            col = args[a * 2]
#            offset = args[a * 2 + 1]
#            _check_colour(col)
#            assert(offset >= 0 and offset <= 1)
#            args[a * 2 + 1] = str(args[a * 2 + 1])
#        return args

#    def fill_linear_gradient(self, area, angle, *args):
#        assert(area in Chart.VALID_SOLID_FILL_TYPES)
#        args = self._check_fill_linear(angle, *args)
#        self.fill_types[area] = Chart.LINEAR_GRADIENT
#        self.fill_area[area] = ','.join([str(angle)] + args)

#    def fill_linear_stripes(self, area, angle, *args):
#        assert(area in Chart.VALID_SOLID_FILL_TYPES)
#        args = self._check_fill_linear(angle, *args)
#        self.fill_types[area] = Chart.LINEAR_STRIPES
#        self.fill_area[area] = ','.join([str(angle)] + args)

#    def fill_to_url(self):
#        areas = []
#        for area in (Chart.BACKGROUND, Chart.CHART, Chart.ALPHA):
#            if self.fill_types[area]:
#                areas.append('%s,%s,%s' % (area, self.fill_types[area], \
#                    self.fill_area[area]))
#        if areas:
#            return 'chf=' + '%7c'.join(areas)

    # DataSet
    # -------------------------------------------------------------------------
        
    def get_dataset(self, index):
        try: 
            return json.dumps(self.chart['data']['datasets'][index])
        except:
            return None
            
    def add_dataset(self, index, data, axis=None,mix_type=None):
        dataset = {'order':index,
                   #'cubicInterpolationMode':'default',
                   #'lineTension':0.4,
                   #'xAxisID':'x-axis-1',
                   #'yAxisID':axis,
                   #'pointStyle':'rectRot',
                   #'pointRadius':0,
                   #'borderColor':'#'+config.color,
                   #'borderWidth':config.thickness,
                   #'borderDash':dash,
                   #'backgroundColor':'#'+fillcolour+"AA",
                   #'fill':fill,
                   'data':data
                  }
                  
        if axis != None:
            axis_type=axis.split('-')[0]
            if axis_type == 'x':
                dataset.update({'xAxisID':axis})
            elif axis_type == 'y':
                dataset.update({'yAxisID':axis})
            
        if mix_type != None:
            dataset.update({'type':mix_type})

        if type(self) in [SimpleLineChart]:
            dataset.update({'lineTension':0.4})

        try:          
            self.chart['data']['datasets'].append(dataset)
            return len(self.chart['data']['datasets']) - 1
        except:
            return False
        
    def set_dataset_label(self, index, label):
        try:
            self.chart['data']['datasets'][index].update({'label':label})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_linestyle(self, index, style):
        try:
            self.chart['data']['datasets'][index].update({'borderDash':style})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_linewidth(self, index, width):
        try:
            self.chart['data']['datasets'][index].update({'borderWidth':width})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_linecolour(self, index, colour):
        try:
            self.chart['data']['datasets'][index].update({'borderColor':colour})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_linetension(self, index, tension=0.4):
        try:
            self.chart['data']['datasets'][index].update({'lineTension':tension})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_fillcolour(self, index, colour):
        try:
            self.chart['data']['datasets'][index].update({'backgroundColor':colour})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_fillstyle(self, index, fill):
        try:
            self.chart['data']['datasets'][index].update({'fill':fill})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_spangaps(self, index, spangaps):
        try:
            self.chart['data']['datasets'][index].update({'spanGaps':spangaps})
        except:
            raise IndexOutOfRangeException("Index out of range")

    # Points
    # -------------------------------------------------------------------------
    def set_dataset_pointstyle(self, index, style):
        styles = ['circle','cross','crossRot','dash','line','rect','rectRounded','rectRot','star','triangle']
        
        assert(style in styles), "unknown point style"

        try:
            self.chart['data']['datasets'][index].update({'pointStyle':style})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_pointsize(self, index, radius):
        try:
            self.chart['data']['datasets'][index].update({'pointRadius':radius})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_pointwidth(self, index, width):
        try:
            self.chart['data']['datasets'][index].update({'pointBorderWidth':width})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_pointcolour(self, index, colour):
        try:
            self.chart['data']['datasets'][index].update({'pointBorderColor':colour})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_pointfillcolour(self, index, colour):
        try:
            self.chart['data']['datasets'][index].update({'pointBackgroundColor':colour})
        except:
            raise IndexOutOfRangeException("Index out of range")


    # Data
    # -------------------------------------------------------------------------

#    def data_class_detection(self, data):
#        """Determines the appropriate data encoding type to give satisfactory
#        resolution (http://code.google.com/apis/chart/#chart_data).
#        """
#        assert(isinstance(data, list) or isinstance(data, tuple))
#        if not isinstance(self, (LineChart, BarChart, ScatterChart)):
#            # From the link above:
#            #   Simple encoding is suitable for all other types of chart
#            #   regardless of size.
#            return AwesomeData
#            #return SimpleData
#        elif self.height < 100:
#            # The link above indicates that line and bar charts less
#            # than 300px in size can be suitably represented with the
#            # simple encoding. I've found that this isn't sufficient,
#            # e.g. examples/line-xy-circle.png. Let's try 100px.
#            return SimpleData
#        else:
#            return AwesomeData
#            #return ExtendedData

#    def _filter_none(self, data):
#        return [r for r in data if r is not None]

#    def data_x_range(self):
#        """Return a 2-tuple giving the minimum and maximum x-axis
#        data range.
#        """
#        try:
#            lower = min([min(self._filter_none(s))
#                         for type, s in self.annotated_data()
#                         if type == 'x'])
#            upper = max([max(self._filter_none(s))
#                         for type, s in self.annotated_data()
#                         if type == 'x'])
#            return (lower, upper)
#        except ValueError:
#            return None     # no x-axis datasets

#    def data_y_range(self):
#        """Return a 2-tuple giving the minimum and maximum y-axis
#        data range.
#        """
#        try:
#            lower = min([min(self._filter_none(s))
#                         for type, s in self.annotated_data()
#                         if type == 'y'])
#            upper = max([max(self._filter_none(s)) + 1
#                         for type, s in self.annotated_data()
#                         if type == 'y'])
#            return (lower, upper)
#        except ValueError:
#            return None     # no y-axis datasets

#    def scaled_data(self, data_class, x_range=None, y_range=None):
#        """Scale `self.data` as appropriate for the given data encoding
#        (data_class) and return it.#
#
#        An optional `y_range` -- a 2-tuple (lower, upper) -- can be
#        given to specify the y-axis bounds. If not given, the range is
#        inferred from the data: (0, <max-value>) presuming no negative
#        values, or (<min-value>, <max-value>) if there are negative
#        values.  `self.scaled_y_range` is set to the actual lower and
#        upper scaling range.
#
#        Ditto for `x_range`. Note that some chart types don't have x-axis
#        data.
#        """
#        self.scaled_data_class = data_class
#
#        # Determine the x-axis range for scaling.
#        if x_range is None:
#            x_range = self.data_x_range()
#            if x_range and x_range[0] > 0:
#                x_range = (x_range[0], x_range[1])
#        self.scaled_x_range = x_range
#
#        # Determine the y-axis range for scaling.
#        if y_range is None:
#            y_range = self.data_y_range()
#            if y_range and y_range[0] > 0:
#                y_range = (y_range[0], y_range[1])
#        self.scaled_y_range = y_range
#
#        scaled_data = []
#        for type, dataset in self.annotated_data():
#            if type == 'x':
#                scale_range = x_range
#            elif type == 'y':
#                scale_range = y_range
#            elif type == 'marker-size':
#                scale_range = (0, max(dataset))
#            scaled_dataset = []
#            for v in dataset:
#                if v is None:
#                    scaled_dataset.append(None)
#                else:
#                    scaled_dataset.append(
#                        data_class.scale_value(v, scale_range))
#            scaled_data.append(scaled_dataset)
#        return scaled_data

#    def add_data(self, data, config):
#        if config.dash is not None:
#            dash = [2,2]
#        else:
#            dash = []
#            
#        if config.area is None:
#           fill=False
#           fillcolour=config.bgcolor
#        else:
#           fill='+1'
#           fillcolour=config.color
#           
#        if config.fill:
#           fill=True
#           fillcolour=config.color
#           
#        dataset = {'order':config.order,
#                   'pointStyle':'rectRot',
#                   'pointRadius':0,
#                   'borderColor':'#'+config.color,
#                   'borderWidth':config.thickness,
#                   'borderDash':dash,
#                   #'backgroundColor':'rgba(128,0,0,0.1)',8D7641
#                   'backgroundColor':'#'+fillcolour+"AA",
#                   'fill':fill,
#                   'data':data
#                  }
#        self.chart['data']['datasets'].append(dataset)
#        self.data.append(data)
#        return len(self.data) - 1  # return the "index" of the data set

#    def data_to_url(self, data_class=None):
#        if not data_class:
#            data_class = self.data_class_detection(self.data)
#        if not issubclass(data_class, Data):
#            raise UnknownDataTypeException()
#        if self.auto_scale:
#            data = self.scaled_data(data_class, self.x_range, self.y_range)
#        else:
#            data = self.data
#        return repr(data_class(data))

#    def annotated_data(self):
#        for dataset in self.data:
#            yield ('x', dataset)

    # Axes
    # -------------------------------------------------------------------------
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    def get_axis(self, query):
        axis = query.split('-')[0]        
        if axis == 'x':
            return self._get_xaxis(query)
        if axis == 'y':
            return self._get_yaxis(query)
        return False
        
    def _get_xaxis(self,query):
       for index, item in enumerate(self.chart['options']['scales']['xAxes']):
          if item['id'] == query:
              return index
       return False
  
    def _get_yaxis(self,query):
       for index, item in enumerate(self.chart['options']['scales']['yAxes']):
          if item['id'] == query:
              return index
       return False

    def add_axis(self, axis, visible=True):
        if self.Cartesian:
            if axis in ('top','bottom','x'):
                index=len(self.chart['options']['scales']['xAxes'])
                id='x-axis-'+str(index)
                self.chart['options']['scales']['xAxes'].append({'id':id})
                self.chart['options']['scales']['xAxes'][index].update({'gridLines':{}})
                #self.chart['options']['scales']['xAxes'][index]['gridLines'].update({'lineWidth':1})
                #self.chart['options']['scales']['xAxes'][index]['gridLines'].update({'zeroLineWidth':3})
                self.chart['options']['scales']['xAxes'][index].update({'ticks':{}})
                self.chart['options']['scales']['xAxes'][index]['ticks'].update({'autoSkipPadding':2})
                #self.chart['options']['scales']['xAxes'][index]['ticks'].update({'display':visible})
                self.chart['options']['scales']['xAxes'][index].update({'labels':[]})
                self.chart['options']['scales']['xAxes'][index].update({'display':visible})
                if axis != 'x':
                    self.chart['options']['scales']['xAxes'][index].update({'position':axis})                
                return id
            if axis in ('left','right','y'):
                index=len(self.chart['options']['scales']['yAxes'])
                id='y-axis-'+str(index)
                self.chart['options']['scales']['yAxes'].append({'id':id})
                self.chart['options']['scales']['yAxes'][index].update({'gridLines':{}})
                #self.chart['options']['scales']['yAxes'][index]['gridLines'].update({'lineWidth':1})
                #self.chart['options']['scales']['yAxes'][index]['gridLines'].update({'zeroLineWidth':3})
                self.chart['options']['scales']['yAxes'][index].update({'ticks':{}})
                #self.chart['options']['scales']['yAxes'][index]['ticks'].update({'autoSkipPadding':2})
                #self.chart['options']['scales']['yAxes'][index]['ticks'].update({'display':visible})
                self.chart['options']['scales']['yAxes'][index].update({'labels':[]})
                self.chart['options']['scales']['yAxes'][index].update({'display':visible})
                if axis != 'y':
                    self.chart['options']['scales']['yAxes'][index].update({'position':axis})                
                return id
        return False
    
    def set_axis_visible(self, axis, visible=True):
        if self.Cartesian:
            axis_type = axis.split('-')[0]
            index = self.get_axis(axis)            
            if axis_type == 'x':
                self.chart['options']['scales']['xAxes'][index].update({'display':visible})
            if axis_type == 'y':
                self.chart['options']['scales']['yAxes'][index].update({'display':visible})
            return axis_type
        if self.Radial:            
            if axis in ('x', 'radial', 'point'):        
                self.chart['options']['scale']['pointLabels'].update({'display':visible})
            if axis in ('y', 'grid', 'data'):        
                self.chart['options']['scale']['ticks'].update({'display':visible})
        return False
        
    def set_axis_style(self, axis, fontSize=12, fontFamily='Arial', fontColor='#666', fontStyle='normal'):
        if self.Cartesian:            
            axis_type = axis.split('-')[0]
            index = self.get_axis(axis)            
            if axis_type == 'x':
                self.chart['options']['scales']['xAxes'][index]['ticks'].update({'fontSize':fontSize})
                self.chart['options']['scales']['xAxes'][index]['ticks'].update({'fontFamily':fontFamily})
                self.chart['options']['scales']['xAxes'][index]['ticks'].update({'fontColor':fontColor})
                self.chart['options']['scales']['xAxes'][index]['ticks'].update({'fontStyle':fontStyle})            
            if axis_type == 'y':
                self.chart['options']['scales']['yAxes'][index]['ticks'].update({'fontSize':fontSize})
                self.chart['options']['scales']['yAxes'][index]['ticks'].update({'fontFamily':fontFamily})
                self.chart['options']['scales']['yAxes'][index]['ticks'].update({'fontColor':fontColor})
                self.chart['options']['scales']['yAxes'][index]['ticks'].update({'fontStyle':fontStyle})
                return axis_type
        if self.Radial:
            if axis in ('x', 'radial', 'point'):        
                #self.chart['options']['scale']['pointLabels'].update({'display':True})
                self.chart['options']['scale']['pointLabels'].update({'fontSize':fontSize})
                self.chart['options']['scale']['pointLabels'].update({'fontFamily':fontFamily})
                self.chart['options']['scale']['pointLabels'].update({'fontColor':fontColor})
                self.chart['options']['scale']['pointLabels'].update({'fontStyle':fontStyle})
            if axis in ('y', 'grid', 'data'):        
                #self.chart['options']['scale']['ticks'].update({'display':True})
                self.chart['options']['scale']['ticks'].update({'fontSize':fontSize})
                self.chart['options']['scale']['ticks'].update({'fontFamily':fontFamily})
                self.chart['options']['scale']['ticks'].update({'fontColor':fontColor})
                self.chart['options']['scale']['ticks'].update({'fontStyle':fontStyle})
            return axis
        return False

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                
    def set_axis_gridlines(self,axis,display):
        #assert(axis_type in Axis.TYPES)
        if self.Cartesian:
            axis_type = axis.split('-')[0]        
            index = self.get_axis(axis)
            if axis_type == 'x':
                self.chart['options']['scales']['xAxes'][index]['gridLines'].update({'display':display})
            if axis_type == 'y':
                self.chart['options']['scales']['yAxes'][index]['gridLines'].update({'display':display})
            return axis_type
        if self.Radial:
            if axis in ('grid','y'):
                self.chart['options']['scale']['gridLines'].update({'display':display})
            if axis in ('angle','radial','x'):
                self.chart['options']['scale']['angleLines'].update({'display':display})
            return axis
        return False
        
    def set_axis_gridline_width(self,axis,width):
        if self.Cartesian:
            axis_type = axis.split('-')[0]        
            index = self.get_axis(axis)
            if axis_type == 'x':
                self.chart['options']['scales']['xAxes'][index]['gridLines'].update({'lineWidth':width})
            if axis_type == 'y':
                self.chart['options']['scales']['yAxes'][index]['gridLines'].update({'lineWidth':width})
                return axis_type
        if self.Radial:
            if axis_type in ('grid','y'):
                self.chart['options']['scale']['gridLines'].update({'lineWidth':width})
            if axis_type in ('angle','radial','x'):
                self.chart['options']['scale']['angleLines'].update({'lineWidth':width})
            return axis
        return False

    def set_axis_zeroline_width(self,axis,width):
        if self.Cartesian:
            axis_type = axis.split('-')[0]        
            index = self.get_axis(axis)
            if axis_type == 'x':
                self.chart['options']['scales']['xAxes'][index]['gridLines'].update({'zeroLineWidth':width})
            if axis_type == 'y':
                self.chart['options']['scales']['yAxes'][index]['gridLines'].update({'zeroLineWidth':width})
                return axis_type
        if self.Radial:
            if axis_type in ('grid','y'):
                self.chart['options']['scale']['gridLines'].update({'zeroLineWidth':width})
            if axis_type in ('angle','radial','x'):
                self.chart['options']['scale']['angleLines'].update({'zeroLineWidth':width})
            return axis
        return False

    # Axis Labels
    # -------------------------------------------------------------------------

    def set_axis_labels(self, axis, values, indexed=False):
        if self.Cartesian and axis is not None:
            idx = []
            if indexed:
                idx = range(0,len(values))
            axis_type = axis.split('-')[0]        
            index = self.get_axis(axis)
            if axis_type == 'x':
                self.chart['options']['scales']['xAxes'][index]['labels']=values
                if indexed:
                    self.chart['options']['scales']['xAxes'][0]['labels']=idx
            if axis_type == 'y':
                self.chart['options']['scales']['yAxes'][index]['labels']=values
                if indexed:
                    self.chart['options']['scales']['yAxes'][0]['labels']=idx
            return axis_type
        if self.Radial or axis is None:            
            self.chart['data']['labels']=values
            return axis
        return False

    def set_axis_labels_suffix(self, axis, suffix):
        callback = r"callback:{function(value) {return '$' + value;}}"
                   
        callback1 = {
                     'callback':{}
                   }
        callback2 = r"function(value) {return '$' + value;}"
        if self.Cartesian and axis is not None:
            pass
        if self.Radial or axis is None:        
            #self.chart['options']['scale'].update({"ticks":{"callback":"function(value) {return value+'%'};"}})
            self.chart['options']['scale']['ticks'].update(callback1)
            self.chart['options']['scale']['ticks']['callback']=callback2
            return axis
        return False
#                    ticks: {
#          callback: function(value) {
#            return '$' + value;
#          }
#        }
 
        
    def set_axis_range(self, axis, low, high, fixed=False):
        axis_type = axis.split('-')[0]        
        index = self.get_axis(axis)
        if axis_type == 'x':
            if low is not None:
                if fixed:
                    self.chart['options']['scales']['xAxes'][index]['ticks']['min']=low
                else:
                    self.chart['options']['scales']['xAxes'][index]['ticks']['suggestedMin']=low
            if high is not None:
                if fixed:
                    self.chart['options']['scales']['xAxes'][index]['ticks']['max']=high
                else:
                    self.chart['options']['scales']['xAxes'][index]['ticks']['suggestedMax']=high
        if axis_type == 'y':
            if low is not None:
                if fixed:
                    self.chart['options']['scales']['yAxes'][index]['ticks']['min']=low
                else:
                    self.chart['options']['scales']['yAxes'][index]['ticks']['suggestedMin']=low
            if high is not None:
                if fixed:
                    self.chart['options']['scales']['yAxes'][index]['ticks']['max']=high
                else:
                    self.chart['options']['scales']['yAxes'][index]['ticks']['suggestedMax']=high
        
#    def set_axis_positions(self, axis_index, positions):
#        try:
#            self.axis[axis_index].set_positions(positions)
#        except IndexError:
#            raise InvalidParametersException('Axis index %i has not been ' \
#                'created' % axis)

#    def set_axis_style_old(self, axis_index, colour, font_size=None, \
#            alignment=None):
#        try:
#            self.axis[axis_index].set_style(colour, font_size, alignment)
#        except IndexError:
#            raise InvalidParametersException('Axis index %i has not been ' \
#                'created' % axis)

#    def axis_to_url(self):
#        available_axis = []
#        label_axis = []
#        range_axis = []
#        positions = []
#        styles = []
#        index = -1
#        for axis in self.axis:
#            available_axis.append(axis.axis_type)
#            if isinstance(axis, RangeAxis):
#                range_axis.append(repr(axis))
#            if isinstance(axis, LabelAxis):
#                label_axis.append(repr(axis))
#            if axis.positions:
#                positions.append(axis.positions_to_url())
#            if axis.has_style:
#                styles.append(axis.style_to_url())
#        if not available_axis:
#            return
#        url_bits = []
#        url_bits.append('chxt=%s' % ','.join(available_axis))
#        if label_axis:
#            url_bits.append('chxl=%s' % '%7c'.join(label_axis))
#        if range_axis:
#            url_bits.append('chxr=%s' % '%7c'.join(range_axis))
#        if positions:
#            url_bits.append('chxp=%s' % '%7c'.join(positions))
#        if styles:
#            url_bits.append('chxs=%s' % '%7c'.join(styles))
#        return '&'.join(url_bits)

    # Markers, Datalabels, Ranges and Fill area (chm)
    # -------------------------------------------------------------------------

    def add_marker(self, mode, content, value, position='center', adjust=0, textcolour='white' , boxcolour='black', linecolour='black', linewidth=2): 
      
        modes = ('x','v','vertical','y','h','horizontal')
        positions = ('top', 'bottom', 'center', 'centre')
        assert(mode in modes), "unknown mode type"
        assert(position in positions), "unknown marker type"
        if mode in ('x','v','vertical'):
            mode = 'vertical'
            scaleID = 'x-axis-0'
            xadjust = adjust
            yadjust = 0
        if mode in ('y','h','horizontal'):
            mode = 'horizontal'
            scaleID = 'y-axis-0'
            xadjust = 0
            yadjust = adjust
            
        marker =    {
                      'type': 'line',
                      'mode': mode,
                      'scaleID': scaleID,
                      'value': value,
                      'borderColor': linecolour,
                      'borderWidth': linewidth,
                      'label': {
                        'position':position,
                        'fontColor': textcolour,
                        #'fontSize': 10,
                        'fontStyle':'normal',
                        'backgroundColor': boxcolour,
                        'xAdjust': xadjust,
                        'yAdjust': yadjust,
		                    'xPadding': 3,
		                    'yPadding': 3,
		                    'cornerRadius': 3,
                        'enabled': True,
                        'content': content
                      }
                    }

        self.chart['options']['annotation']['annotations'].append(marker)            

    def set_datalabels(self,visible):
        try:
            self.chart['options']['plugins']['datalabels'].update({'display':visible})
        except:
            raise InvalidParametersException("Chart does not have datalabels atribute")

    def set_datalabels_style(self, fontSize=12, fontFamily='Arial', fontColor='#666', fontStyle='normal'):
        self.chart['options']['plugins']['datalabels'].update({'color':fontColor})
        self.chart['options']['plugins']['datalabels'].update({'font':{}})
        self.chart['options']['plugins']['datalabels']['font'].update({'family':fontFamily})
        self.chart['options']['plugins']['datalabels']['font'].update({'size':fontSize})
        self.chart['options']['plugins']['datalabels']['font'].update({'style':fontStyle})

    def set_datalabels_border(self, borderRadius=20, borderWidth=1, borderColor=None, backgroundColor=None):
        self.chart['options']['plugins']['datalabels'].update({'borderRadius':borderRadius})
        self.chart['options']['plugins']['datalabels'].update({'borderWidth':borderWidth})
        self.chart['options']['plugins']['datalabels'].update({'borderColor':borderColor})
        self.chart['options']['plugins']['datalabels'].update({'backgroundColor':backgroundColor})
    
    def set_datalabels_align(self, align='center'):
        self.chart['options']['plugins']['datalabels'].update({'align':align})
        #self.chart['options']['plugins']['datalabels'].update({'anchor':anchor})

    def set_datalabels_anchor(self, anchor='center'):
        #self.chart['options']['plugins']['datalabels'].update({'align':align})
        self.chart['options']['plugins']['datalabels'].update({'anchor':anchor})


#@@@@@@@@@@@@@@@@@@@        

    def mumblemumble(self):
        self.chart['options']['plugins']={'datalabels':{}}
        self.chart['options']['plugins']['datalabels']={'display':True}
        self.chart['options']['plugins']['datalabels'].update({'align':'end'})
        self.chart['options']['plugins']['datalabels'].update({'anchor':'center'})
        self.chart['options']['plugins']['datalabels'].update({'backgroundColor':'black'})
        self.chart['options']['plugins']['datalabels'].update({'borderColor':'gray'})
        self.chart['options']['plugins']['datalabels'].update({'borderRadius':25})
        self.chart['options']['plugins']['datalabels'].update({'borderWidth':1})
        self.chart['options']['plugins']['datalabels'].update({'color':'white'})
        self.chart['options']['plugins']['datalabels'].update({'font':{}})
        self.chart['options']['plugins']['datalabels']['font'].update({'family':'Times New Roman'})
        self.chart['options']['plugins']['datalabels']['font'].update({'size':8})
        self.chart['options']['plugins']['datalabels']['font'].update({'style':'italic'})

#        self.chart['data']['datasets'][index]['datalabels']={'display':True}
#        self.chart['data']['datasets'][index]['datalabels'].update({'align':'end'})
#        self.chart['data']['datasets'][index]['datalabels'].update({'anchor':'center'})
#        self.chart['data']['datasets'][index]['datalabels'].update({'backgroundColor':'black'})
#        self.chart['data']['datasets'][index]['datalabels'].update({'borderColor':'gray'})
#        self.chart['data']['datasets'][index]['datalabels'].update({'borderRadius':25})
#        self.chart['data']['datasets'][index]['datalabels'].update({'borderWidth':1})
#        self.chart['data']['datasets'][index]['datalabels'].update({'color':'white'})
#        self.chart['data']['datasets'][index]['datalabels'].update({'font':{}})
#        self.chart['data']['datasets'][index]['datalabels']['font'].update({'family':'Times New Roman'})
#        self.chart['data']['datasets'][index]['datalabels']['font'].update({'size':8})
#        self.chart['data']['datasets'][index]['datalabels']['font'].update({'style':'italic'})





#aaaaaaaa

#    def add_horizontal_range(self, colour, start, stop):
#        self.markers.append(('r', colour, '0', str(start), str(stop)))

#    def add_data_line(self, colour, data_set, size, priority=0):
#        self.markers.append(('D', colour, str(data_set), '0', str(size), \
#            str(priority)))

#    def add_marker_text(self, string, colour, data_set, data_point, size, \
#            priority=0):
#        self.markers.append((str(string), colour, str(data_set), \
#            str(data_point), str(size), str(priority)))        

#    def add_vertical_range(self, colour, start, stop):
#        self.markers.append(('R', colour, '0', str(start), str(stop)))

#    def add_fill_range(self, colour, index_start, index_end):
#        self.markers.append(('b', colour, str(index_start), str(index_end), \
#            '0'))

#    def add_fill_simple(self, colour):
#        self.markers.append(('B', colour, '1', '1', '1'))

    # Line styles
    # -------------------------------------------------------------------------

#    def set_line_style(self, index, thickness=1, line_segment=None, \
#            blank_segment=None):
#        value = []
#        value.append(str(thickness))
#        if line_segment:
#            value.append(str(line_segment))
#            value.append(str(blank_segment))
#        self.line_styles[index] = value

    # Grid
    # -------------------------------------------------------------------------

#    def set_grid(self, x_step, y_step, line_segment=1, \
#            blank_segment=0):
#        self.grid = '%s,%s,%s,%s' % (x_step, y_step, line_segment, \
#            blank_segment)


class ScatterChart(Chart):

    def type_to_url(self):
        return 'cht=s'

class LineChart(Chart):

    def __init__(self, *args, **kwargs):
        if type(self) == LineChart:
            raise AbstractClassException('This is an abstract class')
        Chart.__init__(self, *args, **kwargs)

class SimpleLineChart(LineChart):

    def type_to_url(self):
        return 'line'

class SparkLineChart(SimpleLineChart):

    def type_to_url(self):
        return 'cht=ls'

class XYLineChart(LineChart):

    def type_to_url(self):
        return 'cht=lxy'

class BarChart(Chart):

    def __init__(self, *args, **kwargs):
        if type(self) == BarChart:
            raise AbstractClassException('This is an abstract class')
        Chart.__init__(self, *args, **kwargs)

    # Barchart Specific settings
    # -------------------------------------------------------------------------
    def set_stacked(self,stack,x_axis='x-axis-0',y_axis='y-axis-0'):
        x_axis_type = x_axis.split('-')[0]
        x_index = self.get_axis(x_axis_type)            
        y_axis_type = y_axis.split('-')[0]
        y_index = self.get_axis(y_axis_type)            
    
        self.chart['options']['scales']['yAxes'][y_index].update({'stacked':stack})
        self.chart['options']['scales']['xAxes'][x_index].update({'stacked':stack})
        
    # Dataset
    # -------------------------------------------------------------------------
    def set_dataset_barthickness(self, index, width):
        try:
            self.chart['data']['datasets'][index].update({'barThickness':width})
        except:
            raise IndexOutOfRangeException("Index out of range")

    def set_dataset_maxbarthickness(self, index, width):
        try:
            self.chart['data']['datasets'][index].update({'maxBarThickness':width})
        except:
            raise IndexOutOfRangeException("Index out of range")

class SimpleBarChart(BarChart):

    def type_to_url(self):
        return 'bar'


class HorizontalBarChart(BarChart):

    def type_to_url(self):
        return 'horizontalBar'


class StackedHorizontalBarChart(BarChart):

    def type_to_url(self):
        self.set_stacked(True)
        return 'horizontalBar'


class StackedVerticalBarChart(BarChart):

    def type_to_url(self):
        self.set_stacked(True)
        return 'bar'

class GroupedBarChart(BarChart):

    def __init__(self, *args, **kwargs):
        if type(self) == GroupedBarChart:
            raise AbstractClassException('This is an abstract class')
        BarChart.__init__(self, *args, **kwargs)
        self.bar_spacing = None
        self.group_spacing = None

    def set_bar_spacing(self, spacing):
        """Set spacing between bars in a group."""
        self.bar_spacing = spacing

    def set_group_spacing(self, spacing):
        """Set spacing between groups of bars."""
        self.group_spacing = spacing

    def get_url_bits(self, data_class=None):
        # Skip 'BarChart.get_url_bits' and call Chart directly so the parent
        # doesn't add "chbh" before we do.
        url_bits = BarChart.get_url_bits(self, data_class=data_class,
            skip_chbh=True)
        if self.group_spacing is not None:
            if self.bar_spacing is None:
                raise InvalidParametersException('Bar spacing is required ' \
                    'to be set when setting group spacing')
            if self.bar_width is None:
                raise InvalidParametersException('Bar width is required to ' \
                    'be set when setting bar spacing')
            url_bits.append('chbh=%i,%i,%i'
                % (self.bar_width, self.bar_spacing, self.group_spacing))
        elif self.bar_spacing is not None:
            if self.bar_width is None:
                raise InvalidParametersException('Bar width is required to ' \
                    'be set when setting bar spacing')
            url_bits.append('chbh=%i,%i' % (self.bar_width, self.bar_spacing))
        elif self.bar_width:
            url_bits.append('chbh=%i' % self.bar_width)
        return url_bits


class GroupedHorizontalBarChart(GroupedBarChart):

    def type_to_url(self):
        return 'cht=bhg'


class GroupedVerticalBarChart(GroupedBarChart):

    def type_to_url(self):
        return 'cht=bvg'

    def annotated_data(self):
        for dataset in self.data:
            yield ('y', dataset)


class PieChart(Chart):

    def __init__(self, *args, **kwargs):
        if type(self) == PieChart:
            raise AbstractClassException('This is an abstract class')
        Chart.__init__(self, *args, **kwargs)
        
    # Piechart Specific settings
    # -------------------------------------------------------------------------        
    def set_cutoutPercentage(self, percentage):
        self.chart['options'].update({'cutoutPercentage':percentage})
        
    def set_rotation(self,degrees):
        radians = (-90+degrees) * math.pi/180
        self.chart['options'].update({'rotation':radians})

    def set_circumference(self,degrees):
        radians = degrees * math.pi/180
        self.chart['options'].update({'circumference':radians})

    def set_dataset_backgroundcolour(self, index, colour):
        self.chart['data']['datasets'][index].update({'backgroundColor':colour})

    def set_dataset_borderalign(self, index, align):
        self.chart['data']['datasets'][index].update({'borderAlign':align})
        
    def set_dataset_bordercolour(self, index, colour):
        self.chart['data']['datasets'][index].update({'borderColor':colour})
        
    def set_dataset_borderwidth(self, index, width):
        self.chart['data']['datasets'][index].update({'borderWidth':width})
        
    def set_dataset_weight(self, index, weight):
        self.chart['data']['datasets'][index].update({'weight':weight})
        
    def set_legend_data(self,values):
        self.chart['data']['labels']=values

class SimplePieChart(PieChart):

    def type_to_url(self):
        return 'pie'

class SimpleDoughnutChart(PieChart):

    def type_to_url(self):
        return 'doughnut'


class VennChart(Chart):

    def type_to_url(self):
        return 'cht=v'

    def annotated_data(self):
        for dataset in self.data:
            yield ('y', dataset)


class RadarChart(Chart):

    def type_to_url(self):
        return 'radar'

    # Radarchart Specific settings
    # -------------------------------------------------------------------------
    def set_startangle(self,degrees):
        radians = (-90+degrees) * math.pi/180
        self.chart['options'].update({'startAngle':radians})

    def set_dataset_borderalign(self, index, align):
        self.chart['data']['datasets'][index].update({'borderAlign':align})
        


class PolarChart(Chart):

    def type_to_url(self):
        self.chart['options'].update({'layout':{'padding':5}})
        return 'polarArea'

    # Polarchart Specific settings
    # -------------------------------------------------------------------------
    def set_startangle(self,degrees):
        radians = (-90+degrees) * math.pi/180
        self.chart['options'].update({'startAngle':radians})

    def set_dataset_borderalign(self, index, align):
        self.chart['data']['datasets'][index].update({'borderAlign':align})
        


class SplineRadarChart(RadarChart):

    def type_to_url(self):
        return 'cht=rs'


class MapChart(Chart):

    def __init__(self, *args, **kwargs):
        Chart.__init__(self, *args, **kwargs)
        self.geo_area = 'world'
        self.codes = []
        self.__areas = ('africa', 'asia', 'europe', 'middle_east',
            'south_america', 'usa', 'world')
        self.__ccodes = (
            'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AN', 'AO', 'AQ', 'AR',
            'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF',
            'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BR', 'BS', 'BT',
            'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI',
            'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CX', 'CY', 'CZ',
            'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER',
            'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD',
            'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR',
            'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU',
            'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE',
            'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR',
            'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT',
            'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK',
            'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV',
            'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL',
            'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH',
            'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE',
            'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH',
            'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'ST', 'SV', 'SY',
            'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN',
            'TO', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY',
            'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE',
            'YT', 'ZA', 'ZM', 'ZW')
        
    def type_to_url(self):
        return 'cht=t'

    def set_codes(self, codes):
        '''Set the country code map for the data.
        Codes given in a list.

        i.e. DE - Germany
             AT - Austria
             US - United States
        '''

        codemap = ''
        
        for cc in codes:
            cc = cc.upper()
            if cc in self.__ccodes:
                codemap += cc
            else:
                raise UnknownCountryCodeException(cc)
            
        self.codes = codemap

    def set_geo_area(self, area):
        '''Sets the geo area for the map.

        * africa
        * asia
        * europe
        * middle_east
        * south_america
        * usa
        * world
        '''
        
        if area in self.__areas:
            self.geo_area = area
        else:
            raise UnknownChartType('Unknown chart type for maps: %s' %area)

    def get_url_bits(self, data_class=None):
        url_bits = Chart.get_url_bits(self, data_class=data_class)
        url_bits.append('chtm=%s' % self.geo_area)
        if self.codes:
            url_bits.append('chld=%s' % ''.join(self.codes))
        return url_bits

    def add_data_dict(self, datadict):
        '''Sets the data and country codes via a dictionary.

        i.e. {'DE': 50, 'GB': 30, 'AT': 70}
        '''

        self.set_codes(list(datadict.keys()))
        self.add_data(list(datadict.values()))


class QRChart(Chart):

    def __init__(self, *args, **kwargs):
        Chart.__init__(self, *args, **kwargs)
        #self.BASE_URL = 'http://raspberrypi.smbconsult.local:8080/qr'
        self.BASE_URL = 'http://localhost:8080/qr'
        self.encoding = None
        self.ec_level = None
        self.margin = None
        self.dark = None
        self.light = None
        self.data = []

    def type_to_url(self):
        return ''

    def data_to_url(self, data_class=None):
        if not self.data:
            raise NoDataGivenException()
        return 'text=%s' % quote(self.data[0])

    def set_encoding(self, encoding):
        #pass
        self.encoding = encoding

    def set_ec(self, level):
        levels = ('L','M','Q','H')
        assert level in levels, 'unknown ecLevel'
        self.ec_level = level

    def set_margin(self, margin):
        assert isinstance(margin,int), 'margin must be integer'
        self.margin = margin

    def set_colours(self, dark, light):
        assert not re.search("[^a-fA-F0-9]+", dark)
        assert not re.search("[^a-fA-F0-9]+", light)
        self.dark = dark
        self.light = light
        
    def get_url(self, data_class=None):
        return self.BASE_URL + '?' + self.get_url_extension(data_class)
    
    def get_url_extension(self, data_class=None):
        url_bits = self.get_url_bits(data_class=data_class)
        return '&'.join(url_bits)

    def get_url_bits(self, data_class=None):
        url_bits = []
        url_bits.append('size=%i' % max(self.width,self.height))
        if self.encoding:
            url_bits.append('format=%s' % self.encoding)
        if self.ec_level:
            url_bits.append('ecLevel=%s' % self.ec_level)
        if self.margin:
            url_bits.append('margin=%i' % self.margin)
        if self.dark:
            url_bits.append('dark=%s' % self.dark)
        if self.light:
            url_bits.append('light=%s' % self.light)
        url_bits.append(self.data_to_url(data_class=data_class))
        return url_bits

    def add_data(self, data):
        self.data.append(data)
        return len(self.data) - 1  # return the "index" of the data set

    def download(self, file_name=False, use_post=False):
        if use_post:
            print(self.BASE_URL, self.get_url_extension().encode('utf-8'))
            opener = urlopen(self.BASE_URL, self.get_url_extension().encode('utf-8'))
        else:
            print(self.get_url())
            opener = urlopen(self.get_url())

        if opener.headers['content-type'] != 'image/png' and \
            opener.headers['content-type'] != 'image/svg':
            raise BadContentTypeException('Server responded with a ' \
                'content-type of %s' % opener.headers['content-type'])
        if file_name:
            open(file_name, 'wb').write(opener.read())
        else:
            return opener.read()
