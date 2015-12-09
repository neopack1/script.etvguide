# -*- coding: utf-8 -*-
#
# Author: SamSamSam - samsamsam@o2.pl
#

import os, string, StringIO
import urllib, urllib2, re, sys
from base64 import b64decode
import xbmcaddon, xbmcgui
import xbmc, traceback
if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()
d = xbmcgui.Dialog()

dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

# host settings
USERNAME  = ptv.getSetting('kinopecetowiec_login')
PASSWORD  = ptv.getSetting('kinopecetowiec_password')
SORTBY    = ptv.getSetting('kinopecetowiec_sort')

SERVICE = 'kinopecetowiec'
MAINURL = 'http://www.kino.pecetowiec.pl'
SERIALS_URL = MAINURL + '/seriale-online.html'
LOGOURL = BASE_IMAGE_PATH + SERVICE + '.png'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE + ".cookie"
THUMB_NEXT = BASE_IMAGE_PATH + "dalej.png"

HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
AJAX_HEADER = dict(HEADER)
AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache'} )

SERVICE_MENU_TABLE = {
    1: "Filmy",
    2: "Seriale",
    3: "Wyszukaj",
    4: "Historia wyszukiwania"
}

def printDBG(txt=''):
    if dbg:
        log.info('kinopecetowiec - printDBG: %s' % txt)
        
def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")
    
def GetDataBeetwenMarkers(data, marker1, marker2, withMarkers=True, caseSensitive=True):
    if caseSensitive: idx1 = data.find(marker1)
    else: idx1 = data.lower().find(marker1.lower())
    if -1 == idx1: return False, ''
    if caseSensitive: idx2 = data.find(marker2, idx1 + len(marker1))
    else: idx2 = data.lower().find(marker2.lower(), idx1 + len(marker1))
    if -1 == idx2: return False, ''
    if withMarkers: idx2 = idx2 + len(marker2)
    else: idx1 = idx1 + len(marker1)
    return True, data[idx1:idx2]

def GetSearchGroups(data, pattern, grupsNum=1):
    tab = []
    match = re.search(pattern, data)
    for idx in range(grupsNum):
        try:    value = match.group(idx + 1)
        except: value = ''
        tab.append(value)
    return tab

def clean_html(html):
    if type(html) == type(u''):
        strType = 'unicode'
    elif type(html) == type(''):
        strType = 'utf-8'
        html = html.decode("utf-8")
    # Newline vs <br />
    html = html.replace('\n', ' ')
    html = re.sub(r'\s*<\s*br\s*/?\s*>\s*', '\n', html)
    html = re.sub(r'<\s*/\s*p\s*>\s*<\s*p[^>]*>', '\n', html)
    # Strip html tags
    html = re.sub('<.*?>', '', html)
    if strType == 'utf-8': 
        html = html.encode("utf-8")
    return html.strip()

def RemoveDoubles(data, pattern):
    while -1 < data.find(pattern+pattern) and '' != pattern:
        data = data.replace(pattern+pattern, pattern)
    return data 

