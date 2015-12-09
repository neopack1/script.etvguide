# -*- coding: utf-8 -*-
import os, string, urllib, re, sys
import xbmcaddon, time, traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json 

#ToDo
#    Błąd przy wyszukiwaniu filmów z polskimi znakami

scriptID = sys.modules[ "__main__" ].scriptID
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdParser, sdCommon, sdNavigation, sdErrors, downloader, urlparser, xppod

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

SERVICE = 'anyfiles'
LOGOURL = os.path.join(ptv.getAddonInfo('path'), "images/") + SERVICE + '.png'
THUMB_NEXT = os.path.join(ptv.getAddonInfo('path'), "images/") + 'dalej.png'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE +".cookie"

MAINURL = 'http://video.anyfiles.pl'
SEARCHURL = MAINURL + '/Search.jsp'
NEW_LINK = MAINURL + '/najnowsze/0'
HOT_LINK = MAINURL + '/najpopularniejsze/0'
HEADER = {'Referer': MAINURL}

SERVICE_MENU_TABLE = {
    1: "Kategorie",
    2: "Najnowsze",
    3: "Popularne",
    4: "Wyszukaj",
    5: "Historia wyszukiwania"
}

class AnyFiles:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.history = sdCommon.history()
	self.anyfiles = serviceParser()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()
	self.cm.checkDir(ptv.getAddonInfo('path') + os.path.sep + "cookies")

    def setTable(self):
    	return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def searchTab(self, text):
	if SEARCHURL in text:
	    query_data = {'url': text, 'use_host': False, 'use_cookie': True, 'load_cookie': True, 'save_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True, 'use_header': True, 'header': HEADER}
	    pData = {}
	else:
	    query_data = {'url': SEARCHURL, 'use_host': False, 'use_cookie': True, 'load_cookie': False, 'save_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': True, 'return_data': True, 'use_header': True, 'header': HEADER}
	    pData = {'q': text, 'oe': 'polish'}
	try:
	    data = self.cm.getURLRequestData(query_data, pData)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('src="(.+?)" class="icon-img "></a>.+?<a class="box-title" href="(.+?)">(.+?)</a></td></tr>').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': match[i][2], 'page': MAINURL + match[i][1], 'icon': match[i][0]}
		self.gui.playVideo(params)
	    match = re.search('Paginator.+?,(.+?), 8, (.+?),',data)
	    if match:
		if int(match.group(2)) < int(match.group(1)):
		    nextpage = (int(match.group(2))+1) * 18
		    newpage = SEARCHURL + "?st=" + str(nextpage)
		    params = {'service': SERVICE, 'name': 'nextpage', 'title': 'Następna strona', 'page': newpage, 'icon': THUMB_NEXT}
		    self.gui.addDir(params)
	self.gui.endDir()

    def getCategories(self):
	query_data = { 'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<tr><td><a href="(.+?)" class="kat-box-title">.+?</a></td></tr>').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		c = match[i].split('/')
		title = string.capwords(c[1].replace('+',' '))
		params = {'service': SERVICE, 'name': 'category', 'title': title, 'page': MAINURL + match[i], 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir(True)

    def getMovieTab(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'cookiefile' : COOKIEFILE, 'save_cookie': True, 'load_cookie' : False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('src="(.+?)".+?(?:\n|\r\n?).+?(?:\n|\r\n?).+?(?:\n|\r\n?)<tr><td><a href="(.+?)" class="kat-box-name">(.+?)</a>', re.MULTILINE).findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': match[i][2], 'page': MAINURL + match[i][1], 'icon': match[i][0]}
		self.gui.playVideo(params)
	    match = re.search('Paginator.+?,(.+?), 8, (.+?),',data)
	    if match:
		if int(match.group(2)) < int(match.group(1)):
		    p = url.split('/')
		    nextpage = (int(match.group(2))+1) * 20
		if len(p) == 7:
		    newpage = MAINURL + "/" + p[3] + "/" + p[4] + "/" + p[5] + "/" + str(nextpage)
		else:
		    newpage = MAINURL + "/" + p[3] + "/" + str(nextpage)
		params = {'service': SERVICE, 'name': 'nextpage', 'title': 'Następna strona', 'page': newpage, 'icon': THUMB_NEXT}
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
    #KATEGORIE
	if category == self.setTable()[1]:
	   self.getCategories()
    #NAJNOWSZE
	if category == self.setTable()[2]:
	    self.getMovieTab(NEW_LINK)
    #POPULARNE
	if category == self.setTable()[3]:
	    self.getMovieTab(HOT_LINK)
    #LISTA TYTULOW W KATEGORII
	if name == 'category':
	    self.getMovieTab(page)
    #WYSZUKAJ
	if category == self.setTable()[4]:
	    text = self.gui.searchInput(SERVICE)
	    if text != None:
		self.searchTab(text)

	if name == 'nextpage':
	    if SEARCHURL in page:
		self.searchTab(page)
	    else:
	    	self.getMovieTab(page)
    #HISTORIA WYSZUKIWANIA
	if category == self.setTable()[5]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)

	if name == 'history':
	    self.searchTab(title)

    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    linkVideo = self.anyfiles.getVideoUrl(page)
	    self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)

    #POBIERZ
	if action == 'download' and link != '':
	    if link.startswith('http://'):
		linkVideo = self.anyfiles.getVideoUrl(link)
		if linkVideo != False:
		    self.cm.checkDir(os.path.join(dstpath, SERVICE))
		    dwnl = downloader.Downloader()
		    dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })

class serviceParser:
    def __init__(self):
	self.cm = sdCommon.common()
	self.cm.checkDir(ptv.getAddonInfo('path') + os.path.sep + "cookies")

    def getVideoUrl(self,url):
	#show adult content
	#self.cm.addCookieItem(COOKIEFILE, {'name': 'AnyF18', 'value': 'mam18', 'domain': 'video.anyfiles.pl'}, False)

	u = url.split('/')
	fUrl = MAINURL + "/w.jsp?id=%s&width=620&height=349&pos=&skin=0" % (u[-1])
	HEADER = {'Referer' : url, 'Cookie' : 'JSESSIONID=' + self.cm.getCookieItem(COOKIEFILE,'JSESSIONID')}
	query_data = { 'url': fUrl, 'use_host': False, 'use_header': True, 'header': HEADER, 'use_cookie': True, 'cookiefile': COOKIEFILE, 'load_cookie': True, 'save_cookie': True, 'use_post': False, 'return_data': True }
	data = self.cm.getURLRequestData(query_data)

	#add extra cookie
	match = re.search('document.cookie = "([^"]+?)"',data)
	if match:
	    HEADER['Cookie'] = HEADER['Cookie'] + '; ' + match.group(1)
            HEADER['Referer'] = MAINURL + '/flowplaer/flowplayer.commercial-3.2.16.swf'

	    match = re.search("""var flashvars = {[^"]+?config: "([^"]+?)" }""",data)
	    if not match:
		match = re.search('src="/?(pcsevlet\?code=[^"]+?)"', data)
	    if match:
		query_data = { 'url': MAINURL + '/' + match.group(1), 'use_host': False, 'use_cookie': True, 'cookiefile': COOKIEFILE, 'load_cookie': True, 'save_cookie': False, 'use_post': False, 'use_header': True, 'header': HEADER, 'return_data': True }
		data = self.cm.getURLRequestData(query_data)
		match = re.search("""'url':'(http[^']+?mp4)'""",data)
		if match:
		    return match.group(1)
		else:
		    match = re.search("""'url':'api:([^']+?)'""",data)
		    if match:
			plugin = 'plugin://plugin.video.youtube/?action=play_video&videoid=' + match.group(1)
			return plugin
	return False
