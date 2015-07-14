<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>



## Architecture ##

The wfrog architecture involves three functional modules:

  1. The Driver. Reads data from the connected station and sends it to the logger as events.
  1. The Logger. Logs data into a persistent storage (default is CSV file). It also maintains a XML file with the latest current conditions.
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

Note: a common module named `wfcommon` provides the infrastructure shared by the functional modules (storage, units, ...).

## Running the modules in separate processes ##

### Backend and Renderer ###

Without parameters, the `wfrog` command runs all modules in the same process. _(in this case embedded.yaml is used)_
  * To run the backend (i.e. driver+logger) only: `wfrog --backend`
  * To run the renderer only: `wfrog --renderer` _(wfrender/wflogger/config/wfrender.yaml is used)_

### Logger and Driver ###

You can also separate the driver and logger, although it does not makes lot of sense except if you use an external WESTEP driver or use wfrog as a WESTEP driver sending events to another software.

**Using an external WESTEP driver**

Configure wflogger to use a `!stdio-in` or a `!http-in` input. Then run the logger directly with `wflogger/wflogger.py`.

**Using wfrog as WESTEP driver**

Configure wfdriver to use a`!stdio-out` or a `!http-out` output. Then run the driver directly with `wfdriver/wfdriver.py`.

## Preparing the customization ##

In order not to modify directly the configuration in the wfrog distribution (that would be overwritten when upgrading to a new version, for example), run the following command to prepare your custom configuration:

```
sudo wfrog --customize
```

This will prepare the custom configuration under `/etc/wfrog/` by copying the factory default configuration. If not run as root, it will be prepared under `~/.wfrog`.

When a configuration is available at this location, it will be used instead of the factory configuration. It is your custom configuration that you modify.

**Caution**: Once you have customized your configuration, the config directory of the wfrog installation will not be used anymore. Remember that, especially when you upgrade wfrog because it will not update the customized configuration.

## Configuring the station driver ##

### Specifying your station port ###

