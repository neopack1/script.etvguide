# -*- coding: utf-8 -*-
import xbmcplugin, xbmcgui, xbmcaddon, xbmc, traceback
import os, sys, urllib, re, math, time

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json 

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdParser, sdCommon, sdNavigation, sdErrors

SERVICE = 'tvpvod'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'
THUMB_NEXT = ICONURL + 'dalej.png'

log = sdLog.pLog()

dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

USER_AGENT = 'Apache-HttpClient/UNAVAILABLE (java 1.4)'

MAINURL = 'http://vod.tvp.customers.multiscreen.tv/'
MENU_URL = MAINURL + 'navigation'
PAGE_NUM = ptv.getSetting('tvp_perpage')
PAGE_PARAMS  = 'pageSize=' + str(PAGE_NUM) + '&thumbnailSize=240&deviceType=1&pageNo=%s'
EPISODES_URL = MAINURL + 'Movies/EpisodesJSON?' + PAGE_PARAMS + '&parentId=%s'
SERIES_URL =  MAINURL + 'Movies/SeriesJSON?' + PAGE_PARAMS + '&parentId=%s'
IMAGE_URL = 'http://s.v3.tvp.pl/images/%s/%s/%s/uid_%s_width_500_gs_0.%s'
PARAMS_KEYS = { 'plot' : ['lead_root', 'description_root'] }
FORMATS = {"video/mp4":"mp4"}

proxy = ptv.getSetting('tvp_proxy')
videoQuality = ptv.getSetting('tvp_quality')
tvpvod_url_keys = ("service","id","name","category","page")

