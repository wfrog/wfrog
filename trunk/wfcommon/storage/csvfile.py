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

import os.path
import csv
import time

class CsvStorage(object):
    '''
    Stores samples in a CSV file.
    
    [ Properties ]
    
    path [string]:
        The path to the CSV file.
    '''

    path = None

    columns = [ 'timestamp', 'localtime', 'temp', 'hum', 'wind', 'wind_dir', 'wind_gust', 'wind_gust_dir', 'dew_point', 'rain', 'rain_rate', 'pressure', 'uv_index' ]
    
    logger = logging.getLogger('storage.csv')
    
    def write_sample(self, sample, context={}):
        if os.path.exists(self.path):
            file = open(self.path, 'a')
            writer = csv.writer(file)
        else:
            file = open(self.path, 'w')                
            writer = csv.writer(file)
            writer.writerow(self.columns)
            file.flush()
        
        sample_row = []
        for key in self.columns:
            if key == 'timestamp':
                value = int(time.mktime(sample[key]))
            elif key == 'localtime':
                value = time.strftime('%Y-%m-%d %H:%M:%S', sample['timestamp'])
            else:
                value = sample[key]    
            sample_row.append(value)
            
        writer.writerow(sample_row)
        
        self.logger.debug("Writing row: %s", sample_row)
        
        file.close()
        
            
