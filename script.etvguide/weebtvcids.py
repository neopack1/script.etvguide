# coding=utf8
#      Copyright (C) 2016 Andrzej Mleczko
#      Copyright (C) 2014 Krzysztof Cebulski

import urllib, urllib2, httplib, sys, StringIO, cookielib, copy, re, socket
from xml.etree import ElementTree
import simplejson as json
import xbmc
import time
import os, xbmcaddon
from strings import *
import ConfigParser

url        = 'http://weeb.tv'
jsonUrl    = url + '/api/getChannelList'
playerUrl  = url + '/api/setplayer'

HOST       = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0'
rstrm      = '%s'  #pobierany przepis z xml-a np.: 'service=weebtv&cid=%s'
pathAddons = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'addons.ini')
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')
weebtvChannelList = None
onlineMapFile = 'http://epg.feenk.net/maps/weebtvmap.xml'


class ShowList:
    def __init__(self):
        pass

    def decode(self, string):
        json_ustr = json.dumps(string, ensure_ascii=False)
        return json_ustr.encode('utf-8')

    def JsonToSortedTab(self, json):
        strTab = []
        outTab = []
        for v,k in json.iteritems():
            strTab.append(int(v))
            strTab.append(k)
            outTab.append(strTab)
            strTab = []
        outTab.sort(key=lambda x: x[0])
        return outTab

    def getJsonFromAPI(self, url, post={}):
        result_json = None
        try:
            headers  = { 'Keep-Alive' : 'timeout=60', 'Connection' : 'Keep-Alive', 'User-Agent' : 'Python-urllib/2.1', 'ContentType' : 'application/x-www-form-urlencoded' }
            #post = { 'username': self.login, passphrase: self.password }
            data     = urllib.urlencode(post)
            reqUrl   = urllib2.Request(url, data) #, headers
            reqUrl.add_header('User-Agent', 'Python-urllib/2.1')
            reqUrl.add_header('Keep-Alive', 'timeout=60')
            reqUrl.add_header('Connection', 'Keep-Alive')
            reqUrl.add_header('ContentType', 'application/x-www-form-urlencoded')

            failedCounter = 0
            while failedCounter < 50:
                try:
                    raw_json = urllib2.urlopen(reqUrl, timeout = 2)
                    content_json = raw_json.read()
                    result_json = json.loads(content_json)
                    break
                except (httplib.IncompleteRead, socket.timeout) as ex:
                    failedCounter = failedCounter + 1
                    deb('ShowList getJsonFromAPI exception: %s - retrying failedCounter = %s' % (str(ex), failedCounter))
                    if xbmc.abortRequested:
                        break
                    time.sleep(.100)

        except (urllib2.URLError, NameError, ValueError, httplib.BadStatusLine) as ex:
            deb('ShowList getJsonFromAPI exception: %s - aborting!' % str(ex))
        return result_json

    def getJsonFromExtendedAPI(self, url, post_data = None, save_cookie = False, load_cookie = False, cookieFile = None, jsonLoadsResult = False):

        result_json = None
        customOpeners = []
        cj = cookielib.LWPCookieJar()

        def urlOpen(req, customOpeners):
            if len(customOpeners) > 0:
                opener = urllib2.build_opener( *customOpeners )
                response = opener.open(req, timeout = 2)
            else:
                response = urllib2.urlopen(req, timeout = 2)
            return response

        try:
            if cookieFile is not None:
                customOpeners.append( urllib2.HTTPCookieProcessor(cj) )
                if load_cookie == True:
                    cj.load(cookieFile, ignore_discard = True)

            headers = { 'User-Agent' : HOST }
            data = urllib.urlencode(post_data)
            reqUrl = urllib2.Request(url, data, headers)

            failedCounter = 0
            while failedCounter < 50:
                try:
                    raw_json = urlOpen(reqUrl, customOpeners)
                    result_json = raw_json.read()
                    if jsonLoadsResult == True:
                        result_json = json.loads(result_json)
                    break
                except (httplib.IncompleteRead, socket.timeout) as ex:
                    failedCounter = failedCounter + 1
                    deb('ShowList getJsonFromExtendedAPI exception: %s - retrying failedCounter = %s' % (str(ex), failedCounter))
                    if xbmc.abortRequested:
                        break
                    time.sleep(.100)

            if cookieFile is not None and save_cookie == True:
                cj.save(cookieFile, ignore_discard = True)

        except (urllib2.URLError, NameError, ValueError, httplib.BadStatusLine) as ex:
            deb('ShowList getJsonFromExtendedAPI exception: %s - aborting!' % str(ex))

        return result_json

    def getCookieItem(self, cookiefile, item):
        ret = ''
        if os.path.isfile(cookiefile):
            cj = cookielib.LWPCookieJar()
            cj.load(cookiefile, ignore_discard = True)
            for cookie in cj:
                if cookie.name == item:
                    ret = cookie.value
        return ret

    def downloadUrl(self, url):
        fileContent = None
        try:
            urlFile = urllib2.urlopen(url, timeout=2)
            fileContent = urlFile.read()
        except Exception, ex:
            deb('downloadUrl File download error, exception: %s' % str(ex))
            fileContent = None
        return fileContent

