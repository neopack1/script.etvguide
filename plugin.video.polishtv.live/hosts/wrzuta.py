# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()
dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

SERVICE = 'wrzuta'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'
THUMB_NEXT = ICONURL + 'dalej.png'

MAINURL = 'http://www.wrzuta.pl'
TOPURL = MAINURL + '/filmy/popularne/'
NEWURL = MAINURL + '/filmy/najnowsze/'
CHANURL= MAINURL + '/kanaly'
CHANLIST = '/wrzucone/katalogi/nazwa_rosnaca/'

SERVICE_MENU_TABLE =  {
    1: "Najpopularniejsze",
    2: "Najnowsze",
    3: "Kanały",
    #4: "Zestawienia",
    5: "Wyszukaj",
    6: "Historia Wyszukiwania",
}

CATEGORIES = {
    '': 'Wszystkie',
    'muzyka': 'Muzyka',
    'filmy_trailery': 'Filmy & Trailery',
    'seriale_animacje': 'Seriale & Animacje',
    'sport': 'Sport',
    'motoryzacja': 'Motoryzacja',
    'humor_rozrywka': 'Humor & Rozrywka',
    'zwierzaki': 'Zwierzaki',
    'gry_tech': 'Gry & Tech',
    'erotyka': 'Erotyka'
}

