# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback, xbmcgui

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

SERVICE = 'estadios'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + "estadios.cookie"
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
LOGOURL = BASE_IMAGE_PATH + SERVICE + '.png'
THUMB_NEXT = BASE_IMAGE_PATH +  "dalej.png"

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()

dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

mainUrl = 'http://estadios.pl/'

MENU_TAB = {
    1: "Mecze na żywo",
    2: "Skróty meczów",
    3: "Kluby",
    4: "Video",
    5: "Szukaj drużyny"
}

class Estadios:
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

    def showLive(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()        
	match = re.compile('class="tabela_mecze_lista"(.+?)class="tabela_mecze_lista_paginacja"', re.DOTALL).findall(data)
	if len(match) > 0:
            match2 = re.compile('align="center">(.+?)</td>\r\n.+?align.+?alt=".+?" /></td>\r\n.+?align=.+?</td>\r\n.+?align.+?src.+?alt="(.+?)" /></td>\r\n.+?align="center"><a href="(.+?)" title="Zobacz mecz"><strong>vs</strong></a></td>\r\n.+?align="center"><img.+?src=.+?alt="(.+?)"').findall(match[0])
            if len (match2) > 0:
                for i in range(len(match2)):
                    title = match2[i][0].replace('<span style="color: #08085e;">', '').replace('</span>', '') + ' > ' + match2[i][1] + ' - ' + match2[i][3]
                    params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': match2[i][2], 'icon': LOGOURL}
                    self.gui.addDir(params)
	self.gui.endDir(False, 'movies')

    def showSkroty(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<a href="(.+?)" title="(.+?)">.+?border="0" alt').findall(data)
	if len(match) > 0:
            for i in range(len(match)):
		params = {'service': SERVICE, 'name': 'skroty-lists', 'title': match[i][1], 'page': match[i][0], 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def listsSkroty(self, url, icon):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()        
	match = re.compile('class="tabela_mecze_lista"(.+?)class="tabela_mecze_lista_paginacja"', re.DOTALL).findall(data)
	if len(match) > 0:
            match2 = re.compile('align="center">(.+?)</td>\r\n.+?<td  bgcolor=".+?" width=".+?" align="center"><img src=".+?" border="0" alt=".+?" /></td>\r\n.+?<td  bgcolor=".+?" width=".+?" align=".+?">(.+?)</td>\r\n.+?<td  bgcolor=".+?" width=".+?" align=".+?"><img width=".+?" src=".+?" border=".+?" alt=".+?" /></td>\r\n.+?<td  bgcolor=".+?" width=".+?" align=".+?"><span class=".+?"><a href="(.+?)" title="Zobacz mecz">(.+?)</a></span></td>\r\n.+?<td  bgcolor=".+?" width=".+?" align=".+?"><img width=".+?" src=".+?" border=".+?" alt="(.+?)"').findall(match[0])
            if len (match2) > 0:
                for i in range(len(match2)):
                    title = match2[i][0].replace('<span style="color: #08085e;">', '').replace('</span>', '') + ' - ' + match2[i][1] + ' ' + match2[i][3] + ' ' + match2[i][4]
                    params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': match2[i][2], 'icon': icon}
                    self.gui.playVideo(params)
	match = re.compile('</font></a></span><span class="pkt"><a href="(.+?)">').findall(data)
	if len(match) > 0:
	    params = {'service': SERVICE, 'name': 'skroty-lists', 'title': 'Następna strona', 'page': mainUrl + match[0], 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir(False, 'movies')

    def showNation(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<td width=".+?"><img src.+?alt="(.+?)" style=').findall(data)
	if len(match) > 0:
            for i in range(len(match)):
		params = {'service': SERVICE, 'name': 'nation-lists', 'title': match[i], 'page': match[i], 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def showVideo(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<a href="http://estadios.pl/video,wszystkie">WSZYSTKIE</a>').findall(data)
	if len(match) > 0:
            for i in range(len(match)):
		params = {'service': SERVICE, 'name': 'nation-lists', 'title': match[i], 'page': match[i], 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def showTeam(self, url, fix):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()        
	match = re.compile('<img src="dodane/liga-flagi/.+?" border="0" alt="'+fix+'"(.+?)class="t"', re.DOTALL).findall(data)
	if len(match) > 0:
            match2 = re.compile('<a href="(.+?)" title="Strona klubu: (.+?)"><img src="(.+?)"').findall(match[0])
            if len (match2) > 0:
                for i in range(len(match2)):
                    title = match2[i][1]
                    link = match2[i][0]
                    img = mainUrl + match2[i][2].replace('male/', '')
                    params = {'service': SERVICE, 'name': 'skroty-lists', 'title': title, 'page': link, 'icon': img}
                    self.gui.addDir(params)
	self.gui.endDir(False, 'movies')


    def extractHost(self, url):
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
		data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
		traceback.print_exc()
		self.exception.getError(str(exception))
		exit()
        match = re.compile('src="(.+?)".+?/iframe></div></div><div').findall(data)
        if len(match)>0:
            if not 'http' in match[0]:
                host  = 'http:' + match[0]
            else:
                host = match[0]
            return host
        return False
                

    def listsSearch(self,text):
	query_data = { 'url': mainUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
        match = re.compile('').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		if text.lower() in match[i][1].lower():
		    img = self.getImage(match[i][0])
		    params = {'service': SERVICE, 'name': 'serial-season', 'title': '', 'page': '', 'icon': ''}
		    self.gui.addDir(params)
	self.gui.endDir(True)

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
	link = self.parser.getParam(params, "url")
	icon = self.parser.getParam(params, "icon")
	service = self.parser.getParam(params, "service")
	action = self.parser.getParam(params, "action")
	path = self.parser.getParam(params, "path")

    	self.parser.debugParams(params, dbg)

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(MENU_TAB)

	if category == self.setTable()[1]:
	    self.showLive(mainUrl + 'mecze-na-zywo')
	    
    #SKRÓTY MECZÓW
	if category == self.setTable()[2]:
	    self.showSkroty(mainUrl + 'skroty-meczow')
	if name == 'skroty-lists':
	    self.listsSkroty(page, icon)

	if category == self.setTable()[3]:
	    self.showNation(mainUrl + 'kluby')
	if name == 'nation-lists':
	    self.showTeam(mainUrl + 'kluby', title)
	    
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
	    linkVideo = None
            ID = self.extractHost(page)
	    if (ID != False):
                linkVideo = self.up.getVideoLink(ID)
	    else:
		d = xbmcgui.Dialog()
		d.ok(SERVICE + ' - przepraszamy', 'Ten materiał nie został jeszcze dodany', 'Zapraszamy w innym terminie.')
		return False
            self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)
