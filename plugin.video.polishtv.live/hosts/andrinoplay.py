# -*- coding: utf-8 -*-

import os, re, sys
import xbmcaddon, xbmcgui
import traceback
from xml.dom.minidom import parseString, parse

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = 'plugin.video.polishtv.live'
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()

SERVICE = 'andrinoplay'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL =  'http://cdnx.andrinoplay.pl/index.php/site/'

#andrinoplay_proxy = ptv.getSetting('andrinoplay_proxy')
andrinoplay_proxy = 'false'

class andrinoplay:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()
        self.api = API()


    def getMovieList(self, id):
        data = self.api.getAPI('movies', 'category=' + id)
	for node in data.getElementsByTagName('movie'):
	    print str(node)
            params = {'service': SERVICE, 'id': node.getElementsByTagName('movie_id')[0].firstChild.wholeText, 'category': 'playSelectedVideo', 'title': node.getElementsByTagName('movie_title')[0].firstChild.wholeText.encode('UTF-8'), 'icon': node.getElementsByTagName('movie_thumb')[0].firstChild.wholeText}
            self.gui.addDir(params)
	self.gui.endDir(True)
        
             
        
    def getCategoriesList(self):
        data = self.api.getAPI('categories')
	for node in data.getElementsByTagName('category'):
	    params = {'service': SERVICE, 'id': node.getElementsByTagName('category_name')[0].firstChild.wholeText, 'category': 'categories', 'title': node.getElementsByTagName('category_label')[0].firstChild.wholeText.encode('UTF-8'), 'icon': THUMB_SERVICE}
	    self.gui.addDir(params)
        self.gui.endDir(True)


    def getMovieUrl(self, id):
    	url = ''
    	data = self.api.getAPI('playlist', 'movie=' + id)
    	if len(data) != 0:
    	    url = data[0]['movie_link']
    	return url

    
    def handleService(self):
        params = self.parser.getParams()
        title = str(self.parser.getParam(params, "title"))
        category = str(self.parser.getParam(params, "category"))
        url = str(self.parser.getParam(params, "url"))
        id = str(self.parser.getParam(params, "id"))
        
        #MAINMENU
        if category == 'None':
            self.api.geoCheck()
            self.getCategoriesList()
                   
        #VIDEO W KATEGORII
        if category == 'categories':
             self.getMovieList(id)
            		
        #VIDEO
        if category == 'playSelectedVideo':
            url = self.getMovieUrl(id)
            self.common.LOAD_AND_PLAY_VIDEO(url, title)
			
			
class API:
    def __init__(self):
        self.exception = sdErrors.Exception()
        self.common = sdCommon.common()
	self.proxy = sdCommon.proxy()  

        
    def getAPI(self, method, args=''):
	if args != '':
	    args = '&' + args
	url = MAINURL + method + '?type=smart&limit=500' + args
        if method == 'playlist' and andrinoplay_proxy == 'true': url = self.proxy.useProxy(url)

        query_data = {'url': url, 'use_host': False, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.common.getURLRequestData(query_data)
            
            if method != 'playlist': #XML
            	result = parseString(data)
            else: #JSON
            	result = _json.loads(data)
            	
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        return result


    def geoCheck(self):
        if andrinoplay_proxy != 'true':
            if self.proxy.geoCheck() == False:
                d = xbmcgui.Dialog()
                d.ok(SERVICE, 'Limitowany material na terenie twojego kraju.', 'Odwiedz sd-xbmc.org w celu uzyskania pelnego dostepu.')



