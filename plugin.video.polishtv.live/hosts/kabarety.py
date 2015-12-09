# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback, xbmc

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdNavigation, sdErrors

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

SERVICE = 'kabarety'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'
THUMB_NEXT = ICONURL + 'dalej.png'

MAINURL = 'http://www.kabarety.odpoczywam.net/'
IMGURL = 'http://i.ytimg.com/vi/'

NAJ_LINK = MAINURL + '/bestof/page:'
NOW_LINK = MAINURL + '/index/page:'

SERVICE_MENU_TABLE = {
    1: "Najnowsze",
    2: "Najlepsze",
    3: "Kategorie",
    4: "Wyszukaj",
    5: "Historia wyszukiwania"
}

class Kabarety:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.history = sdCommon.history()
	self.chars = sdCommon.Chars()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def getCategories(self,url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<b>Kategorie</a><br><br>(.+?)<br><br>', re.DOTALL).findall(data)
	if len(match) > 0:
	    match2 = re.compile('href="(.+?)">(.+?)</a>').findall(match[0])
	    if len(match2) > 0:
		for i in range(len(match2)):
		    title = self.cm.html_entity_decode(match2[i][1])
		    params = {'service': SERVICE, 'name': 'category', 'title': title, 'category': match2[i][0], 'icon': LOGOURL}
		    self.gui.addDir(params)
	self.gui.endDir(True)

    def getFilmTab(self, url, page):
	query_data = { 'url': url+page, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	link = data.replace('\n', '') #MOD
	match = re.compile('<a class="video-mini" title="(.+?)" href=".+?">.+?<span class="duration".+?<img class="video-mini-img".+?src="http://i.ytimg.com/vi/(.+?)/0.jpg" />').findall(link)
	if len(match) > 0:
	    for i in range(len(match)):
		title = self.cm.html_entity_decode(match[i][0])
		img = IMGURL + match[i][1] + '/0.jpg'
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': match[i][1], 'icon': img}
		self.gui.playVideo(params)
	match = re.compile('<span><a href=".+?" class="next shadow-main">&raquo;</a></span>').findall(data)
	if len(match) > 0:
	    newpage = str(int(page) + 1)
	    params = {'service': SERVICE, 'name': 'nextpage', 'title': 'Następna strona', 'category': url, 'page': newpage, 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsHistory(self, table):
	for i in range(len(table)):
	    if table[i] <> '':
		params = {'service': SERVICE, 'name': 'history', 'title': table[i],'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def getMovieUrl(self, vID, download = False):
	movieUrl = None
	if download  == True:
	    movieUrl = 'plugin://plugin.video.youtube?path=%s&action=download&videoid=%s' % ('/root/video', vID)
	else:
	    movieUrl = 'plugin://plugin.video.youtube?path=%s&action=play_video&videoid=%s' % ('/root/video', vID)
	return movieUrl

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

	if str(page)=='None' or page=='': page = '1'

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(SERVICE_MENU_TABLE)
    #NAJNOWSZE
	elif category == self.setTable()[1]:
	    self.getFilmTab(NOW_LINK, page)
    #NAJLEPSZE
	elif category == self.setTable()[2]:
	    self.getFilmTab(NAJ_LINK, page)
    #KATEGORIE
	elif category == self.setTable()[3]:
	    self.getCategories(MAINURL)
    #WYSZUKAJ
	elif category == self.setTable()[4]:
	    text = self.gui.searchInput(SERVICE)
	    if text != None:
	    	self.getFilmTab(MAINURL + '/search/' + text + '/page:', page)
    #HISTORIA WYSZUKIWANIA
	elif category == self.setTable()[5]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)

	if name == 'history':
	    self.getFilmTab(MAINURL + '/search/' + title + '/page:', page)
    #LISTA TYTULOW
	if name == 'category' or  name == 'nextpage':
	    url = category + '/page:'
	    self.getFilmTab(url, page)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    page = self.getMovieUrl(page)
	    self.gui.LOAD_AND_PLAY_VIDEO(page, title)
    #POBIERZ
	if action == 'download' and link != '':
	    linkVideo = self.getMovieUrl(link, True)
	    if linkVideo.startswith("plugin://plugin.video.youtube"):
		xbmc.executebuiltin('XBMC.RunPlugin(%s)' % (linkVideo))
