<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>



# Introduction #

The wfrog software is likely to be run on a low-consumption PC like an [Alix](http://www.pcengines.ch) board

There are not many alternatives in chosing an OS for such devices. One that seems appropriate is [Voyage Linux](http://linux.voyage.hk/) because it is debian-based and offers easy installation of dependency packages (see [Documentation](Documentation.md)).

Voyage Linux is based on Debian Etch, which is:
  * good because it is proven very stable
  * bad because it offers some outdated software packages like Python 2.4 instead of 2.5, which is required by wfrog.

This guide is an attempt to collect installation steps of needed dependencies on Voyage
Linux.

# Guide #

## Preparing Voyage Linux ##

You may want to get rid of the read-only mount of / in order to write the data on the disk. For that, change `/etc/init.d/mountall.sh`.

## Python 2.5 ##

```
apt-get install python2.5
```

Then relink `/usr/bin/python` to `python2.5`

You can install the setup tools (easy\_install) from http://pypi.python.org/pypi/setuptools/

Then you will have to use `easy_install2.5` or relink `easy_install` to it.

## Firebird ##

  * Activate the backports repository by adding to `/etc/apt/sources`:
```
deb http://www.backports.org/debian etch-backports main contrib non-free
```
  * Add a package pinning to `/etc/apt/preferences`
```
Package: firebird2.0-super
Pin: release a=etch-backports
Pin-Priority: 999
```
  * Get the `python-kinterbasdb` manually from the lenny repository: http://packages.debian.org/fr/lenny/python/python-kinterbasdb
  * Install it with `--force-depends`

## Cheetah ##

The binary package is too old. You have to install the pure python package with:
```
easy_install2.5 cheetah
```