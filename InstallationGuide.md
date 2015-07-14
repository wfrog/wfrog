<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>
## <img src='http://wfrog.googlecode.com/svn/wiki/images/ubuntu_logo.png' /> Debian, Ubuntu, Linux Mint ##
_In fact, this will work with any debian based Linux distribution_
  * Download and install the latest wfrog package **.deb** file from the [download page](http://code.google.com/p/wfrog/downloads/list?can=2)
  * Plug your station and [check notes about your station model](SupportedStations.md).
  * Run `sudo wfrog` and answer the questions.
  * Open http://localhost:7680/

## <img src='http://wfrog.googlecode.com/svn/wiki/images/linux_logo.png' /> Other Linux Distributions ##

  * Download and decompress the latest **.tgz** wfrog distribution from the [download page](http://code.google.com/p/wfrog/downloads/list?can=2&q=OpSys%3DLinux) or [checkout from subversion](http://code.google.com/p/wfrog/source/checkout).
  * Install the dependencies
```
sudo easy_install cheetah                  # Template engine
sudo easy_install lxml                     # XML serialization 
sudo easy_install pyusb                    # (optional) If your station is USB
sudo easy_install pyserial                 # (optional) If your station is serial
sudo easy_install pyyaml                   # For reading config files
sudo easy_install pygooglechart            # Chart rendering
```
  * Plug your station and [check notes about your station model](SupportedStations.md)
  * Run `sudo bin/wfrog` and answer the questions.
  * Open http://localhost:7680/

## <img src='http://wfrog.googlecode.com/svn/wiki/images/windows_logo.png' /> Windows ##

  * Download and install the latest win32 wfrog zip file from the [download page](http://code.google.com/p/wfrog/downloads/list?can=2&q=OpSys%3DWindows)
  * Plug your station and [check notes about your station model](SupportedStations.md).
  * Run `wfrog.exe` and answer the questions.
  * Open http://localhost:7680/

If you want to build wfrog for windows yourself, click [here](BuildOnWindows.md)

<p align='right'><img src='http://wfrog.googlecode.com/svn/wiki/images/small-frog.png' /></p>