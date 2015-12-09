# -*- coding: utf-8 -*-
import os, re, sys
import xbmcaddon, xbmcgui
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json 

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdNavigation, sdErrors

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg

HOST = 'XBMC'
SERVICE = 'poplertv'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'

mainUrl = 'http://www.popler.tv'
apiLiveList = mainUrl + '/api/live_list.php'
apiVOD = mainUrl + '/api/vod.php'

SERVICE_MENU_TABLE = {
    1: "Telewizja na żywo",
    2: "Najnowsze nagrania",
    3: "Najpopularniejsze nagrania",
    4: "Polecane nagrania"
}

class poplertv:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def getVideoTable(self, url):
	query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': True}
	response = self.cm.getURLRequestData(query_data)
	result = _json.loads(response)
	for channel in result:
	    name = self.cm.html_entity_decode(channel['name'].encode('UTF-8'))
	    if name == '':
		path = channel['path'].split('/')
		name = path[-1]
	    error = ''
	    if 'error' in channel:
		if channel['error'] != None:
		    error = channel['error'].encode('UTF-8')
		else:
		    if 'rtsp' in channel:
			self.cm.makeSTRMFile(SERVICE, name, {'page': channel['rtmp'], 'name' : 'playSelectedVideo'} )
	    if error != '':
		label = "[COLOR FFFF0000]" + name + "[/COLOR]"
	    else:
		label = name
	    params = {'service': SERVICE, 'title': label, 'page': channel['rtmp'], 'icon': channel['thumb'], 'error': error}
	    self.gui.playVideo(params)
	self.gui.endDir()

    def handleService(self):
	params = self.parser.getParams()
	name = self.parser.getParam(params, "name")
	title = self.parser.getParam(params, "title")
	page = self.parser.getParam(params, "page")
	category = self.parser.getParam(params, "category")
	error = self.parser.getParam(params, "error")

	self.parser.debugParams(params, dbg)

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(self.setTable())
    #TELEWIZJA NA ŻYWO
	if category == self.setTable()[1]:
	    self.getVideoTable(apiLiveList)
    #NAJNOWSZE NAGRANIA
	if category == self.setTable()[2]:
	    self.getVideoTable(apiVOD + '?func=nowe')
    #NAJPOPULARNIEJSZE NAGRANIA
	if category == self.setTable()[3]:
	   self.getVideoTable(apiVOD + '?func=popularne')
    #POLECANE NAGRANIA
	if category == self.setTable()[4]:
	    self.getVideoTable(apiVOD + '?func=polecane')
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    if error != None:
		d = xbmcgui.Dialog()
		msg = self.cm.formatDialogMsg(error)
		d.ok('popler.tv',msg[0], msg[1], msg[2])
	    else:
		self.gui.LOAD_AND_PLAY_VIDEO(page, title)
