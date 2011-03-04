from distutils.core import setup
import py2exe
import glob, os.path

# To build for windows:
# Install from website:
#  python 2.6
#  easy_install
#  cheetah (feisley) 2.2.2
#  pywws -> unzip into python\lib
# Install with easy_install:
#  pyyaml
#  pyserial
#  python-lxml 2.2.2
# Get wfrog source under wfrog\
# copy wfrog\bin\wfrog wfrog\wfrog.py
# copy wfrog\pkg\setup.py wfrog
# cd wfrog
# python setup.py py2exe

def find_data_files(source,target,patterns):
    """Locates the specified data-files and returns the matches
    in a data_files compatible format.

    source is the root of the source data tree.
        Use '' or '.' for current directory.
    target is the root of the target data tree.
        Use '' or '.' for the distribution directory.
    patterns is a sequence of glob-patterns for the
        files you want to copy.
    """
    if glob.has_magic(source) or glob.has_magic(target):
        raise ValueError("Magic not allowed in src, target")
    ret = {}
    for pattern in patterns:
        pattern = os.path.join(source,pattern)
        for filename in glob.glob(pattern):
            if os.path.isfile(filename):
                targetpath = os.path.join(target,filename)
                print targetpath
                path = os.path.dirname(targetpath)
                ret.setdefault(path,[]).append(filename)
    return sorted(ret.items())


setup(console=['wfrog.py'],         
      data_files=find_data_files('','',[
                    'wfcommon/config/*',
                    'wfdriver/config/*',
                    'wflogger/config/*',
                    'wfrender/config/*',
                    'wfrender/config/default/*',
                    'wfrender/templates/default/*'
                    ]),
      options={
                "py2exe":{
                    "includes" : ["lxml._elementpath", "gzip", "Cheetah.DummyTransaction"],
                    "bundle_files" : 2

                        }
                }

)
