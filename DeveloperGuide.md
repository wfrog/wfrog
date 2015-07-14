<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>



## Generating the configuration reference HTML pages ##

```
cd wfcommon/gendoc/
./gendoc.sh
```

It creates a `doc/` directory.

## Writing a station driver ##

### The `Station` interface ###

A station class must implement the following method:
```
   def run(self, generate_event, send_event)
```

The station class is responsible of connecting to the station, managing its own loop and issuing events via the `generate_event` and `send_event` callbacks.

Notes: It must have a class comment to be documented in the -H help.

### Events ###

Event objects are constructed using the `generate_event` callback. The only parameter is the type of the event (temp, hum, ...) as in the [WESTEP](WeatherStationEventProtocol.md) specification.

For structured events, use the `create_child` method.

### Example ###

This is an example behaving like the simulator station provided in wfrog. It illustrate how to create events and send them.

```
import time
import random
import copy


def detect():
    return MyStation()

class MyStation(object):

    '''
    Simulates a station. Issues events randomly with random variations.
    '''

    name = "My Station"

    types = [ 'temp', 'press', 'hum', 'rain', 'wind', 'uv', 'rad' ]
    init_values = [ 10, 1020, 65, 10, [ 3, 180], 1, 2 ]
    range = [ 30, 100, 40, 20, [6, 360], 5, 4 ]

    rain_total = 55

    def new_value(self, current, init, range):
        step = random.random()*(range/8.0) - range/16.0
        dev = current-init # deviation from init
        delta = round(step-dev/16.0,1) # encourage keeping around init
        new = current + delta
        # keep in range
        if new < init -range/2.0:
            new = init - range/2.0
        if new > init + range/2.0:
            new = init + range/2.0
        return new

    def run(self, generate_event, send_event):
        current_values = copy.copy(self.init_values)

        while True:
            t = random.randint(0,len(self.types)-1)
            type = self.types[t]
            e = generate_event(type)

            if type == 'temp' or type=='hum':
                e.sensor = random.randint(0,1)
            if type == 'wind':
                current_values[t][0] = self.new_value(current_values[t][0], self.init_values[t][0], self.range[t][0])
                current_values[t][1] = self.new_value(current_values[t][1], self.init_values[t][1], self.range[t][1])
                e.create_child('mean')
                e.mean.speed=current_values[t][0]
                e.mean.dir=current_values[t][1]
                e.create_child('gust')
                e.gust.speed=current_values[t][0] + random.randint(0,2)
                e.gust.dir=current_values[t][1]
            else:
                current_values[t] = self.new_value(current_values[t], self.init_values[t], self.range[t])
                if type == 'rain':
                    e.rate = current_values[t]
                    e.total = self.rain_total
                    self.rain_total = self.rain_total + random.randint(0,2)
                elif type == 'uv':
                    e.value = abs(int(current_values[t]))
                else:
                    e.value = current_values[t]

            send_event(e)
            time.sleep(2)
```

### Making it configurable in yaml files ###

To make it usable in the wfdriver configuration, declare the following class (typically in the `__init__.py` file):

```
class YamlMyStation(mystation.MyStation, yaml.YAMLObject):
    yaml_tag = u'!mystation'
```

### Auto-detect feature ###

You can enable auto-detect for your station, e.g. based on USB vendor/product ids.

The station class must be alone in its python module and the following defined at module level:

```
def detect():
```
Must return a station object or None if not detected.

```
name
```
Contains the name displayed by the auto-detect code.

You need then to register it into the the auto-detect list (typically in the `__init__.py` file):

```
auto.stations.append(mystation)
```

### Packaging outside of wfrog ###

If you want to develop/package your station driver outside of the wfrog directory, you can use the extension mechanism.

```
export PYTHONPATH=/path/to/my/driver/python/module/called/mydriver
./wfdriver.py -e mydriver
```

### Submit your station driver ###

We are very welcoming station drivers contribution and will open commiter accounts for those wanting to maintain them themselves.

## Making a release of wfrog ##

Make sure that the version number is correct in trunk's `wfcommon/config.py`

In order to build a debian package, you should have these requirements installed (currently tested on Ubuntu 10.10, should work on Debian lenny/squeeze, too).

```
apt-get update
apt-get install tar subversion devscripts debhelper
```

_Postfix installmode -> 'No configuration'._

Download _/trunk/pkg/make-release.sh_ and save it.

Now, simply run it:

```
sh make-release.sh
```

This will guide you step by step through the release process. It is interruptable anytime:

  1. Get a fresh checkout of the project
  1. Build the .tgz and .deb packages
  1. Upload them on google code

Of course, you will need commit permission on the SVN to do a upload to Googlecode, if you dont have the rights, simply press Ctrl+C if the installer is done with building the .deb

<p align='right'><img src='http://wfrog.googlecode.com/svn/wiki/images/small-frog.png' /></p>