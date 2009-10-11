from pygooglechart import Chart
from pygooglechart import _check_colour
from pygooglechart import Axis
from pygooglechart import RadarChart
from pygooglechart import SimpleLineChart
import random, yaml

class Test1(object):
    """
    This is a test extension
    """

class TestElement(Test1, yaml.YAMLObject):
    yaml_tag = "!test"

def random_data(points=16, maximum=100):
    return [random.random() * maximum for a in xrange(points)]

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

def simple_random():
    color ='000000'
    bg='FFFFFF'
    size=60

    chart = RadarChart(120, 120, y_range=(0,100) )
    chart.add_data([0] * 2)
    chart.add_data([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,100])
    chart.add_data([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,size*1.5])
    chart.add_data([size,0,0,0,0,0,0,0,0,0,0,0,0,0,size,0])
    chart.add_data([100] * 2)

    #chart.add_fill_range(color, 0, 2)
    chart.set_colours( [bg, 'BBBBBB', color, color, bg] )
    chart.set_axis_labels(Axis.BOTTOM, ['N', '', 'NE', '', 'E', '', 'SE', '', 'S', '', 'SW', '', 'W', '', 'NW', ''])
    chart.set_axis_style(0, 'BBBBBB', 10, 0, 'l', bg);
    chart.set_line_style(1, 1)
    chart.set_line_style(2, 1+size/30)
    chart.set_line_style(3, 1+size/30)
    print chart.get_url()
    chart.download('test.png')

#simple_random()
