# -*- coding: utf-8 -*-
import os, sys
import xbmcaddon
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = 'plugin.video.polishtv.live'
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)

BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdParser, sdCommon, sdNavigation, sdErrors, urllib

log = sdLog.pLog()

SERVICE = 'goldvod'
LOGOURL = BASE_IMAGE_PATH + SERVICE + '.png'
tmpStrm = ""

SERVICE_MENU_TABLE = { 1: "TV",
			2: "Filmy",
			3: "Seriale",
                        4: "Kabarety"}

login = ptv.getSetting('goldvod_login')
password = ptv.getSetting('goldvod_password')
strmdir = ptv.getSetting('default_strm') + 'goldvod'

class GoldVOD:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.exception = sdErrors.Exception()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()


    def getAPI(self, method, ID=0):
        query_data = { 'url': 'http://goldvod.tv/api/' + method + '.php', 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True}
	post_data = { 'username': login, 'password': password}

        if ID != 0:
            post_data['id'] = ID
        try:
	    data = self.common.getURLRequestData(query_data, post_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
        return data


    def setMainMenu(self):
	for num, val in SERVICE_MENU_TABLE.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listChannels(self):
        result = _json.loads(self.getAPI('getTvChannels'))
        for item in result:
            params = {'service': SERVICE, 'name': 'playSelectedVideo', 'url': item['rtmp'], 'title': item['name'].encode('UTF-8'), 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

        
    def listCategories(self, method, category):
        result = _json.loads(self.getAPI(method))
        for item in result:
            params = {'service': SERVICE, 'name': category, 'category': item['id'], 'title': item['name'], 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()


    def listVODs(self, method, categoryId):
        result = _json.loads(self.getAPI(method, categoryId))
        for item in result:
            params = {'service': SERVICE, 'name': 'playSelectedVideo', 'url': item['urlen'], 'title': item['title'], 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

  

    def handleService(self):
        params = self.parser.getParams()
        name = str(self.parser.getParam(params, "name"))
        title = str(self.parser.getParam(params, "title"))
        category = str(self.parser.getParam(params, "category"))
        url = str(self.parser.getParam(params, "url"))
       
    #MAINMENU
        if name == 'None':
            self.setMainMenu()
    #TV
        if category == SERVICE_MENU_TABLE[1]:
            self.listChannels()
    #FILMY        
        if category == SERVICE_MENU_TABLE[2]:
            self.listCategories('getCategoriesMovie', 'movies')
        if name == 'movies':
            self.listVODs('getMovies', category)
    #SERIALE
        if category == SERVICE_MENU_TABLE[3]:
            self.listCategories('getNameSerials', 'series')
        if name == 'series':
            self.listVODs('getSerials', category)
    #KABARETY        
        if category == SERVICE_MENU_TABLE[4]:
            self.listCategories('getNameCabarets', 'cabarets')            
        if name == 'cabarets':
            self.listVODs('getCabarets', category)

        if name == 'playSelectedVideo':
            self.common.LOAD_AND_PLAY_VIDEO(url, title)

    #CREATE STRM FILES
        result = _json.loads(self.getAPI('getTvChannels'))
        for item in result:
            self.common.makeSTRMFile(SERVICE, item['name'].encode('utf-8'), {'name' : 'playSelectedVideo', 'url' : item['rtmp']})
