# -*- coding: utf-8 -*-

import os, re, sys
import xbmcaddon, xbmcgui
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = 'plugin.video.polishtv.live'
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()

SERVICE = 'polvod'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL =  'http://polvod.pl/api.php?smarttv=&authKey=7b16f80e756f88bec18a82c7754d0c25&device=samsung&ver=1032'

MENU_TABLE = {
    1: "Polecane",
    2: "Najpopularniejsze",
    3: "Kategorie",
    4: "Seriale",
    5: "Wyszukaj",
    6: "Historia wyszukiwania"
}

polvod_proxy = ptv.getSetting('polvod_proxy')
polvod_url_keys = ("service","id","season","category","url")

class polvod:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()
        self.history = sdCommon.history()
        self.api = API()
        
        
    def getMainMenu(self):
        for num, val in MENU_TABLE.items():
            params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': THUMB_SERVICE}
            self.gui.addDir(params, params_keys_needed = polvod_url_keys)
        self.gui.endDir()   

    def getMovieList(self, method, params = []):
        data = self.api.getAPI(method, params)
        for item in data['result']:
            if item['plik'] is not None:
                params = {'service': SERVICE, 'url': item['plik'][0], 'category': 'playSelectedVideo', 'title': item['title'].encode('UTF-8'), 
                          'icon': self.api.icon(item['okladka']), 'plot': item['description_short'].encode('UTF-8'), 'year': item['year'],
                          'country': item['production'].encode('UTF-8'),'genre': self.api.genres(item['genres'])}
                params.update({'duration': self.api.duration(item['duration2']), 'rating': self.api.rating(item['filmweb_ocena'])})
                self.gui.playVideo(params, isPlayable = True, params_keys_needed = polvod_url_keys)
        self.gui.endDir(sort=True, content='movies')

    def getSeriesList(self):
        data = self.api.getAPI('getSeries', ["last",{}])
        for item in data['result']:
            params = {'service': SERVICE, 'id': item['id'], 'category': 'series', 'title': item['title'].encode('UTF-8'), 
                      'icon': self.api.icon(item['okladka']), 'plot': item['description_short'].encode('UTF-8'), 'year': item['year']}
            self.gui.addDir(params, params_keys_needed = polvod_url_keys)
        self.gui.endDir(sort=True)
    
    
    def getEpisodesList(self, id, season):
        data = self.api.getAPI('getVideo',[id])
        g = self.api.genres(data['result']['genres'])
        y = data['result']['year']
        p = data['result']['description_short'].encode('UTF-8')
        for item in data['result']['seasons'][str(season)]['episodes']:
            if item['plik'] is not None:
                if len(item['episode_name']) > 2:
                    t =  'Odcinek '.encode('UTF-8') + item['episode_real_nr'].encode('UTF-8') + ' - ' + item['episode_name'].encode('UTF-8')
                else:
                    t =  'Odcinek ' + item['episode_real_nr']
                params = {'service': SERVICE, 'url': item['plik'][0], 'category': 'playSelectedVideo', 'title': t , 
                          'icon': self.api.icon(item['okladka']),'genre': g, 'year': y , 'plot' : p}
                params.update({'duration': self.api.duration(item['duration']), 'episode': item['episode_nr'] ,'season': str(season)})
                self.gui.playVideo(params, isPlayable = True, params_keys_needed = polvod_url_keys)
        self.gui.endDir(sort=True, content="episodes")

        
    def getSeasonsList(self, id):
        data = self.api.getAPI('getVideo',[id])

        if len(data['result']['seasons']) == 1:
            self.getEpisodesList(id,1)
        else:            
            for i in range(len(data['result']['seasons'])):
                params = {'service': SERVICE, 'id': id, 'season': (i+1), 'category': 'season', 'title': 'Sezon ' + str(i+1), 
                          'icon': self.api.icon(data['result']['seasons']['1']['episodes'][0]['okladka'])}
                self.gui.addDir(params, params_keys_needed = polvod_url_keys)                     
        self.gui.endDir(sort=True)
        
        
    def getCategoriesList(self):
        data = self.api.getAPI('getKategorie')
        for item in data['result']:
            params = {'service': SERVICE, 'id': item['id'], 'category': 'categories', 'title': item['title'].encode('UTF-8'), 'icon': THUMB_SERVICE}
            self.gui.addDir(params, params_keys_needed = polvod_url_keys)
        self.gui.endDir(sort=True)
    
    
    def getHistory(self, table):
        for i in range(len(table)):
            if table[i] <> '':
                params = {'service': SERVICE, 'category': 'history', 'title': table[i],'icon': THUMB_SERVICE}
                self.gui.addDir(params)
        self.gui.endDir()    
    
    
    def handleService(self):
        params = self.parser.getParams()
        title = str(self.parser.getParam(params, "title"))
        category = str(self.parser.getParam(params, "category"))
        season = str(self.parser.getParam(params, "season"))
        url = str(self.parser.getParam(params, "url"))
        id = str(self.parser.getParam(params, "id"))
        
        #MAINMENU
        if category == 'None':
            self.api.geoCheck()
            self.getMainMenu()
            
        #POLECANE       
        if category == MENU_TABLE[1]:
            self.getMovieList('getGlownaFull')
        
        #NAJPOPULRANIEJSZE
        if category == MENU_TABLE[2]:
            self.getMovieList('getTop')
            
        #KATEGORIE
        if category == MENU_TABLE[3]:
            self.getCategoriesList()
        
        #VIDEO W KATEGORII
        if category == 'categories':
             self.getMovieList('getVideosByGenresId',[id])
            
        #SERIALE
        if category == MENU_TABLE[4]:
            self.getSeriesList()

        #SEZONY SERIALU
        if category == 'season':
            self.getEpisodesList(id,season)
            
        #ODCINKI SERIALU
        if category == 'series':
            self.getSeasonsList(id)
            
        #WYSZUKAJ
        if category == MENU_TABLE[5]:
            text = self.gui.searchInput(SERVICE)
            if text != None:
                self.getMovieList('search',[text])
                
        #HISTORIA WYSZUKIWANIA
        if category == MENU_TABLE[6]:
            history = self.history.loadHistoryFile(SERVICE)
            self.getHistory(history)
        if category == 'history':
            self.getMovieList('search',[title])

        #VIDEO
        if category == 'playSelectedVideo':
            self.gui.LOAD_AND_PLAY_VIDEO_WATCHED(url)

