#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import time, datetime
import os, xbmcaddon, xbmcgui
import weebtvcids
from strings import *


goldUrlSD = 'http://goldvod.tv/api/getTvChannelsSD.php'
goldUrlHD = 'http://goldvod.tv/api/getTvChannels.php'
goldImgBase = 'http://goldvod.tv/api/images/'
goldServiceName = 'goldvod.tv'
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')
onlineMapFile = 'http://epg.feenk.net/maps/goldvodmap.xml'

goldVODChannelList = None
goldVODLastUpdate = None

class GoldVodUpdater:
    def __init__(self):
        self.sl       = weebtvcids.ShowList()
        self.login    = ADDON.getSetting('usernameGoldVOD')
        self.password = ADDON.getSetting('userpasswordGoldVOD')

        if ADDON.getSetting('video_qualityGoldVOD') == 'true':
            self.url = goldUrlHD
        else:
            self.url = goldUrlSD

    def getChannelList(self, silent = False):

        global goldVODChannelList
        global goldVODLastUpdate
        try:
            if goldVODLastUpdate is not None and goldVODChannelList is not None and (datetime.datetime.now() - goldVODLastUpdate).seconds < 120:
                deb('GoldVodUpdater getChannelList using cached list')
                return copy.deepcopy(goldVODChannelList)
        except:
            pass

        if silent is not True:
            deb('\n\n')
            deb('[UPD] Pobieram listę dostępnych kanałów goldvod.tv z %s' % self.url)
            deb('[UPD] -------------------------------------------------------------------------------------')
            deb('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-RTMP-'))
        result = list()
        channelsArray = None
        failedCounter = 0
        post = { 'username': self.login, 'password': self.password }
        channelsArray = self.sl.getJsonFromAPI(self.url, post)

        if channelsArray is None:
            deb('Error while loading Json from URL: %s - aborting' % self.url)
            return result

        if len(channelsArray) > 0:
            try:
                for s in range(len(channelsArray)):
                    cid = self.sl.decode(channelsArray[s]['id']).replace("\"", '')
                    url = self.sl.decode(channelsArray[s]['rtmp']).replace("\"", '')
                    name = self.sl.decode(channelsArray[s]['name']).replace("\"", '')
                    ico = goldImgBase + self.sl.decode(channelsArray[s]['image']).replace("\"", '')
                    if silent is not True:
                        deb('[UPD] %-10s %-35s %-35s' % (cid, name, url))
                    result.append(weebtvcids.WeebTvCid(cid, name, name, '2', url, ico))
                goldVODChannelList = copy.deepcopy(result)
                goldVODLastUpdate  = datetime.datetime.now()
            except KeyError, keyerr:
                print 'GoldVodUpdater getChannelList exception while looping channelsArray, error: %s' % str(keyerr)
        else:
            print 'GoldVodUpdater getChannelList returned empty channel array!!!!!!!!!!!!!!!!'
            xbmcgui.Dialog().ok(strings(SERVICE_ERROR),"\n\t" + strings(SERVICE_NO_PREMIUM) + ' ' + goldServiceName)
        return result

    def loadChannelList(self):
        try:
            mapfile = self.sl.downloadUrl(onlineMapFile)
            if mapfile is None:
                deb('GoldVodUpdater loadChannelList map file download Error, using local instead!')
                pathMap = os.path.join(pathMapBase, 'goldvodmap.xml')
                mapfile = weebtvcids.MapString.loadFile(pathMap)
            else:
                deb('GoldVodUpdater loadChannelList success downloading online map file: %s' % onlineMapFile)

            self.channels = self.getChannelList()
            self.automap = weebtvcids.MapString.Parse(mapfile)

            deb('\n')
            deb('[UPD] Wyszykiwanie STRM')
            deb('-------------------------------------------------------------------------------------')
            deb('[UPD] %-30s %-30s %-15s %-35s' % ('-ID mTvGuide-', '-    Orig Name    -', '-    SRC   -', '-    STRM   -'))
            for x in self.automap:                                     #mapa id naszego kanalu + wyr regularne
                if x.strm != '':
                    x.src = 'CONST'                             #informacja o tym że STRM pochodzi z pliku mapy
                    deb('[UPD] %-30s %-15s %-35s' % (x.channelid, x.src, x.strm))
                    continue
                try:
                    error=""
                    p = re.compile(x.titleRegex, re.IGNORECASE)
                    for y in self.channels:                        #cidy weeb.tv
                        b=p.match(y.title)
                        if (b):
                            x.strm = weebtvcids.rstrm % y.cid
                            x.src  = goldServiceName
                            y.strm = x.strm
                            y.src = x.src
                            deb('[UPD] %-30s %-30s %-15s %-35s ' % (x.channelid, y.name, x.src, x.strm))
                            #break

                except Exception, ex:
                    print '%s Error %s %s' % (x.channelid, x.titleRegex, str(ex))

            deb('\n')
            deb('[UPD] Nie znaleziono/wykorzystano odpowiedników w goldvod.tv dla:')
            deb('-------------------------------------------------------------------------------------')
            for x in self.automap:
                if x.src!=goldServiceName:
                    deb('[UPD] CH=%-30s SRC=%-15s STRM=%-35s' % (x.channelid, x.src, x.strm))

            deb('\n')
            deb('[UPD] Nie wykorzystano STRM nadawanych przez goldvod.tv programów:')
            deb('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != goldServiceName:
                    deb ('[UPD] CID=%-10s NAME=%-40s STRM=%-45s' % (y.cid, y.name, str(y.strm)))

            deb("[UPD] Zakończono analizę...\n\n")

        except Exception, ex:
            print 'Error %s' % str(ex)

    def getChannel(self, cid):
        channels = self.getChannelList(True)
        for chann in channels:
            if chann.cid == cid:
                deb('GoldVodUpdater getChannel found matching channel: cid %s, name %s, rtmp %s' % (chann.cid, chann.name, chann.strm))
                return chann
        return None
