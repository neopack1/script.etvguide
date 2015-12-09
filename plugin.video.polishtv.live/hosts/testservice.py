# -*- coding: utf-8 -*-
import os, re, sys, traceback
import xbmcaddon, xbmcgui

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
scriptname = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
THUMB_NEXT = os.path.join(ptv.getAddonInfo('path'), "images/") + 'dalej.png'

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()
dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

SERVICE = 'testservice'

SERVICE_MENU_TABLE = {
	1: "Testy hostingów",
	2: "Testy kodów HTTP"
}

HTTP_CODES = {
	200: "OK",
	201: "Created",
	202: "Accepted",
	203: "Non-Authoritative Information",
	204: "No Content",
	205: "Reset Content",
	206: "Partial Content",
	300: "Multiple Choices",
	301: "Moved Permanently",
	302: "Found",
	303: "See Other",
	304: "Not Modified",
	305: "Use Proxy",
	306: "Unused",
	307: "Temporary Redirect",
	308: "Permanent Redirect",
	400: "Bad Request",
	401: "Unauthorized",
	402: "Payment Required",
	403: "Forbidden",
	404: "Not Found",
	405: "Method Not Allowed",
	406: "Not Acceptable",
	407: "Proxy Authentication Required",
	408: "Request Timeout",
	409: "Conflict",
	410: "Gone",
	411: "Length Required",
	412: "Precondition Required",
	413: "Request Entry Too Large",
	414: "Request-URI Too Long",
	415: "Unsupported Media Type",
	416: "Requested Range Not Satisfiable",
	417: "Expectation Failed",
	418: "I'm a teapot",
	428: "Precondition Required",
	429: "Too Many Requests",
	431: "Request Header Fields Too Large",
	500: "Internal Server Error",
	501: "Not Implemented",
	502: "Bad Gateway",
	503: "Service Unavailable",
	504: "Gateway Timeout",
	505: "HTTP Version Not Supported",
	511: "Network Authentication Required"
}

class TestService:
	def __init__(self):
		log.info('Loading ' + SERVICE)
		self.settings = sdSettings.TVSettings()
		self.parser = sdParser.Parser()
		self.cm = sdCommon.common()
		self.history = sdCommon.history()
		self.exception = sdErrors.Exception()
		self.gui = sdNavigation.sdGUI()
		self.up = urlparser.urlparser()
		
	def listsMainMenu(self, table):
		tabMenu = []
		for num, val in table.items():
				tabMenu.append(val)
		tabMenu.sort()
		for i in range(len(tabMenu)):
				params = {'service': SERVICE, 'name': 'main-menu', 'title': tabMenu[i], 'category': tabMenu[i]}
				self.gui.addDir(params)
		self.gui.endDir()
		
	def listsHttpCodes(self, table):
		for num, val in table.items():
			params = {'service': SERVICE, 'name': 'http-codes', 'title': "[B]"+str(num)+"[/B] - [I]"+val+"[/I]", 'category': str(num)}
			self.gui.addDir(params)
		self.gui.endDir(True)

	def testUrlParser(self):
		query_data = { 'url': 'http://witczak.net.pl/sdxbmc', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		match = []
		match = re.compile('src="(.+?)"').findall(data)
		return match

	def getHostingTable(self,lists):
		valTab = []
		if len(lists) > 0:
			for i in range(len(lists)):
				hostingname = self.up.getHostName(lists[i])
				valTab.append(self.cm.setLinkTable(lists[i], hostingname))
				log.info(" - Znaleziono serwis "+hostingname+" z linkiem "+lists[i])
			d = xbmcgui.Dialog()
			item = d.select("Wybór hostingu", self.cm.getItemTitles(valTab))
			if item != -1:
				return valTab[item]
			else:
				exit()
		else:
			d = xbmcgui.Dialog()
			d.ok('Brak hostingu', SERVICE + ' - nie dodano jeszcze tego wideo.', 'Zapraszamy w innym terminie.')
			exit()

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
		elif category == SERVICE_MENU_TABLE[1]:
			urls = self.testUrlParser()
			log.info('urlparser Terser')
			url = self.getHostingTable(urls)

			linkVideo = self.up.getVideoLink(url[0])
			self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, "Test hostingu "+url[1])
		elif category == SERVICE_MENU_TABLE[2]:
			self.listsHttpCodes(HTTP_CODES)
			
			
		if name == "http-codes":
			url = "http://httpstat.us/"+category
			query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
			try:
				data = self.cm.getURLRequestData(query_data)
			except Exception, exception:
				log.info("ddd")
				traceback.print_exc()
				self.exception.getError(str(exception))
				exit()
			log.info("test kodu http "+category)
			log.info(data)