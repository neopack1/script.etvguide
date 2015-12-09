# -*- coding: utf-8 -*-
import os, sys
import xbmcaddon, traceback
import StorageServer, re, urllib2,  urllib

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json 

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdNavigation, sdErrors

log = sdLog.pLog()

SERVICE = 'polwizjer'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL  + SERVICE + '.png'
MAINURL = 'http://www.polwizjer.com'
		 
polwizjer_activationkey = ptv.getSetting('polwizjer_activationkey')

MENU_TABLE = {
    1: "Telewizja na zywo",
    2: "Filmy",
#    3: "Seriale polskie",
#    4: "Seriale zagraniczne",
#    5: "Programy informacyjne",
#    6: "Publicystyka",
#    7: "Programy rozrywkowe",
#    8: "Dokument",
    9: "Teatr",
#    10: "Programy dla dzieci",
#    11: "Programy sportowe"
}


class polwizjer:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.parser = sdParser.Parser()
	self.gui = sdNavigation.sdGUI()
	self.common = sdCommon.common()
        self.cache = StorageServer.StorageServer(SERVICE, 1)
        self.serviceCache = self.cache.cacheFunction(self.getSessionId)


    def getSessionId(self):
        post_data = {'format': 'json', 'regkey': polwizjer_activationkey}
	query_data = {'url': 'http://licb.sigmamediaplayer.net', 'use_host': True, 'host': 'Sigma media player v1.3 ' + polwizjer_activationkey, 'use_header': False, 'use_cookie': False, 'use_post': True, 'post_data': post_data, 'return_data': True}
	try:
	    data = self.common.getURLRequestData(query_data, post_data)
	    result = _json.loads(data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	return result


    def getMainMenu(self):
        for num, val in MENU_TABLE.items():
            params = {'service': SERVICE, 'name': val, 'title': val, 'icon': THUMB_SERVICE}
            self.gui.addDir(params)
        self.gui.endDir() 


    def getChannels(self):
	query_data = {'url': MAINURL+ '/kategoria/telewizja-na-zywo/-300/', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	data = self.common.getURLRequestData(query_data)        
        match = re.compile('class="islive">\n.+?<a href="/kategoria/telewizja-na-zywo/channel/(.+?)/-300/" border="0"><img src="/media/stream/img/(.+?)_thumb.png">').findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                params = {'service': SERVICE, 'name' : 'livetv', 'title': match[i][1].capitalize(), 'url': MAINURL +'/kategoria/telewizja-na-zywo/watch/' + match[i][0] + '/', 'icon': MAINURL + '/media/stream/img/' + match[i][1] + '_thumb.png'}
                self.gui.addDir(params)
            self.gui.endDir(False)            


    def getVideoUrl(self, url):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	data = self.common.getURLRequestData(query_data)
        
        ret = ''
        match = re.compile('<location>(.+?)</location>').findall(data)
        if len(match) > 0:
	    
	    #z jakiegos powodu redirect na liveTV ma problem z odtwarzaniem. trzaba bylo zrobic 'ghetto' rozwiazanie
	    if 'playlist.m3u8' in match[0]:
		opener = urllib2.build_opener(NoRedirectHandler())
		urllib2.install_opener(opener)
		request = urllib2.Request(match[0], headers={'User-Agent':'Sigma media player v2.1 ' + self.serviceCache['sessid']})
		response = urllib2.urlopen(request)
		ret = response.info().getheader('Location')
	    else:
		ret = match[0]
        return ret


    def getVOD(self):
	query_data = {'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	data = self.common.getURLRequestData(query_data)        
        match = re.compile('<a href="/kategoria/filmy/(.+?)/">(.+?)</a>').findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                params = {'service': SERVICE, 'name' : 'vod', 'title': match[i][1].capitalize(), 'url': MAINURL +'/kategoria/filmy/' + match[i][0] + '/', 'icon': THUMB_SERVICE}
                self.gui.addDir(params)
            self.gui.endDir(False)

    
    def getVODCategory(self, url):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	data = self.common.getURLRequestData(query_data)
	#href="/opis/archaniol,4142/" class="fileNameHref"> Archanioł</a>
        match = re.compile('href="/opis/(.+?)/" class="fileNameHref">(.+?)</a>').findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                params = {'service': SERVICE, 'name' : 'vod', 'category': 'movie','title': match[i][1], 'url': MAINURL +'/opis/' + match[i][0] + '/', 'icon': THUMB_SERVICE}
                self.gui.addDir(params)
            self.gui.endDir(False)

	
    def getVODVideoUrl(self, url):
	ret = ''
 	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	data = self.common.getURLRequestData(query_data)
	match = re.compile('href="/plik/(.+?)">').findall(data)
	if len(match) > 0:
	    ret = MAINURL + '/plik/' + match[0]
	return ret


    def handleService(self):
	params = self.parser.getParams()
	title = self.parser.getParam(params, "title")
	name = self.parser.getParam(params, "name")
	url = self.parser.getParam(params, "url")
	category = self.parser.getParam(params, "category")

	#MAINMENU
	if name == None:
	    self.getMainMenu()

	#TELEWIZJA NA ZYWO
        if name == MENU_TABLE[1]:
            self.getChannels()

	#FILM
        if name == MENU_TABLE[2]:
            self.getVOD()
	    
	#TEATR
        if name == MENU_TABLE[9]:
            self.getVODCategory(MAINURL + '/kategoria/inne/teart-tv/')
	    
	    
	#KATEGORIE FILMOWE
	if name == 'vod' and category == None:
	    self.getVODCategory(url)
	
	if name == 'vod' and category == 'movie':
	    videoUrl = self.getVODVideoUrl(url)
	    url = self.getVideoUrl(videoUrl)
	    name = 'playSelectedVideo'
	    

        if name == 'livetv':
            url = self.getVideoUrl(url)
            name = 'playSelectedVideo'
            
	
	if name == 'playSelectedVideo':
	    videoUrl = url + '|User-Agent=Sigma media player v2.1 ' + self.serviceCache['sessid']
	    self.gui.LOAD_AND_PLAY_VIDEO(videoUrl, title)
	    
	    
class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl
    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302
