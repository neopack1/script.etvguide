# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys, math, time
import xbmcaddon, traceback, xbmcgui
import xml.etree.ElementTree as ET 

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdNavigation, sdCommon, sdErrors, downloader

log = sdLog.pLog()

dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

SERVICE = 'ipla'
BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
LOGOURL = BASE_IMAGE_PATH + SERVICE + ".png"
HOST = 'mipla/23'

URL_IPLA = 'http://getmedia.redefine.pl'
IDENTITY = 'login=9j3fi376&passwdmd5=79fb619cc2d042eb686c556f8fc147f8&cuid=9887518'

URL_CATEGORIES = URL_IPLA + '/r/l_x_35_ipla/categories/list/?'
URL_MOVIE = URL_IPLA + '/action/2.0/vod/list/?category='
URL_SEARCH = URL_IPLA + '/vods/search/?vod_limit=50&page=0&keywords='

SERVICE_MENU_TABLE = {
    1: "Kategorie",
    2: "Wyszukaj",
    3: "Historia wyszukiwania"
}

ipla_quality = ptv.getSetting('ipla_quality')

ipla_url_keys = ("service","name","category","page")

class IPLA:
    def __init__(self):
        self.settings = sdSettings.TVSettings()
        self.parser = sdParser.Parser()
        self.cm = sdCommon.common()
        self.history = sdCommon.history()
        self.gui = sdNavigation.sdGUI()
        self.exception = sdErrors.Exception()

    def setTable(self):
        return SERVICE_MENU_TABLE

    def getIdentity(self):
        query_data = { 'url': 'http://sd-xbmc.info/support/ipla_identity.php', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            response = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        if response == 'error':
            msg = xbmcgui.Dialog()
            msg.ok("Błąd API", "Nie moge pobrac listy wideo.")
            exit()
        else:
            return response

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
            self.gui.addDir(params, params_keys_needed = ipla_url_keys)
        self.gui.endDir()

    def getCategories(self, url):
        query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': False }
        try:
            response = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        elems = ET.parse(response).getroot()
#        print ET.tostring(elems, encoding='utf8', method='xml')
        cats = elems.findall("cat")
        for cat in cats:
            val = cat.attrib
            try:
                pid = val['pid']
                if pid == '0':
                    title = string.capwords(val['title'])
                    id = val['id']
                    thumb = val['thumbnail_big']
                    plot = val['descr'].encode('UTF-8')
                    params = {'service': SERVICE, 'name': 'main-categories', 'title': title, 'page': url, 'icon': thumb, 'category': id, 'plot': plot }
                    self.gui.addDir(params, params_keys_needed = ipla_url_keys)
            except:
                pass
        self.gui.endDir()

    def listsTitles(self, url, idKey):
        query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': False }
        try:
            response = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        elems = ET.parse(response).getroot()
        titles = elems.findall("cat")
        for title in titles:
            val = title.attrib
            try:
                pid = val['pid']
                if pid == idKey:
                    title = val['title'].encode('UTF-8')
                    id = val['id']
                    thumb = val['thumbnail_big']
                    #desc = val['descr'].encode('UTF-8')
                    params = {'service': SERVICE, 'name': 'title-categories', 'title': title, 'page': url, 'icon': thumb, 'category': id}
                    self.gui.addDir(params, params_keys_needed = ipla_url_keys)
            except:
                pass
        self.gui.endDir()

    def switcher(self, url, idKey):
        out = 'false'
        query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': False }
        try:
            response = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        elems = ET.parse(response).getroot()
        seasons = elems.findall("cat")
        for season in seasons:
            val = season.attrib
            try:
               pid = val['pid']
               if pid == idKey:
                   out = True
                   break
            except:
                pass
        if out == True:
            self.listsSeasons(url, idKey)
        else:
            identity = self.getIdentity()
            self.listsMovieVOD(URL_MOVIE + idKey + '&' + identity)

    def listsSeasons(self, url, idKey):
        query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': False }
        try:
            response = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        elems = ET.parse(response).getroot()
        seasons = elems.findall("cat")
        for season in seasons:
            val = season.attrib
            try:
                pid = val['pid']
                if pid == idKey:
                    title = val['title'].encode('UTF-8')
                    id = val['id']
                    thumb = val['thumbnail_big']
                    plot = val['descr'].encode('UTF-8')
                    params = {'service': SERVICE, 'name': 'movie-categories', 'title': title, 'page': url, 'icon': thumb, 'category': id, 'plot': plot}
                    self.gui.addDir(params, params_keys_needed = ipla_url_keys)
            except:
                    pass
        self.gui.endDir()

    def listsMovieVOD(self, mUrl):
        strTab = []
        valTab = []
        num = '0'
        query_data = { 'url': mUrl, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': False }
        try:
            response = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()

        elems = ET.parse(response).getroot()
        try:
            vods = elems.find("VoDs").findall("vod")
        except AttributeError:
            vods = elems.find("media").findall("vod")

        movies = []
        for vod in vods:
            elv = vod.attrib
            if elv.has_key('title'):
                title = elv['title'].encode('UTF-8')
            else:
                title = elv['descr'].encode('UTF-8')
            thumbs = vod.findall("thumb")
            for t in thumbs:
                tll = t.attrib
                thumb = tll['url']
                break

            desc = elv['descr'].encode('UTF-8')
            duration = elv['dur'].encode('UTF-8')
            links = vod.findall("srcreq")

            valTab = []
            for link in links:
                ell = link.attrib
                drm = ell['drmtype']
                if drm == '0':
                    url = ell['url'].encode('UTF-8')
                    quality = ell['quality'].encode('UTF-8')
                    format = ell['format'].encode('UTF-8')
                    bitrate = ell['bitrate'].encode('UTF-8')
                    strTab.append(url)
                    strTab.append(quality)
                    strTab.append(bitrate)
                    strTab.append(format)
                    valTab.append(strTab)
                    strTab = []
            valTab.sort(key = lambda x: x[1], reverse = True)

            try:
                if ipla_quality == 'Niska': link = valTab[-1][0]
                if ipla_quality == 'Wysoka': link = valTab[0][0]
                if ipla_quality == 'Średnia':
                    i = int(math.ceil(len(valTab)/2))
                    link = valTab[i][0]
                #link = valTab[0][0]
            except IndexError:
                continue
            params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': link, 'icon': thumb, 'duration': self.getMovieTime(duration), 'plot': desc, 'genre': 'Film/Serial'}
            rating = elv['age_group']
            if rating != None and len(rating) > 0:
                if rating != '0' :
                    params.update({'mpaa': 'Od '+rating+ ' lat'})
                else:
                    params.update({'mpaa': 'Bez ograniczeń'})
            rel_unixtime = elv['timestamp']
            if rel_unixtime != None:
                t = time.localtime(int(rel_unixtime))
                params.update({'year': time.strftime("%Y",t)})
                params.update({'premiered': time.strftime("%d.%m.%Y",t)})
            movies.append(params)
        for params in sorted(movies, key=lambda x: x['title']):
            self.gui.playVideo(params, isPlayable = True, params_keys_needed = ipla_url_keys)
        self.gui.endDir(False, 'episodes')

    def getMovieTime(self, seconds):
        m = '00'
        s = '00'
        minute = int(seconds) / 60
        m = str(minute)
        if len(m) == 1:
            m = '0' + m
        sec = int(seconds) - (int(minute) * 60)
        s = str(sec)
        if len(s) == 1:
            s = '0' + s
#        time = m + ':' + s      # czas kodi raaportuje tylko w minutach
        time = m
        return time

    def listsHistory(self, table):
        for i in range(len(table)):
            if table[i] <> '':
                params = {'service': SERVICE, 'name': 'history', 'title': table[i],'icon': LOGOURL}
                self.gui.addDir(params)
        self.gui.endDir()

    def handleService(self):
        params = self.parser.getParams()
        name = self.parser.getParam(params, "name")
        title = self.parser.getParam(params, "title")
        category = self.parser.getParam(params, "category")
        page = self.parser.getParam(params, "page")
        link = self.parser.getParam(params, "url")
        path = self.parser.getParam(params, "path")
        service = self.parser.getParam(params, "service")
        action = self.parser.getParam(params, "action")

        self.parser.debugParams(params, dbg)

    #MAIN MENU
        if name == None:
            self.listsMainMenu(SERVICE_MENU_TABLE)
    #KATEGORIE
        if category == self.setTable()[1]:
           self.getCategories(URL_CATEGORIES)

        if name == 'main-categories':
            self.listsTitles(page, category)
        elif name == 'title-categories':
            self.switcher(page, category)
        elif name == 'movie-categories':
            identity = self.getIdentity()
            self.listsMovieVOD(URL_MOVIE + category + '&' + identity)
    #WYSZUKAJ
        if category == self.setTable()[2]:
            text = self.gui.searchInput(SERVICE)
            if text != None:
                self.listsMovieVOD(URL_SEARCH+urllib.quote_plus(text))
    #HISTORIA WYSZUKIWANIA
        if category == self.setTable()[3]:
            t = self.history.loadHistoryFile(SERVICE)
            self.listsHistory(t)
        if name == 'history':
            self.listsMovieVOD(URL_SEARCH+urllib.quote_plus(title))
    #ODTWÓRZ VIDEO
        if name == 'playSelectedVideo':
            self.gui.LOAD_AND_PLAY_VIDEO_WATCHED(page)
    #POBIERZ
        if action == 'download' and link != '':
            self.cm.checkDir(os.path.join(dstpath, SERVICE))
            dwnl = downloader.Downloader()
            dwnl.getFile({ 'title': title, 'url': link, 'path': path })
