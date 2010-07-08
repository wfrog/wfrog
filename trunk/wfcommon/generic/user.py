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
import wrapper
import os
import copy

class UserChoiceElement(wrapper.ElementWrapper):
    """
    Wrap an element by picking it from a dictionary according to the
    current user, owner of the process.

    [ Properties ]

    choices [dict]:
        The candidate elements keyed by username. The key 'default' is
        chosen if none matches.

    """

    choices = None
    logger = logging.getLogger("generic.user")
    target = None

    def _init(self, context=None):

        if not self.target:
            user = os.getenv('USER')
            if(user == None):
                user = os.getenv('USERNAME')
            if not self.choices.has_key(user):
                user = 'default'
            self.logger.debug('Current user:'+user)

            self.target = self.choices[user]

        return self.target

    def _call(self, attr, *args, **keywords):

        if keywords.has_key('context'):
            self._init(keywords['context'])
            context = copy.copy(keywords['context'])
            context['_yaml_config_file'] = self.abs_path
            keywords['context'] = context
        else:
            self._init()

        self.logger.debug('Calling '+attr+' on ' + str(self.target))
        return self.target.__getattribute__(attr).__call__(*args, **keywords)
