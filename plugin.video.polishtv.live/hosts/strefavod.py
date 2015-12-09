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

SERVICE = 'strefavod'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL =  'http://samsung.api.strefavod.pl/api/'

MENU_TABLE = {
    1: "Polecane",
    2: "Kategorie"
}

strefavod_quality = ptv.getSetting('strefavod_quality')

class strefavod:
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
            self.gui.addDir(params)
        self.gui.endDir()   


    def getMovieList(self, id=0):
    	if (id != 0):
            data = self.api.getAPI('GetMovies', 'categoryIds=' + id)
        else:
            data = self.api.getAPI('GetPromoMovies')
        for item in data['Result']['Movies']:
	    icon = item['ImageUrl'].replace('Baner','PlayerLarge')
            params = {'service': SERVICE, 'id': item['Id'], 'category': 'playSelectedVideo', 'title': item['Title'].encode('UTF-8'), 'icon': icon.encode('UTF-8')}
	    self.gui.addDir(params)
        self.gui.endDir(True)
        
      
    def getCategoriesList(self):
        data = self.api.getAPI('GetCategories','type=Genre')
        for item in data['Result']:
	    params = {'service': SERVICE, 'id': item['Id'], 'category': 'categories', 'title': item['Name'].encode('UTF-8'), 'icon': THUMB_SERVICE}
	    self.gui.addDir(params)
        self.gui.endDir(True)
    

    def getMovieUrl(self, id):
	if strefavod_quality == 'Wysoka': mediaFormat = 'HLS'
	else: mediaFormat = 'MP4'
    	url = ''
	
        data = self.api.getAPI('GetMovie', 'id=' + id)
        for item in data['Result']['Movie']['MediaFiles']:
            if item['MediaFileRole'] == 'Main':
		for media in item['MediaFileFormats']:
		    if media['Container'] == mediaFormat:
                  	url = media['Url']
	return url 
    
    
    def handleService(self):
        params = self.parser.getParams()
        title = str(self.parser.getParam(params, "title")) 
        category = str(self.parser.getParam(params, "category")) 
        id = str(self.parser.getParam(params, "id")) 
        
        #MAINMENU
        if category == 'None':
            self.getMainMenu()

        #POLECANE       
        if category == MENU_TABLE[1]:
            self.getMovieList()  
            
        #KATEGORIE
        if category == MENU_TABLE[2]:
            self.getCategoriesList()
        
        #VIDEO W KATEGORII
        if category == 'categories':
	    self.getMovieList(id)            
		
        #VIDEO
        if category == 'playSelectedVideo':
	    videoUrl = self.getMovieUrl(id) 
            self.common.LOAD_AND_PLAY_VIDEO(videoUrl, title)
			
			
class API:
    def __init__(self):
        self.exception = sdErrors.Exception()
        self.common = sdCommon.common()
        
        
    def getAPI(self, method, args=''):	    
	url = MAINURL + method + '?limit=1000&sort=Name&' + args
        query_data = {'url': url, 'use_host': False, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.common.getURLRequestData(query_data)
            result = _json.loads(data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        return result




