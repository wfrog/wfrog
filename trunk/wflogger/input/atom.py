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
import base
import time
import feedparser

#feedparser._debug = True

class AtomInput(base.XmlInput):
    """
    Poll an Atom feed containing events according to the WESTEP ATOM transport (which is not yet formally defined).

    [ Properties ]

    url [string]:
        The URL of the feed to poll.
        
    period [numeric] (optional):
        The number of seconds between two polls. Defaults to 60.

    """

    url = None
    period = 60
    
    logger = logging.getLogger('input.atom')

    def do_run(self):
        self.logger.debug('Starting')
        
        # Does not accept events pre-dating the startup
        self.last_event = time.gmtime()
        
        if self.url == None:
            raise Exception('Attribute url must be set')
        
        while True:
            self.logger.debug("Reading feed")            
            feed = feedparser.parse(self.url)
                        
            last_update = self.last_event
            
            new_events=0
            old_events=0

            for entry in feed.entries:
                if entry.updated_parsed > self.last_event:
                    new_events = new_events + 1
                    event = entry.content[0]['value']
                    self.process_message(event)                    
                else:
                    old_events = old_events + 1
                if entry.updated_parsed > last_update:
                    last_update = entry.updated_parsed

            if new_events:
                self.logger.info("Got %s new events dated %s", new_events, time.asctime(last_update))
            
            if old_events:
                self.logger.debug("Skipped %s old events dated %s", old_events, time.asctime(last_update))
            
            if last_update > self.last_event:
                self.last_event = last_update
            
            # Notifies errors            
            if feed.bozo:
                self.logger.warn('Unable to open feed %s: %s', self.url, feed.bozo_exception)
            
            time.sleep(self.period)

# Tweek feedparser to accept XML as content

def unknown_starttag(self, tag, attrs):
    attrs = [(k.lower(), v) for k, v in attrs]
    attrs = [(k, k in ('rel', 'type') and v.lower() or v) for k, v in attrs]
    attrsD = dict(attrs)       
    for prefix, uri in attrs:
        if prefix.startswith('xmlns:'):
            self.trackNamespace(prefix[6:], uri)
        elif prefix == 'xmlns':
            self.trackNamespace(None, uri)
    if self.incontent:
        tag = tag.split(':')[-1]
        return self.handle_data('<%s%s>' % (tag, ''.join([' %s="%s"' % t for t in attrs])), escape=0)
    if tag.find(':') <> -1:
        prefix, suffix = tag.split(':', 1)
    else:
        prefix, suffix = '', tag
    prefix = self.namespacemap.get(prefix, prefix)
    if prefix:
        prefix = prefix + '_'
    if (not prefix) and tag not in ('title', 'link', 'description', 'name'):
        self.intextinput = 0
    if (not prefix) and tag not in ('title', 'link', 'description', 'url', 'href', 'width', 'height'):
        self.inimage = 0
    methodname = '_start_' + prefix + suffix
    try:
        method = getattr(self, methodname)
        return method(attrsD)
    except AttributeError:
        return self.push(prefix + suffix, 1)

def unknown_endtag(self, tag):
    if tag.find(':') <> -1:
        prefix, suffix = tag.split(':', 1)
    else:
        prefix, suffix = '', tag
    prefix = self.namespacemap.get(prefix, prefix)
    if prefix:
        prefix = prefix + '_'
    methodname = '_end_' + prefix + suffix
    try:
        method = getattr(self, methodname)
        method()
    except AttributeError:
        self.pop(prefix + suffix)
    if self.incontent:
        tag = tag.split(':')[-1]
        self.handle_data('</%s>' % tag, escape=0)
    if self.basestack:
        self.basestack.pop()
        if self.basestack and self.basestack[-1]:
            self.baseuri = self.basestack[-1]
    if self.langstack:
        self.langstack.pop()
        if self.langstack:
            self.lang = self.langstack[-1]

feedparser._FeedParserMixin.unknown_starttag = unknown_starttag
feedparser._FeedParserMixin.unknown_endtag = unknown_endtag
feedparser._sanitizeHTML = lambda source, encoding:  source