Serial stations need to communicate via a port. To configure it:

  * Be sure to have [prepared your custom configuration](http://code.google.com/p/wfrog/wiki/CustomizationGuide?ts=1283113562&updated=CustomizationGuide#Preparing_the_customization)
  * Modify the file `wfdriver/config/embedded.yaml` to uncomment and complete the port line under the station line.

## Configuring the renderer ##

### Serve static files with HTTP renderer ###

To make the HTTP render serve other files (e.g. generataed webcam images), simply add to `wfrender/config/embedded.yaml` (or `wfrender.yaml` if renderer running alone) the `static` property defining the URL path under which you want the files served and the `docroot` property pointing to the filesystem directory. Example:

```
renderer: !http
    cookies: [ units ]
    root: !include
        path: default/24hours.yaml
    renderers:
        3hours.html: !include
            path: default/3hours.yaml
        24hours.html: !include
            path: default/24hours.yaml
        30days.html: !include
            path: default/30days.yaml
        365days.html: !include
            path: default/365days.yaml
        check: !include
            path: default/check.yaml
    static: test
    docroot: /home/user/webcam
```

Will serve the content of `/home/user/webcam` under http://localhost:7680/test.

### Make wfrog be reloaded on configuration change ###

This trick allows for avoiding to restart wfrog manually while editing configuration and templates.

  * Install dnotify:
    * `sudo apt-get install dnotify`
  * `dnotify -r -M ~/.wfrog/wfrender -e sh -c "killall wfrog; bin/wfrog -R -d &"`

This will monitor the directory `/.wfrog/wfrender` and restart wfrog each time a file is modified in this directory.

## Using a database storage instead of a CSV file ##
### Firebird ###
#### Needed dependencies ####

```
sudo apt-get install firebird2.0-super    #  Firebird database 2.0 
sudo apt-get install python-kinterbasdb   #  Python Firebird driver
```

Other versions of Firebird (like 2.1) can also be used, as long as their corresponding kinterbasdb driver is also available.

#### Start Database Server ####

```
sudo mkdir -p /var/run/firebird/2.0
sudo dpkg-reconfigure firebird2.0-super
```

#### Create Database and Tables ####

```
sudo mkdir /var/lib/firebird/2.0/data
cd database
isql-fb -u sysdba -p masterkey
SQL> create database 'localhost:/var/lib/firebird/2.0/data/wfrog.db';
SQL> IN db-firebird-0.9.sql;
```

#### Configure the Storage ####

  * Edit `wfcommon/config/storage.yaml` to enable the `!firebird` storage.


### Mysql ###
#### Needed dependencies ####

```
sudo apt-get install python-mysqldb    #  Mysql Python driver 
```

mysql server should be installed and started in the system (or another available system)
TODO: specify how to install and setup mysql if necessary

#### Create Database and Tables ####

```
cd database
mysql --user=root --password=secret
SQL> create database wfrog;
SQL> exit
mysql --user=root --password=secret --database=wfrog < db-mysql-0.3.sql
```

#### Configure the Storage ####

  * Edit `wfcommon/config/storage.yaml` to enable the `!mysql` storage. (check [issue 124](https://code.google.com/p/wfrog/issues/detail?id=124) if your password consits of numbers only)

## Support for multiple TH sensors ##

Multiple sensors are only supported when using database storage (both Firebird and mysql).

### Logger ###

Just uncomment the relevant lines in the table creation script and the additional sensors data will be recorded. I.e. the logger checks the available fields in the database and then records corresponding available sensors.

Additional sensors (inside th and th sensors 2-9) are only supported when using database storage.

### Renderer ###

In order to render additional sensors you need to:

  1. Configure the logger to record these additional sensors (see previous section)
  1. Uncomment the relevant sections in **all** the following files:
  * wfrender/config/default/charts.yaml
  * wfrender/config/default/chart\_accumulator.yaml
  * wfrender/config/default/table\_accumulator.yaml
_Note: wfrender/templates/default/main.html needs to be updated to current version in trunk (the one from 0.8.2. doesn't include the needed changes yet)_

## Install as a Boot-Time Services ##

Steps to make wfrog start and stop automatically on a debian-based system:

  * Only for non-debian installations: Make links to the daemon scripts. Adapt the target path to your wfrog directory.
```
cd /etc/init.d/
sudo ln -s /opt/wfrog/init.d/wfrender 
sudo ln -s /opt/wfrog/init.d/wflogger 
```
  * Make these scripts be called by the system (as root)<br>
Debian:<br>
<pre><code>sudo update-rc.d wfrender defaults 99<br>
sudo update-rc.d wflogger defaults 99<br>
</code></pre>
Fedora/RedHat:<br>
<pre><code>sudo chkconfig httpd --add<br>
sudo chkconfig  httpd  on --level 2,3,5<br>
</code></pre></li></ul>

<h2>Sending pages to a FTP server ##

The default configuration starts an internal web-server on port 7680.

To send the generated page periodically to a FTP site instead of serving it in the internal web-server, you need to uncomment the relevant section of the /etc/wfrog/wfrender/config/wfrender.yaml (or embedded.yaml if using a single wfrog process):

```
        ## Uncomment to publish files by ftp (compatible with http server)
        #ftp: !scheduler
        #    period: 600  # in seconds
        #    delay: 60 # in seconds, delay before start rendering
        #    renderer: !ftp
        #        host: HOST.COM 
        #        username: USERNAME
        #        password: PASSWORD
        #        directory: DIRECTORY
        #        renderers:
        #            3hours.html: !file
        #                path: /tmp/3hours.html
        #                renderer: !include
        #                    path: default/3hours.yaml
        #            24hours.html: !file
        #                path: /tmp/24hours.html
        #                renderer: !include
        #                    path: default/24hours.yaml
        #            30days.html: !file
        #                path: /tmp/30days.html
        #                renderer: !include
        #                    path: default/30days.yaml
        #            365days.html: !file
        #                path: /tmp/365days.html
        #                renderer: !include
        #                    path: default/365days.yaml
        #            ## Uncomment to activate www.meteoclimatic.com ftp publisher
        #            #meteoclimatic.txt: !file
        #            #    path: /tmp/meteoclimatic.txt
        #            #    renderer: !meteoclimatic
        #            #        id: STATION_ID  
        #            #        storage: !service
        #            #            name: storage   
```

Note that you need to inform host, user, password and directory to be used in the ftp connection.

Both http and ftp publishing can coexist.

## Getting Help ##

See the [Configuration Reference](http://www.windmaster.ch/wfrog/doc) for details on configuration elements.

The configuration reference is also available in the builtin help of each module, e.g.:

```
wfdriver/wfdriver.py --help             # General help
wfdriver/wfdriver.py -H                 # List and descriptions of configuration !elements
wfdriver/wfdriver.py -E ELEMENT         # Help on a specific element
```


<p align='right'><img src='http://wfrog.googlecode.com/svn/wiki/images/small-frog.png' /></p>