import os,sys
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__": sys.path.append(os.path.abspath(sys.path[0] + '/../..'))

import wfrender.datasource.accumulator
import wfcommon.storage.csvfile
import wfcommon.storage.simulator

a = wfrender.datasource.accumulator.AccumulatorDatasource()

a.slice = 'day'
a.span = 4
#a.storage = wfcommon.storage.csvfile.CsvStorage()
#a.storage.path = '../../wflogger/test/wfrog.csv'

a.storage = wfcommon.storage.simulator.SimulatorStorage()
a.storage.seed = 4

print repr(a.execute( data={ 'time_end': '2010-03-25Z12:00:00' }))

print repr(a.execute( data={ 'time_end': '2010-03-26Z12:00:00' }))

print repr(a.execute( data={ 'time_end': '2010-03-26Z12:00:00' }))
