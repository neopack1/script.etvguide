# -*- coding: utf-8 -*-
import os, urllib, re, sys
import xbmcaddon, traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()

dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

SERVICE = 'wptv'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'
THUMB_NEXT = ICONURL + 'dalej.png'

MAINURL = 'http://wp.tv/app'

SERVICE_MENU_TABLE = {
    1: "Polecane",
    2: "Kanały",
    3: "Serie",
    4: "TOP100 Tygodnia",
    5: "TOP100 Miesiąca",
    6: "Wyszukaj",
    7: "Historia Wyszukiwania"
}

class WPTV:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.history = sdCommon.history()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return SERVICE_MENU_TABLE

    def listsItems(self, url, clip = True):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	    result = _json.loads(data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	if clip:
	    for item in result['clips']:
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': item['title'].encode('UTF-8'), 'page': item['clipUrl'].encode('UTF-8'), 'icon': item['thumbnail'].encode('UTF-8'), 'plot': item['description'].encode('UTF-8')}
		self.gui.playVideo(params)
	    if result['page'] != result['pageCount']:
		pager = url + "&page=" + str(result['page']+1)
		params = {'service': SERVICE, 'name': 'nextpage', 'title': 'Następna strona', 'page': pager, 'icon': THUMB_NEXT}
	    	self.gui.addDir(params)
	else:
	    for item in result:
		#skip {"catId":4050,"name":"Najnowsze","description":"","logo":null,"priority":0}
		if item['name'] != 'Najnowsze':
		    title = self.cm.html_entity_decode(item['name'].encode('UTF-8'))
		    params = {'service': SERVICE, 'name': 'sub-menu', 'category':str(item['catId']), 'title': title, 'plot': item['description'].encode('UTF-8'), 'icon': item['logo']}
		    self.gui.addDir(params)
	self.gui.endDir()

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsHistory(self, table):
	for i in range(len(table)):
	    if table[i] <> '':
		params = {'service': SERVICE, 'name': 'history', 'title': table[i],'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

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
	    self.listsMainMenu(SERVICE_MENU_TABLE)
    #POLECANE
	if category == self.setTable()[1]:
	    self.listsItems(MAINURL + "/recommended?")
    #KANAŁY
	if category == self.setTable()[2]:
	    self.listsItems(MAINURL + "/channellist?", False)
    #SERIE
	if category == self.setTable()[3]:
	    self.listsItems(MAINURL + "/serieslist?", False)
    #TOP100 TYGODNIA
	if category == self.setTable()[4]:
	    self.listsItems(MAINURL + "/toprated?type=week")
    #TOP100 MIESIACA
	if category == self.setTable()[5]:
	    self.listsItems(MAINURL + "/toprated?type=month")
    #WYSZUKAJ
	if category == self.setTable()[6]:
	    text = self.gui.searchInput(SERVICE)
	    if text != None:
		self.listsItems(MAINURL + "/search?queryType=2&query=" + urllib.quote(text))
    #HISTORIA WYSZUKIWANIA
	if category == self.setTable()[7]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)

	if name == 'history':
	    self.listsItems(MAINURL + "/search?queryType=2&query=" + urllib.quote(title))
    #LISTA ITEMS W KATEGORII/SERIE
	if name == 'sub-menu':
	    self.listsItems(MAINURL + "/cliplist?catid=" + category)
    #NASTEPNA STRONA
	if name == 'nextpage':
	    self.listsItems(page)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    self.gui.LOAD_AND_PLAY_VIDEO(page, title)
    #POBIERZ
	if action == 'download' and link != '':
	    self.cm.checkDir(os.path.join(dstpath, SERVICE))
	    if link.startswith('http://'):
		dwnl = downloader.Downloader()
		dwnl.getFile({ 'title': title, 'url': link, 'path': path })
