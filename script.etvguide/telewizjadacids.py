#      Copyright (C) 2016 Andrzej Mleczko

import urllib, sys, copy, re
import xbmc
import os, xbmcaddon
from strings import *
from serviceLib import *


telewizjadaMainUrl  = 'http://www.telewizjada.net/'
serviceName   = 'telewizjada.net'
serviceRegex  = "service=telewizjada&cid=%"
onlineMapFile = 'http://epg.feenk.net/maps/telewizjadamap.xml'
localMapFile  = 'telewizjadamap.xml'
servicePriority = int(ADDON.getSetting('priority_telewizjada'))
COOKIE_FILE   = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')) , 'telewizjada.cookie')

telewizjadaChannelList = None

class TelewizjaDaUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.serviceName = serviceName
        self.serviceRegex = serviceRegex
        self.servicePriority = servicePriority
        self.onlineMapFile = onlineMapFile
        self.localMapFile = localMapFile
        self.maxAllowedStreams = 1

    def getChannelList(self):
        try:
            global telewizjadaChannelList
            self.log('\n\n')
            if telewizjadaChannelList is not None:
                self.log('getChannelList return cached channel list')
                return copy.deepcopy(telewizjadaChannelList)

            self.log('getChannelList downloading channel list')

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
                        result.append(WeebTvCid(ID, displayName, displayName, '2', url, img))
                    else:
                        self.log('getChannelList skipping disabled channel %s' % displayName)
                telewizjadaChannelList = copy.deepcopy(result)

            return result

        except Exception, ex:
            self.log('getChannelList Error %s' % str(ex))

    def getChannel(self, cid):
        try:
            for chann in telewizjadaChannelList:
                if chann.cid == cid:
                    failedCounter = 0
                    while failedCounter < 5:
                        if xbmc.abortRequested:
                            break
                        tmp_url = ''
                        data = { 'url': chann.strm }
                        self.sl.getJsonFromExtendedAPI(telewizjadaMainUrl + 'set_cookie.php', post_data = data, cookieFile = COOKIE_FILE, save_cookie = True)

                        data = { 'cid': cid }
                        tmp_url = self.sl.getJsonFromExtendedAPI(telewizjadaMainUrl + 'get_channel_url.php', post_data = data, cookieFile = COOKIE_FILE, load_cookie = True, jsonLoadsResult = True)

                        if tmp_url is None:
                            self.log('getChannel: Error - failed to fetch tmp url from API get_channel_url.php')
                            failedCounter = failedCounter + 1
                            continue
                        else:
                            tmp_url = str(tmp_url['url'])
                            if tmp_url == '':
                                failedCounter = failedCounter + 1
                                continue

                        msec = self.sl.getCookieItem(COOKIE_FILE, 'msec')
                        sessid = self.sl.getCookieItem(COOKIE_FILE, 'sessid')

                        final_url = tmp_url + '|Cookie='+ urllib.quote_plus('msec=' + msec + '; sessid=' + sessid )

                        channel = copy.deepcopy(chann)
                        channel.strm = final_url

                        channel.ffmpegdumpLink = list()
                        channel.ffmpegdumpLink.append("-headers")
                        channel.ffmpegdumpLink.append(('Cookie: sessid=%s; msec=%s; path=\"/\"; domain=\".telewizjada.net\"; path_spec; domain_dot; discard; version=0' % (sessid, msec)) + '\r\n' + 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0' + '\r\n' + 'Host: www.telewizjada.net' + '\r\n' + 'Content-Type: application/x-www-form-urlencoded' + '\r\n')
                        channel.ffmpegdumpLink.append("-i")
                        channel.ffmpegdumpLink.append("%s" % tmp_url.split("?")[0]) #tmp_url

                        self.log('getChannel: found matching channel: cid: %s, name: %s, rtmp: %s' % (channel.cid, channel.name, channel.strm))
                        return channel

                    return None

        except Exception, ex:
            self.log('getChannelUrl Error %s' % str(ex))

        return None
