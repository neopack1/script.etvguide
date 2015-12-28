#      Copyright (C) 2014 Krzysztof Cebulski

import urllib, urllib2, httplib, sys, StringIO, cookielib, re
from xml.etree import ElementTree
import simplejson as json
import xbmc
import time
import os, xbmcaddon
from strings import *
import ConfigParser

url        = 'http://weeb.tv'
jsonUrl    = url + '/api/getChannelList'
goldUrlSD = 'http://goldvod.tv/api/getTvChannelsSD.php'
goldUrlHD = 'http://goldvod.tv/api/getTvChannels.php'

HOST       = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0'
rstrm      = '%s'  #pobierany przepis z xml-a np.: 'service=weebtv&cid=%s'
pathAddons = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'addons.ini')
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')

class ShowList:
    def __init__(self):
        self.login = ''
        self.password = ''
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
    
    def setLoginData(self, login, password):
        self.login = login
        self.password = password
    
    def getJsonFromFile(self, url):
        result_json = { '0': 'Null' }
        try:
            with open(url, "r") as text_file:
                 content_json = text_file.read()
            result_json = json.loads(content_json)
        except Exception, ex:
            print 'Error %s' % str(ex)
        return result_json

    def getJsonFromAPI(self, url, passphrase):
        result_json = { '0': 'Null' }
        try:
            headers = { 'User-Agent': HOST, 'ContentType': 'application/x-www-form-urlencoded' }
            post = { 'username': self.login, passphrase: self.password }
            data = urllib.urlencode(post)
            reqUrl = urllib2.Request(url, data, headers)
            raw_json = urllib2.urlopen(reqUrl)
            
            content_json = raw_json.read()
            result_json = json.loads(content_json)

        except urllib2.URLError, urlerr:
            result_json = { '0': 'Error' }
            print urlerr
        except NameError, namerr:
            result_json = { '0': 'Error' }
            print namerr
        except ValueError, valerr:
            result_json = { '0': 'Error' }
            print valerr
        except httplib.BadStatusLine, statuserr:
            result_json = { '0': 'Error' }
            print statuserr
        return result_json

    def loadChannels(self, uri, uritype, passphrase):
        deb('[UPD] Pobieram listę dostępnych kanałów Weeb.tv z %s' % uri)
        deb('[UPD] -------------------------------------------------------------------------------------')
        deb('[UPD] %-7s %-35s %-30s' % ('-CID-', '-NAME-', '-TITLE-'))
        result = list()
        channelsArray = None
        failedCounter = 0
        while failedCounter < 20:
            try:
                if (uritype == 'file'):
                    channelsArray = self.JsonToSortedTab(self.getJsonFromFile(uri))
                else:
                    channelsArray = self.JsonToSortedTab(self.getJsonFromAPI(uri, passphrase))
                break
            except httplib.IncompleteRead:
                failedCounter = failedCounter + 1
                deb('loadChannels IncompleteRead exception - retrying failedCounter = %s' % failedCounter)
                time.sleep(.200)
        if channelsArray is None:
            deb('Error while loading Json from Url: %s - aborting' % uri)
            return result
        
        if len(channelsArray) > 0:
            try:
                if channelsArray[0][1] == 'Null':
                    print ('Warning !')
                elif channelsArray[0][1] != 'Error' and channelsArray[0][1] != 'Null':
                    for i in range(len(channelsArray)):
                        k = channelsArray[i][1]
                        name    = self.decode(k['channel_name']).replace("\"", '')
                        cid     = self.decode(k['cid']).replace("\"", '')
                        title   = self.decode(k['channel_title']).replace("\"", '')
                        #desc   = self.decode(k['channel_description']).replace("\"", '')
                        #tags   = self.decode(k['channel_tags']).replace("\"", '')
                        #image  = k['channel_logo_url']
                        #rank   = k['rank']
                        #bitrate= k['multibitrate']
                        #user   = self.decode(k['user_name']).replace("\"", '')
                        online = k['channel_online']
                        #if online == '2':
                        #    action = 1
                        #else:
                        #    action = 0
                        deb('[UPD] %-7s %-35s %-30s' % (cid, name, title))
                        result.append(WeebTvCid(cid, name, title, online))
            except KeyError, keyerr:
                print keyerr
        else:
            print keyerr
        return result


    def loadChannelsGoldVod(self, uri, uritype, passphrase, silent = False):
        if silent is not True: 
            deb('\n\n[UPD] Pobieram listę dostępnych kanałów goldvod.tv z %s' % uri)
            deb('[UPD] -------------------------------------------------------------------------------------')
            deb('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-RTMP-'))
        result = list()
        channelsArray = None
        failedCounter = 0
        while failedCounter < 50:
            try:
                channelsArray = self.getJsonFromAPI(uri, passphrase)
                break
            except httplib.IncompleteRead:
                failedCounter = failedCounter + 1
                deb('loadChannels IncompleteRead exception - failedCounter = %s' % failedCounter)
                time.sleep(.100)
                
        if channelsArray is None:
            deb('Error while loading Json from Url: %s - aborting' % uri)
            return result
        
        if len(channelsArray) > 0:
            try:
                for s in range(len(channelsArray)):
                    cid = self.decode(channelsArray[s]['id']).replace("\"", '')
                    url = self.decode(channelsArray[s]['rtmp']).replace("\"", '')
                    name = self.decode(channelsArray[s]['name']).replace("\"", '')
                    ico = 'http://goldvod.tv/api/images/' + self.decode(channelsArray[s]['image']).replace("\"", '')
                    if silent is not True:
                        deb('[UPD] %-10s %-35s %-35s' % (cid, name, url))
                    result.append(WeebTvCid(cid, name, name, '2', url, ico))
            except KeyError, keyerr:
                print 'loadChannelsGoldVod exception while looping channelsArray, error: %s' % str(keyerr)
        else:
            print 'loadChannelsGoldVod empty channel array!!!!!!!!!!!!!!!!'
        return result


    def getJsonFromExtendedAPI(self, url, post_data = None, save_cookie = False, load_cookie = False, cookieFile = None):
        
        result_json = { '0': 'Null' }
        customOpeners = []
        cj = cookielib.LWPCookieJar()

        def urlOpen(req, customOpeners):
            if len(customOpeners) > 0:
                opener = urllib2.build_opener( *customOpeners )
                response = opener.open(req)
            else:
                response = urllib2.urlopen(req)
            return response
        
        try:
            if cookieFile is not None:
                customOpeners.append( urllib2.HTTPCookieProcessor(cj) )
                if load_cookie == True:
                    cj.load(cookieFile, ignore_discard = True)
                
            headers = { 'User-Agent' : HOST }
            data = urllib.urlencode(post_data)
            reqUrl = urllib2.Request(url, data, headers)
            raw_json = urlOpen(reqUrl, customOpeners)
            result_json = raw_json.read()
            
            if cookieFile is not None and save_cookie == True:
                cj.save(cookieFile, ignore_discard = True)
                
        except urllib2.URLError, urlerr:
            result_json = { '0': 'Error' }
            print urlerr
        except NameError, namerr:
            result_json = { '0': 'Error' }
            print namerr
        except ValueError, valerr:
            result_json = { '0': 'Error' }
            print valerr
        except httplib.BadStatusLine, statuserr:
            result_json = { '0': 'Error' }
            print statuserr
            
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

