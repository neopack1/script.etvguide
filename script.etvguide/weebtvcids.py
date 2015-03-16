#      Copyright (C) 2014 Krzysztof Cebulski

import urllib, urllib2, httplib, sys, StringIO, re
from xml.etree import ElementTree
import simplejson as json #import json
import xbmc
import os, xbmcaddon
from strings import *
import ConfigParser

url        = 'http://weeb.tv'
jsonUrl    = url + '/api/getChannelList'
HOST       = 'XBMC'
login      = ADDON.getSetting('username')
password   = ADDON.getSetting('userpassword')
rstrm      = '%s'  #pobierany przepis z xml-a np.: 'service=weebtv&cid=%s'
pathMap    = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'weebtvmap.xml')
pathAddons = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'addons.ini')
#pathJson   = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'weebtv.json')
#updaddon   = ADDON.getSetting('AutoUpdateCidAddons').lower() == 'true'

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

    def getJsonFromFile(self, url):
        result_json = { '0': 'Null' }
        try:
            with open(url, "r") as text_file:
                 content_json = text_file.read()
            result_json = json.loads(content_json)
        except Exception, ex:
            print 'Error %s' % str(ex)
        return result_json

    def getJsonFromAPI(self, url):
        result_json = { '0': 'Null' }
        try:
            headers = { 'User-Agent': HOST, 'ContentType': 'application/x-www-form-urlencoded' }
            post = { 'username': login, 'userpassword': password }
            data = urllib.urlencode(post)
            reqUrl = urllib2.Request(url, data, headers)
            raw_json = urllib2.urlopen(reqUrl)
            content_json = raw_json.read()

            #with open("Output.txt", "w") as text_file:
            #     text_file.write(content_json)

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

    def loadChannels(self, uri, uritype):
        deb('[UPD] Pobieram listę dostępnych kanałów Weeb.tv z %s' % uri)
        deb('[UPD] -------------------------------------------------------------------------------------')
        deb('[UPD] %-7s %-35s %-30s' % ('-CID-', '-NAME-', '-TITLE-'))
        result = list()
        if (uritype == 'file'):
            channelsArray = self.JsonToSortedTab(self.getJsonFromFile(uri))
        else:
            channelsArray = self.JsonToSortedTab(self.getJsonFromAPI(uri))

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

class WeebTvCid:
    def __init__(self, cid, name, title, online):
        self.cid = cid
        self.name = name
        self.title = title
        self.online = online
        self.strm = None
        self.src = ""

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
        deb('\n[UPD] Wczytywanie mapy weebtv => mtvguide: %s' % path)
        with open(path, 'r') as content_file:
            content = content_file.read()
        return content #.replace("\t", "")


class WebbTvStrmUpdater:

    def __init__(self):

        try:
            sl = ShowList()
            #self.weebTvChannels  = sl.loadChannels(pathJson, 'file')
            self.weebTvChannels = sl.loadChannels(jsonUrl, 'url')

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
                    for y in self.weebTvChannels:                        #cidy weeb.tv
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
            for y in self.weebTvChannels:
                if y.src == '' or y.src != 'weeb.tv':
                    deb ('[UPD] ID=%-30s TITLE=%-40s STRM=%-25s SRC=%s' % (y.name, y.title, str(y.strm), y.src))

            deb("[UPD] Zakończono analizę...")

        except Exception, ex:
            print 'Error %s' % str(ex)
            raise

