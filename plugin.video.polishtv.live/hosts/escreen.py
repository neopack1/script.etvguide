# -*- coding: utf-8 -*-
import re, sys, os
import xbmcaddon, xbmcgui
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdParser, sdNavigation, sdCommon, sdErrors

log = sdLog.pLog()
SERVICE = 'escreen'

dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

mainUrl = 'https://xbmc.e-screen.tv'
loginUrl = mainUrl + '/api/verify.php'
channelsUrl = mainUrl + '/api/channels'
urlparams=' swfUrl=flowplayer.swf pageUrl=http://pl.e-screen.tv flashVer=XBMC live=true'# swfVfy=true'

username = ptv.getSetting('escreen_login')
password = ptv.getSetting('escreen_password')
hq = ptv.getSetting('escreen_hq') in ('true')

class EScreen:
    def __init__(self):
    	log.info('Loading ' + SERVICE)
        if username == "":
            xbmcgui.Dialog().ok("Serwis E-Screen.tv wymaga logowania", "Nie można uruchomić serwisu bez logowania.[CR][CR]Przejdź do ustawień i wprowadź swoje dane.")

	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.gui = sdNavigation.sdGUI()

    def login(self, post):
        query_data = { 'url': loginUrl, 'use_host': True, 'host': 'XBMC', 'use_cookie': False, 'use_post': True, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data, post)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        obj_data = _json.loads(data)

        if len(obj_data) is 0:
           return False
        else:
           return obj_data[0]['hash']

    def listChannels(self, channels, hash):
    	if len(channels) > 0:
    	    for i in range(len(channels)):
    	    	title = channels[i]['channel']
    	    	icon = channels[i]['icon']
    	    	urlbase = channels[i]['rtmpserver']
    	    	if (hq == True) and (len(channels[i]['hd'])>0):
    	    	    url = urlbase+'/vod?user='+username+'#pass='+hash+'/'+channels[i]['hd']+urlparams
                    title += ' [COLOR red]HD[/COLOR]'
                else:
                    url = urlbase+'/vod?user='+username+'#pass='+hash+'/'+channels[i]['sd']+urlparams
                params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': url, 'icon': icon}
                self.gui.playVideo(params)
        self.gui.endDir()

    def getChannels(self):
        query_data = { 'url': channelsUrl, 'use_host': True, 'host': 'XBMC', 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        obj_data = _json.loads(data)
	return obj_data
	
    def handleService(self):
        params = self.parser.getParams()
        name = self.parser.getParam(params, "name")
        title = self.parser.getParam(params, "title")
        page = self.parser.getParam(params, "page")
        icon = self.parser.getParam(params, "icon")
        service = self.parser.getParam(params, "service")

        self.parser.debugParams(params, dbg)
	#MAIN MENU + LOGOWANIE
        if name == None:
            if username != '' and password != '':
            	loginData = { 'user': username, 'pass': password }
            	hash = self.login(loginData)
            	channels = self.getChannels()
            	self.listChannels(channels, hash)

	#ODTWÓRZ VIDEO
        if name == 'playSelectedVideo':
            self.gui.LOAD_AND_PLAY_VIDEO(page, title)