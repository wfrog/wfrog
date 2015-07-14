**wfrog 0.8.2 - 18.02.2012**

  * [Fixed issues](http://code.google.com/p/wfrog/issues/list?q=label:Milestone-Release0.8.2)
  * Many small bugs fixed
  * Default template now has tabs for charts and numerical data and a date picker that allows to view history data (only in http mode).
  * Added new native publisher for wetter.com
  * New static file renderer, to be used with ftp or http renderers to publish single static files
  * New native driver for Davis VantagePro2 weather stations.
  * OS-WMR928NX driver now is able to receive multiple TH and T sensors
  * Added support for several temp/hum sensors when using database storage (i.e. firebird or mysql storage).
  * The configuration files now have additional commented out sections to allow easier configuration of:
    * ftp publishing / compatible with http rendering
    * pws, weather underground, wetter.com and meteoclimatic data publishing
    * humidex and wind chill in graphs
    * additional sensors
  * Interior temp and hum now allow units configuration.
  * Fix barometer overflow in WMRS200 driver.
  * Several fixes in WMRS200 driver to improve data reporting and error management.

Upgrade notes: If you have customized your configuration: in order to
have the new settings take effect, you have to upgrade the wfdriver
config files to the latest version and execute wfrog -S.

**wfrog 0.8.1 - 22.03.2011**

Dramatically simplified the configuration by choosing the station in startup settings. Some fixes.

  * [Fixed Issues](http://code.google.com/p/wfrog/issues/list?can=1&q=label%3ARelease0.8.1)
  * WMR200: Corrected decoding of high gust values.
  * WMR928NX: added pressure\_cal parameter in order to be able to calibrate pressure.
  * Fixed sporadic problem creating files under `/root/.wfrog`

_Upgrade notes:_ If you have customized your configuration: in order to have the new settings take effect, you have to upgrade the wfdriver config files to the latest version and execute `wfrog -S`.

**wfrog 0.8 - 04.03.2011**

Many fixes and improvements, added upload to wunderground, numerical data summary and improved support of WH1081-like and VantagePro stations.

  * [Fixed Issues](http://code.google.com/p/wfrog/issues/list?can=1&q=label%3ARelease0.8)
  * Many small bugs fixed.
  * Added upload to Wunderground
  * Added VantagePro support via PyWeather.
  * Added numerical data summary to generated pages.
  * Added support to decode historic data from station memory of WMR200.
  * Consolidated station driver for Fine Offset WH1080, WH1081, WH1090, WH1091, WH2080, WH2081. This also covers all the re-branded weather stations working with EasyWeather.
  * Windows build consolidated.
  * Under Windows, new wfrog data location is now %APPDATA%\Wfrog, _please move former %HOMEDIR%\.wfrog to this location._
  * Make table name configurable in database storages.
  * Fixed logo lost on the right of large screens
  * Fixed pygooglechart dependency version too recent for debian lenny.
  * Added configurable delay to the scheduler (by default 60 secs).
  * Added WESTEP input reading station events from Atom feeds (to support custom web-based stations).

**wfrog 0.7 - 25.08.2010**
> WMR200 driver, .deb packaging, better configurability. **Caution**: The configuration structure has changed since version 0.6. You will have to re-adapt your configuration using wfrog --customize.
  * [Fixed Issues](http://code.google.com/p/wfrog/issues/list?can=1&q=label%3ARelease0.7)
  * Added bootstrap script bin/wfrog to run all wfrog in one single command.
  * Added WMR200 driver.
  * Changed default port to an uncommon one to avoid conflicts (7680).
  * Prepare wfrog config files to optionally allow sending email messages on critical events.
  * Added auto-detect station. In debug mode, if no station is detected, the simulator is used.
  * Made log file and data files default location different if running as root or not.
  * Added init section in config to initialize reused components like storage
  * Fixed major layout problems for IE, Opera and Safari.
  * Made Beaufort digit more legible.
  * Added wind direction on line graph.
  * Added WindChill, HeatIndex and Humidex formulas.
  * Corrected many bugs in slice calculations and chart rendering.
  * Made rain graph accumulative.
  * Made all graphs ignore flat series by default.
  * Added .deb and .rpm packaging.
  * Put settings (former context) into a separate settings.yaml file configurable interactively.
  * New formulas Last and Count.
  * New render datatable, to present textual data.
  * New page to check wfrog status (http://localhost:7680/check).
  * Added --customize option to wfrog script for preparing user custom config/template directory.
  * Correcter bug: wfrender fails (does not find wfcommon modules) when called "python wfrender.py" and must always be called "./wfrender.py".
  * Removed http log on stdout and now logs requests in default log.
  * Performance improvement: slice unit for 365 days is week.


**wfrog 0.6 - 07.06.2010**
> Main feature: Accumulator for rendering able to read from any storage.
  * [Fixed Issues](http://code.google.com/p/wfrog/issues/list?can=1&q=label%3ARelease0.6)
  * Now default storage is CSV, no database installation needed (unless you want it)

**wfrog 0.5 - 28.03.2010**
> Unified configuration, [WESTEP](http://www.westep.org) compliance, new architecture
  * [Fixed Issues](http://code.google.com/p/wfrog/issues/list?can=1&q=label%3AMilestone-Release0.5&colspec=ID+Type+Status+Priority+Milestone+Owner+Summary&cells=tiles)
  * The architecture has been reworked to allow the driver and logger modules to run in separate processes. This enables integrating with drivers written in other languages.
  * All modules now offer full extensibility through an homogeneous YAML configuration system.
  * MySQL and CSV file storages (only wflogger).
  * Generated [Configuration Reference](http://www.windmaster.ch/wfrog/doc/)
  * Changes in the YAML configuration:
    * The element !multi is now generic. Its children must not be named 'renderers' but 'children'.
    * The chart options that took 'on' or 'off' are now taking 'true or false', to be consistent.
    * The chart option y\_margin is now ymargin, to be consistent as well.
    * Changed the !include and !template tags so that the paths are relative to the file where they appear and not from the current working directory.

**wfrog 0.2 - 23.01.2010**
> A stable new version with a simpler db structure and improved error control in the drivers.

**wfrog 0.1 - 24.11.2009**
> Simple but somewhat stable release