class WeebTvCid:
    def __init__(self, cid, name, title, online, strm = "", img = ""):
        self.cid = cid
        self.name = name
        self.title = title
        self.online = online
        self.strm = strm
        self.src = ""
        self.img = img

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

class GoldVodTvStrmUpdater:
    def __init__(self):
        try:
            sl = ShowList()
            sl.setLoginData(ADDON.getSetting('usernameGoldVOD'), ADDON.getSetting('userpasswordGoldVOD'))
            pathMap = os.path.join(pathMapBase, 'goldvodmap.xml')
            
            if ADDON.getSetting('video_qualityGoldVOD') == 'true':
                self.channels = sl.loadChannelsGoldVod(goldUrlHD, 'url', 'password')
            else:
                self.channels = sl.loadChannelsGoldVod(goldUrlSD, 'url', 'password')
            
            mapfile = MapString.loadFile(pathMap)
            self.automap = MapString.Parse(mapfile)
            
            deb('\n[UPD] Wyszykiwanie STRM')
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
                            #x.strm = y.strm
                            x.strm = rstrm % y.cid
                            x.src  = 'goldvod.tv'
                            y.strm = x.strm
                            y.src = x.src
                            deb('[UPD] %-30s %-30s %-15s %-35s ' % (x.channelid, y.name, x.src, x.strm))
                            #break

                except Exception, ex:
                    print '%s Error %s %s' % (x.channelid, x.titleRegex, str(ex))

            deb ('\n[UPD] Nie znaleziono/wykorzystano odpowiedników w goldvod.tv dla:')
            deb('-------------------------------------------------------------------------------------')
            for x in self.automap:
                if x.src!='goldvod.tv':
                    deb('[UPD] CH=%-30s SRC=%-15s STRM=%-35s' % (x.channelid, x.src, x.strm))

            deb ('\n[UPD] Nie wykorzystano STRM nadawanych przez goldvod.tv programów:')
            deb('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != 'goldvod.tv':
                    deb ('[UPD] CID=%-10s NAME=%-40s STRM=%-45s' % (y.cid, y.name, str(y.strm)))

            deb("[UPD] Zakończono analizę...")
            
        except Exception, ex:
            print 'Error %s' % str(ex)

class WebbTvStrmUpdater:

    def __init__(self):

        try:
            sl = ShowList()
            sl.setLoginData(ADDON.getSetting('username'), ADDON.getSetting('userpassword'))
            pathMap = os.path.join(pathMapBase, 'weebtvmap.xml')
            
            
            self.channels = sl.loadChannels(jsonUrl, 'url', 'userpassword')

            mapfile = MapString.loadFile(pathMap)
            self.automap = MapString.Parse(mapfile)

            config = ConfigParser.RawConfigParser()
            config.read(pathAddons)

            deb('\n[UPD] Wyszykiwanie STRM')
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

            deb ('\n[UPD] Nie znaleziono/wykorzystano odpowiedników w weeb.tv dla:')
            deb('-------------------------------------------------------------------------------------')
            config = ConfigParser.RawConfigParser()
            config.read(pathAddons)
            for x in self.automap:
                if x.src!='weeb.tv':
                    deb('[UPD] CH=%-30s STRM=%-25s SRC=%s' % (x.channelid, x.strm, x.src))

            deb ('\n[UPD] Nie wykorzystano CID nadawanych przez weeb.tv programów:')
            deb('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != 'weeb.tv':
                    deb ('[UPD] ID=%-30s TITLE=%-40s STRM=%-25s SRC=%s' % (y.name, y.title, str(y.strm), y.src))

            deb("[UPD] Zakończono analizę...")

        except Exception, ex:
            print 'Error %s' % str(ex)

