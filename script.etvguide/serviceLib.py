#      Copyright (C) 2016 Andrzej Mleczko

import urllib, urllib2, httplib, sys, StringIO, cookielib, re, socket
from xml.etree import ElementTree
import simplejson as json
import xbmc
import time
import os, xbmcaddon
from strings import *
import threading
import platform

HOST       = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0'
pathAddons = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'addons.ini')
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')

TIMEZONE = ADDON.getSetting('Time.Zone')
CHECK_NAME = ADDON.getSetting('username')
ADDON_VERSION =  ADDON.getAddonInfo('version')
PLATFORM_INFO = platform.system()
KODI_VERSION = xbmc.getInfoLabel( "System.BuildVersion" )


if CHECK_NAME:
    USER_AGENT = ADDON.getSetting('username')
else:
    USER_AGENT = ADDON.getSetting('usernameGoldVOD')

class ShowList:
    def __init__(self, logCall=deb):
        self.logCall = logCall

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
            data     = urllib.urlencode(post)
            reqUrl   = urllib2.Request(url, data)
            reqUrl.add_header('User-Agent', 'Python-urllib/2.1')
            reqUrl.add_header('Keep-Alive', 'timeout=60')
            reqUrl.add_header('Connection', 'Keep-Alive')
            reqUrl.add_header('ContentType', 'application/x-www-form-urlencoded')

            failedCounter = 0
            while failedCounter < 50:
                try:
                    raw_json = urllib2.urlopen(reqUrl, timeout = 3)
                    content_json = raw_json.read()
                    result_json = json.loads(content_json)
                    break
                except (httplib.IncompleteRead, socket.timeout) as ex:
                    failedCounter = failedCounter + 1
                    self.logCall('ShowList getJsonFromAPI exception: %s - retrying failedCounter = %s' % (str(ex), failedCounter))

                except urllib2.HTTPError as ex:
                    if ex.code == 500:
                        failedCounter = failedCounter + 10
                        self.logCall('ShowList getJsonFromAPI exception: %s - retrying failedCounter = %s' % (str(ex), failedCounter))

                except urllib2.URLError as ex:
                    if 'timed out' in str(ex):
                        failedCounter = failedCounter + 10
                        self.logCall('ShowList getJsonFromAPI exception: %s - retrying failedCounter = %s' % (str(ex), failedCounter))
                    else:
                        raise

                if xbmc.abortRequested:
                    break
                time.sleep(.050)

        except (urllib2.URLError, NameError, ValueError, httplib.BadStatusLine) as ex:
            self.logCall('ShowList getJsonFromAPI exception: %s - aborting!' % str(ex))
            return None
        return result_json

    def getJsonFromExtendedAPI(self, url, post_data = None, save_cookie = False, load_cookie = False, cookieFile = None, jsonLoadsResult = False):
        result_json = None
        customOpeners = []
        cj = cookielib.LWPCookieJar()

        def urlOpen(req, customOpeners):
            if len(customOpeners) > 0:
                opener = urllib2.build_opener( *customOpeners )
                response = opener.open(req, timeout = 3)
            else:
                response = urllib2.urlopen(req, timeout = 3)
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
                    self.logCall('ShowList getJsonFromExtendedAPI exception: %s - retrying failedCounter = %s' % (str(ex), failedCounter))

                except urllib2.URLError as ex:
                    if 'timed out' in str(ex):
                        failedCounter = failedCounter + 10
                        self.logCall('ShowList getJsonFromAPI exception: %s - retrying failedCounter = %s' % (str(ex), failedCounter))
                    else:
                        raise

                if xbmc.abortRequested:
                    break
                time.sleep(.050)

            if cookieFile is not None and save_cookie == True:
                cj.save(cookieFile, ignore_discard = True)

        except (urllib2.URLError, NameError, ValueError, httplib.BadStatusLine) as ex:
            self.logCall('ShowList getJsonFromExtendedAPI exception: %s - aborting!' % str(ex))
            return None

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
            urlFile = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0 (AGENT:' + USER_AGENT + ' TIMEZONE:' + TIMEZONE + ' PLUGIN_VERSION:' + ADDON_VERSION + ' PLATFORM:' + PLATFORM_INFO + ' KODI_VERSION:' + KODI_VERSION + ')' })
            response = urllib2.urlopen(urlFile,timeout=2)
            #urlFile = urllib2.urlopen(url, timeout=2)
            fileContent = response.read()
            #response.close()
        except Exception, ex:
            self.logCall('File download error, exception: %s' % str(ex))
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
        self.rtmpdumpLink = None
        self.ffmpegdumpLink = None

