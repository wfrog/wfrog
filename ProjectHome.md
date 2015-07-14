<p align='right'><a href='http://code.google.com/p/wfrog/downloads/list?can=2&q=OpSys%3DWindows'><img src='http://wfrog.googlecode.com/svn/wiki/images/windows_logo.png' border='0' /></a>   <a href='http://code.google.com/p/wfrog/downloads/list?can=2&q=OpSys%3DLinux'><img src='http://wfrog.googlecode.com/svn/wiki/images/linux_logo.png' border='0' /></a></p><p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' />
<br />
</p>
<p align='center'><b>
<a href='InstallationGuide.md'>Documentation</a> | <a href='SupportedStations.md'>Supported Stations</a> | <a href='SeeItInAction.md'>Online User Stations</a> | <a href='http://code.google.com/p/wfrog/downloads/list'>Download</a> | <a href='http://groups.google.com/group/wfrog-users'>User Forum</a> | <a href='ReleaseNotes.md'>Release Notes</a> | <a href='Contribute.md'>Contribute</a></b>
</p>

**wfrog** is a web-based weather station software with nice charts and many ways to publish them on the web, and much more...

The architecture is meant to be very easy to add support for other weather station models and allow for rendering the weather data in several formats and medias using an extensible renderer structure.

The processing and memory footprint of wfrog is very low, making it suitable to run on low-power equipment like PC-engine Alix, Cisco NLSU2 or SheevaPlug.

Currently supported weather stations:
  * Ambient Weather WS1080
  * Davis VantagePro, VantagePro2
  * Elecsa AstroTouch 6975
  * Fine Offset Electronics WH1080, WH1081, WH1090, WH1091, WH2080, WH2081
  * Freetec PX1117
  * LaCrosse 2300 series
  * Oregon Scientific WMR100N, WMR200, WMRS200, WMR928X
  * PCE FWS20
  * Scientific Sales Pro Touch Screen Weather Station
  * Topcom National Geographic 265NE
  * Watson W8681
  * Any station using the [WESTEP protocol](WeatherStationEventProtocol.md)

Currently supported weather data publishers:
  * www.wunderground.com
  * www.pwsweather.com
  * www.meteoclimatic.com
  * www.wetter.com
  * www.openweathermap.org

Tested on Linux, alpha stage on Windows and may work on OS X.

<img src='http://wfrog.googlecode.com/svn/wiki/images/graphs.png' />