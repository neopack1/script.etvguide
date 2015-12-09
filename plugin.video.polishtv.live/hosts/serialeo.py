# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback, xbmcgui

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

SERVICE = 'serialeo'
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
LOGOURL = BASE_IMAGE_PATH + 'serialeo.png'
THUMB_NEXT = BASE_IMAGE_PATH + "dalej.png"

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()

dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

mainUrl = 'http://serialeonline.org.pl/'
NewUrl = mainUrl + 'nowe-odcinki'
SerchUrl = mainUrl + 'index.php?menu=search&query='


MENU_TAB = {
	1: "Kategorie",
	2: "Ostatnio uzupełnione seriale",
	3: "Wyszukaj",
	4: "Historia Wyszukiwania"
        }

class serialeo:
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

	def listsKATMenu(self, url):
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		match = re.compile(mainUrl + 'tv-tagi/(.+?)">(.+?)</a>').findall(data)
		if len(match) > 0:
                        for i in range(len(match)):
                                page = mainUrl + 'tv-tagi/' + match[i][0]
                                params = {'service': SERVICE, 'name': 'kat-menu', 'tvshowtitle': '',  'title': match[i][1], 'page': page, 'icon': LOGOURL}
                                self.gui.addDir(params)
		self.gui.endDir()

	def getLastParts(self, url):
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		match = re.compile('portfolio(.+?)pagination', re.DOTALL).findall(data)
		if len(match) > 0:
			match2 = re.compile('href="(.+?)" class="spec-border-ie.+?\n.+?php.+?src=(.+?)&amp').findall(match[0])
			match3 = re.compile('href="http://serialeonline.org.pl/index.php.+?title="(.+?)">').findall(match[0])
			match4 = re.compile('<p class="left">(.+?)</p>').findall(match[0])
			if len(match2) and len (match3) > 0:
				for i in range(len(match2)):
					title = match3[i] + ' - ' + match4[i]
					url = match2[i][0]
					img = match2[i][1]
                                        params = {'service': SERVICE, 'dstpath': dstpath, 'tvshowtitle': title,  'title': title, 'page': url, 'icon': img}
                                        self.gui.playVideo(params)
		self.gui.endDir(False)

	def showKATParts(self, page , url, pager):
                print url
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		match = re.compile('poster(.+?)clear:both', re.DOTALL).findall(data)
		if len(match) > 0:
			match2 = re.compile('href="(.+?)" title="(.+?)">').findall(match[0])
			match3 = re.compile('timthumb.+?src=(.+?)&amp').findall(match[0])
			if len(match2) and len (match3) > 0:
				for i in range(len(match2)):
					title = match2[i][1]
					urll = match2[i][0]
					img = match3[i]
                                        params = {'service': SERVICE, 'name': 'kat-parts', 'tvshowtitle': title,  'title': title, 'page': urll, 'icon': img}
                                        self.gui.addDir(params)
                match = re.compile('<li><a href="(.+?)">&raquo;</a></li>').findall(data)
                if len(match) > 0:
                    params = {'service': SERVICE, 'name':'kat-menu', 'title': 'Następna strona', 'page': page, 'category': str(int(pager) + 1), 'icon': THUMB_NEXT}
                    self.gui.addDir(params)
		self.gui.endDir(False)

	def getListsSearch(self, text):
		query_data = { 'url': SerchUrl + text, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		match = re.compile('<a class="link" href="(.+?)/season.+?" title="(.+?)">').findall(data)
		match2 = re.compile('timthumb.+?src=(.+?)&amp').findall(data)
		if len(match) and len (match2) > 0:
			for i in range(len(match)):
				title = match[i][1]
				url = match[i][0]
				print url
				img = match2[i]
                                params = {'service': SERVICE, 'name': 'kat-parts', 'tvshowtitle': title,  'title': title, 'page': url, 'icon': img}
                                self.gui.addDir(params)
		self.gui.endDir(False)

	def listsSerial(self, url, img):
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		sezon = self.showSeason(data)
		match = re.compile(sezon+'(.+?)tv_container', re.DOTALL).findall(data.replace('stylesheet', 'tv_container'))
		if len(match) > 0:
			match2 = re.compile('href="(.+?)">(.+?) <span class="tv_episode_name">(.+?)</span></a>').findall(match[0])
			if len(match2) > 0:
				for i in range(len(match2)):
					title = match2[i][1] + match2[i][2]
					url = match2[i][0]
                                        params = {'service': SERVICE, 'dstpath': dstpath, 'tvshowtitle': title,  'title': title, 'page': url, 'icon': img}
                                        self.gui.playVideo(params)
		self.gui.endDir(False)

	def showSeason(self, data):
		strTab = []
		valTab = []
		sezon = ''
		r = re.compile('<h2>Sezon(.+?)</h2>').findall(data)
		if len(r)>0:
			for i in range(len(r)):
				title = r[i]
				href = 'Sezon' + r[i]
				strTab.append(href)
				strTab.append('Sezon' + title)
				valTab.append(strTab)
				strTab = []
			d = xbmcgui.Dialog()
			item = d.select("Wybierz sezon", self.cm.getItemTitles(valTab))
			if item != -1:
				sezon = str(valTab[item][0])
				log.info('S-ID: ' + sezon)
			return sezon
		else:
			return False

	def getPlayTable(self,url):
		strTab = []
		valTab = []
		videoH = ''
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		#r = re.compile('bezlimitu.png(.+?)disqus_thread', re.DOTALL).findall(data)
		r = re.compile('row-pages-wrapper(.+?)disqus_thread', re.DOTALL).findall(data)
		if len(r)>0:
		  #r2 = re.compile('href="(.+?)" target="_blank').findall(r[0])
		  r2 = re.compile('href="(.+?)" target="_blank">Oglądaj').findall(r[0])
		  r3 = re.compile('http://serialeonline.org.pl/templates/trakt/images/(.+?).gif').findall(r[0])
		  if len(r2)>0:
			  for i in range(len(r2)):
				  title = r3[i].replace('pl1', 'Napisy').replace('eng', 'Oryginał').replace('pol', 'Lektor') + ' - ' + self.up.getHostName(r2[i], False)
				  href = r2[i]
				  strTab.append(href)
				  strTab.append(str(i+1) + '. ' + title)
				  valTab.append(strTab)
				  strTab = []
			  d = xbmcgui.Dialog()
			  item = d.select("Wybierz wersję i hosting", self.cm.getItemTitles(valTab))
			  if item != -1:
				  videoH = str(valTab[item][0])
				  log.info('H-ID: ' + videoH)
			  return videoH
		  else:
			  return False
		else:
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
		link = self.parser.getParam(params, "url")
		icon = self.parser.getParam(params, "icon")
		service = self.parser.getParam(params, "service")
		action = self.parser.getParam(params, "action")
		path = self.parser.getParam(params, "path")
		sezon = self.parser.getParam(params, "season")
		epizod = self.parser.getParam(params, "episode")
		serial = self.parser.getParam(params, "tvshowtitle")

		self.parser.debugParams(params, dbg)
		
		if str(category)=='None' or category=='': category = '1'

	#MAIN MENU
		if name == None:
			self.listsMainMenu(MENU_TAB)
			
	#SERIALE KATEGORIE
		if category == self.setTable()[1]:
			self.listsKATMenu(mainUrl)
		if name == 'kat-menu':
			self.showKATParts(page ,page + '/abc/' + str(category), category)
		elif name == 'kat-parts':
			self.listsSerial(page, icon)
			
	#OSTATNIO UZUPEŁNIONE SERIALE
		if category == self.setTable()[2]:
			self.getLastParts(NewUrl)
			
	#WYSZUKAJ
		if category == self.setTable()[3]:
			text = self.gui.searchInput(SERVICE)
			self.getListsSearch(text)
			
	#HISTORIA WYSZUKIWANIA
		if category == self.setTable()[4]:
			t = self.history.loadHistoryFile(SERVICE)
			self.listsHistory(t)

		if name == 'history':
			self.getListsSearch(title)
			
	#ODTWÓRZ VIDEO
		if name == 'playSelectedVideo':
			linkVideo = ''
			code = self.getPlayTable(page)
			if (code != False):
				linkVideo = self.up.getVideoLink(code)
			else:
				d = xbmcgui.Dialog()
				d.ok(SERVICE + ' - przepraszamy', 'Ten materiał nie został jeszcze dodany', 'Zapraszamy w innym terminie.')
				return False
                        self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)
			
	#POBIERZ
		if action == 'download' and link != '':
			if link.startswith('http://'):
				urlTempVideo = self.getPlayTable(link)
				linkVideo = self.up.getVideoLink(urlTempVideo)
			if linkVideo != False:
				self.cm.checkDir(os.path.join(dstpath, SERVICE))
				dwnl = downloader.Downloader()
				dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })
