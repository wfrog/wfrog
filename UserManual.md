<p align='center'><img src='http://wfrog.googlecode.com/svn/wiki/images/logo-web.png' /></p>



## Troubleshooting ##

When running wfrog on the command line without parameters, the errors are logged only in the `/var/log/wfrog.log` file.

You can make wfrog issue these messages on the standard output with

```
sudo wfrog -v
```

## Trying wfrog before buying a station ##

You can figure out what wfrog looks like even without station.

Choose the {{random-simulator - Station Simulator}} station driver in the settings (see below).

This is useful during the very development of wfrog, to test configuration and can also give an idea how wfrog works if we don't have any station (yet).

## Changing the settings ##

At first run of wfrog, the settings are interactively setup. You can re-enter them with:

```
sudo wfrog -S
```

## Running wfrog as user or root ##

The usual way is to run wfrog as root. You may want however to test some configuration or for any other reason run wfrog under a different user.

Here are the differences between running as root or as a user:

### As root ###

  * Data are located in `/var/lib/wfrog`
  * Settings are located in `/etc/wfrog/settings.yaml`
  * Custom configuration is located in `/etc/wfrog/`.
  * Logs are located in `/var/log`

### As user ###

  * Data are located in `~/.wfrog/data`
  * Settings are located in `~/.wfrog/settings.yaml`. If absent, wfrog uses the ones in `/etc/wfrog/settings.yaml`
  * Custom configuration is located in `~/wfrog/`. If absent, and a custom configuration exists in `/etc/wfrog`, this latter is used.
  * Logs are located in `~/.wfrog`