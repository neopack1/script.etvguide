#      Copyright (C) 2016 Andrzej Mleczko

import urllib, sys, copy, re
import xbmc
import os, xbmcaddon
from strings import *
from serviceLib import *

serviceName   = 'playlist'
serviceRegex  = "service=playlist&cid=%"
servicePriority = int(ADDON.getSetting('priority_playlist'))
playlistChannelList = None

if ADDON.getSetting('playlist_source') == 'Url':
    playlistFile = ADDON.getSetting('playlist_url')
else:
    playlistFile = xbmc.translatePath(ADDON.getSetting('playlist_file'))


class PlaylistUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.serviceName = serviceName
        self.serviceRegex = serviceRegex
        self.servicePriority = servicePriority
        self.url = playlistFile
        self.rstrm = serviceRegex + 's'

    def getChannelList(self):
        result = list()
        try:
            global playlistChannelList
            if playlistChannelList is not None:
                return copy.deepcopy(playlistChannelList)

            data = {}
            title = None
            nextFreeCid = 0
            self.log('\n\n')
            self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
            self.log('[UPD] -------------------------------------------------------------------------------------')
            self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-RTMP-'))

            if os.path.isfile(self.url):
                channelsArray = open(self.url, 'r').read()
            else:
                channelsArray = self.sl.getJsonFromExtendedAPI(self.url, post_data = data)

            if channelsArray is not None and len(channelsArray) > 0:
                for line in channelsArray.split('\n'):
                    stripLine = line.strip()
                    if "#EXTM3U" in stripLine:
                        continue
                    regex = re.compile('tvg-id="[^"]*"', re.IGNORECASE)
                    match = regex.findall(stripLine)
                    if len(match) > 0:
                        title = match[0].replace("tvg-id=","").replace('"','').strip()
                    elif title is not None and len(stripLine) > 0:
                        if title != '':
                            result.append(WeebTvCid(nextFreeCid, title, title, '2', stripLine, ''))
                            self.log('[UPD] %-10s %-35s %-35s' % (nextFreeCid, title, stripLine))
                            nextFreeCid = nextFreeCid + 1
                        else:
                            self.log('[UPD] %-10s %-35s %-35s' % ('-', 'No title!', stripLine))

                playlistChannelList = copy.deepcopy(result)

        except Exception, ex:
            self.log('getChannelList Error %s' % str(ex))
        return result

    def loadChannelList(self):
        self.automap = list()
        self.channels = self.getChannelList()
        self.log('[UPD] Wyszykiwanie STRM')
        self.log('-------------------------------------------------------------------------------------')
        self.log('[UPD] %-30s %-20s %-35s' % ('-ID mTvGuide-', '-    SRC   -', '-    STRM   -'))
        for channel in self.channels:
            strm = self.rstrm % channel.cid
            mapStr = MapString(channel.title, channel.title, strm, self.serviceName)
            self.automap.append(mapStr)
            self.log('[UPD] %-30s %-20s %-35s ' % (mapStr.channelid, mapStr.src, mapStr.strm))

        self.log("[UPD] Zakonczono analize...")
        self.log('\n')
        self.close()

    def getChannel(self, cid):
        try:
            channels = self.getChannelList()
            for channel in channels:
                if str(channel.cid) == str(cid):
                    self.log('getChannel: found matching channel: cid %s, name %s, stream %s' % (channel.cid, channel.name, channel.strm))
                    return channel
        except Exception, ex:
            self.log('getChannelUrl Error %s' % str(ex))
        return None
