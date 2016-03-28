#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
from strings import *
from serviceLib import *

Url = 'http://api1.moje-filmy.tk/api2/getTv.php'

onlineMapFile = 'http://mods-kodi.pl/m-tvguide/maps/mojefilmymap.xml'
localMapFile = 'mojefilmymap.xml'
serviceName = 'moje-filmy.tk'
serviceRegex = "service=mojefilmy&cid=%"
servicePriority = int(ADDON.getSetting('priority_mojefilmy'))

mojefilmyChannelList = None

class MojeFilmyUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.login    = ADDON.getSetting('mail_mojefilmy')
        self.password = ADDON.getSetting('userpasswordMojeFilmy')
        self.serviceName = serviceName
        self.serviceRegex = serviceRegex
        self.servicePriority = servicePriority
        self.breakAfterFirstMatchFromMap = False #Look for better quality streams if available
        self.onlineMapFile = onlineMapFile
        self.localMapFile = localMapFile
        self.maxAllowedStreams = 1
        self.url = Url
        self.addDuplicatesToList = True
        self.post = { 'password' : self.password, 'email' : self.login }
        self.headers = {'Token' : 'HSYW73^@*SJDEU@ks', 'ContentType' : 'application/x-www-form-urlencoded', 'User-Agent' : 'XBMC-KODI-MOJE-FILMY.TK'}

    def getChannelList(self, silent = False):
        global mojefilmyChannelList
        if mojefilmyChannelList is not None:
            self.log('getChannelList return cached channel list')
            return copy.deepcopy(mojefilmyChannelList)

        if silent is not True:
            self.log('\n\n')
            self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
            self.log('[UPD] -------------------------------------------------------------------------------------')
            self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-URL-'))
        result = list()
        channelsArray = self.sl.getJsonFromExtendedAPI(self.url, post_data = self.post, jsonLoadResult = True, customHeaders = self.headers)

        if channelsArray is None:
            self.log('Error while loading Json from URL: %s - aborting' % self.url)
            return result

        if len(channelsArray) > 0:
            try:
                for s in range(len(channelsArray['data'])):
                    url = channelsArray['data'][s]['url'].strip()
                    title = channelsArray['data'][s]['name'].replace(':', '').replace('1080p', '').replace('(ENG)', '').replace('SD', '').replace('18+', '')
                    try:
                        title = re.sub('- mirror\s*\d*', '', title, flags=re.IGNORECASE).replace('  ', ' ').strip()
                    except:
                        title = re.sub('- mirror\s*\d*', '', title).replace('  ', ' ').strip()
                    ico = channelsArray['data'][s]['img'].strip()
                    if silent is not True:
                        self.log('[UPD] %-10s %-35s %-35s' % (s, title, url))
                    mojeFilmyProgram = WeebTvCid(cid=str(s), name=title, title=title, online='2', strm=url, img=ico)
                    result.append(mojeFilmyProgram)
                mojefilmyChannelList = copy.deepcopy(result)
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
                #chann.strm = self.sl.getJsonFromExtendedAPI(chann.strm, post_data = self.post, customHeaders = self.headers)
                self.log('getChannel found matching channel: cid: %s, name: %s, rtmp: %s' % (chann.cid, chann.name, chann.strm))
                return chann
        return None
