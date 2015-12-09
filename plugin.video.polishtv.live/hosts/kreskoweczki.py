# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback
import xbmcgui

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation, downloader, urlparser

SERVICE = 'kreskoweczki'
LOGOURL = os.path.join(ptv.getAddonInfo('path'), "images/") + SERVICE + '.png'
THUMB_NEXT = os.path.join(ptv.getAddonInfo('path'), "images/") + 'dalej.png'

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

MAINURL = 'http://www.kreskoweczki.pl'

MENU_TAB = {
    1: "Kreskówki alfabetycznie",
    2: "Ostatnio uzupełnione",
    3: "Wyszukaj",
    4: "Historia Wyszukiwania"
}

class Kreskoweczki:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.up = urlparser.urlparser()
	self.history = sdCommon.history()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return MENU_TAB

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsABCMenu(self, table):
	for i in range(len(table)):
	    params = {'service': SERVICE, 'name': 'abc-menu','category': table[i], 'title': table[i], 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def showTitles(self, letter):
	query_data = {'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	matchAll = re.compile('<ul class="menu" id="categories_block">(.+?)</ul>', re.DOTALL).findall(data)
	if len(matchAll) > 0:
	    match = re.compile('<a href=.(.+?). class=.level0. alt=.(.+?) \(([0-9]+?)\).>').findall(matchAll[1])
	    if len(match) > 0:
		for i in range(len(match)):
		    addItem = False
		    title = match[i][1].strip()

		    if letter == '0 - 9' and (ord(title[0]) < 65 or ord(title[0]) > 91): addItem = True
		    if (letter == title[0].upper()): addItem = True
		    if int(match[i][2]) == 0: addItem = False
		    if (addItem):
			params = {'service': SERVICE, 'name': 'episode', 'tvshowtitle': title,  'title': title, 'page': match[i][0], 'icon': LOGOURL}
			self.gui.addDir(params)
	self.gui.endDir(True)

    def showParts(self, url):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	matchAll = re.compile("<div class='list-videos'>(.+?)<br />", re.DOTALL).findall(data)
	if len(matchAll) > 0:
	    match = re.compile("<a href='(.+?)' title='(.+?)'><img src='(.+?)'.+?<dt class='series'>.+?title='(.+?)'>", re.DOTALL).findall(matchAll[0])
	    if len(match) > 0:
		for i in range(len(match)):
		    serial = match[i][3]
		    title = '%s - %s' % (serial, match[i][1])
		    link = match[i][0]
		    params = {'service': SERVICE, 'dstpath': dstpath, 'tvshowtitle': serial, 'title': title, 'page': link, 'icon': match[i][2]}
		    self.gui.playVideo(params)
	match2 = re.compile("class='active'>.+?</a>  <a href='(.+?)#'").findall(data)
	log.info(str(match2))
	if len(match2) > 0:
	    params = {'service': SERVICE, 'name': 'nextpage', 'title': 'Następna strona', 'page': match2[0], 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir(False, 'episodes', 503)

    def listsHistory(self, table):
	for i in range(len(table)):
	    if table[i] <> '':
		params = {'service': SERVICE, 'name': 'history', 'title': table[i],'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def getVideoUrl(self, url):
	videoUrl = ''
	vid = re.compile("kreskowka/(.+?)/").findall(url)
	HEADER = {'Referer' : url}
	query_data = {'url': 'http://www.kreskoweczki.pl/fullscreen/', 'use_header': True, 'header': HEADER, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True}
	postdata = {'v_id' : vid[0]}
	try:
	    data = self.cm.getURLRequestData(query_data, postdata)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	matchAll = re.compile("Loader.skipBanners(.+?)Loader.skipBanners", re.DOTALL).findall(data)
	log.info(str(matchAll))
	if len(matchAll) > 0:
	    match = re.compile('Loader.loadFlashFile."(.+?)"').findall(matchAll[0])
	    if len(match) > 0:
		videoUrl = match[0]
	    else:
		match = re.compile('src="(.+?)"').findall(matchAll[0])
		if len(match) > 0:
		    videoUrl = match[0]
	return self.up.getVideoLink(videoUrl)

    def handleService(self):
	params = self.parser.getParams()
	name = self.parser.getParam(params, "name")
	title = self.parser.getParam(params, "title")
	category = self.parser.getParam(params, "category")
	page = self.parser.getParam(params, "page")
	link = self.parser.getParam(params, "url")
	service = self.parser.getParam(params, "service")
	action = self.parser.getParam(params, "action")
	path = self.parser.getParam(params, "path")
	sezon = self.parser.getParam(params, "season")
	serial = self.parser.getParam(params, "tvshowtitle")

    	self.parser.debugParams(params, dbg)

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(MENU_TAB)
    #KRESKÓWKI ALFABETYCZNIE
	if category == self.setTable()[1]:
	    self.listsABCMenu(self.cm.makeABCList())

	if name == 'abc-menu':
	    self.showTitles(category)
	elif name == 'episode' or name == 'nextpage':
	    self.showParts(page)
    #OSTATNIO UZUPEŁNIONE
	if category == self.setTable()[2]:
	    self.showParts(MAINURL)
    #WYSZUKAJ
	if category == self.setTable()[3]:
	    text = self.gui.searchInput(SERVICE)
	    self.showParts(MAINURL+"/search/?keywords="+urllib.quote_plus(text))
    #HISTORIA WYSZUKIWANIA
	if category == self.setTable()[4]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)

	if name == 'history':
	    self.showParts(MAINURL+"/search/?keywords="+urllib.quote_plus(title))
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    videoUrl = self.getVideoUrl(page)
	    self.gui.LOAD_AND_PLAY_VIDEO(videoUrl, title)
    #POBIERZ
	if action == 'download' and link != '':
	    if link.startswith('http://'):
		linkVideo = self.getVideoUrl(link)
		if linkVideo != False:
		    self.cm.checkDir(os.path.join(dstpath, SERVICE))
		    dwnl = downloader.Downloader()
		    dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })
