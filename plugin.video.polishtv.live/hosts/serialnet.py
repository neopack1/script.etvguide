# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback
import base64, binascii, xbmcgui

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation, downloader

SERVICE = 'serialnet'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

MAINURL = 'http://serialnet.pl'

MENU_TAB = {
    1: "Seriale alfabetycznie",
    2: "Ostatnio uzupełnione seriale",
    3: "Wyszukaj",
    4: "Historia Wyszukiwania"
}

class SerialNet:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
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

    def showLastParts(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<h2>Ostatnio dodane</h2>(.+?)</div></div>', re.DOTALL).findall(data)
	if len(match) > 0:
	    match2 = re.compile('<a href="http://serialnet.pl(/serial/.+?/.+?)">.+?img.+?src="(.+?)".+?<p id="s_title">(.+?)</p>', re.DOTALL).findall(match[0])
	    if len(match2) > 0:
		for i in range(len(match2)):
		    params = {'service': SERVICE, 'name': 'serial-season', 'tvshowtitle': match2[i][2].strip(),  'title': match2[i][2].strip(), 'page': MAINURL + match2[i][0], 'icon': match2[i][1]}
		    self.gui.addDir(params)
	self.gui.endDir()

    def showSerialTitles(self, letter):
	query_data = {'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
     
	match = re.compile('<li><a href="http://serialnet.pl(/serial-online/.+?/.+?)">(.+?)(?:<p>(.+?)</p>)?</a>').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		addItem = False
		if match[i][2] != '': title = match[i][2].strip()
		else: title = match[i][1].strip()

		if letter == '0 - 9' and (ord(title[0]) < 65 or ord(title[0]) > 91): addItem = True
		if (letter == title[0].upper()): addItem = True
		if (addItem):
		    params = {'service': SERVICE, 'name': 'serial-season', 'tvshowtitle': title,  'title': title, 'page': MAINURL + match[i][0], 'icon': LOGOURL}
		    self.gui.addDir(params)
	self.gui.endDir(True)

    def getInfo(self, data):
	outTab = []
	match = re.compile('img src="(.+?/thumbs/.+?.jpg)"').findall(data)
	if len(match) > 0: imageLink = match[0]
	else: imageLink = ''
	outTab.append(imageLink)
	d = data.replace("<br/>","").replace("\n","")
	match = re.compile('<p><fb:like href=.+?</p><strong>(.+?)</strong></p></div>').findall(d)
	if len(match) > 0: desc = match[0]
	else: desc = ''
	outTab.append(desc)
	return outTab

    def showSeason(self, url, serial):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	info = self.getInfo(data)
	match = re.compile('<div style=".+?"><h3>Sezon (.+?)</h3></div>').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		params = {'service': SERVICE, 'name': 'serial-episode', 'tvshowtitle': serial, 'season': match[i],  'title': 'Sezon '+match[i], 'page': url, 'icon': info[0]}
		self.gui.addDir(params)
	self.gui.endDir(False, 'tvshows', 503)

    def showSerialParts(self, url, serial, sezon):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()

	info = self.getInfo(data)
	#match = re.compile('title="(.+?)".+?href="(.+?)sezon-' + sezon + '-odcinek-(.+?)">').findall(data)
	match = re.compile('a title=.+?style=".+?" href="(.+?)sezon-' + sezon + '-odcinek-(.+?)">').findall(data)

        
	if len(match) > 0:
	    for i in range(len(match)):
		title = '%s S%sE%s' % (serial, sezon, match[i][1])
		link = match[i][0] + "sezon-" + sezon +" -odcinek- " + match[i][1]
		params = {'service': SERVICE, 'dstpath': dstpath, 'episode': match[i][1], 'tvshowtitle': serial, 'season': sezon, 'title': title, 'page': link, 'icon': info[0]}
		self.gui.playVideo(params)
	self.gui.endDir(False, 'episodes', 503)

    def listsSearch(self,tex):
	query_data = { 'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<li><a href="http://serialnet.pl(/serial/.+?/.+?)">(.+?)(?:<p>(.+?)</p>)?</a>').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		if tex.lower() in match[i][2].lower() or tex.lower() in match[i][1].lower():
		    if match[i][2] != '':
			title = match[i][2].strip()
		    else:
			title = match[i][1].strip()
		    params = {'service': SERVICE, 'name': 'serial-season', 'tvshowtitle': title,  'title': title, 'page': MAINURL + match[i][0], 'icon': LOGOURL}
		    self.gui.addDir(params)
	self.gui.endDir(True)

    def listsHistory(self, table):
	for i in range(len(table)):
	    if table[i] <> '':
		params = {'service': SERVICE, 'name': 'history', 'title': table[i],'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def getVideoUrl(self, url):
	servset = self.settings.getSettings(SERVICE)
	videoUrl = ''
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<iframe id="framep" class="radi" src="(.+?)"').findall(data)
	if len(match) > 0:
	    nUrl = match[0]
	    if servset[SERVICE + '_wersja'] == 'false':
		d = xbmcgui.Dialog()
		item = d.select("Wybór wersji", ["Napisy","Bez lektora i napisów"])
		if item == -1: return videoUrl
		elif item == 0: nUrl = match[0] + '&wersja=napisy'
	    nUrl = nUrl+'&wi=va'
	    log.info("wersja: " + nUrl)
	    query_data = {'url': nUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	    data = self.cm.getURLRequestData(query_data)

	    if "url: escape('" in data:
		match = re.compile("url: escape\('(.+?)'\),").findall(data)
		if len(match) > 0: videoUrl = match[0]

	    if "var flm = '" in data and videoUrl == '':
		match = re.compile("var flm = '(.+?)';").findall(data)
		if len(match) > 0: videoUrl = match[0]

	    if 'primary: "html5"' in data and videoUrl == '':
		match = re.compile('file: "(.+?)"').findall(data)
		if len(match) > 0: videoUrl = match[0]

	    if "eval(function(p,a,c,k,e,d)" in data and videoUrl == '':
		match = re.compile('eval\((.+?),0,{}\)\)',re.DOTALL).findall(data)
		if len(match) > 0: videoUrl = self.decodeJS('eval(' + match[0] + ',0,{}))')

	return videoUrl

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
	epizod = self.parser.getParam(params, "episode")
	serial = self.parser.getParam(params, "tvshowtitle")

    	self.parser.debugParams(params, dbg)

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(MENU_TAB)
    #SERIALE ALFABETYCZNIE
	if category == self.setTable()[1]:
	    self.listsABCMenu(self.cm.makeABCList())

	if name == 'abc-menu':
	    self.showSerialTitles(category)
	elif name == 'serial-season':
	    self.showSeason(page, serial)
	elif name == 'serial-episode':
	    self.showSerialParts(page, serial, sezon)
    #OSTATNIO UZUPEŁNIONE SERIALE
	if category == self.setTable()[2]:
	    self.showLastParts(MAINURL)
    #WYSZUKAJ
	if category == self.setTable()[3]:
	    text = self.gui.searchInput(SERVICE)
	    self.listsSearch(text)
    #HISTORIA WYSZUKIWANIA
	if category == self.setTable()[4]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)

	if name == 'history':
	    self.listsSearch(title)
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

    def int2base(self, x, base):
	digs = string.digits + string.lowercase + string.uppercase
	if x < 0: sign = -1
	elif x==0: return '0'
	else: sign = 1
	x *= sign
	digits = []
	while x:
	    digits.append(digs[x % base])
	    x /= base
	if sign < 0:
	    digits.append('-')
	digits.reverse()
	return ''.join(digits)

    def unpack(self, p, a, c, k, e=None, d=None):
	for i in xrange(c-1,-1,-1):
	    if k[i]:
		p = re.sub('\\b'+self.int2base(i,a)+'\\b', k[i], p)
	return p

    def decodeJS(self, s):
	ret = ''
	if len(s) > 0:
	    js = 'unpack' + s[s.find('}(')+1:-1]
	    js = js.replace("unpack('",'''unpack("''').replace(");'",''');"''').replace("\\","/")
	    js = js.replace("//","/").replace("/'","'")
	    js = "self." + js

	    match = re.compile("\('(.+?)'").findall(eval(js))
	    if len(match) > 0:
		ret = base64.b64decode(binascii.unhexlify(match[0].replace("/x","")))
	return ret