class KinoPecetowiec:
    SORT_BY_MAP = {
    'data premiery'   : 'data-premiery',
    'ocena'           : 'ocena',
    'komentarze'      : 'komentarze', 
    }

    def __init__(self):
        log.info('Loading ' + SERVICE)
        
        #Login data
        self.LOGIN           = USERNAME
        self.PASSWORD        = PASSWORD
        if '' == self.LOGIN.strip() or '' == self.PASSWORD.strip():
            self.PREMIUM = False
        else:
            self.PREMIUM = True
        self.filmssortField  = 'sort_field=%s&sort_method=desc' % KinoPecetowiec.SORT_BY_MAP.get(SORTBY, 'data-premiery')
        
        self.settings = sdSettings.TVSettings()
        self.parser = sdParser.Parser()
        self.up = urlparser.urlparser()
        self.cm = sdCommon.common()
        self.history = sdCommon.history()
        self.exception = sdErrors.Exception()
        self.gui = sdNavigation.sdGUI()
        
    def _cleanHtmlStr(self, str):
        return clean_html(RemoveDoubles(str, ' ').replace(' )', ')').strip())
        
    def _getfromJson(self, data, type='films'):
        try:
            data = _json.loads(data)
            if  isinstance(data, dict):
                data['html'] = data['html'].encode('utf-8')
                if type == 'films':
                    data['moviesCount'] = int(data['moviesCount'])
                    data['promotedCount'] = int(data['moviesCount'])
                if 'lastPage' in data and None == data['lastPage']:
                    data['lastPage'] = False
                return True,data
        except:
            printExc()
        return False,{}
       
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  MAINURL + '/' + url
        return url

    def setTable(self):
        return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'service': SERVICE, 'name': 'main-menu', 'title': val, 'category': val, 'icon': LOGOURL}
            self.gui.addDir(params)
        self.gui.endDir()
        
    def listSerialsAlphabeticallyMenu(self, cItem, nextCategory):
        printDBG("KinoPecetowiec.listSerialsAlphabeticallyMenu")
        query_data = { 'url' : SERIALS_URL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()

        data = GetDataBeetwenMarkers(data, '<div class="filter">', '</ul>', False)[1]
        data = re.compile('<a href="/?(seriale-online,[^"]+?)">[^>]*?<b>([^<]+?)</b>[^>]*?<span[^>]+?class="number">([0-9]+?)<').findall(data)
        for item in data:
            url =  self._getFullUrl( item[0] )
            params = {'service': SERVICE, 'name': 'category', 'title': item[1] + ' (%s)' % item[2], 'category': nextCategory, 'url': url, 'icon': LOGOURL}
            self.gui.addDir(params)
        self.gui.endDir(True)
    
    def listSerials(self, cItem, nextCategory):
        printDBG("KinoPecetowiec.listSerialSeasons cItem[%r]" % cItem)
        
        query_data = { 'url':cItem['url'], 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        
        url = cItem['url']
        page = cItem.get('page', '-1')
        if page != '-1':
            url += '&load'
            NEW_HEADER = dict(AJAX_HEADER)
        else:
            NEW_HEADER = dict(HEADER)
        NEW_HEADER['Referer'] = url

        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True, 'use_header': True, 'header': NEW_HEADER}
        post_data = {'page':page}
        try:
            data = self.cm.getURLRequestData(query_data, post_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        
        if page == '-1':
            tmp = {}
            if 'class="loadMore"' in data: 
                tmp['lastPage'] = False
            else:
                tmp['lastPage'] = True
            tmp['html'] = GetDataBeetwenMarkers(data, '<a href="/seriale-online,wszystkie,0,data-dodania,desc.html">', '<div id="subNav">', False)[1]
            data = tmp
            del tmp
            sts = True
        else:
            sts, data = self._getfromJson(data, 'serials')
        if sts:
            nextPageItem = None
            if False == data.get('lastPage', True):
                page = str(int(page)+1)
                nextPageItem = dict(cItem)
                nextPageItem['page'] = page
                nextPageItem['title'] = 'Następna strona'
            data = data['html'].split('<li>')
            del data[0]
            self.listItems(itemsTab=data, itemType=nextCategory, nextPageItem=nextPageItem)
            
    def listSerialSeasons(self, cItem, category):
        printDBG("KinoPecetowiec.listSerialSeasons cItem[%r]" % cItem)
        
        query_data = { 'url' : cItem['url'], 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()

        plot = GetDataBeetwenMarkers(data, 'itemprop="description">', '</p>', False)[1]
        plot = self._cleanHtmlStr(plot)
        data = GetDataBeetwenMarkers(data, '<div class="season">', '<div class="right">', False)[1]
        data = data.split('<div class="season">')

        for idx in range(len(data)):
            seasonTitle = GetDataBeetwenMarkers(data[idx], '<h3>', '</h3>', False)[1].strip()
            if seasonTitle.startswith('Sezon'):
                params = dict(cItem)
                params.update({'title': seasonTitle, 'plot':plot, 'serialCache': data[idx], 'category':category})
                self.gui.addDir(params)
        self.gui.endDir(True)
    
    def listSerialEpisodes(self, cItem):
        printDBG("listSerialEpisodes")
        if 0 < len(cItem['serialCache']):
            data = cItem['serialCache'].split('</li>')
            for item in data:
                item = re.search('href="/?([^"]+?)">[^<]*?<span class="number">([^<]+?)</span>([^<]+?)<', item)
                if item:
                    url   = self._getFullUrl(item.group(1))
                    title = self._cleanHtmlStr(item.group(2) + ". " + item.group(3))
                    params = dict(cItem)
                    params.update({'service': SERVICE, 'dstpath': dstpath, 'title': title, 'url':url})
                    self.gui.playVideo(params)
        self.gui.endDir(False, 'movies')

    def listFilmsCategories(self, nextCategory):
        printDBG("listFilmsCategories nextCategory[%s]" % nextCategory)
        query_data = { 'url': MAINURL + "/kategorie.html", 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        
        params = {'service': SERVICE, 'name': 'category', 'title': '-- Wszystkie --', 'category': nextCategory, 'cat': 'kategorie', 'icon': LOGOURL}
        self.gui.addDir(params)
        data  = GetDataBeetwenMarkers(data, '<ul class="videosCategories">', '</ul>', False)[1]
        data  = re.compile('href="/?(filmy,[^,]+?)\.[^>]+?>(.+?)</a>', re.DOTALL).findall(data)
        for item in data:
            params = {'service': SERVICE, 'name': 'category', 'title': self._cleanHtmlStr(item[1]), 'category': nextCategory, 'cat': item[0], 'icon': LOGOURL}
            self.gui.addDir(params)
        self.gui.endDir(True)
        
    def listFilmsFilters(self, cItem, nextCategory): 
        printDBG('KinoPecetowiec.listFilmsFilters cat[%s]' % cItem['cat'])
        query_data = { 'url': MAINURL + '/' + cItem['cat'] + ".html", 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        data  = GetDataBeetwenMarkers(data, '<div class="filter">', '</div>', False)[1]
        rawQFilters  = re.compile('href="/?%s,0,([^,]+?),wszystkie,dowolny-rok,,([^,.]+?)\..+?<b>([^<>"]+?)</b>.+?lass="number">([0-9]+?)<' % cItem['cat'], re.DOTALL).findall(data)
        rawLFilters  = re.compile('href="/?%s,0,([^,.]+?)\..+?<b>([^<>"]+?)</b>.+?lass="number">([0-9]+?)<' % cItem['cat'], re.DOTALL).findall(data)
        del data
        baseParams = dict(cItem)
        baseParams.update({'category': nextCategory, 'qual':'wszystkie', 'lang':'wszystkie'})
        
        params = dict(baseParams)
        params.update({'title': '-- Wszystkie --'})
        self.gui.addDir( params )
        for item in rawQFilters:
            if 'Wszystkie' not in item[2] and 0 < int(item[3]):
                params = dict(baseParams)
                params.update({'title': self._cleanHtmlStr(item[2]) + ' (%s)' % item[3], 'lang': item[0], 'qual': item[1]})
                self.gui.addDir( params )
        for item in rawLFilters:
            params = dict(baseParams)
            params.update({'title': self._cleanHtmlStr(item[1]) + ' (%s)' % item[2], 'lang': item[0]})
            self.gui.addDir( params )
        self.gui.endDir(True)
        
    def listFilms(self, cItem):
        printDBG("KinoPecetowiec.listFilms cItem[%r]" % cItem)
        page = cItem.get('page', '0')

        url = MAINURL + '/%s,0,%s,wszystkie,dowolny-rok,,%s.html' % (cItem['cat'], cItem['lang'], cItem['qual']) + '?' + self.filmssortField + '&load=1&moviesCount=%s&promotedCount=%s' % (cItem.get('moviesCount', 0), cItem.get('promotedCount', 0),)
        NEW_HEADER = dict(AJAX_HEADER)
        NEW_HEADER['Referer'] = url
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True, 'use_header': True, 'header': NEW_HEADER}
        post_data = {'page':page}
        try:
            data = self.cm.getURLRequestData(query_data, post_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        
        sts, data = self._getfromJson(data)
        if sts:
            nextPageItem = None
            # Unfortunately nextPage can not be checked based on filed 'lastPage'
            # because its contain wrong information sometimes
            #if False == data.get('lastPage', True):
            try:
                url = MAINURL + '/%s,0,%s,wszystkie,dowolny-rok,,%s.html' % (cItem['cat'], cItem['lang'], cItem['qual']) + '?' + self.filmssortField + '&load=1&moviesCount=%s&promotedCount=%s' % (data.get('moviesCount', 0), data.get('promotedCount', 0),)
                query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True, 'use_header': True, 'header': NEW_HEADER}
                post_data = {'page':str(int(page)+1)}
                try:    data2 = self.cm.getURLRequestData(query_data, post_data)
                except: printExc()
                sts, data2 = self._getfromJson(data2)
                data2 = data2['html']
                if '</li>' in data2:
                    page = str(int(page)+1)
                    nextPageItem = dict(cItem)
                    nextPageItem['page'] = page
                    nextPageItem['title'] = 'Następna strona'
                    nextPageItem['moviesCount'] = data['moviesCount']
                    nextPageItem['promotedCount'] = data['promotedCount']
                del data2
            except:
                printExc()

            data = data['html'].split('</li>')
            self.listItems(itemsTab=data, itemType='video', nextPageItem=nextPageItem, addParams= {'lang': cItem['lang'], 'qual': cItem['qual']})
        
    def listItems(self, itemsTab, itemType, nextPageItem=None, getPlot=None, addParams={}):
        printDBG("KinoPecetowiec.listItems itemsTab.len[%d]" % (len(itemsTab)) )
        for item in itemsTab:
            icon  = GetSearchGroups(item, 'src="([^"]+?jpg)"')[0]
            if '' == icon:
                icon  = GetSearchGroups(item, "background-image: url\('([^']+?\.jpg)'")[0].replace('_vertical', '').replace('_horizontal', '').replace('_promo', '')
            url   = GetSearchGroups(item, 'data-url="([^"]+?)"')[0]

            title = self._cleanHtmlStr( GetDataBeetwenMarkers(item, '<div class="t1">', '</div>', False)[1] )
            subTitle = self._cleanHtmlStr( GetDataBeetwenMarkers(item, '<div class="t2">', '</div>', False)[1] )
            if '' != subTitle:
                title += " (%s)" % subTitle

            if None == getPlot: plot = GetDataBeetwenMarkers(item, '<div class="description">', '<a', False)[1]
            else:               plot = getPlot(item)
            plot  = self._cleanHtmlStr(plot)
            # validate data
            if '' == url or '' == title: continue
            url = self._getFullUrl(url)
            icon = self._getFullUrl(icon)
            
            if 'video' == itemType:
                params = {'service': SERVICE, 'dstpath': dstpath, 'title':title, 'url':url, 'icon':icon, 'plot': plot}
                params.update(addParams)
                self.gui.playVideo(params)
            else:
                params = {'service': SERVICE, 'name': 'category', 'title':title, 'category': itemType, 'url':url, 'icon':icon, 'plot': plot}
                params.update(addParams)
                self.gui.addDir(params)
                
        if None != nextPageItem:
            self.gui.addDir(nextPageItem)
        self.gui.endDir(False, 'movies')

    def listsHistory(self, table, ser):
        for i in range(len(table)):
            if table[i] <> '':
                params = {'service': SERVICE, 'name': 'history', 'category': ser, 'title': table[i],'icon':'' }
                self.gui.addDir(params)
        self.gui.endDir()

    def getLinks(self, verItem, playerType):
        printDBG("getLinks verItem[%r], playerType[%r]" % (verItem, playerType) )
        hostingTab = []
        NEW_HEADER = dict(HEADER)
        NEW_HEADER['Referer'] = verItem['url']
        params = {  'action'    :'getPlayer',
                    'playerType':playerType['val'],
                    'fileId'    :'' }
        formatLang = ''
        if 'lang' in verItem:
            params['fileLang'] = verItem['lang']
            formatLang += ' | ' + verItem['lang']
        if 'type' in verItem:
            params['fileType'] = verItem['type']
            formatLang += ' | ' + verItem['type']
        if 'title' in verItem:
            formatLang += ' | ' + verItem['title']

        if 'free' == playerType['val']:
            query_data = {'url': verItem['url'], 'use_host': False, 'use_post': True, 'return_data': True, 'use_header': True, 'header': NEW_HEADER, 'use_cookie': False}
        else:
            query_data = {'url': verItem['url'], 'use_host': False, 'use_post': True, 'return_data': True, 'use_header': True, 'header': NEW_HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': COOKIEFILE}
        
        try:
            data = self.cm.getURLRequestData(query_data, params)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
            
        print "KUPS"
        data = GetSearchGroups(data, '<div id="player-element"[^>]+?data-key="([^>]+?)"[^>]+?>')[0]
        try: data = b64decode(data[2:]).replace('\\/', '/')
        except: data = ''
        if 'stream.streamo.tv' in data:
            videoUrl = GetSearchGroups(data, '"url":"([^"]+?)"')[0]
            urlTitle = '%s %s %s' % (verItem['lang'], verItem['type'], playerType['val'])
            hostingTab.append( {'name': urlTitle, 'url': videoUrl} )        
            
        #data = GetDataBeetwenMarkers(data, '<div class="services">', '</div>', False)[1]
        #data = re.compile('data-id="([0-9]+?)"[^>]*?>([^<]+?)<').findall(data) #data-playertype="([^"]+?)"
        #for item in data:
        #    tmp = {'name': '%s %s | %s' % (playerType['title'], formatLang, self._cleanHtmlStr(item[1])), 'url': '%s|%s|%s|%s|%s' % (verItem['url'], verItem.get('lang',''), verItem.get('type', ''), playerType['val'], item[0]) } # url|fileLang|fileType|playerType|fileId
        #    hostingTab.append(tmp)
        return hostingTab
    
    def getHostingTable(self, url):
        printDBG("getHostingTable url[%s]" % url)
            
        hostingTab = []
        verTab = []
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        
        avTypes = GetDataBeetwenMarkers(data, 'var __avTypes = ', ';', False)[1]
        try:
            avTypes = _json.loads(avTypes)
            for type in avTypes.keys():
                for lang in avTypes[type]:
                    item = {'url':url, 'lang':lang, 'type':type}
                    if item in verTab:
                        printExc('KinoPecetowiec.getHostingTable: link duplication!!!')
                    else:
                        verTab.append(item)
        except:
            printExc()
            
        if 0 == len(verTab):
            data = GetDataBeetwenMarkers(data, '<li class="icons">', '</li>', False)[1]
            data = re.compile('<a href="/?([^"]+?)">[^<]*?<span class="[^"]+?" title="([^"]+?)"').findall(data)
            for item in data:
                if item[1] == 'SD': continue
                tmpUrl = item[0]
                tmpUrl = self._getFullUrl(tmpUrl)
                verTab.append( {'url': tmpUrl, 'title': item[1]} )
            
        for verItem in verTab: 
            tmpTab = []
            if self.PREMIUM:
                tmpTab = self.getLinks(verItem, {'val': 'premium', 'title':'Premium'})
            if 0 == len(tmpTab):
                tmpTab = self.getLinks(verItem, {'val': 'free', 'title':'Free'})
            hostingTab.extend(tmpTab)

        return self.hostSelect(hostingTab)
        
    def hostSelect(self, hostingTab):
        if len(hostingTab) > 0:
            valTab = []
            i = 0
            for item in hostingTab:
                i=i+1
                valTab.append(str(i) + '. ' + item['name'])
            item = d.select("Wybor hostingu", valTab)
            if item >= 0: 
                printDBG(hostingTab[item]['url'])
                return hostingTab[item]['url']
            return False
        d.ok ('Brak linkow','Przykro nam, ale nie znalezlismy zadnego linku do video.', 'Sproboj ponownie za jakis czas')
        return False
        
    def getLink(self, url):
        printDBG("getLink url[%s]" % url)
        urlItem = url.split('|')
        # url|fileLang|fileType|playerType|fileId
        if 5 == len(urlItem):
            url        = urlItem[0]
            post_data = {  'action'    :'getPlayer',
                           'playerType':urlItem[3] }
            if '' != urlItem[1]:
                post_data['fileLang'] = urlItem[1]
                post_data['fileId'] = urlItem[4]
            if '' != urlItem[2]:
                post_data['fileType'] = urlItem[2]
                post_data['fileId'] = urlItem[4]
            if 'fileId' not in post_data:
                post_data['id'] = urlItem[4]

            NEW_HEADER = dict(AJAX_HEADER)
            NEW_HEADER['Referer'] = url
            if 'free' == urlItem[3]:
                query_data = {'url': url, 'use_host': False, 'use_post': True, 'return_data': True, 'use_header': True, 'header': NEW_HEADER, 'use_cookie': False}
            else:
                query_data = {'url': url, 'use_host': False, 'use_post': True, 'return_data': True, 'use_header': True, 'header': NEW_HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': COOKIEFILE}
            try:
                data = self.cm.getURLRequestData(query_data, post_data)
            except Exception, exception:
                traceback.print_exc()
                self.exception.getError(str(exception))
                exit()
            
            if 'free' == urlItem[3]:
                data = GetSearchGroups(data, '<iframe [^>]*?src="([^"]+?)"')[0]
                query_data = { 'url': data, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
                try:
                    data = self.cm.getURLRequestData(query_data)
                except Exception, exception:
                    traceback.print_exc()
                    self.exception.getError(str(exception))
                    exit()
                data = GetSearchGroups(data, '<iframe [^>]*?src="([^"]+?)"')[0]
                return self.up.getVideoLink( data )
            else:
                return GetSearchGroups(data, 'url: [\'"](http[^\'"]+?)[\'"]')[0]
        return False

    def getStype(self):
        stype = ''
        wybierz = ['Filmy','Seriale']
        d = xbmcgui.Dialog()
        item = d.select("Co chcesz znaleść?", wybierz)
        if item == 0:
            stype =  'Filmy:'
        elif item == 1:
            stype = 'Seriale:'
        return stype
        
    def listSearchResults(self, pattern, searchType):
        printDBG("KinoPecetowiec.listSearchResults pattern[%s], searchType[%s]" % (pattern, searchType))
        url = MAINURL + '/szukaj.html?query=%s&mID=' % pattern
        query_data = { 'url' : url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        if 'Filmy:' == searchType:
            sts, data = GetDataBeetwenMarkers(data, 'id="movies-res"', 'res">', False)
            category = 'video'
        else:
            sts, data = GetDataBeetwenMarkers(data, 'id="serials-res"', 'res">', False)
            category = 'serial_seasons_list'
        data = data.split('<li>')
        self.listItems(data, category)  
        
    def tryTologin(self):
        if not self.PREMIUM:
            return
        printDBG('tryTologin start')
        loginData = {'email':self.LOGIN, 'password':self.PASSWORD}
        self.cm.requestLoginData(MAINURL + "/logowanie.html", 'wyloguj.html', COOKIEFILE, loginData)

    def handleService(self):
        params   = self.parser.getParams()
        name     = self.parser.getParam(params, "name")
        title    = self.parser.getParam(params, "title")
        category = self.parser.getParam(params, "category")
        cat      = self.parser.getParam(params, "cat")
        page     = self.parser.getParam(params, "page")
        icon     = self.parser.getParam(params, "icon")
        link     = self.parser.getParam(params, "url")
        service  = self.parser.getParam(params, "service")
        action   = self.parser.getParam(params, "action")
        path     = self.parser.getParam(params, "path")

        self.parser.debugParams(params, dbg)

        if page==None or page=='': page = '1'

    #MAIN MENU
        if name == None:
            self.tryTologin()
            self.listsMainMenu(SERVICE_MENU_TABLE)
    #FILMY
        elif category == self.setTable()[1]:
            self.listFilmsCategories('films_filters')
        elif category == 'films_filters':
            self.listFilmsFilters(params, 'films_list')
        elif category == "films_list":
            self.listFilms(params)
    #SERIALE
        elif category == "Seriale":
            self.listSerialsAlphabeticallyMenu(params, 'serials_list')
        elif category == "serials_list":
            self.listSerials(params, 'serial_seasons_list')
        elif category == "serial_seasons_list":
            self.listSerialSeasons(params, 'serial_episodes_list')
        elif category == "serial_episodes_list":
            self.listSerialEpisodes(params)
    #WYSZUKAJ
        elif category == self.setTable()[3]:
            searchType = self.getStype()
            searchPattern = self.gui.searchInput(SERVICE + searchType)
            if searchPattern != None:
                pattern = urllib.quote_plus(searchPattern)
                self.listSearchResults(pattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == self.setTable()[4]:
            searchType = self.getStype()
            t = self.history.loadHistoryFile(SERVICE + searchType)
            self.listsHistory(t, searchType)
        if name == 'history':
            pattern = urllib.quote_plus(title)
            self.listSearchResults(pattern, category)
    #ODTWÓRZ VIDEO
        if name == 'playSelectedVideo':

            url = self.getHostingTable(link)
            print "KUPS"
            print str(url)
            if url != False:
                self.gui.LOAD_AND_PLAY_VIDEO(url, title)
            else:
                pass
    #POBIERZ
        if action == 'download' and link != '':
            if link.startswith('http://'):
                linkVideo = self.getLink(self.getHostingTable(link))
                if linkVideo != False:
                    self.cm.checkDir(os.path.join(dstpath, SERVICE))
                    dwnl = downloader.Downloader()
                    dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })
