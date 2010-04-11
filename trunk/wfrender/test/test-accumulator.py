import os,sys
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__": sys.path.append(os.path.abspath(sys.path[0] + '/../..'))

import wfrender.datasource.accumulator
import wfcommon.storage.csvfile

a = wfrender.datasource.accumulator.AccumulatorDatasource()

a.slice = 'month'
a.span = 2
a.storage = wfcommon.storage.csvfile.CsvStorage()
a.storage.path = '../../wflogger/test/wfrog.csv'

print repr(a.execute( data={ 'time_end': '2010-03-25' }))

print repr(a.execute( data={ 'time_end': '2010-03-26' }))

print repr(a.execute( data={ 'time_end': '2010-03-26' }))