class MapString:
    def __init__(self, channelid, titleRegex, strm, src):
        self.channelid = channelid
        self.titleRegex = titleRegex
        self.strm = strm
        self.src = src

    @staticmethod
    def Parse(xmlstr, logCall=deb):
        rstrm = ''
        logCall('\n')
        logCall('[UPD] Parsowanie pliku mapy')
        io = StringIO.StringIO(xmlstr)
        context = ElementTree.iterparse(io, events=("start", "end"))
        event, root = context.next()
        elements_parsed = 0
        if ADDON.getSetting('debug_log') == 'true':
            logCall('[UPD] %-35s %-35s %s' % ('ID' , 'TITLE_REGEX', 'STRM'))
        result = list()
        for event, elem in context:
            if event == "end":
                if elem.tag == "channel":
                    aid    = elem.get("id")
                    atitle = elem.get("title")
                    astrm  = elem.get("strm")
                    if ADDON.getSetting('debug_log') == 'true':
                        logCall('[UPD] %-35s %-35s %s' % (aid, atitle, astrm))
                    result.append(MapString(aid, atitle, astrm, ''))
                if elem.tag == "map":
                    rstrm = elem.get("strm")
        logCall('[UPD] Stream rule = %s' % rstrm)
        return [result, rstrm]

    @staticmethod
    def loadFile(path, logCall=deb):
        logCall('\n')
        logCall('[UPD] Wczytywanie mapy => mtvguide: %s' % path)
        with open(path, 'r') as content_file:
            content = content_file.read()
        return content #.replace("\t", "")

class baseServiceUpdater:
    def __init__(self):
        self.sl = ShowList(self.log)
        self.login = ''
        self.password = ''
        self.highQuality = 'true'
        self.url = ''
        self.thread = None
        self.serviceName = 'baseService'
        self.serviceRegex = ''
        self.servicePriority = int(0)
        self.useCid = True
        self.traceList = list()
        self.traceList.append('\n')
        self.traceList.append('##############################################################################################################')
        self.traceList.append('\n')
        self.rstrm = ''
        self.forcePrintintingLog = False
        self.printLogTimer = None
        self.breakAfterFirstMatchFromMap = True
        self.onlineMapFile = ''
        self.localMapFile = ''
        self.maxAllowedStreams = 1

    def waitUntilDone(self):
        if self.thread is not None:
            return self.thread.join()

    def log(self, message):
        if self.thread is not None and self.thread.is_alive() and self.forcePrintintingLog == False:
            self.traceList.append(self.__class__.__name__ + ' ' + message)
        else:
            deb(self.__class__.__name__ + ' ' + message)

    def printLog(self):
        for trace in self.traceList:
            deb(trace)
        del self.traceList[:]

    def startLoadingChannelList(self):
        self.thread = threading.Thread(name='loadChannelList thread', target = self.loadChannelList)
        self.thread.start()
        self.printLogTimer = threading.Timer(6, self.printLogTimeout)
        self.printLogTimer.start()

    def printLogTimeout(self):
        self.printLogTimer = None
        self.forcePrintintingLog = True
        if self.thread is not None and self.thread.is_alive():
            self.printLog()

    def loadChannelList(self):
        self.log('loadChannelList Error: this operation needs to be overloaded!')

    def close(self):
        if self.printLogTimer is not None:
            self.printLogTimer.cancel()
            self.printLog()

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

            self.log('\n')
            self.log('[UPD] Wyszykiwanie STRM')
            self.log('-------------------------------------------------------------------------------------')
            self.log('[UPD] %-30s %-30s %-20s %-35s' % ('-ID mTvGuide-', '-    Orig Name    -', '-    SRC   -', '-    STRM   -'))

            for x in self.automap:
                if x.strm != '':
                    x.src = 'CONST'
                    self.log('[UPD] %-30s %-15s %-35s' % (x.channelid, x.src, x.strm))
                    continue
                try:
                    p = re.compile(x.titleRegex, re.IGNORECASE)
                    for y in self.channels:
                        b=p.match(y.title)
                        if (b):
                            if self.useCid == True:
                                x.strm = self.rstrm % y.cid
                            else:
                                x.strm = y.strm
                            y.strm = x.strm
                            x.src  = self.serviceName
                            y.src = x.src
                            self.log('[UPD] %-30s %-30s %-20s %-35s ' % (x.channelid, y.name, x.src, x.strm))
                            if self.breakAfterFirstMatchFromMap:
                                break

                except Exception, ex:
                    self.log('%s Error %s %s' % (x.channelid, x.titleRegex, str(ex)))

            #self.log('\n')
            #self.log('[UPD] Nie znaleziono/wykorzystano odpowiednikow w %s dla:' % self.serviceName)
            #self.log('-------------------------------------------------------------------------------------')
            #for x in self.automap:
                #if x.src!=self.serviceName:
                    #self.log('[UPD] CH=%-30s SRC=%-15s STRM=%-35s' % (x.channelid, x.src, x.strm))

            self.log('\n')
            self.log('[UPD] Nie wykorzystano STRM nadawanych przez %s programow:' % self.serviceName)
            self.log('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != self.serviceName:
                    self.log('[UPD] CID=%-10s NAME=%-40s STRM=%-45s' % (y.cid, y.name, str(y.strm)))

            self.log("[UPD] Zakonczono analize...")
            self.log('\n')

        except Exception, ex:
            self.log('loadChannelList Error %s' % str(ex))
        self.close()
