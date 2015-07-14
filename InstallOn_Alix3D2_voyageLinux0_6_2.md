<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>



# Introduction #

Following is how I set up voyage linux 0.6.2 and wfrog working in a PC Engines ALIX 3D2 board in the hope it might be useful for other people. I suppose similar instructions apply for any other ALIX board.

# Installing voyage linux on the CF card #

I installed voyage linux 0.6.2, the latest stable version at the moment. Mainly follow instructions from voyage wiki page:

http://linux.voyage.hk/content/getting-started-v06x

Since the database server needs to be able to write to the CF card we will create two partitions, first bootable with 250Mb or more for the system, and the rest of the CF cart (in my case 750Mb) for the firebird database. Then just proceed with the installation using partition 1.

Once the installation is finished we can prepare also the data partition (assuming CF is /dev/sdb):

```
$ sudo /sbin/mkfs -t ext2 /dev/sdb2
$ sudo tune2fs -c 0 /dev/sdb2 -L DATAFS
```

# Configuring the operating system #

Remember to change the root password!

## Network ##
voyage should automatically connect to the network using DHCP. In my case DHCP failed. I prefered a static interface, so I edited /etc/network/interfaces:
```
iface eth0 inet static
        address 192.168.1.25
        netmask 255.255.255.0
        broadcast 192.168.1.255
        gateway 192.168.1.1
```

And also edited /etc/resolv.conf to specify my internet provider nameservers:

```
nameserver xxx.xxx.xxx.xxx
nameserver xxx.xxx.xxx.xxx
```

File /etc/hosts should contain at least:

```
127.0.0.1 localhost
```

## Host name ##

If we like, we can change the host name:

```
$ hostname -v wfrog
$ echo wrog > /etc/hostname
```

## Set the timezone (internal clock is UTC) ##

```
$ echo > /etc/timezone
$ dpkg-reconfigure tzdata
```

## Watchdog configuration ##

Edit /etc/watchdog.conf to check for wfrog processes:

```
watchdog-device = /dev/watchdog
interval = 15

max-load-1 = 24
max-load-5 = 18
max-load-15 = 12

pidfile = /var/run/wflogger.pid
pidfile = /var/run/wfrender.pid

file = /var/log/messages
```

## Clock sync ##

It is important that our clock is correctly synchronized, so that the measures are correctly written to the database.

### Install adjtimex ###

```
$ apt-get install adjtimex
```

At any point it is possible to rerun the configuration:

```
$ rm /etc/default/adjtimex 
$ adjtimexconfig
Comparing clocks (this will take 70 sec)...done.
Adjusting system time by -2028.8 sec/day to agree with CMOS clock...done.
```

### Install nptd service ###

Install this service using:

```
$ apt-get install ntpd
```

Now we can select geographically close servers (http://psp2.ntp.org/bin/view/Servers/StratumOneTimeServers) and add them to /etc/ntp.conf. ntpdate-debian which is run at boot time will automatically use the servers configured in ntp.conf.  Then ntpd will keep the clock in sync with a minimal bandwith usage.

We can see the actual offset with:

```
$ ntpdate-debian -q 
```

And deactivate nptdate call on if-up to prevent interference with ntpd:

```
$ cat /etc/network/if-up.d/ntpdate 
#!/bin/sh

exit 0

[...]
```

# Installing wfrog dependencies #

First we need to run `apt-get update` to read all package lists. Then we can follow wfrog installation instructions. Just take into account that package python-pyusb is now python-usb. We will use python 2.5 and firebird 2.0.

I also installed nano, the text editor I happen to use most:

```
apt-get install nano
```


# Cleaning up #

I removed several packages which are not going to be used (asuming the ALIX box is connected through a cable to the router):

```
$ apt-get remove dnsmasq dnsmasq-base
$ apt-get remove hostapd hostap-utils
$ apt-get remove madwifi-tools madwifi-modules-2.6.26-486-voyage
$ apt-get remove ppp pptpd bcrelay
$ apt-get remove wireless-tools
$ apt-get remove wpasupplicant
$ apt-get upgrade
$ apt-get autoremove
$ remove.docs 
```

# Configuring firebird database #

## Temporal files ##

We need to make sure temporal files go to /tmp (a tmpfs filesystem). So we edit /etc/firebird/2.0/firebird.conf and uncomment the temp directory line:

```
TempDirectories = /tmp
```

## Mounting data partition ##

To mount the data partition, first we will rename /var/lib/firebird/2.0/ directory and create the mounting point

```
$ cd /var/lib/firebird/
$ mv 2.0 2.0_tmp
$ mkdir 2.0
```

Then we edit /etc/fstab  adding the following line:

```
/dev/hda2	/var/lib/firebird/2.0/	ext2	defaults,noatime,rw	0	0
```

And finally we can mount the data partition and move the existing firebird files:

```
$ mount /dev/hda2
$ mv 2.0_tmp/* 2.0
$ rmdir 2.0_tmp
```

Then we can reboot and reconfigure firebird package which should work now without problems when the main system partition is read only.


## Moving the database from and old system ##

In case we already have a wfrog running and want to move the existing database, this is a good way to do it. We should do it from another system over the network. This way we reduce the writting to the CF (substitute newhost and oldhost with the corresponding IPs):

```
$ gbak -v -t -user SYSDBA -password "masterkey" oldhost:/var/lib/firebird/2.0/data/wfrog.db wfrog.fbk
$ gbak -v -rep -use_all_space -user SYSDBA -password "masterkey" wfrog.fbk newhost:/var/lib/firebird/2.0/data/wfrog.db
```

## Improving database space usage ##

Since our database will always grow up, we can configure firebird to use full pages instead of reserving blank space. This way we should reduce the space occupied by the database:

```
gfix -use full localhost:/var/lib/firebird/2.0/data/wfrog.db -user sysdba -password masterkey
```