class tvpvod:
	def __init__(self):
		log.info('Loading ' + SERVICE)
		self.cm = sdCommon.common()
		self.proxy = sdCommon.proxy()
		self.parser = sdParser.Parser()
		self.exception = sdErrors.Exception()
		self.gui = sdNavigation.sdGUI()

	def listMainMenu(self, url):
		try:
		   result = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
		except Exception, exception:
		   traceback.print_exc()
		   self.exception.getError(str(exception))
		   exit()
		result = _json.loads(result)
		for item in result:
			if 'VOD' == item['Title']:
				data = item['SubCategories']
				for item in data:
					params = {'service': SERVICE, 'name': 'category', 'title': item['Title'].encode("utf-8"), 'category': item['ListType'].encode("utf-8"), 'id': str(item['Id']).encode("utf-8"), 'icon': LOGOURL}
					self.gui.addDir(params, params_keys_needed = tvpvod_url_keys)
				break
		self.gui.endDir()

	def getJItemStr(self, item, key, default=''):
		v = item.get(key, None)
		if None == v:
			return default
		return v.encode('utf-8')

	def listItems(self, baseUrl, category, nextCategory, id, page):
		url = baseUrl % (page, id)
		try:
		   data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
		except Exception, exception:
		   traceback.print_exc()
		   self.exception.getError(str(exception))
		   exit()
		num = 0
		data = _json.loads(data)
		for item in data:
			title =  self.getTitle(item).strip()
			icon = self.getImageUrl(item)
			fanart = icon.replace('width_500', 'width_1500')
			plot = self.getStrParam('plot', item).replace('\n', ' ').replace('<br />',' ')
			params = {'service': SERVICE, 'title': title, 'id': str(item['asset_id']), 'icon': icon, 'plot': plot, 'fanart': fanart}
			if 'video' == self.getJItemStr(item, 'type'):
				sec = item.get('duration', None)
				if sec != None:
					params.update({'duration': str(sec//60)})
				rel_milis = item.get('release_date_long', None)
				if rel_milis != None:
					t = time.localtime(int(rel_milis)//1000)
					params.update({'year': time.strftime("%Y",t)})
					params.update({'premiered': time.strftime("%d.%m.%Y",t)})
				self.gui.playVideo(params, isPlayable = True, params_keys_needed = tvpvod_url_keys)
			else:
				params.update({'name': 'category', 'category': nextCategory})
				self.gui.addDir(params, params_keys_needed = tvpvod_url_keys )
			num += 1
		if num > 0:
			page = str(int(page) + 1)
			url = baseUrl % (page, id)
			try:
			   data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
			except Exception, exception:
			   traceback.print_exc()
			   self.exception.getError(str(exception))
			   exit()
			if 'asset_id' in data:
				params = {'service': SERVICE, 'name': 'category', 'title': '[COLOR FF0084ff]>> Następna strona[/COLOR]', 'category': category, 'id': id, 'page':page, 'icon': THUMB_NEXT}
				self.gui.addDir(params, params_keys_needed = tvpvod_url_keys)
		self.gui.endDir()

	def getTitle(self, item):
		title = self.getJItemStr( item, 'Title' ) 
		if 2 < len(title):return title
		title = self.getJItemStr( item, 'title_root' )
		if 2 < len(title): return title
		return self.getJItemStr( item, 'website_title' )  + ' ' + self.getJItemStr( item, 'title' )

	def getImageUrl(self, item):
		keys = ['logo_4x3', 'image_16x9', 'image_4x3', 'image_ns954', 'image_ns644', 'image']
		iconFile = ""
		for key in keys:
			if None != item.get(key, None):
				iconFile = self.getJItemStr( item[key][0], 'file_name')
			if len(iconFile):
				tmp = iconFile.split('.')
				return IMAGE_URL % (iconFile[0], iconFile[1], iconFile[2], tmp[0], tmp[1])

	def getStrParam(self, param, item):
		value = ''
		for key in PARAMS_KEYS[param]:
			tmp = self.getJItemStr( item, key ) 
			if len(tmp) > len(value):
				value = tmp
		return value

	def getVideoLink(self, asset_id):
		url = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?object_id=' + asset_id
		if proxy == 'true':
			url = self.proxy.useProxy(url)
		try:
		   data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
		except Exception, exception:
		   traceback.print_exc()
		   self.exception.getError(str(exception))
		   exit()
		videoTab = []
		data = _json.loads( data )

                if (isinstance(data['formats'],list)):
                    for item in data['formats']:
                        if item['mimeType'] == 'unknown':
                            return item['url']
                        if item['mimeType'] in FORMATS.keys():
                            videoTab.append( {'bitrate': str(item['totalBitrate']), 'url' : item['url'].encode('utf-8') })
                    videoTab.sort(key = lambda x: int(x['bitrate']), reverse=True)
                    videoUrl = videoTab[0]['url']
                
                    if videoQuality == 'Niska': videoUrl = videoTab[-1]['url']
                    if videoQuality == 'Wysoka': videoUrl = videoTab[0]['url']
                    if videoQuality == 'Średnia':
                        length = len(videoTab)            
                        i = int(math.ceil(float(length/2)))
                        videoUrl = videoTab[i]['url']
                else:
                    videoUrl = data['formats']['url']
	
		if proxy == 'true':
		    try:
		        data = self.cm.getURLRequestData({ 'url': self.proxy.useProxy(videoUrl), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
		    except Exception, exception:
		        traceback.print_exc()
		        self.exception.getError(str(exception))
		        exit() 
		    videoUrl = data
		
		return videoUrl


	def handleService(self):
		params = self.parser.getParams()
		name = self.parser.getParam(params, "name")
		category = self.parser.getParam(params, "category")
		page = self.parser.getParam(params, "page")
		id = self.parser.getParam(params, "id")
		service = self.parser.getParam(params, "service")

		self.parser.debugParams(params, dbg)

		if page == None or page == '': page = 0

	#MAIN MENU
		if name == None:
			self.listMainMenu(MENU_URL)
	#FILMY
		elif category == "episodes": 
			self.listItems(EPISODES_URL, category, 'episodes', id, page)
		elif category == "series":
			self.listItems(SERIES_URL, category, 'episodes', id, page)
	#WYSZUKAJ
		elif category == "Wyszukaj":
			pattern = urllib.quote_plus(searchPattern)
			printDBG("Wyszukaj: pattern[%s]" % pattern)
			self.listItems(self.SEARCH_URL, category, 'episodes', pattern, page)
			
	#HISTORIA WYSZUKIWANIA
		elif category == "Historia wyszukiwania":
			self.listsHistory()
	#ODTWÓRZ VIDEO
		elif name == 'playSelectedVideo':
			videoUrl = self.getVideoLink(id)
			self.gui.LOAD_AND_PLAY_VIDEO_WATCHED(videoUrl)