# -*- coding: utf-8 -*-

#TO DO:
# - LIVETV: add more icons
# - VOD: getting URL but not playing :(
# - ARCHIVE: dont know how it works :( broken support in kartina plugin.

import os, re, sys
import xbmcaddon, xbmcgui, xbmc
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = 'plugin.video.polishtv.live'
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()

SERVICE = 'polskytv'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL =  'http://iptv.polsky.tv'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE +".cookie"

SETTINGS = ['stream_server', 'timeshift', 'bitrate', 'timezone']

username = ptv.getSetting('polskytv_login')
password = ptv.getSetting('polskytv_password')
protect_code = ptv.getSetting('polskytv_code')

SERVICE_MENU_TABLE = {
    1: "Telewizja",
    2: "VOD",
    #3: "Archiwum",
    4: "Ustawienia"
}

LOGO_TABLE = {
    537 : "http://www.lyngsat-logo.com/hires/tt/tvp1.png",
    539 : "http://www.lyngsat-logo.com/hires/tt/tvp2.png",
    791 : "http://www.lyngsat-logo.com/hires/tt/tvp_kultura.png",
    819 : "http://www.lyngsat-logo.com/hires/tt/tvp_polonia.png"
}


class polskytv:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()
        self.api = API()
	self.common.checkDir(ptv.getAddonInfo('path') + os.path.sep + "cookies")

    def setTable(self):
    	return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
	data = self.api.getAPI('login','login=' + username + '&pass=' + password)
	if 'error' in data:
	    d = xbmcgui.Dialog()
	    d.ok(SERVICE, data['error']['message'])
	else:	
	    for num, val in table.items():
		if (num==1 or num==4) or (num==2 and data['services']['vod'] == 1) or (num==3 and data['services']['archive'] == 1):
		    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': ''}
		    self.gui.addDir(params)
	    self.gui.endDir()        
        
	
    def getChannelList(self):
        data = self.api.getAPI('channel_list')
        for item in data['groups']:
            for channel in item['channels']:
		icon = self.getChannelLogo(channel['id'], MAINURL + channel['icon'])
                params = {'service': SERVICE, 'category': 'livetv', 'id': channel['id'], 'title': channel['name'].encode('UTF-8'), 'icon': icon}
                self.gui.playVideo(params)
	self.gui.endDir(True)
        

    def getChannelUrl(self, id):
        videoUrl = ''
        data = self.api.getAPI('get_url','cid=' + id)
        if 'url' in data:
            videoUrl = re.sub('http/ts(.*?)\s(.*)', 'http\\1', data['url'])
        return videoUrl
    
    
    def getChannelLogo(self, id, default):
	ret = ''
	if id in LOGO_TABLE:
	    ret = LOGO_TABLE[id]
	else:
	    ret = default
	return ret
    
    
    def getVODGenres(self):
        data = self.api.getAPI('vod_genres')
        for item in data['genres']:
            params = {'service': SERVICE, 'category': 'vod-genres', 'id': item['id'], 'title': item['name'].encode('UTF-8'), 'icon': ''}
            self.gui.addDir(params)
	self.gui.endDir(True)
	
	
    def getVODList(self,id):
        data = self.api.getAPI('vod_list','nums=500&type=last&genre=' +id)
        for item in data['rows']:
            params = {'service': SERVICE, 'category': 'playSelectedVideo', 'id': item['id'], 'title': item['name'].encode('UTF-8'), 'icon': ''}
            self.gui.addDir(params)
	self.gui.endDir(True) 	


    def getVODUrl(self, id):
        videoUrl = ''
        data = self.api.getAPI('vod_geturl','fileid=' + id)
	if 'url' in data:
	    url = data['url'].split(" ")
	    videoUrl = url[0]
	return videoUrl	
    
         
    def getSettings(self):
	ret = {}
	for item in SETTINGS:
	    data = self.api.getAPI('settings','var=' + item)
	    #print str(data)
	    if 'settings' in data:
		ret[data['settings']['name']] = {}
		ret[data['settings']['name']]['current'] = data['settings']['value']
		if 'list' in data['settings']:
		    ret[data['settings']['name']]['list'] = data['settings']['list']	
	return ret
    
    
    def getSettingsList(self):
	data = self.getSettings()
	for item in data:
	    title = item + ': ' + str(data[item]['current'])
	    params = {'service': SERVICE, 'category': 'settings', 'id': item, 'title' : title, 'icon': ''}
	    self.gui.addDir(params)
	self.gui.endDir(True)
    
    
    def getSettingsDetails(self, id):
	data = self.getSettings()
	values = []
	d = xbmcgui.Dialog()
	if id == 'timezone':
	    url = "http://gomashup.com/json.php?fds=geo/timezone/locations"
	    query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_header': False, 'use_post': False, 'return_data': True}
            data = self.common.getURLRequestData(query_data)
	    data = data.replace('(','').replace(')','')
            result = _json.loads(data)
	    for item in result['result']:
		values.append(item['TimeZoneId'] + ' ' + item['GMT'])

	  #  print str(data)
	  #  exit()
	  #  for x in range(-12, 13): values.append(str(x))
	elif id == 'stream_server':
	    for server in data[id]['list']:
		values.append(server['descr'] + ' - ' + server['ip'])
	else: values = data[id]['list']
		
	item = d.select(id, values)
	if item != -1:
	    val = values[item].rsplit(' ')
	    self.setSettings(id, val[-1])
	    xbmc.executebuiltin("Container.Refresh")

    
    def setSettings(self, name, value):
	data = self.api.getAPI('settings_set','var=' + name + '&val=' + value)
	
	   
    def handleService(self):
        params = self.parser.getParams()
	category = str(self.parser.getParam(params, "category")) 
        title = str(self.parser.getParam(params, "title")) 
        id = str(self.parser.getParam(params, "id"))

	print category
        
        #MAIN MENU
        if category == 'None':
	    print "foobar"
	    self.listsMainMenu(SERVICE_MENU_TABLE)
    
	#TELEWIZJA
	if category == self.setTable()[1]:
	   self.getChannelList()
	   
	#VOD KATEGORIE
	if category == self.setTable()[2]:
	   self.getVODGenres()
	   
	#VOD TYTULY W KATEGORII
	if category == 'vod-genres':
	   self.getVODList(id)  	   

	#USTAWIENIA
	if category == self.setTable()[4]:
            settings = self.getSettingsList()

	#ZMIANA USTAWIEN
	if category == 'settings':
	    self.getSettingsDetails(id)

	
	#PLAY LIVE TV
	if category == 'livetv':            
	    videoUrl = self.getChannelUrl(id)
	    if videoUrl != '': self.gui.LOAD_AND_PLAY_VIDEO(videoUrl, title)
	
	#PLAY VOD
	if category == 'playSelectedVideo':
	    videoUrl = self.getVODUrl(id)
	    if videoUrl != '': self.gui.LOAD_AND_PLAY_VIDEO(videoUrl, title)
        
        
class API:
    def __init__(self):
        self.exception = sdErrors.Exception()
        self.common = sdCommon.common()

      
    def getAPI(self, method, args=''):
	url = MAINURL +'/api/json/' + method + '?protect_code=' + protect_code + '&' + args
        query_data = {'url': url, 'use_host': False, 'use_cookie': True, 'load_cookie': True, 'save_cookie': False, 'cookiefile': COOKIEFILE, 'use_header': False, 'use_post': False, 'return_data': True}

        if method == 'login':
            query_data['load_cookie'] = False;
            query_data['save_cookie'] = True;
        try:
            data = self.common.getURLRequestData(query_data)
            result = _json.loads(data)
            
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        return result