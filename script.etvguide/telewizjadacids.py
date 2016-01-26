#      Copyright (C) 2016 Andrzej Mleczko

import urllib, httplib, sys, copy, re
import simplejson as json
import xbmc
import time
import os, xbmcaddon
from strings import *
import weebtvcids

HOST                = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0'
telewizjadaMainUrl  = 'http://www.telewizjada.net/'

COOKIE_FILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')) , 'telewizjada.cookie')
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')
onlineMapFile = 'http://epg.feenk.net/maps/telewizjadamap.xml'

telewizjadaChannelList = None

class TelewizjaDaUpdater:
    def __init__(self):
        self.sl = weebtvcids.ShowList()

    def loadChannelList(self):
        try:
            mapfile = self.sl.downloadUrl(onlineMapFile)
            if mapfile is None:
                deb('TelewizjaDaUpdater loadChannelList map file download Error, using local instead!')
                pathMap = os.path.join(pathMapBase, 'telewizjadamap.xml')
                mapfile = weebtvcids.MapString.loadFile(pathMap)
            else:
                deb('TelewizjaDaUpdater loadChannelList success downloading online map file: %s' % onlineMapFile)

            self.channels = self.getChannelList()
            self.automap = weebtvcids.MapString.Parse(mapfile)

            deb('\n[UPD] Wyszykiwanie STRM')
            deb('-------------------------------------------------------------------------------------')
            deb('[UPD] %-30s %-30s %-20s %-35s' % ('-ID mTvGuide-', '-    Orig Name    -', '-    SRC   -', '-    STRM   -'))
            for x in self.automap:
                if x.strm != '':
                    x.src = 'CONST'
                    deb('[UPD] %-30s %-15s %-35s' % (x.channelid, x.src, x.strm))
                    continue
                try:
                    error=""
                    p = re.compile(x.titleRegex, re.IGNORECASE)
                    for y in self.channels:
                        b=p.match(y.title)
                        if (b):
                            x.strm = weebtvcids.rstrm % y.cid
                            x.src  = 'telewizjada.net'
                            y.strm = x.strm
                            y.src = x.src
                            deb('[UPD] %-30s %-30s %-20s %-35s ' % (x.channelid, y.name, x.src, x.strm))
                            break
                except Exception, ex:
                    print '%s Error %s %s' % (x.channelid, x.titleRegex, str(ex))
            deb ('\n[UPD] Nie znaleziono/wykorzystano odpowiedników w telewizjada.net dla:')
            deb('-------------------------------------------------------------------------------------')
            for x in self.automap:
                if x.src!='telewizjada.net':
                    deb('[UPD] CH=%-30s SRC=%-15s STRM=%-35s' % (x.channelid, x.src, x.strm))

            deb ('\n[UPD] Nie wykorzystano STRM nadawanych przez telewizjada.net programów:')
            deb('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != 'telewizjada.net':
                    deb ('[UPD] CID=%-10s NAME=%-40s STRM=%-45s' % (y.cid, y.name, str(y.strm)))

            deb("[UPD] Zakończono analizę...")

        except Exception, ex:
            print 'TelewizjaDaUpdater loadChannelList Error %s' % str(ex)

    def getChannelList(self):
        try:
            global telewizjadaChannelList
            deb('\n\n')
            if telewizjadaChannelList is not None:
                deb('TelewizjaDaUpdater getChannelList return cached channel list')
                return copy.deepcopy(telewizjadaChannelList)

            deb('TelewizjaDaUpdater getChannelList downloading channel list')

            channelsArray = list()
            result = list()
            channelsArray = self.sl.getJsonFromAPI(telewizjadaMainUrl + 'get_channels.php')

            if channelsArray is not None and len(channelsArray) > 0:
                for x in range(0, len(channelsArray['channels'])):
                    chann = self.sl.decode(channelsArray['channels'][x])
                    args = chann.split(",")
                    url = ''
                    ID = ''
                    img = ''
                    displayName = ''
                    description = ''
                    online = ''

                    for index in range(0, len(args)):
                        arg = args[index].split(":")
                        if "id" in arg[0]:
                            ID = arg[1].replace('"', '').strip()
                        if "displayName" in arg[0]:
                            displayName = arg[1].replace('"', '').strip()
                        if "url" in arg[0]:
                            url = arg[1].replace('"', '').strip()
                        if "thumb" in arg[0]:
                            img = telewizjadaMainUrl + arg[1].replace('"', '').strip()
                        if "description" in arg[0]:
                            description = arg[1].replace('"', '').strip()
                        if "online" in arg[0]:
                            online = arg[1].replace('"', '').strip()

                    if online == '1':
                        result.append(weebtvcids.WeebTvCid(ID, displayName, displayName, '2', url, img))
                    else:
                        deb('TelewizjaDaUpdater getChannelList skipping disabled channel %s' % displayName)
                telewizjadaChannelList = copy.deepcopy(result)

            return result

        except Exception, ex:
            print 'TelewizjaDaUpdater getChannelList Error %s' % str(ex)

    def getChannel(self, cid):
        try:
            for chann in telewizjadaChannelList:
                if chann.cid == cid:
                    tmp_url = ''

                    data = { 'url': chann.strm }
                    self.sl.getJsonFromExtendedAPI(telewizjadaMainUrl + 'set_cookie.php', post_data = data, cookieFile = COOKIE_FILE, save_cookie = True)

                    data = { 'cid': cid }
                    tmp_url = self.sl.getJsonFromExtendedAPI(telewizjadaMainUrl + 'get_channel_url.php', post_data = data, cookieFile = COOKIE_FILE, load_cookie = True, jsonLoadsResult = True)

                    if tmp_url is None:
                        deb('TelewizjaDaUpdater getChannel: Error - failed to fetch tmp url from API get_channel_url.php')
                        return None
                    else:
                        tmp_url = tmp_url['url']

                    msec = self.sl.getCookieItem(COOKIE_FILE, 'msec')
                    sessid = self.sl.getCookieItem(COOKIE_FILE, 'sessid')

                    final_url = tmp_url + '|Cookie='+ urllib.quote_plus('msec=' + msec + '; sessid=' + sessid )

                    channel = copy.deepcopy(chann)
                    channel.strm = final_url
                    deb('TelewizjaDaUpdater getChannel: found matching channel: cid %s, name %s, rtmp %s ' % (channel.cid, channel.name, channel.strm))
                    return channel

        except Exception, ex:
            print 'TelewizjaDaUpdater getChannelUrl Error %s' % str(ex)

        return None