class WeebTvCid:
    def __init__(self, cid, name, title, online, strm = "", img = "", multibitrate = 0):
        self.cid = cid
        self.name = name
        self.title = title
        self.online = online
        self.strm = strm
        self.src = ""
        self.img = img
        self.multibitrate = multibitrate
        self.premium = 1

class MapString:
    def __init__(self, channelid, titleRegex, strm, src):
        self.channelid = channelid
        self.titleRegex = titleRegex
        self.strm = strm
        self.src = src

    @staticmethod
    def Parse(xmlstr):
        global rstrm
        deb('\n[UPD] Parsowanie pliku mapy')
        io = StringIO.StringIO(xmlstr)
        context = ElementTree.iterparse(io, events=("start", "end"))
        event, root = context.next()
        elements_parsed = 0
        deb('[UPD] %-25s %-35s %s' % ('ID' , 'TITLE_REGEX', 'STRM'))
        result = list()
        for event, elem in context:
            if event == "end":
                if elem.tag == "channel":
                    aid    = elem.get("id")
                    atitle = elem.get("title")
                    astrm  = elem.get("strm")
                    deb('[UPD] %-25s %-35s %s' % (aid, atitle, astrm))
                    result.append(MapString(aid, atitle, astrm, ''))
                if elem.tag == "map":
                    rstrm = elem.get("strm")
        deb('[UPD] Stream rule = %s' % rstrm)
        return result

    @staticmethod
    def loadFile(path):
        deb('\n[UPD] Wczytywanie mapy => mtvguide: %s' % path)
        with open(path, 'r') as content_file:
            content = content_file.read()
        return content #.replace("\t", "")

