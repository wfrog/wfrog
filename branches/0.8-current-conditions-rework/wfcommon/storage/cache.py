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

from collections import deque

class CacheStorage(object):

    storage = None

    retention = 60

    # caution lobal !!!
    cache = deque()

    def write_sample(sample):
        self.cache.append(sample)
        self.storage.write_sample(sample)

    def samples(from_time, to_time):
        now = datetime.datetime.now()
        trunc_time = now - datetime.timedelta(self.retention)
        trunc_count = 0

        for cached_sample in cache:
            cached_sample_time = cached_sample['localtime']
            if cached_sample_time < trunc_time:
                trunc_count = trunc_count + 1
            if cache_sample_time >= from_time:
                # Beginning of range is in cache
                if cache_sample_time <= to_time
                    yield cached_sample
                else
                    break # finished loop
            else
                # Beginning of range is not in cache
                for storage_sample in self.storage.samples(from_time, sample_time):
                    yield storage_sample


