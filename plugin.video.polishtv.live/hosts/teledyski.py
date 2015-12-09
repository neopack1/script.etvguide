# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon
import xbmc, traceback

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

SERVICE = 'teledyski'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'
THUMB_NEXT = ICONURL + 'dalej.png'

MAINURL = 'http://www.teledyskihd.pl'
SURL = MAINURL + '/search.php?btn.x=0&btn.y=0&keywords='

MENU_TAB = {
    1: "Kategorie",
    2: "Najnowsze",
    3: "TOP",
    4: "Wyszukaj",
    5: "Historia Wyszukiwania"
}

class Teledyski:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.history = sdCommon.history()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return MENU_TAB

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsCategoriesMenu(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<li class=""><a href="(.+?)-videos-.+?-date.html">(.+?)</a></li>').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		title = self.cm.html_entity_decode(match[i][1])
		params = {'service': SERVICE, 'name': 'submenu','category': match[i][0], 'title': title, 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir(True)

    def getFilmTable(self,url,category,page):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<div class=.+?>(.+?)</div>.\n.+?<div class=.+?>(.+?)</div>.\n.+?<div class=.+?><img src="http://.+?com/vi/(.+?)/0.jpg"').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		img = 'http://i.ytimg.com/vi/' + match[i][2] + '/0.jpg'
		title = match[i][1] + ' - ' + match[i][0]
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': match[i][2], 'icon': img}
		self.gui.playVideo(params)
	match2 = re.compile('<a href="(.+?)">następne &raquo;</a></div>').findall(data)
	if len(match2) > 0:
	    params = {'service': SERVICE, 'category': category, 'name': 'submenu', 'category': category, 'title': 'Następna strona', 'page': str(int(page)+1), 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def getFilmTable1(self,url,category,page):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()

	match = re.compile('<div class="nazwa"><a title="(.+?)" href=".+?">(.+?)</a></div>.+?(?:\n|\r\n?).+?<div class="nazwa2">.+?</div>.+?(?:\n|\r\n?).+?<div class="datai">.+?(?:\n|\r\n?).+?<a title=".+?<img src="http://.+?com/vi/(.+?)/0.jpg"', re.MULTILINE).findall(data)
	#match = re.compile('<div class=.+?><a title="(.+?)" href=".+?">.+?\. ? (.+?)</a></div>.\n.+?<div class.+?</a></div>.\n.+?<div class="datai">.\n.+?<a title=.+?><img src="http://.+?com/vi/(.+?)/0.jpg"').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		img = 'http://i.ytimg.com/vi/' + match[i][2] + '/0.jpg'
		title = match[i][1] + ' - ' + match[i][0]
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': match[i][2], 'icon': img}
		self.gui.playVideo(params)
	match2 = re.compile('<a href="(.+?)">następne &raquo;</a></div>').findall(data)
	if len(match2) > 0:
	    params = {'service': SERVICE, 'category': category, 'name': category, 'category': category, 'title': 'Następna strona', 'page': str(int(page)+1), 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def getFilmSearch(self,url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<div class=.+?>(.+?)</div></a>.\n.+?<div class=.+?>(.+?)</div>.\n.+?<div class=.+?><img src="http://.+?com/vi/(.+?)/0.jpg"').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		img = 'http://i.ytimg.com/vi/' + match[i][2] + '/0.jpg'
		title = match[i][1] + ' - ' + match[i][0]
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': match[i][2], 'icon': img}
		self.gui.playVideo(params)
	self.gui.endDir()

    def listsHistory(self, table):
	for i in range(len(table)):
	    if table[i] <> '':
		params = {'service': SERVICE, 'name': 'history', 'title': table[i],'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def getMovieUrl(self, videoID, download = ''):
	movieUrl = ''
	if download != '':
	    movieUrl = 'plugin://plugin.video.youtube?path=%s&action=download&videoid=%s' % ('/root/video', videoID)
	else:
	    movieUrl = 'plugin://plugin.video.youtube?path=%s&action=play_video&videoid=%s' % ('/root/video', videoID)
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

	if page==None or page=='': page = '1'
    #MAIN MENU
	if name == None:
	    self.listsMainMenu(MENU_TAB)
    #KATEGORIE
	elif category == self.setTable()[1]:
	    self.listsCategoriesMenu(MAINURL)
    #NAJNOWSZE
	elif category == self.setTable()[2]:
	    url = MAINURL + '/newvideos.html?&page=' + page
	    self.getFilmTable1(url, category, page)
    #TOP
	elif category == self.setTable()[3]:
	    url = MAINURL + '/topvideos.html'
	    self.getFilmTable1(url, category, page)
    #WYSZUKAJ
	elif category == self.setTable()[4]:
	    text = self.gui.searchInput(SERVICE)
	    url = SURL + text
	    self.getFilmSearch(url)
    #HISTORIA WYSZUKIWANIA
	elif category == self.setTable()[5]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)	
	if name == 'history':
	    url = SURL + title
	    self.getFilmSearch(url)
	
	if name == 'submenu':
	    url = category + '-videos-' + page + '-date.html'
	    self.getFilmTable(url, category, page)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    self.gui.LOAD_AND_PLAY_VIDEO(self.getMovieUrl(page), title)
    #POBIERZ
	if action == 'download' and link != '':
	    linkVideo = self.getMovieUrl(link, path)
	    if linkVideo.startswith("plugin://plugin.video.youtube"):
		xbmc.executebuiltin('XBMC.RunPlugin(%s)' % (linkVideo))
