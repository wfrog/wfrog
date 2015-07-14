You can build wfrog yourself, using the wfrog win-build helper. It downloads all necessary dependencies and install them. After the installation of alls necessary tools, the helper can huod wfrog.



# How can I build wfrog on windows? #
It's now very easy ;)

  1. Download the **complete** "windows" folder from /trunk/pkg
  1. run setup.bat
  1. Follow the instructions on the screen.

The setup.bat download the necessary files and download the latest /trunk to build wfrog for windows.

The tool has an integrated update-check, so you can always use the latest version of it.

## What software is being installed? ##
These dependencies are being installed:

  * Python 2.6
  * SlikSVN
  * easy\_install
  * Cheetah
  * LibUSB
  * Py2EXE
  * PyYAML
  * PyWWS
  * PyGoogleChart
  * lxml (over easy\_install)
  * PySerial
  * PyUSB
  * Cheetah's namemapper.pyd

## Tested stations ##
These stations are successfully installed over this program:

  * WMRS200

Your station is working over this tool, too? Let us know!

# Problems #
## Some downloads are not working anymore! ##
Try it again or report this problem, we'll have a look at this.

## I have suggestions/problems ##
Please open a ticket and describe your suggestion/problem.