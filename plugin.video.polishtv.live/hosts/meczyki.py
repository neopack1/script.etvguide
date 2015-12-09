# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback, xbmcgui

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

SERVICE = 'meczyki'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + "meczykl.cookie"
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
LOGOURL = BASE_IMAGE_PATH + SERVICE + '.png'
THUMB_NEXT = BASE_IMAGE_PATH +  "dalej.png"
HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()

dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

mainUrl = 'http://meczyki.pl'

MENU_TAB = {
    1: "Mecze na żywo",
    2: "Skróty meczów",
    3: "Filmiki sportowe",
    4: "Wyszukaj",
    5: "Historia Wyszukiwania",
}

class Meczyki:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.up = urlparser.urlparser()
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

    def listsMatchesLive(self, url):
	query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	matchAll = re.compile('<div class="transmission(.+?)</table>', re.DOTALL).findall(data)
	if len(matchAll) > 0:
	    for i in range(len(matchAll)):
		match = re.compile('<div class="time" style="float: left;">(.+?)</div>.+?<div class="name">.+?<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(matchAll[i])
		if len(match) > 0:
		    tytul = match[0][0] + ' ' + ' '.join(match[0][2].translate(None, string.whitespace[:5]).split())
		    tytul =  self.cm.html_entity_decode(re.compile(r'<.*?>').sub('', tytul))
		    params = {'service': SERVICE, 'name':'matchLive', 'title': tytul, 'page': match[0][1],  'icon': LOGOURL}
		    self.gui.addDir(params)
	self.gui.endDir()
	
    def extractHost(self, url):
	query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<td class="flag"><img src="(.+?)" />.+?<span class="channel_name">(.+?)</span>.+?<td class="desc">(.+?)</td>.+?href="(.+?)"', re.DOTALL).findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		    tytul = match[i][2].replace('&nbsp;','').replace('WWW','').strip()+' '+match[i][1].strip()
		    params = {'service': SERVICE, 'title': tytul, 'page': match[i][3].strip(),  'icon': mainUrl + match[i][0]}
		    self.gui.playVideo(params)
	self.gui.endDir()


    def handleService(self):
	params = self.parser.getParams()
	name = self.parser.getParam(params, "name")
	title = self.parser.getParam(params, "title")
	category = self.parser.getParam(params, "category")
	page = self.parser.getParam(params, "page")
	link = self.parser.getParam(params, "url")
	icon = self.parser.getParam(params, "icon")
	service = self.parser.getParam(params, "service")
	action = self.parser.getParam(params, "action")
	path = self.parser.getParam(params, "path")

    	self.parser.debugParams(params, dbg)

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(MENU_TAB)
	    
    #MECZE NA ŻYWO
	if category == self.setTable()[1]:
	    self.listsMatchesLive(mainUrl)
	    
	if name == 'matchLive':
	    self.extractHost(mainUrl + page)
	    
    #WYSZUKAJ
	if category == self.setTable()[4]:
	    text = self.gui.searchInput(SERVICE)
	    self.listsSearch(text)
	    
    #HISTORIA WYSZUKIWANIA
	if category == self.setTable()[5]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)

	if name == 'history':
	    self.listsSearch(title)
	    
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    linkVideo = self.crawlStream(page)
	    log.info("TEST6-1"+str(linkVideo))
	    
    def crawlStream(self,url):
	query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	log.info("TEST7-1"+str(data))

	
