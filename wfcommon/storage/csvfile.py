## Copyright 2009 Laurent Bovet <laurent.bovet@windmaster.ch>
##                Jordi Puigsegur <jordi.puigsegur@gmail.com>
##
##  This file is part of wfrog
##
##  wfrog is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

import os
import os.path
import csv
import time
from datetime import datetime
import sys

class CsvStorage(object):
    '''
    Stores samples in a CSV file. Only supports one TH sensor (number 1).

    [ Properties ]

    path [string]:
        The path to the CSV file.
    '''

    path = None

    columns = [ 'timestamp', 'localtime', 'temp', 'hum', 'wind', 'wind_dir', 'wind_gust', 'wind_gust_dir', 'dew_point', 'rain', 'rain_rate', 'pressure', 'uv_index' ]

    logger = logging.getLogger('storage.csv')

    def write_sample(self, sample, context={}):
        self.logger.debug(sample)
        if os.path.exists(self.path):
            file = open(self.path, 'a')
            writer = csv.writer(file)
        else:
            dir = os.path.realpath(os.path.dirname(self.path))
            if not os.path.exists(dir):
                os.makedirs(dir)
            file = open(self.path, 'w')
            writer = csv.writer(file)
            writer.writerow(self.columns)
            file.flush()

        sample_row = []

        now = sample['localtime']
        sample_row.append(int(time.mktime(now.timetuple()))) # timestamp
        sample_row.append(now.strftime('%Y-%m-%d %H:%M:%S')) # localtime
        for key in self.columns[2:]:
            sample_row.append(sample[key])

        writer.writerow(sample_row)

        self.logger.debug("Writing row: %s", sample_row)

        file.close()

    def keys(self, context={}):
        return ['localtime',
                'temp',
                'hum',
                'wind',
                 'wind_dir',
                'wind_gust',
                'wind_gust_dir',
                'dew_point',
                'rain',
                'rain_rate',
                'pressure',
                'uv_index',
                'utctime']

    def samples(self, from_time=datetime.fromtimestamp(0), to_time=datetime.now(), context={}):
        if not os.path.exists(self.path):
            self.logger.warning("File '"+self.path+"' not found")
            raise StopIteration
        from_timestamp = int(time.mktime(from_time.timetuple()))
        file = self._position_cursor(from_timestamp)
        to_timestamp = time.mktime(to_time.timetuple())
        reader = csv.reader(file)
        counter=0
        try:
            for line in reader:
                counter=counter+1
                if len(line) == 0 or line[0].strip() == '':
                    self.logger.warn('Encountered empty line after '+str(counter)+' lines')
                    continue
                ts = int(line[0])
                if ts < from_timestamp:
                    continue
                if ts >= to_timestamp:
                    raise StopIteration
                sample = line[1:]
                sample[0] = datetime.fromtimestamp(ts)
                length = len(sample)

                for i in range(1,length):
                    if sample[i] != '' and sample[i] != None:
                        sample[i] = float(sample[i])
                    else:
                        sample[i] = None

                sample.append(datetime.utcfromtimestamp(ts))

                yield sample
        finally:
            file.close()

    def _position_cursor(self, timestamp):
        size = os.path.getsize(self.path)
        step = offset = size / 2
        file = open(self.path, 'r')

        while abs(step) > 1:
            last_pos = file.tell()
            if last_pos + offset < 0:
                break

            file.seek(offset, os.SEEK_CUR)
            (current_timestamp, shift) = self._get_timestamp(file)

            if current_timestamp is None:
                file.seek(last_pos)
                break

            pos = file.tell()

            if current_timestamp == timestamp:
                break

            if current_timestamp < timestamp:
                step = abs(step) / 2
            else:
                step = - abs(step) / 2

            offset = step - shift

        return file

    timestamp_length = 10

    def _get_timestamp(self, file):
        skip = file.readline()
        shift = len(skip) + len('\n')
        timestamp_string = file.read(self.timestamp_length)
        if(timestamp_string.strip() == ''): # End of file
            return (None, 0)
        file.seek(-self.timestamp_length, os.SEEK_CUR)
        return ( int(timestamp_string), shift)


def dump(value, context):
    print repr(value)


if __name__ == '__main__':

    s = CsvStorage()

    s.path = '/tmp/wfrog.csv'

    timestamp = int(sys.argv[1])

    f = s._position_cursor(timestamp)

    if f is not None:
        print f.readline()
        f.close()

    s = CsvStorage()

    s.path = '/tmp/wfrog.csv'

    format = "%Y-%m-%d %H:%M:%S"

    samples = s.samples(from_time=datetime.strptime('2010-03-22 22:58:33', format) ,
        to_time=datetime.strptime('2010-03-22 23:00:35', format))

    for i in samples:
        print repr(i)
