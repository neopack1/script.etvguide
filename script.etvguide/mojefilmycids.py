#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
from strings import *
from serviceLib import *
import operator

onlineMapFile = 'http://epg.feenk.net/maps/mojefilmymap.xml'
localMapFile = 'mojefilmymap.xml'
serviceName = 'moje-filmy.tk'
serviceRegex = "service=mojefilmy&cid=%"
servicePriority = int(ADDON.getSetting('priority_mojefilmy'))
Url = ADDON.getSetting('mojefilmy_playlist')

mojefilmyChannelList = None

class MojeFilmyUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.serviceName = serviceName
        self.serviceRegex = serviceRegex
        self.servicePriority = servicePriority
        self.breakAfterFirstMatchFromMap = False #Look for better quality streams if available
        self.onlineMapFile = onlineMapFile
        self.localMapFile = localMapFile
        self.maxAllowedStreams = 4
        self.url = Url
        self.addDuplicatesToList = True
        self.addDuplicatesAtBeginningOfList = True

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
                            result.append(TvCid(nextFreeCid, title, title, stripLine, ''))
                            self.log('[UPD] %-10s %-35s %-35s' % (nextFreeCid, title, stripLine))
                            nextFreeCid += 1

                #result = sorted(result, key=operator.attrgetter('title'))
                #nextFreeCid = 0
                #for channel in sorted_result:
                    #channel.cid = nextFreeCid
                    #channel.title = re.sub(' XHD', ' HD', channel.title)
                    #channel.name = channel.title
                    #self.log('[UPD] %-10s %-35s %-35s' % (channel.cid, channel.title, channel.strm))
                    #nextFreeCid += 1

                mojefilmyChannelList = copy.deepcopy(result)

        except Exception, ex:
            self.log('getChannelList Error %s' % str(ex))
        return result

    def getChannel(self, cid):
        channels = self.getChannelList()
        for chann in channels:
            if chann.cid == int(cid):
                self.log('getChannel found matching channel: cid: %s, name: %s, rtmp: %s' % (chann.cid, chann.name, chann.strm))
                return chann
        return None
