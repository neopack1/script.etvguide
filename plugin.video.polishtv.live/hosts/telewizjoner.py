# -*- coding: utf-8 -*-
import os, re, sys, xbmc
import xbmcaddon, traceback

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
LOGOURL = ptv.getAddonInfo('path') + os.path.sep + "images" + os.path.sep + "telewizjoner.png"

import sdLog, sdSettings, sdParser, sdCommon, sdNavigation, sdErrors

log = sdLog.pLog()
dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

SERVICE = 'telewizjoner'
MAINURL = 'http://www.telewizjoner.pl'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE + ".cookie"
username = ptv.getSetting('ustream_login')
password = ptv.getSetting('ustream_password')

class Telewizjoner:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()
	

    def listsPlaylists(self):
	query_data = {'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('href="(.+?)" class="link"><img src=".+?" alt="(.+?)" width="75" height="75"/><span class="color"><img src="(.+?)" alt').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		icon = match[i][2]
		title = match[i][1]
		page = MAINURL + match[i][0]
		params = {'service': SERVICE,'dstpath': dstpath, 'title': title, 'page': page, 'icon': icon}
		self.gui.playVideo(params)
	self.gui.endDir()

    def getVideoUrl(self, page):
	query_data = {'url': page, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile("http://www.ustream.tv/embed/(.+?)v").findall(data)
	if len(match) > 0:
            uid = match[0].replace('?', '')
            query_data = {'url': 'http://www.ustream.tv/channel/' + uid, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except Exception, exception:
                traceback.print_exc()
                self.exception.getError(str(exception))
                exit()
            videoUrl = 'http://iphone-streaming.ustream.tv/ustreamVideo/' + uid + '/streams/live/playlist.m3u8'
            query_data = {'url': videoUrl, 'use_host': False, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True}
            try:
                data = self.cm.getURLRequestData(query_data)
            except Exception, exception:
                traceback.print_exc()
                self.exception.getError(str(exception))
                exit()
            if 'Still loading... please try again' in data:
                xbmc.sleep(5000)
                return videoUrl
            if 'EXT-X-STREAM-INF' in data:
                return videoUrl
            else:
                return False
        else:
            return False

    def handleService(self):
	params = self.parser.getParams()
	name = self.parser.getParam(params, "name")
	title = self.parser.getParam(params, "title")
	category = self.parser.getParam(params, "category")
	page = self.parser.getParam(params, "page")
	icon = self.parser.getParam(params, "icon")
	link = self.parser.getParam(params, "url")
	service = self.parser.getParam(params, "service")
	action = self.parser.getParam(params, "action")
	path = self.parser.getParam(params, "path")

	self.parser.debugParams(params, dbg)

    #MAIN MENU
	if name == None:
            loginData = { 'username': username, 'password': password, "remember": "true", "refUrl": "" }
	    self.cm.requestLoginData("https://www.ustream.tv/ajax/experience/login.json?pageUrl=/", '"loggedIn":true', COOKIEFILE, loginData)
            self.listsPlaylists()
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    self.gui.LOAD_AND_PLAY_VIDEO(self.getVideoUrl(page), title)