class API:
    def __init__(self):
        self.exception = sdErrors.Exception()
        self.common = sdCommon.common()
        self.proxy = sdCommon.proxy()
        
        
    def getAPI(self, method, params = []):
        if polvod_proxy == 'true': url = self.proxy.useProxy(MAINURL)
        else: url = MAINURL
        
        post_data = {"jsonrpc":"2.0","method": method, "params": params, "id":1}
        query_data = {'url': url, 'use_host': False, 'use_header': False, 'use_cookie': False, 'use_post': True, 'raw_post_data': True, 'return_data': True}
        try:
            data = self.common.getURLRequestData(query_data, _json.dumps(post_data))
            result = _json.loads(data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        return result

    def duration(self, duration_sec):
        return str( int(float(duration_sec)) // 60 )

    def icon(self, icon_url):
        return icon_url.replace('150x214','330x0')

    def rating(self, rating_filmweb):
        try:
            a = str( float( rating_filmweb.replace(',','.') ) )
            return a
        except ValueError:
            return ""

    def genres(self, genres_list_or_dict):
        if type(genres_list_or_dict) is list:
            return ' / '.join(genres_list_or_dict).encode('UTF-8')
        if type(genres_list_or_dict) is dict:
            return ' / '.join(genres_list_or_dict.values()).encode('UTF-8')
        return("")
        
    def geoCheck(self):
        if polvod_proxy != 'true':
            if self.proxy.geoCheck() == False:
                d = xbmcgui.Dialog()
                d.ok(SERVICE, 'Limitowany material na terenie twojego kraju.', 'Odwiedz sd-xbmc.org w celu uzyskania pelnego dostepu.')



