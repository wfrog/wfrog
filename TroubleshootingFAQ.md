<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>

## FAQ ##

**Q: I start wfrog, nothing happens. Where is the graph window?**

A: It is normal behaviour. The wfrog application provides its UI as a web application. Open http://localhost:7680 .

**Q: The graphs are empty and measures show 9999**

A: Graphs are updated every 10 minutes. The values are updated more often (every 10 seconds).
If they stay at 9999, it means that the station is not properly recognized (see below).

**Q: My station seems not to be recognized.**

A: Currently, only WMRS200 and WMR200 are auto-detected. If you have another station model, you need to [Customize the configuration](http://code.google.com/p/wfrog/wiki/CustomizationGuide#Preparing_the_customization) and [specify your station model](http://code.google.com/p/wfrog/wiki/CustomizationGuide#Specifying_your_station_model).

**Q: I don't have any clue what happens inside wfrog**

Three options:

1. Start it with
```
sudo wfrog -v
```

2. To see errors on the console, check the log file: `/var/log/wfrog.log` for INFO level messages.

3. [Customize the configuration](http://code.google.com/p/wfrog/wiki/CustomizationGuide#Preparing_the_customization) and change root log level in ` ~/.wfrog/wflogger/config/wfrog.yaml ` from `info` to `debug` and find the debug messages in `/var/log/wfrog.log`.