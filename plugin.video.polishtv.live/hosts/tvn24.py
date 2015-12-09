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

SERVICE = 'tvn24'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL = 'http://api.tvn24.pl'            
HOST = 'Apache-HttpClient/UNAVAILABLE (java 1.4)'
APIKEY = '70487a5562bef96d33225a1df16ec081'

MENU_TABLE = {
    1: "Najnowsze",
 #   2: "Najwazniejsze",
 #   3: "Informacje",
    4: "Magazyny",
    5: "Kategorie"
}

STATIC_MAGAZINES = [{'id':'FAKTY', 'title':'Fakty', 'icon':'http://www.tvnfakty.pl/assets/images/newsy_2012/nowaczolowka_big.jpg'},
                    {'id':'SPORT', 'title':'Sport', 'icon':''},]

class TVN24:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()
        self.api = API()


    def getMainMenu(self):
        for num, val in MENU_TABLE.items():
            params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': THUMB_SERVICE}
            self.gui.addDir(params)
        self.gui.endDir()		

	
    def getNewest(self, url):  
        data = self.api.getAPI(url)
        for item in data:
            if 'Video_Video' in item['related']:
                url = item['related']['Video_Video']['url'].replace('https','http')
                title = self.common.html_entity_decode(item['related']['Video_Video']['title'].encode('UTF-8'))
                if 'pht_url' in item:
                    icon = item['pht_url'].replace('https','http')
                else:
                    icon = THUMB_SERVICE
                
                params = {'service': SERVICE, 'url': url, 'category': 'playSelectedVideo', 'title': title, 'icon': icon}
                self.gui.addDir(params)
        self.gui.endDir()
        
        
    def getMagazines(self, url):
        data = self.api.getAPI(url)
        for item in data['items']:
            
            title = self.common.html_entity_decode(item['title'].encode('UTF-8'))
            
            if 'Photo_Photo' in item['related']:
                icon = item['related']['Photo_Photo']['url']
            else:
                icon = THUMB_SERVICE
                    
            params = {'service': SERVICE, 'id': item['id'], 'category': 'magazines', 'title': title, 'icon': icon}
            self.gui.addDir(params)
            
        for item in STATIC_MAGAZINES:
            params = {'service': SERVICE, 'id': item['id'], 'category': 'magazines', 'title': item['title'], 'icon': item['icon']}
            self.gui.addDir(params)
        self.gui.endDir(True)
        
        
    def getCategories(self, url):
        data = self.api.getAPI(url)
        for item in data:
            
            title = self.common.html_entity_decode(item['title'].encode('UTF-8'))
            icon = THUMB_SERVICE
                    
            params = {'service': SERVICE, 'id': item['tcg_id'], 'category': 'categories', 'title': title, 'icon': icon}
            self.gui.addDir(params)
        self.gui.endDir()
        

    def getItems(self, url):  #mozna ja uzyc w kilku miejscach
        data = self.api.getAPI(url)
        for item in data['items']:
            if 'Video_Video' in item['related']:
                url = item['related']['Video_Video']['url'].replace('https','http')
                title = self.common.html_entity_decode(item['title'].encode('UTF-8'))
                if 'pht_url' in item:
                    icon = item['pht_url'].replace('https','http')
                else:
                    icon = THUMB_SERVICE
                
                params = {'service': SERVICE, 'url': url, 'category': 'playSelectedVideo', 'title': title, 'icon': icon}
                self.gui.addDir(params)
        self.gui.endDir()

    
    def handleService(self):
        params = self.parser.getParams()
        title = str(self.parser.getParam(params, "title"))
        category = str(self.parser.getParam(params, "category"))
        url = str(self.parser.getParam(params, "url"))
        id = str(self.parser.getParam(params, "id"))
		
		#MAINMENU
        if category == 'None':
            self.getMainMenu()
            
        #NAJNOWSZE
        if category == MENU_TABLE[1]:
            self.getNewest('http://api.tvn24.pl/articles/newest/70487a5562bef96d33225a1df16ec081/100')

        #MAGAZYNY
        if category == MENU_TABLE[4]:
            self.getMagazines('http://api.tvn24.pl/magazines/70487a5562bef96d33225a1df16ec081/1,100') #nie ma paginacji i spokoj
            
        #DETALE MAGAZYNU lub KATEGORII
        if category == 'magazines' or category == 'categories':
            self.getItems('http://api.tvn24.pl/'+ category +'/articles/70487a5562bef96d33225a1df16ec081/' + id + ',1,100') #pasowalo by dozucic paginacje

        #KATEGORIE
        if category == MENU_TABLE[5]:
            self.getCategories('http://api.tvn24.pl/categories/70487a5562bef96d33225a1df16ec081')

        #VIDEO
        if category == 'playSelectedVideo':
            self.common.LOAD_AND_PLAY_VIDEO(url, title)
			
			
class API:
	def __init__(self):
		self.exception = sdErrors.Exception()
		self.common = sdCommon.common()
        
	
	def getAPI(self, url):	
		query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
		try:
			data = self.common.getURLRequestData(query_data)
			result = _json.loads(data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		return result
