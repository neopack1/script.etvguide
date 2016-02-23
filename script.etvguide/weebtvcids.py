#      Copyright (C) 2016 Andrzej Mleczko
#      Copyright (C) 2014 Krzysztof Cebulski

import urllib, sys, StringIO, copy, re
import xbmc
import os, xbmcaddon
from strings import *
import ConfigParser
from serviceLib import *
import io

url        = 'http://weeb.tv'
jsonUrl    = url + '/api/getChannelList'
playerUrl  = url + '/api/setplayer'

serviceName = 'weeb.tv'
serviceRegex = "service=weebtv&cid=%"
if ADDON.getSetting('e-TVGuide') == "0":
    onlineMapFile = 'http://epg.feenk.net/maps/weebtvmap.xml'
elif ADDON.getSetting('e-TVGuide') == "1":
    onlineMapFile = 'https://epg2.feenk.net/maps/weebtvmap.xml'

localMapFile = 'weebtvmap.xml'
servicePriority = int(ADDON.getSetting('priority_weebtv'))
weebtvChannelList = None

class WebbTvStrmUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.login    = ADDON.getSetting('username')
        self.password = ADDON.getSetting('userpassword')
        self.highQuality = ADDON.getSetting('video_quality')
        self.url = jsonUrl
        self.serviceName = serviceName
        self.serviceRegex = serviceRegex
        self.servicePriority = servicePriority
        self.onlineMapFile = onlineMapFile
        self.localMapFile = localMapFile

    def loadChannelList(self):
        try:
            mapfile = self.sl.downloadUrl(self.onlineMapFile)
            if mapfile is None:
                self.log('loadChannelList map file download Error, using local instead!')
                pathMap = os.path.join(pathMapBase, self.localMapFile)
                mapfile = MapString.loadFile(pathMap, self.log)
            else:
                self.log('loadChannelList success downloading online map file: %s' % self.onlineMapFile)

            self.channels = self.getChannelList()
            self.automap, self.rstrm = MapString.Parse(mapfile, self.log)

            config = ConfigParser.RawConfigParser()
            config.read(pathAddons)

            self.log('\n')
            self.log('[UPD] Wyszykiwanie STRM')
            self.log('-------------------------------------------------------------------------------------')
            self.log('[UPD] %-30s %-25s %s' % ('-ID mTvGuide-', '-    STRM   ', '-    SRC   -'))

            for x in self.automap:
                if x.strm != '':
                    x.src = 'CONST'
                    self.log('[UPD] %-30s %-25s %s' % (x.channelid, x.strm, x.src))
                    continue
                try:
                    error=""
                    p = re.compile(x.titleRegex, re.IGNORECASE)
                    for y in self.channels:
                        b=p.match(y.title)
                        if (b):
                            x.strm = self.rstrm % y.cid
                            x.src  = self.serviceName
                            y.strm = x.strm
                            y.src = x.src
                            self.log('[UPD] %-30s %-25s %s' % (x.channelid, x.strm, x.src))
                            break

                    if x.strm == '':
                        try:
                            addonini_strm = config.get(ADDON_ID, x.channelid)
                            if addonini_strm:
                                x.strm = addonini_strm
                                x.src = 'addons.ini [%s]' % ADDON_ID
                                self.log('[UPD] %-30s %-25s %s' % (x.channelid, error+x.strm, x.src))
                        except Exception, ex:
                            error = ' ERROR=%s' % str(ex)

                except Exception, ex:
                    self.log('%s Error %s %s' % (x.channelid, x.titleRegex, str(ex)))

            #self.log('\n')
            #self.log('[UPD] Nie znaleziono/wykorzystano odpowiednikow w %s dla:' % self.serviceName)
            #self.log('-------------------------------------------------------------------------------------')
            #config = ConfigParser.RawConfigParser()
            #config.read(pathAddons)
            #for x in self.automap:
                #if x.src!=self.serviceName:
                    #self.log('[UPD] CH=%-30s STRM=%-25s SRC=%s' % (x.channelid, x.strm, x.src))

            self.log('\n')
            self.log('[UPD] Nie wykorzystano CID nadawanych przez %s programow:' % self.serviceName)
            self.log('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != self.serviceName:
                    self.log('[UPD] ID=%-30s TITLE=%-50s STRM=%-25s SRC=%s' % (y.name, y.title, str(y.strm), y.src))

            self.log("[UPD] Zakonczono analize...")
            self.log('\n')

        except Exception, ex:
            self.log('Error %s' % str(ex))

        self.close()

    def getChannelList(self):
        self.log('\n\n')
        global weebtvChannelList
        if weebtvChannelList is not None:
            self.log('getChannelList return cached channel list')
            return copy.deepcopy(weebtvChannelList)

        self.log('[UPD] Pobieram liste dostepnych kanalow Weeb.tv z %s' % self.url)
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-7s %-35s %-30s' % ('-CID-', '-NAME-', '-TITLE-'))
        result = list()
        channelsArray = None
        failedCounter = 0
        post = { 'username': self.login, 'userpassword': self.password }
        tmpChannels = self.sl.getJsonFromAPI(self.url, post)

        if tmpChannels is None:
            self.log('getChannelList: Error while loading Json from Url: %s - aborting' % self.url)
            return result

        channelsArray = self.sl.JsonToSortedTab(tmpChannels)

        if len(channelsArray) > 0:
            try:
                if channelsArray[0][1] == 'Null':
                    print ('Warning !')
                elif channelsArray[0][1] != 'Error' and channelsArray[0][1] != 'Null':
                    for i in range(len(channelsArray)):
                        k = channelsArray[i][1]
                        name     = self.sl.decode(k['channel_name']).replace("\"", '')
                        cid      = self.sl.decode(k['cid']).replace("\"", '')
                        title    = self.sl.decode(k['channel_title']).replace("\"", '')
                        image   = k['channel_logo_url'].replace("\"", '')
                        mbitrate = k['multibitrate']
                        online   = k['channel_online']

                        self.log('[UPD] %-7s %-35s %-30s' % (cid, name, title))
                        result.append(WeebTvCid(cid, name, title, online, img=image, multibitrate=mbitrate))
            except KeyError, keyerr:
                self.log('getChannelList exception while looping channelsArray, error: %s' % str(keyerr))

            weebtvChannelList = copy.deepcopy(result)
        else:
            self.log('getChannelList returned empty channel array!!!!!!!!!!!!!!!!')
            xbmcgui.Dialog().ok(strings(SERVICE_ERROR),"\n\t" + strings(SERVICE_NO_PREMIUM) + ' ' + self.serviceName)
        return result

    def getChannel(self, cid):
        channels = self.getChannelList()
        for chann in channels:
            if chann.cid == cid:
                self.log('getChannel found matching channel: cid: %s, name: %s title: %s' % (chann.cid, chann.name, chann.title))
                return self.updateChannelRTMP(chann)

    def updateChannelRTMP(self, channel):
        post = { 'cid': channel.cid, 'platform': 'XBMC', 'username': self.login, 'userpassword': self.password }
        params = self.sl.getJsonFromExtendedAPI(playerUrl, post_data = post)
        if params == None:
            self.log('updateChannelRTMP failed to fetch channel data')
            return None

        pairParams = (params.replace('?', '')).split('&')
        param = {}
        for i in range(len(pairParams)):
            splitparams = pairParams[i].split('=')
            if (len(splitparams)) == 2:
                param[int(splitparams[0].strip())] = urllib.unquote_plus(splitparams[1])

        rtmpLink = param[10]
        playPath = param[11]
        ticket = param[73]

        if channel.multibitrate == '1' and self.highQuality == 'true':
            playPath = playPath + 'HI'

        channel.strm    = str(rtmpLink) + '/' + str(playPath) + ' swfUrl='  + str(ticket) + ' pageUrl=token' + ' live=true'
        channel.premium = int(param[5])
        channel.rtmpdumpLink = list()
        channel.rtmpdumpLink.append("--rtmp")
        channel.rtmpdumpLink.append("%s/%s"  % (str(rtmpLink), str(playPath)) )
        channel.rtmpdumpLink.append("-s")
        channel.rtmpdumpLink.append("%s" % str(ticket))
        channel.rtmpdumpLink.append("-p")
        channel.rtmpdumpLink.append("token")

        #channel.rtmpdumpLink = "--rtmp %s/%s -s %s -p token" % (str(rtmpLink), str(playPath), str(ticket))

        self.log('updateChannelRTMP generated RTMP is %s' % channel.strm)
        #print channel.rtmpdumpLink
        return channel
