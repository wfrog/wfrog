import sys, os.path
if __name__ == "__main__": sys.path.append(os.path.abspath(sys.path[0] + '/..'))

from wfdriver import Driver
from output import call

def out(event):
    print '> '+str(event)

call.call = out
Driver.DEFAULT_CONFIG='call-test.yaml'
Driver().run()



