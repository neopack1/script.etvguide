#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
from strings import *
from serviceLib import *

serviceName = 'GoldVOD'

goldUrl = 'http://goldvod.tv/api/get_tv_channels'

goldVODChannelList = None
goldVODLastUpdate = None

class GoldVodUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.serviceName        = serviceName
        self.serviceEnabled     = ADDON.getSetting('GoldVOD_enabled')
        self.login              = ADDON.getSetting('usernameGoldVOD')
        self.password           = ADDON.getSetting('userpasswordGoldVOD')
        self.servicePriority    = int(ADDON.getSetting('priority_goldvod'))
        self.onlineMapFile      = 'http://epg.feenk.net/maps/goldvodmap.xml'
        self.localMapFile       = 'goldvodmap.xml'
        self.serviceRegex       = "service=" + self.serviceName + "&cid=%"
        self.rstrm              = self.serviceRegex + 's'
        self.url                = goldUrl
        self.maxAllowedStreams  = 2
        self.addDuplicatesAtBeginningOfList = True
        self.breakAfterFirstMatchFromMap = False #Look for better quality streams if available

        if ADDON.getSetting('assign_all_streams_goldvod') == 'true':
            self.addDuplicatesToList = True

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
        post = { 'login': self.login, 'pass': self.password }
        channelsArray = self.sl.getJsonFromAPI(self.url, post)

        if channelsArray is None:
            self.log('Error while loading Json from URL: %s - aborting' % self.url)
            return result

        if len(channelsArray) > 0:
            try:
                for s in range(len(channelsArray)):
                    url_hd = ''
                    cid = self.sl.decode(channelsArray[s]['id']).replace("\"", '')
                    ico = self.sl.decode(channelsArray[s]['icon']).replace("\"", '')
                    url = self.sl.decode(channelsArray[s]['url_sd']).replace("\"", '')
                    if len(channelsArray[s]['url_hd']) is not 0 and ADDON.getSetting('video_qualityGoldVOD') == 'true':
                        url_hd = self.sl.decode(channelsArray[s]['url_hd']).replace("\"", '')
                    name = self.sl.decode(channelsArray[s]['name']).replace("\"", '')
                    try:
                        name = re.sub('SERWER\s*\d*', '', name, flags=re.IGNORECASE).replace('  ', ' ').strip()
                    except:
                        #fix for old python not supporting 'flags' argument
                        name = re.sub('SERWER\s*\d*', '', name).replace('  ', ' ').strip()

                    if url_hd == '':
                        if silent is not True:
                            self.log('[UPD] %-10s %-35s %-35s' % (cid + "_SD", name, url))
                        goldvodProgram = TvCid(cid + "_SD", name, name, url, ico)
                        goldvodProgram.rtmpdumpLink = list()
                        goldvodProgram.rtmpdumpLink.append("--rtmp")
                        goldvodProgram.rtmpdumpLink.append("%s" % url)
                        result.append(goldvodProgram)
                    else:
                        if ADDON.getSetting('assign_all_streams_goldvod') == 'true':
                            if silent is not True:
                                self.log('[UPD] %-10s %-35s %-35s' % (cid + "_SD", name, url))
                            goldvodProgram = TvCid(cid + "_SD", name, name, url, ico)
                            goldvodProgram.rtmpdumpLink = list()
                            goldvodProgram.rtmpdumpLink.append("--rtmp")
                            goldvodProgram.rtmpdumpLink.append("%s" % url)
                            result.append(goldvodProgram)

                        if silent is not True:
                            self.log('[UPD] %-10s %-35s %-35s' % (cid + "_HD", name, url_hd))

                        goldvodProgram = TvCid(cid + "_HD", name, name, url_hd, ico)
                        goldvodProgram.rtmpdumpLink = list()
                        goldvodProgram.rtmpdumpLink.append("--rtmp")
                        goldvodProgram.rtmpdumpLink.append("%s" % url_hd)
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
                return chann
        return None
