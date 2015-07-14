

# Architecture Details #

It is structured in 4 components:


1) driver

- reads / retrieves / receives / etc. data from the weather station and sends part of it (external temperature & humidity, wind, station pressure and rain) to the logger via messages. Optionally the driver can produce an xml file with the current conditions as would be seen on the station console.

2) logger

- Receives the data from the driver and every n minutes writes a new record to the database.

_Comment by Laurent_

I think that there are actually three steps in collecting the data:

i) The driver collects "raw" data at a rate decided by the station and not the same for all sensors. Then it sends this data to

ii) An aggregator which accumulate the data until a "sample" should be issued. A sample is actually the content of a db row. Accumulating means calculating the min max. The time between two samples is precisely the configurable value which is typically 15 min. The accumulator also maintains the current-condition xml file. When the aggregator "issues" samples, it sends them to

iii) The actual logger which simply does inserts in the table.

In my opinion, these three components should have each one its own thread. They communicate though a Queue (in blocking manner). Then, in a further step, we can even imagine running them in different processes, so that they can be deployed remotely, for example. It makes also sense to have a decoupling in the case the driver is developed in another technology. In this latter case, decoupling the driver and aggregator makes the work of writing a new driver very simple.

_End of Comment_

_Comment by Jordi_

I agree that the driver should be a separate process.
Also, I see two advantages of decoupling the aggregator and the database writer might help in having adapters for several databases. It also makes possible to enqueue database writes and thus be able to perform maintenance operations on the database much easily.

_End of Comment_


3) database

- Use real multiuser DBMS, allowing data query from other computers, online backups, etc.

- Keep SQL sentences standard so that most DBMS can be used. So far we have tested Firebird 2.1

- Keep the database simple: 1 table with one record every n minutes (by default 15) plus 1 index. This gives around 35000 rows per year at 15 min. period or 105000 rows per year writting data at 5 min. intervals. In both cases most reasonable queries could be run directly on that table.

- The database units should be metric.

4) renderer & uploader

- Produces any file (html / xml / txt / graphs / etc.) requested by the user containing current data, daily/monthly/yearly aggregates, etc. etc. The renderer obtains the data by accessing to the database, and uploads those files to the requested destinations.

Ideally 1,2 and 4 should be separate OS processes (3 will always be), with separate configs, etc. (this implies using some os mechanism like named pipes, etc. to communicate, which is not that difficult).

# Interprocess communication #

In order to be able to have different process for the logger, driver and renderer we need means of communication between them. The goal is to have the most generic type of communication possible in order to allow processes to run on different machines, different platforms (windows and linux for instance), etc. Here is a proposal that should allow this:

1 ) logger -> renderer

The renderer process extracts all information directly from the database. In order to detect the arrival of new data it can easily query the database every min or 30 sec. with the following select:

SELECT MAX(TIMESTAMP\_UTC) FROM METEO.

Since there is an ascending index such query is fast and light and therefore there's no need to have other means of communication.


2) driver -> logger

Use XMLRPC calls. XMLRPC is a simple RPC protocol without the compatibility issues of SOAP and very easy to implement in Python. Python has the following two modules:

- SimpleXMLRPCServer  (xmlrpc.server in Python 3.0)
- xmlrpcclib  (xmlrpc.client in Python 3.0)

Eventually it would also be possible to write drivers in another language implementing this protocol.

The idea would be to implement the following calls:

report\_rain(total, rate)
report\_wind(dirDeg, avgSpeed, gustSpeed)
report\_barometer(pressure)
report\_temperature(temp, humidity)
report\_uv(uv)

_Comment by Laurent_

I've read your ideas about xmlrpc. I think it is a good idea to provide a XML over HTTP communication channel. However, if we base the internal architecture on Queues and want to describe univoqually the XML interface with a XSD schema, we should maybe prefer a more message-oriented integration. Like simply accept the driver events as schema-defined XML messages POSTed on a SimpleHTTPServer. This way, we could use the same XML messages also if some integration is done through another transport (pipes, files, ...).

In my idea, it would be possible to launch the driver and logger with such commands:
```
wfdriver --station=wmrs200 --device=/dev/usbTTy0 --output=stdout | wflogger --input=stdin
```
Or if we have them on a different machine:
```
wfdriver --station=wmrs200 --device=/dev/usbTTy0 --output=http --url=http://loggerhost:7878/wflogger

wflogger --input=http --port=7878
```

See below the message-oriented alternative.

_End of Comment_

_Comment by Jordi_

It is a good idea to use a message oriented approach instead of using remote calls. It simplifies concurrency and makes it easier to have in the long run more heterogeneous sources of information.

_End of Comment_


## Message-Oriented Alternative ##

In a more message-oriented way, the idea is to pass events instead of performing calls. A typical event would be:

