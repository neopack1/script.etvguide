# -*- coding: utf-8 -*-
import cookielib, os, string, StringIO
import os, urllib, re, sys, traceback
import xbmcaddon

scriptID = sys.modules[ "__main__" ].scriptID
ptv = xbmcaddon.Addon(scriptID)

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg

dstpath = ptv.getSetting('default_dstpath')

SERVICE = 'tvs'
MAINURL = 'http://www.tvs.pl'
INFORMACJEURL = 'http://www.tvs.pl/silesiainformacje'

SERVICE_MENU_TABLE = {
	#1: "Programy TVS",
	3: "Silesia Informacje"
}
  
class TVSilesia:
	def __init__(self):
		log.info('Loading ' + SERVICE)
		self.parser = sdParser.Parser()
		self.cm = sdCommon.common()
		self.exception = sdErrors.Exception()
		self.gui = sdNavigation.sdGUI()
		self.LOGOURL = self.gui.getLogoImage(SERVICE)
		self.THUMB_NEXT = self.gui.getThumbNext()

	def setTable(self):
		return SERVICE_MENU_TABLE
	
	def listsMainMenu(self, table):
		for num, val in table.items():
			params = {'service': SERVICE, 'name': 'main-menu', 'title': val, 'category': val, 'icon': self.LOGOURL}
			self.gui.addDir(params)
		self.gui.endDir()
		
	def listsShows(self, url):
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
		r = re.compile('<div class="middle_center_box">(.+?)</div><br style="clear: both;" />', re.DOTALL).findall(data)
		if len(r)>0:
			r2 = re.compile('<div class="movie_foto_ramka".+?<img src="(.+?)" />.+?<span>(.+?)</span>.+?<a href="(.+?)">Zobacz online</a>', re.DOTALL).findall(r[0])
			if len(r2)>0:
				for i in range(len(r2)):
					self.addDir(SERVICE, 'shows', r2[i][1], '', '', r2[i][2], r2[i][0], True, False)
				xbmcplugin.endOfDirectory(int(sys.argv[1]))
				
	def listsInfos(self, url, page):
		url = url + '/' + page
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
		r = re.compile('video-date">(.+?)<.+?href="(.+?)"', re.DOTALL).findall(data)
		if len(r)>0:
			log.info("TVS REG1"+str(r))
			for i in range(len(r)):
				log.info("TVS REG2 "+str(r[i][0].strip()))
				params = {'service': SERVICE, 'dstpath': dstpath, 'title': r[i][0].strip(), 'page': r[i][1].strip(), 'category': 'infos', 'icon': 'http://i.imgur.com/cSIXqtk.jpg'}
				self.gui.playVideo(params)
			nextr = re.compile('pag_next.+?data-page="(.+?)"').findall(data)
			if len(nextr) > 0:
				params = {'service': SERVICE, 'name':'infosPage', 'title': 'Następna strona', 'page': nextr[0], 'icon': self.THUMB_NEXT}
				self.gui.addDir(params)
		self.gui.endDir()
				
	def listsShowsEpisodes(self, url, category):
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
		r = re.compile('<div class="bottom_box">(.+?)<div style="clear: both;"></div>', re.DOTALL).findall(data)
		if len(r)>0:
			r2 = re.compile('<div class="movie_foto_ramka".+?<img src="(.+?)" />.+?;">(.+?)</span></span>.+?<a href="(.+?)">Zobacz online</a>', re.DOTALL).findall(r[0])
			if len(r2)>0:
				for i in range(len(r2)):
					self.addDir(SERVICE, 'playSelectedMovie', category, category+" - "+r2[i][1], '', r2[i][2], r2[i][0], True, False)
				xbmcplugin.endOfDirectory(int(sys.argv[1]))
			else:
				d = self.gui.dialog()
				d.ok('Brak hostingu', SERVICE + ' - nie dodano jeszcze tego wideo.', 'Zapraszamy w innym terminie.')
	
	def setLinkTable(self, url, host):
		strTab = []
		strTab.append(url)
		strTab.append(host)
		return strTab
	
	def getItemTitles(self, table):
		out = []
		for i in range(len(table)):
			value = table[i]
			out.append(value[1])
		return out
	
	def getHostingTable(self,url):
		valTab = []
		query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
		filename = re.compile('"file":"(.+?)",', re.DOTALL).findall(data)
		streamer = re.compile('"streamer":"(.+?)",', re.DOTALL).findall(data)
		streamer = streamer[0].replace("rtmpt://","rtmp://").replace('\/', '/')
		if len(filename) > 0 and len(streamer) > 0:
			return streamer+" playpath=mp4:"+filename[0].replace('\/', '/')+" swfUrl=http://www.tvs.pl/mediaplayer-5.7-licensed/player.swf live=true swfVfy=true"
		else:
			d = self.gui.dialog()
			d.ok('Brak hostingu', SERVICE + ' - nie dodano jeszcze tego wideo.', 'Zapraszamy w innym terminie.')

	def handleService(self):
		params = self.parser.getParams()
		name = self.parser.getParam(params, "name")
		title = self.parser.getParam(params, "title")
		category = self.parser.getParam(params, "category")
		page = self.parser.getParam(params, "page")
		icon = self.parser.getParam(params, "icon")
		link = self.parser.getParam(params, "url")
		vtitle = self.parser.getParam(params, "vtitle")
		service = self.parser.getParam(params, "service")
		action = self.parser.getParam(params, "action")
		path = self.parser.getParam(params, "path")

		self.parser.debugParams(params, dbg)

		if str(page)=='None' or page=='': page = '1'
	#MAIN MENU
		if name == None:
			self.listsMainMenu(SERVICE_MENU_TABLE)

	#PROGRAMY TVS