class Wrzuta:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.up = urlparser.urlparser()
	self.cm = sdCommon.common()
	self.history = sdCommon.history()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsCategories(self, url, category):
	for num, val in CATEGORIES.items():
	    params = {'service': SERVICE, 'name': category, 'page': url+num, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsChannels(self, url, page, category):
	query_data = { 'url': url+'/'+page, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	r = re.compile('class="big-avatar">.+?<img src="(.+?)".+?<a href="(.+?)" class="channel-name">(.+?)</a>', re.DOTALL).findall(data)
	if len(r)>0:
	    for i in range(len(r)):
		params = {'service': SERVICE, 'name': 'chanvideo', 'title': r[i][2], 'page': r[i][1], 'icon': r[i][0]}
		self.gui.addDir(params)
	r2 = re.compile('<a class="paging-next" rel="(.+?)"').findall(data)
	if len(r2)>0:
	    params = {'service': SERVICE, 'name': 'nextpage', 'category': category, 'title': 'Następna strona', 'page': r2[0], 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsChanDirs(self, url, page): #img maybe?
	query_data = { 'url': url+CHANLIST+page, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	r = re.compile('<a href="(.+?)" class="file-name">(.+?)</a>').findall(data)
	log.info("tst2 "+str(r))
	if len(r)>0:
	    params = {'service': SERVICE, 'name': 'chandirvideo', 'title': 'Ostatnio dodane', 'page': url+'/materialy/filmy', 'icon': LOGOURL}
	    self.gui.addDir(params)
	    for i in range(len(r)):
		params = {'service': SERVICE, 'name': 'chandirvideo', 'title': r[i][1], 'page': r[i][0], 'icon': LOGOURL}
		self.gui.addDir(params)
	r2 = re.compile('<a class="paging-next" rel="(.+?)"').findall(data)
	if len(r2)>0:
	    params = {'service': SERVICE, 'name': 'chanvideo', 'category': r2[0], 'title': 'Następna strona', 'page': url, 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsVideo(self,url, name, category): #Duration #mod & join next
    	if category != '': nUrl = url+'/'+category
	else: nUrl = url
	query_data = { 'url': nUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()

    #   r = re.compile('<img src="(.+?)".+? (?:height="81" width="144"|width="144" height="81").+?class="(?:box-entry-duration|mini-time|file-time)">(.+?)<.+?<div class="(?:file-info|info-inside|file-detail)">.+?<a href="(.+?)".+?>(.+?)</a>', re.DOTALL).findall(data)
	if name == 'topvideo' or name == 'newvideo':
	    r = re.compile('<a href="(.+?)" class=".+?">\n.+?\n.+?<img src="(.+?)" alt="(.+?)"').findall(data)
	elif name == 'servideo':
	     r = re.compile('<a href="(.+?)".+?<img src="(.+?)" alt="(.+?)"').findall(data)

	if len(r)>0:
	    for i in range(len(r)):
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': self.cm.html_entity_decode(r[i][2].strip()), 'page': r[i][0], 'icon': r[i][1]}
		self.gui.playVideo(params)
	r2 = re.compile('<a class="paging-next" rel="(.+?)"').findall(data)
	if len(r2)>0:
	    params = {'service': SERVICE, 'name': name, 'category': r2[0], 'title': 'Następna strona', 'page': url, 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsChanVideo(self, url, name, category): #Duration
	query_data = { 'url': url+'/'+category, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	r = re.compile('<img (?:width="184" height="104"|width="144" height="81") src="(.+?)".+?<div class="file-time">(.+?)</div>.+?<a class="file-name" href="(.+?)">(.+?)</a>', re.DOTALL).findall(data)
	if len(r)>0:
	    for i in range(len(r)):
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': self.cm.html_entity_decode(r[i][3].strip()), 'page': r[i][2], 'icon': r[i][0]}
		self.gui.playVideo(params)
	r2 = re.compile('<a class="paging-next" rel="(.+?)"').findall(data)
	if len(r2)>0:
	    params = {'service': SERVICE, 'name': name, 'category': r2[0], 'title': 'Następna strona', 'page': url, 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def getVideoLink(self,url):
	nurl = url.split("/")
	url = 'http://'+ nurl[2] + '/u/' + nurl[4]
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('var _src = {(.+?)};', re.DOTALL).findall(data)
	if len(match) > 0:
	    match2 = re.compile("\t'(.+?)': (.+?),?\n").findall(match[0])
	    for num, item in match2[::-1]:
		if item != '""':
		    parts = re.compile('"(.*?)"').findall(item)
		    linkVideo = ''.join(parts)
		    return linkVideo
	return False

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

	if category == None: category = ''
	if page == None: page = ''

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(SERVICE_MENU_TABLE)
    #NAJPOPULARNIEJSZE
    	elif category == self.setTable()[1]:
	    self.listsCategories(TOPURL, 'topvideo')
    #NAJNOWSZE
    	elif category == self.setTable()[2]:
	    self.listsCategories(NEWURL, 'newvideo')
    #KANAŁY
    	elif category == self.setTable()[3]:
	    self.listsChannels(CHANURL, page, category)
    #ZESTAWIENIA
    	#~ elif category == self.setTable()[4]:
	    #~ pass
    #WYSZUKAJ
	elif category == self.setTable()[5]:
	    text = self.gui.searchInput(SERVICE)
	    url = MAINURL + '/szukaj/filmow/' + urllib.quote_plus(text)
	    self.listsVideo(url, 'servideo', '')
    #HISTORIA WYSZUKIWANIA
	elif category == self.setTable()[6]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)
	if name == 'history':
	    url = MAINURL + '/szukaj/filmow/' + urllib.quote_plus(title)
	    self.listsVideo(url, 'servideo', '')
    #LISTA FILMÓW
    	if name == 'topvideo' or name == 'newvideo' or name == 'servideo':
	    self.listsVideo(page, name, category)

    	if name == 'chanvideo':
	    self.listsChanDirs(page, category)
	
	if name == 'chandirvideo':
	    self.listsChanVideo(page, name, category)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    linkVideo = self.getVideoLink(page)
	    self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)
    #POBIERZ
	if action == 'download' and link != '':
	    if link.startswith('http://'):
		linkVideo = self.getVideoLink(link)
		if linkVideo != False:
		    self.cm.checkDir(os.path.join(dstpath, SERVICE))
		    dwnl = downloader.Downloader()
		    dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })
