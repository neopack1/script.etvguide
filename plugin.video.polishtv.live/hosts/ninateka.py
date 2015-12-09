# -*- coding: utf-8 -*-
import os, string
import urllib, re, sys
import xbmcaddon, traceback, xbmcgui

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
ptv = xbmcaddon.Addon(scriptID)
language = ptv.getLocalizedString

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
THUMB_NEXT = os.path.join(ptv.getAddonInfo('path'), "images/") + 'dalej.png'

import sdLog, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()

dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

SERVICE = 'ninateka'
MAINURL = 'http://ninateka.pl'
QUERYURL = '/filmy?MediaType=video&Paid=False'
LOGOURL = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'

SERVICE_MENU_TABLE = {
    1: "Wideoteka (wg. kategori)",
    2: "Wideoteka (wg. gatunku)",
    3: "Wyszukaj",
    4: "Historia Wyszukiwania",
    5: "Wyczyść Historię"
}

class Ninateka:
    def __init__(self):
	log.info('Loading ' + SERVICE)
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

    def listsCategoryMenu(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	r = re.compile('li data-codename=".+?"><a href="/filmy/(.+?)">(.+?)</a></li>').findall(data)
	if len(r)>0:
	    for i in range(len(r)):
		params = {'service': SERVICE, 'category': r[i][0], 'name': 'catset', 'title': string.capwords(r[i][1]), 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir(True)

    def listsGenreMenu(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	r = re.compile('<select .+? id="CategoryCodenames" .+?wszystkie gatunki</option>(.+?)</select>', re.DOTALL).findall(data)
	if len(r)>0:
	    r2 = re.compile('<option value="(.+?)">(.+?)</option>').findall(r[0])
	    if len(r2)>0:
		for i in range(len(r2)):
		    params = {'service': SERVICE, 'category': r2[i][0], 'name': 'genset', 'title': string.capwords(self.cm.html_entity_decode(r2[i][1])), 'icon': LOGOURL}
		    self.gui.addDir(params)
	self.gui.endDir(True)

    def parseDuration(self, st):
	hours_minutes = st.split('&')[0]
	t1 = hours_minutes.split(':')
	if len(t1) == 1:
		duration = str( int(t1[0])+1 )
	else:
		duration = str( int(t1[0])*60+int(t1[1])+1 )
	return duration

    def listsWideo(self, url, page):
	query_data = { 'url': url+page, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	pattern = '<a href="(.+?)" class="image">\r\n.+?<img.+?alt="(.+?)" src="(.+?).m=crop.+?" />'
	pattern += '\r\n.+?\r\n.+?\r\n.+?aria-hidden="true">(\d.+?)</span></span>' #duration
	pattern += '\r\n\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?text">(.+?)</span>' #plot
	r = re.compile(pattern).findall(data)
	if len(r)>0:
	    for i in range(len(r)):
		duration = self.parseDuration(r[i][3])
		plot = self.cm.html_entity_decode(r[i][4])
		params = {'service': SERVICE, 'dstpath': dstpath, 'plot': plot, 'duration': duration, 'title': self.cm.html_entity_decode(r[i][1]).strip().replace("|","-"), 'page': MAINURL + r[i][0], 'icon': r[i][2], 'fanart': r[i][2]}
		self.gui.playVideo(params)
	    if 'class="nextPage">Następna &raquo;</a>' in data or 'class="lastPage">Ostatnia &raquo;</a>' in data:
		params = {'service': SERVICE, 'category': url, 'name': 'nextpage', 'title': 'Następna strona', 'page': str(int(page)+1), 'icon': THUMB_NEXT}
		self.gui.addDir(params)
	self.gui.endDir()

    def listsHistory(self, table):
	for i in range(len(table)):
	    if table[i] <> '':
		params = {'service': SERVICE, 'name': 'history', 'title': table[i],'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def getVideoLink(self,url):
	videoID = ''
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('var playerOptionsWithMainSource = (.+?);',).findall(data)
	if len(match) > 0:
		result = _json.loads(match[0])
		for source in result['playlist'][0]['sources']:
			print source['file']
			if source['file'].find("m3u8") >= 0:
				videoID = source['file']
				break
			if source['file'].find("mp4") >= 0: 
				videoID = source['file']
			if source['file'].find("m4a") >= 0: 
				videoID = source['file']
	return videoID

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
    #KATEGORIE
	if category == self.setTable()[1]:
	    self.listsCategoryMenu(MAINURL+"/strona/dostepnosc")
    #GATUNKI
	if category == self.setTable()[2]:
	    self.listsGenreMenu(MAINURL+"/filmy")
    #LISTA FILMÓW
	if name == 'genset' or name == 'catset':
	    url = MAINURL+QUERYURL+"&CategoryCodenames="+category+"&page="
	    self.listsWideo(url, page)

	if name == 'nextpage':
	    self.listsWideo(category, page)
    #WYSZUKAJ
	if category == self.setTable()[3]:
	    text = self.gui.searchInput(SERVICE)
	    url = MAINURL+QUERYURL+"&SearchQuery="+urllib.quote(text)+"&page="
	    self.listsWideo(url, page)
    #HISTORIA WYSZUKIWANIA
	if category == self.setTable()[4]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)

	if name == 'history':
	    url = MAINURL+QUERYURL+"&SearchQuery="+title+"&page="
	    self.listsWideo(url, page)
    #KASOWANIE HISTORII WYSZUKIWANIA
        if category == self.setTable()[5]:
            self.history.clearHistoryItems(SERVICE)
            cleared_msg=language(31001)
            dialog = xbmcgui.Dialog()
            dialog.notification('SD-XBMC', cleared_msg, ptv.getAddonInfo('icon'), 2200, False)
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
