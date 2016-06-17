#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
from strings import *
from serviceLib import *
import operator

serviceName = 'MojeFilmy'

mojefilmyChannelList = None

class MojeFilmyUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.serviceName        = serviceName
        self.serviceEnabled     = ADDON.getSetting('MojeFilmy_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_mojefilmy'))
        self.url                = ADDON.getSetting('mojefilmy_playlist')
        self.onlineMapFile      = 'http://epg.feenk.net/maps/mojefilmymap.xml'
        self.localMapFile       = 'mojefilmymap.xml'
        self.serviceRegex       = "service=" + self.serviceName + "&cid=%"
        self.rstrm              = self.serviceRegex + 's'
        self.maxAllowedStreams  = 4
        self.addDuplicatesToList = True
        self.addDuplicatesAtBeginningOfList = True
        self.breakAfterFirstMatchFromMap = False #Look for better quality streams if available

    def getChannelList(self):
        result = list()
        try:
            global mojefilmyChannelList
            if mojefilmyChannelList is not None:
                return copy.deepcopy(mojefilmyChannelList)

            data = {}
            title = None
            nextFreeCid = 0
            self.log('\n\n')
            self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
            self.log('[UPD] -------------------------------------------------------------------------------------')
            self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-RTMP-'))

            channelsArray = self.sl.getJsonFromExtendedAPI(self.url, post_data = data)

            if channelsArray is not None and len(channelsArray) > 0:
                regex = re.compile(".*?tvg-id.*?audio-track.*?group-title.*?tvg-logo=\".*?\",(.*)", re.IGNORECASE)
                for line in channelsArray.split('\n'):
                    stripLine = line.strip()
                    if "#EXTM3U" in stripLine:
                        continue
                    match = regex.findall(stripLine)
                    if len(match) > 0:
                        title = match[0]
                        title = re.sub(' 480p', '', title)
                        title = re.sub(' 360p', '', title)
                        title = re.sub(' HQ', ' HD', title)
                        title = re.sub(' LQ', '', title)
                        title = re.sub(' FHD', ' HD', title)
                        title = re.sub('HD Ready', 'HD', title)
                        #title = re.sub(' FHD', ' XHD', title) #we do this so FHD will be assigned higher than HD
                        title = re.sub('18\+', '', title)
                        try:
                            title = re.sub('test', '', title, flags=re.IGNORECASE)
                        except:
                            title = re.sub('test', '', title)
                            title = re.sub('Test', '', title)
                        title = title.strip()
                    elif title is not None and len(stripLine) > 0:
                        if title != '':
                            channelCid = str(nextFreeCid)
                            if ' HD' in title:
                                channelCid = channelCid + '_HD'
                            else:
                                channelCid = channelCid + '_SD'
                            result.append(TvCid(channelCid, title, title, stripLine, ''))
                            self.log('[UPD] %-10s %-35s %-35s' % (channelCid, title, stripLine))
                            nextFreeCid += 1

                result = sorted(result, key=operator.attrgetter('title'))

                mojefilmyChannelList = copy.deepcopy(result)

        except Exception, ex:
            self.log('getChannelList Error %s' % str(ex))
        return result

    def getChannel(self, cid):
        channels = self.getChannelList()
        for chann in channels:
            if chann.cid == cid:
                self.log('getChannel found matching channel: cid: %s, name: %s, rtmp: %s' % (chann.cid, chann.name, chann.strm))
                return chann
        return None
