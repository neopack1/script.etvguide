#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
from strings import *
from serviceLib import *
import io

goldUrlSD = 'http://goldvod.tv/api/getTvChannelsSD.php'
goldUrlHD = 'http://goldvod.tv/api/getTvChannels.php'
goldImgBase = 'http://goldvod.tv/api/images/'

if ADDON.getSetting('e-TVGuide') == "1":
    onlineMapFile = 'http://epg.feenk.net/maps/goldvodmap.xml'
elif ADDON.getSetting('e-TVGuide') == "2":
    onlineMapFile = 'https://epg2.feenk.net/maps/goldvodmap.xml'

localMapFile = 'goldvodmap.xml'
serviceName = 'goldvod.tv'
serviceRegex = "service=goldvod&cid=%"
servicePriority = int(ADDON.getSetting('priority_goldvod'))

goldVODChannelList = None
goldVODLastUpdate = None

class GoldVodUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.login    = ADDON.getSetting('usernameGoldVOD')
        self.password = ADDON.getSetting('userpasswordGoldVOD')
        self.serviceName = serviceName
        self.serviceRegex = serviceRegex
        self.servicePriority = servicePriority
        self.breakAfterFirstMatchFromMap = False #Look for better quality streams if available
        self.onlineMapFile = onlineMapFile
        self.localMapFile = localMapFile
        self.maxAllowedStreams = 2

        if ADDON.getSetting('video_qualityGoldVOD') == 'true':
            self.url = goldUrlHD
        else:
            self.url = goldUrlSD

    def getChannelList(self, silent = False):
        global goldVODChannelList
        global goldVODLastUpdate
        try:
            if goldVODLastUpdate is not None and goldVODChannelList is not None and (datetime.datetime.now() - goldVODLastUpdate).seconds < 120:
                self.log('getChannelList using cached list')
                return copy.deepcopy(goldVODChannelList)
        except:
            pass

        if silent is not True:
            self.log('\n\n')
            self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
            self.log('[UPD] -------------------------------------------------------------------------------------')
            self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-RTMP-'))
        result = list()
        channelsArray = None
        failedCounter = 0
        post = { 'username': self.login, 'password': self.password }
        channelsArray = self.sl.getJsonFromAPI(self.url, post)

        if channelsArray is None:
            self.log('Error while loading Json from URL: %s - aborting' % self.url)
            return result

        if len(channelsArray) > 0:
            try:
                for s in range(len(channelsArray)):
                    cid = self.sl.decode(channelsArray[s]['id']).replace("\"", '')
                    url = self.sl.decode(channelsArray[s]['rtmp']).replace("\"", '')
                    name = self.sl.decode(channelsArray[s]['name']).replace("\"", '')
                    ico = goldImgBase + self.sl.decode(channelsArray[s]['image']).replace("\"", '')
                    if silent is not True:
                        self.log('[UPD] %-10s %-35s %-35s' % (cid, name, url))
                    goldvodProgram = WeebTvCid(cid, name, name, '2', url, ico)
                    goldvodProgram.rtmpdumpLink = list()
                    goldvodProgram.rtmpdumpLink.append("--rtmp")
                    goldvodProgram.rtmpdumpLink.append("%s" % url)
                    result.append(goldvodProgram)
                goldVODChannelList = copy.deepcopy(result)
                goldVODLastUpdate  = datetime.datetime.now()
            except KeyError, keyerr:
                self.log('getChannelList exception while looping channelsArray, error: %s' % str(keyerr))
        else:
            self.log('getChannelList returned empty channel array!!!!!!!!!!!!!!!!')
            xbmcgui.Dialog().ok(strings(SERVICE_ERROR),"\n" + strings(SERVICE_NO_PREMIUM) + ' ' + self.serviceName)
        return result

    def getChannel(self, cid):
        channels = self.getChannelList(True)
        for chann in channels:
            if chann.cid == cid:
                self.log('getChannel found matching channel: cid: %s, name: %s, rtmp: %s' % (chann.cid, chann.name, chann.strm))
                #print chann.rtmpdumpLink
                return chann
        return None