```
event.type = 'temp'
event.sensor = 0
event.value = 15
```

With a corresponding XML representation:
```
<temp>
  <sensor>0</sensor>
  <value>15</value>
</temp>
```

Setting up connectors able to listen evens from stdin or http requires a bit of low-level infrastructure illustrated in: http://code.google.com/p/wfrog/source/browse/trunk/wfrender/test/xmlstream.py

This example file is working and shows boths of these connectors. The XML binding requires lxml:
```
$ easy_install lxml
```

To test the stdin connector:
```
$ cat stream.xml | python xmlstream.py
```

To test the http one:
```
python xmlstream.py -s http
```
and in another shell:
```
wget -t 1 --post-data "<temp><sensor>0</sensor><value>4</value></temp>" http://localhost:8080
```

The example also shows internal decoupling with a blocking queue and local creation of events in the case where the driver would be embedded in the sames python process as the logger.

# Data model #

```
CREATE TABLE METEO
(
  TIMESTAMP_UTC Timestamp NOT NULL,
  TIMESTAMP_LOCAL Timestamp NOT NULL,
  TEMP Numeric(3,1),
  HUM Numeric(3,1),
  WIND Numeric(4,1),
  WIND_DIR Smallint,
  WIND_GUST Numeric(4,1),
  WIND_GUST_DIR Smallint,
  DEW_POINT Numeric(3,1),
  RAIN Numeric(4,1),
  RAIN_RATE Numeric(4,1),
  PRESSURE Numeric(5,1),
  UV_INDEX Smallint,
  CONSTRAINT PK_METEO PRIMARY KEY (TIMESTAMP_UTC)
);

UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'TEMPERATURE (ºC)'  where RDB$FIELD_NAME = 'TEMP' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = '% RELATIVE HUMIDITY'  where RDB$FIELD_NAME = 'HUM' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'WIND AVERAGE SPEED (m./sec.)'  where RDB$FIELD_NAME = 'WIND' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'WIND PREDOMINANT DIRECTION (0º-359º)'  where RDB$FIELD_NAME = 'WIND_DIR' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'WIND GUST SPEED (m./sec.)'  where RDB$FIELD_NAME = 'WIND_GUST' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'WIND GUST DIRECTION (0º-359º)'  where RDB$FIELD_NAME = 'WIND_GUST_DIR' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'DEWPOINT TEMPERATURE (ºC)'  where RDB$FIELD_NAME = 'DEW_POINT' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'RAIN FALL (mm.)'  where RDB$FIELD_NAME = 'RAIN' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'RAIN RATE (mm./hr.)'  where RDB$FIELD_NAME = 'RAIN_RATE' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'ATMOSFERIC PRESSURE (mb.)'  where RDB$FIELD_NAME = 'PRESSURE' and RDB$RELATION_NAME = 'METEO';
UPDATE RDB$RELATION_FIELDS set RDB$DESCRIPTION = 'UV INDEX'  where RDB$FIELD_NAME = 'UV_INDEX' and RDB$RELATION_NAME = 'METEO';
CREATE DESCENDING INDEX IDX_METEO1 ON METEO (TIMESTAMP_LOCAL);
```

Row size is aprox. 40 bytes.


# Database abstaction layer / datasoure refactoring #

Proposal from Jordi following Laurent's proposal in [issue num. 15](http://code.google.com/p/wfrog/issues/detail?id=15)

## Storage abstraction class ##

Layer providing abstraction and unified access to wfrog's data storage. Initially we have database storage and therefore this module is responsible to create the SQLs etc. In the future we could have other storage implementations, e.g. csv flat files.

The idea is that we will have a method to register one or several datasources and then a run() or populate() method. This method would obtain the required data from the database and feed it to the registered datasources which will process it on the fly.

## Datasource classes ##

Layer providing access to the meteorological data through aggregation. A datasource object will be determined by the following initializating parameters:
  * span: e.g. current\_year, current\_month, begin date-end date, begin datetime-end datetime, last n days, etc
  * slice: e.g. year, month, day, minute, hour, etc.
  * optional filters: eg. only data gathered between 00:00 and 08:00, when wind > 10/Km.h, etc.
  * formulas: a set of min, max, avg, tendency, etc. to be calculated of each meteo variable
  * measures:  temperature, pressure, wind chill, etc etc. Some of them might exist in the database while others are the product of formulas. _L: in the current datasource, this is the 'measure' list_

Datasource objects would work, whenever possible, in an incremental way. Each datasource will have a method data\_since() which will be used by the storage abstraction layer to know which data has to be feeded to the datasource on each run. Ideally, only new data since last run will have to be feeded.

_L: I like this idea of incremental feed_

## Measure classes ##