#		if category == self.setTable()[1]:
#			self.listsShows(MAINURL+'/tv/programy/')
#		
#		if name == 'shows':
#			self.listsShowsEpisodes(str(page).replace('program,','archiwum,'), str(category))

	#SILESIA INFORMACJE
		if category == self.setTable()[3] or name == 'infosPage':
			self.listsInfos(INFORMACJEURL, page)
	
	#ODTWÓRZ VIDEO
		if name == 'playSelectedVideo':
			linkVideo = self.getHostingTable(MAINURL+page)
			log.info("LOGPSV "+linkVideo)
			if linkVideo != False:
				self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)
			else:
				d = self.gui.dialog()
				d.ok('Brak linku', SERVICE + ' - przepraszamy, chwilowa awaria.', 'Zapraszamy w innym terminie.')
				
#	ToDo
#		if service == SERVICE and action == 'download' and link != '':
#			self.cm.checkDir(os.path.join(dstpath, SERVICE))
#			if dbg == 'true':
#				log.info(SERVICE + ' - handleService()[download][0] -> title: ' + urllib.unquote_plus(vtitle))
#				log.info(SERVICE + ' - handleService()[download][0] -> url: ' + urllib.unquote_plus(link))
#				log.info(SERVICE + ' - handleService()[download][0] -> path: ' + path)
#			if urllib.unquote_plus(link).startswith('http://'):
#				linkVideo = self.getHostingTable(urllib.unquote_plus(link))
#				if dbg == 'true':
#					log.info(SERVICE + ' - handleService()[download][2] -> title: ' + urllib.unquote_plus(vtitle))
#					log.info(SERVICE + ' - handleService()[download][2] -> url: ' + linkVideo)						
#				if linkVideo != False:
#					if dbg == 'true':
#						log.info(SERVICE + ' - handleService()[download][3] -> title: ' + urllib.unquote_plus(vtitle))
#						log.info(SERVICE + ' - handleService()[download][3] -> url: ' + linkVideo)
#						log.info(SERVICE + ' - handleService()[download][3] -> path: ' + path)						
#					dwnl = downloader.Downloader()
#					dwnl.getFile({ 'title': urllib.unquote_plus(vtitle), 'url': linkVideo, 'path': path })
