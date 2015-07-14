<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>



# Architecture #

Out-of-the-box, two processes are involved:

  1. The Logger with embedded Driver. Reads data from the USB station, logs data into a CSV file storage. It also maintains a XML file with current conditions.
  1. The Renderer. Reads data from the database and/or the XML file and renders it on a web page, either served by an internal web server or sent on a FTP site.

```
          +--------------+             +--------------+
          |   Station    |             |   Browser    |
          +--------------+             +--------------+
                 |                            ^     ^
                 |                            |     |
          +--------------+                    |     |
          |              |                    |     |
          |   wfdriver   |                    |   +--------------+
          |              |                    |   |   FTP site   |
          +--------------+                    |   +--------------+
                 |                            |       ^
                 | events                     |       |
                 |                            |  HTML |
                 v                            |       |
          +--------------+                +-----------+--+
          |              |                |              |
          |   wflogger   |                |   wfrender   |
          |              |                |              |
          +--------------+                +--------------+
                 |                               ^
                 |         ,-----------.         |
         samples |        (             )        | samples
                 |        |`-----------'|        |
                 +------->|             |--------+
                          |   Storage   |
                          |             |
                           `-----------'
```

# Installation Guide #

## Needed dependencies ##

The dependencies are of two types:
  * Binary packages. We show here how to install them on a debian-based distribution using apt-get.
  * Python eggs installed using 'easy\_install' from pypi setuptools.

**Binaries**
```
sudo apt-get install python2.6             # Python 2.6 or 
#sudo apt-get install python2.5            # Python 2.5
sudo apt-get install python-setuptools     # Python setup tools for `easy_install`
sudo apt-get install firebird2.1-super     # (optional) Firebird database 2.1 or
#sudo apt-get install firebird2.0-super    # (optional) Firebird database 2.0 
sudo apt-get install python-kinterbasdb    # (optional) Python binding for firebird
sudo apt-get install python-cheetah        # Template engine
sudo apt-get install python-lxml           # XML serialization 
sudo apt-get install python-pyusb          # USB (only for WMRS200 station)
sudo apt-get install python-serial         # Serial (only for WMR928NX station)
```

**Python eggs**
```
sudo easy_install pyyaml                   # For reading config files
sudo easy_install pygooglechart            # Chart rendering
sudo easy_install webcolors                # Color names for chart
```

## Download ##

  * Download the wfrog distribution from the [download page](http://code.google.com/p/wfrog/downloads/list) or [checkout from subversion](http://code.google.com/p/wfrog/source/checkout).

## Prepare Database ##

### CSV Files ###

This is the default storage and it requires no installation.

### Firebird 2.0 ###

#### Start Database Server ####

```
sudo mkdir -p /var/run/firebird/2.0
sudo dpkg-reconfigure firebird2.0-super
```

#### Create Database and Tables ####

```
sudo mkdir /var/lib/firebird/2.0/data
isql-fb -u sysdba -p masterkey
cd wflogger/db
SQL> create database 'localhost:/var/lib/firebird/2.0/data/wfrog.db';
SQL> IN db.sql;
```


## Install as a Boot-Time Services ##

Steps to make wfrog start and stop automatically on a debian-based system:

  * Unzip wfrog in `/opt/wfrog`
  * Make links to the daemon scripts (as root)
```
cd /etc/init.d/
ln -s /opt/wfrog/bin/wfrender 
ln -s /opt/wfrog/bin/wflogger 
```
  * Make these scripts be called by the system (as root)
```
update-rc.d wfrender defaults 99
update-rc.d wflogger defaults 99
```

# User Manual #

## Logger and Driver ##

### Configuration ###

Adapt values in

  * `wfcommon/config/storage.yaml` (specify your DB and URL if you use one)
  * `wfcommon/config/loghandler.yaml` (where to write technical log files)
  * `wfdriver/config/wfdriver.yaml` (choose you station)
  * `wflogger/config/wflogger.yaml` (set the station altitude)

See the [Configuration Reference](http://www.windmaster.ch/wfrog/doc) for details on configuration elements.

### Starting the Logger ###

```
cd wflogger
./wflogger.py
```

To start with debug output on the console:
```
./wflogger.py -d
```

## Renderer ##

### Configuration ###

  * Adapt values in `wfrender/config/wfrender.yaml`

## Changing Default Units ##

In `wfrender.yaml`, add a `units:` section in the `context:` section. Example:

```
context:
    units: 
        temp: F
        press: mmHg
        wind: kt
        rain: in     
```

Supported units:
  * temp
    * C
    * F
  * press
    * hPa
    * mmHg
    * inHg
  * wind
    * m/s
    * km/h
    * mph
    * kt
    * bft
  * rain
    * mm
    * in


### Starting the Renderer ###

```
cd wfrender
./wfrender.py
```

To start with debug output on the console:
```
./wfrender.py -d
```


### Internal Web-Server ###

The default configuration starts an internal web-server on port 8080.

### FTP ###

To send the generated page periodically to a FTP site instead of serving it in the internal web-server, replace the following part of the configuration file:

```
renderer: !http
    root: !template
```

with

```
renderer: !scheduler
    period: 120  # in seconds
    renderer: !ftp
        host: myhost.mydomain.com            # where to send the file
        username: myusername
        password: mypassword
        renderers:
            wfrender.html: !file             # The remote filename
                path: /tmp/wfrender.html     # The local one
                renderer: !template         
```

And indent the configuration below so that it is one level below the `render: !template` line.

### Getting Help ###

See the [Configuration Reference](http://www.windmaster.ch/wfrog/doc) for details on configuration elements.

The configuration reference is also available in the builtin help, e.g.:

```
./wfrender.py --help             # General help
./wfrender.py -H                 # List and descriptions of configuration !elements
./wfrender.py -E ELEMENT         # Help on a specific element
```

<p align='right'><img src='http://wfrog.googlecode.com/svn/wiki/images/small-frog.png' /></p>