There will be different classes for the measures coming from the station sensors:

  * temperature  (or temperature(1), temperature(2), etc. if several sensors are recorded)
  * humidity  (or humidity(1), humidity(2), etc. if several sensors are recorded)
  * pressure
  * wind speed (avg)
  * wind dir (avg)
  * wind speed (gust)
  * wind dir (gust)
  * rain
  * rain rate

and other measures calculated:

  * wind chill
  * heat index
  * evaporation
  * etc....

_L: This is covered by the new module driver. Check it out (see the simulator)_

_J: What do you mean by this comment? Are wind chill or heat index going to be calculated on the driver instead of the logger? Maybe this should be further explained._

## General schema ##


```
DBFactory <--- Storage     <----Logger ----+
DBObjects      Abstraction                 |
                    |                      |
                    +-- Datasources <-+-- Render ,etc.
                               |
                               +-- Measures ---- Units
```

The idea behind this schema is that each wfrog process (e.g. the renderer) will have a unique instance of the storage abstraction class. _I agree_ Each render will register one or several datasources which in turn will have been initialized with several measures (whith a specific unit request). Whenever a http request is received or the scheduler determines it is time to run, then the storage abstraction is requested to read data from the database and update the datasrouce which will calculate the results for each of the measures registered. Since this datasources would be incremental, only new data will have to be sent to them, and won't be necessary to read all the records of the database each time.

_L: I don't see how we can integrate this in the current renderer architecture, which is hierarchical. Currently, a HTTP request follows a given path in the renderer tree. It must not go through everything, only what is requested. Moreover, updating all datasources potentially makes useless computing (if a datasource slice is set to minutes when the page I request provides only hourly data). This is not a problem for FTP rendering, because one need to generate all, but it is for HTTP responsiveness._

_I would prefer not giving the control to the storage but to each datasource. All datasources have a reference to the storage (which is unique to the process). The storage may provide caching mechanism (through wrapping) in order to avoid fetching the same data for all datasources (or group of) that are called in a same short time. This caching could even be used for writes in the case where the renderer and logger run in the same process. This way, most of the rendering requests will not make any call to the database!_

_There is also a tricky thing to solve with the datasources being stateful: the concurrency. If we lock all datasources during computing, concurrent requests are serialized. If we lock only the concerned datasource, the bottleneck is limited_

_J: I see your point with the hierarchical architecture. Maybe we could run the calculations only for a subset of datasources  instead of all of them. One way could be to have a populate\_datasources method in the Storage class, that takes a set of datasources and populates them. See the API modifications below._

Maybe the instantiation of the storage abstraction class might be controlled by yaml and so have more control on the number of instances, which renders use each class, etc.

The logger would attack directly to the Storage Abstraction layer to register new data and use the datasource to obtain the last 12 h. temperature (this is the only data used by the logger).

## API ##

Here is a proposal of class/method signatures for the datasource and storage in a scenario where datasources have control (in opposite to above where the storage trigger the datasource updates).

### Storage ###

```
class Storage:

    def write_sample(self, sample)
    
    def traverse_samples(self, callback, from_timestamp=ever, to_timestamp=now)
```

A sample is a dictionary corresponding to the table/csv columns. e.g.

```
{ 'temp0': 4.5, 'hum': 45, 'wind': 3.5, 'wind_dir': 22.5, ... }
```

'callback' is a function taking a timestamp-enriched sample as parameter.

### Datasource ###

The datasource updates its state by traversing new samples and computing new slices accordingly.

```
class DataSource

    def execute(self,data={}, context={})

```

It is the same as the current datasource concept in the renderer of wfrog 0.2. It returns a data structure containing the computed series. Example:

```
{
            "temp" : {
                "value" : 3,
                "min" : 1,
                "max" : 6,
                "series" : {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "avg" : [ -1, -0.6, 1, 2.5, None, 4.2, 3.5, 1, 3.2, 3 ],
                    "min" : [ -3, -3.2, -2, 1, None, 3, 1, 0.2, 2.4, 2.8 ],
                    "max" : [ 2, 1.4, 3, 2.8, None, 4.5, 4.6, 4.3, 5, 5  ]
                    }
                },

            "dew" : {
                "value" : 3,
                "series" : {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "avg" : [ -4, -3.8, -3.5, -2, None, 1.2, .3, -0.2, 0, 1],
                    }
                },
            "wind" : {
                "value" : 2.2,
                "max" : 6,
                "deg" : 43,
                "dir" : "NE",
                "series" : {
                    "lbl" : [ "7:00", "8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00" ],
                    "avg" : [ 4, 3.8, None, 1, 1.2, .3, 0.2, 0, 1 , 1],
                    "max" : [ 5, 6, None, 1.3, 1.3, .4, 0.2, 0, 1.2 , 1],
                    "deg" : [ 318, None, 300, 310, 300, 300, 300, 345, 12, 60 ],
                    "dir": [ 'NNW', None, 'NW', 'NW', 'NW', 'NW', 'N', 'NNE', 'NE', 'NE']
                    },
                "sectors" : {
                    "lbl" : ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'],
                    "freq" :  [ 0.2, 0.1, 0.2, 0.05, 0.05, 0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.3 ],
                    "avg" :   [ 0.3, 1, 0.3, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0, 2, 3 ],
                    "max" :  [ 2.1, 2, 0.3, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0,0.0, 0.0, 0.0, 0.0, 0.0, 2.4, 6 ]
                    }
                    
                }                

            }
```