class WebbTvStrmUpdater:
    def __init__(self):
        self.sl = ShowList()
        self.login    = ADDON.getSetting('username')
        self.password = ADDON.getSetting('userpassword')
        self.highQuality = ADDON.getSetting('video_quality')
        self.url = jsonUrl

    def getChannelList(self):
        deb('\n\n')
        global weebtvChannelList
        if weebtvChannelList is not None:
            deb('WebbTvStrmUpdater getChannelList return cached channel list')
            return copy.deepcopy(weebtvChannelList)

        deb('[UPD] Pobieram listę dostępnych kanałow Weeb.tv z %s' % self.url)
        deb('[UPD] -------------------------------------------------------------------------------------')
        deb('[UPD] %-7s %-35s %-30s' % ('-CID-', '-NAME-', '-TITLE-'))
        result = list()
        channelsArray = None
        failedCounter = 0
        post = { 'username': self.login, 'userpassword': self.password }
        tmpChannels = self.sl.getJsonFromAPI(self.url, post)

        if tmpChannels is None:
            deb('WebbTvStrmUpdater getChannelList: Error while loading Json from Url: %s - aborting' % self.url)
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
                        #desc    = self.decode(k['channel_description']).replace("\"", '')
                        #tags    = self.decode(k['channel_tags']).replace("\"", '')
                        image   = k['channel_logo_url'].replace("\"", '')
                        #rank    = k['rank']
                        mbitrate = k['multibitrate']
                        #user    = self.decode(k['user_name']).replace("\"", '')
                        online   = k['channel_online']
                        #if online == '2':
                        #    action = 1
                        #else:
                        #    action = 0

                        deb('[UPD] %-7s %-35s %-30s' % (cid, name, title))
                        result.append(WeebTvCid(cid, name, title, online, img=image, multibitrate=mbitrate))
            except KeyError, keyerr:
                print keyerr

            weebtvChannelList = copy.deepcopy(result)
        else:
            print 'WebbTvStrmUpdater getChannelList returned empty channel array!!!!!!!!!!!!!!!!'
            xbmcgui.Dialog().ok(strings(SERVICE_ERROR),"\n\t" + strings(SERVICE_NO_PREMIUM) + ' weeb.tv')
        return result

    def loadChannelList(self):
        try:
            mapfile = self.sl.downloadUrl(onlineMapFile)
            if mapfile is None:
                deb('WebbTvStrmUpdater loadChannelList map file download Error, using local instead!')
                pathMap = os.path.join(pathMapBase, 'weebtvmap.xml')
                mapfile = MapString.loadFile(pathMap)
            else:
                deb('WebbTvStrmUpdater loadChannelList success downloading online map file: %s' % onlineMapFile)

            self.channels = self.getChannelList()
            self.automap = MapString.Parse(mapfile)

            config = ConfigParser.RawConfigParser()
            config.read(pathAddons)

            deb('\n')
            deb('[UPD] Wyszykiwanie STRM')
            deb('-------------------------------------------------------------------------------------')
            deb('[UPD] %-30s %-25s %s' % ('-ID mTvGuide-', '-    STRM   ', '-    SRC   -'))
            for x in self.automap:                                     #mapa id naszego kanalu + wyr regularne
                if x.strm != '':
                    x.src = 'CONST'                             #informacja o tym że STRM pochodzi z pliku mapy
                    deb('[UPD] %-30s %-25s %s' % (x.channelid, x.strm, x.src))
                    continue
                try:
                    error=""
                    p = re.compile(x.titleRegex, re.IGNORECASE)
                    for y in self.channels:                        #cidy weeb.tv
                        b=p.match(y.title)
                        if (b):
                            x.strm = rstrm % y.cid
                            x.src  = 'weeb.tv'
                            y.strm = x.strm
                            y.src = x.src
                            deb('[UPD] %-30s %-25s %s' % (x.channelid, x.strm, x.src))
                            break

                    if x.strm == '':
                        try:
                            addonini_strm = config.get(ADDON_ID, x.channelid)
                            if addonini_strm:
                                x.strm = addonini_strm
                                x.src = 'addons.ini [%s]' % ADDON_ID
                        except Exception, ex:
                            error = ' ERROR=%s' % str(ex)
                            pass
                        deb('[UPD] %-30s %-25s %s' % (x.channelid, error+x.strm, x.src))

                except Exception, ex:
                    print '%s Error %s %s' % (x.channelid, x.titleRegex, str(ex))

            deb('\n')
            deb('[UPD] Nie znaleziono/wykorzystano odpowiedników w weeb.tv dla:')
            deb('-------------------------------------------------------------------------------------')
            config = ConfigParser.RawConfigParser()
            config.read(pathAddons)
            for x in self.automap:
                if x.src!='weeb.tv':
                    deb('[UPD] CH=%-30s STRM=%-25s SRC=%s' % (x.channelid, x.strm, x.src))

            deb('\n')
            deb('[UPD] Nie wykorzystano CID nadawanych przez weeb.tv programów:')
            deb('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != 'weeb.tv':
                    deb ('[UPD] ID=%-30s TITLE=%-40s STRM=%-25s SRC=%s' % (y.name, y.title, str(y.strm), y.src))

            deb("[UPD] Zakończono analizę...\n\n")

        except Exception, ex:
            print 'Error %s' % str(ex)

    def getChannel(self, cid):
        channels = self.getChannelList()
        for chann in channels:
            if chann.cid == cid:
                deb('WebbTvStrmUpdater getChannel found matching channel: cid %s, name %s title %s' % (chann.cid, chann.name, chann.title))
                return self.updateChannelRTMP(chann)

    def updateChannelRTMP(self, channel):
        post = { 'cid': channel.cid, 'platform': 'XBMC', 'username': self.login, 'userpassword': self.password }
        params = self.sl.getJsonFromExtendedAPI(playerUrl, post_data = post)
        if params == None:
            deb('WebbTvStrmUpdater updateChannelRTMP failed to fetch channel data')
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
        deb('WebbTvStrmUpdater updateChannelRTMP generated RTMP is %s' % channel.strm)
        return channel