# Configuration #

This is an example of what configuration files of wfrog 0.5 will resemble to. I tried to capture the following:
  * Unification of configuration format (yaml)
  * Driver configuration, transport configuration (local, http)
  * Common configuration (logging, database) with parametrization (process name as log filename).
  * Embedding of driver and logger in same process (in wflogger)
  * Datasource-storage relation (with caching)

```
wfdriver/config/wfdriver.yaml
-----------------------------

station: !wmrs200 {}
#station: !wmr928n { port: COM1 }
output: !service { name: events }    # Use a local service to send events
#output: !http-out { url: http://localhost:8888 }


wflogger/config/wflogger.yaml
-----------------------------

context:
    altitude: 430           # The context is propagated to the aggregator
input: !service               # Use a local service to receive events
    name: events
    instance: !function
#input: !http-in { port: 8888 }
output: !multi
    outputs:        
        aggregator : !aggregator
            period: 300
            storage : !include { path: ../wfcommon/config/storage.yaml }  
            #storage : !local { name: storage, object: path: ../wfcommon/config/storage.yaml }
        current : !currentxml
            path: /tmp/currentconditions.xml
        
logging:
    level: info
    handlers:
        default: !include 
            path: ../wfcommon/config/loghandler.yaml
            variables:
                process: wflogger
        smtp: !smtphandler
            threshold: critical
            address: webmaster@wfrog.org
        
embed:
    wfdriver: { config: ../wfdriver/config/embedded.yaml } # Run the
                                       # driver embedded in the logger
                                       # process. Hence the 'local'
                                       # transport.

wfcommon/config/storage.yaml   
----------------------------

storage: !cache              # wraps the underlying storage in cache
    storage: !mysql { url: mysql://blabla, user: admin, password: bla }
    strategy: FIFO           # replace the oldest item first
    size: 10000              # number of rows to cache
#storage !csv { path: /var/log/wfrog.csv  }


wfcommon/config/loghandler.yaml
-------------------------------

loghandler: !rotating
    path: /var/log/${process}.log
    size: 262144
    backup: 2


wfrender/config/wfrender.yaml
-----------------------------

storages: 
    default: !include { path: ../wfcommon/config/storage.yaml }
...
    renderer: !data
        datasource: !aggregator
            storage: default
            slice: day
            span: 365
            filters:
                noon: !timefilter
                    range: [ 12:00, 12:00 ]
        renderer: ...
...
logging:
    level: info
    handlers:
        default: !include 
            path: ../wfcommon/config/loghandler.yaml 
            variables:
                process: wfrender

```


# Project Structure #

Proposal for the project structure. Taken from http://jcalderone.livejournal.com/39794.html and state-of-the-art on other projects.

```
trunk/           (will be copied to tags/wfrog-0.x and targzipped for release)
   bin/          (bootstrap executable files)
     wfdriver
     wflogger
     wfrender
   wfdriver/
     -base python files-
     station/
        wmrs200.py
        wmr98nx.py
     config/
        -default and sample configuration files-
   wflogger/
     -python files-
     db/
       db.sql  
     config/
        -default and sample configuration files-
   wfrender/
     -python files-
     data/
        -python files-
     renderer/
        -python files-
     templates/
        -builtin templates-
     config/
        -default and sample configuration files-
  README
  setup.py
```

# Units #

_Proposal from Laurent_

There are several places where unit conversion can occur. Especially in the driver and renderer.

I suggest that unit conversion sits in a dedicated module (something like wfcommon).

The rule would be to use only refrence units taken inspired from SI units at the following places:
  * Communication. E.g. between driver and logger
  * Storage in database
Then, conversion would occur only in the driver from the station units to SI and in the renderer from SI to user units.

We have basically the following quantities to measure with the most suitable SI unit and the non-SI units we support.
| **Quantity** | **Reference** | **Supported** |
|:-------------|:--------------|:--------------|
| Temperature  | C             | F             |
| Pressure     | hPa (=mbar)   | mmHg, inHg    |
| Wind speed   | m/s           | km/h, knt, mph, beaufort |
| Rain rate    | mm/h          | in/h          |
| Rain sum     | mm            | in            |

  * Relative humidity is in %, which is not a unit.
  * UV Index is defined as such.