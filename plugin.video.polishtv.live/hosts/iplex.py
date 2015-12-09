# -*- coding: utf-8 -*-
import os, re, sys
import base64, codecs, blowfish
import xbmcaddon, xbmcgui
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = 'plugin.video.polishtv.live'
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()

SERVICE = 'iplex'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL =  'http://samsung.iplex.pl/'             
HOST = 'Mozilla/5.0 (Windows; U; en-US; rv:1.8.1.11; Gecko/20071129; Firefox/2.5.0) Maple 5.1.00277 Navi'

iplex_proxy = ptv.getSetting('iplex_proxy')

class IPLEX:
	def __init__(self):
		log.info('Loading ' + SERVICE)
		self.parser = sdParser.Parser()
		self.gui = sdNavigation.sdGUI()
		self.common = sdCommon.common()
		self.api = API()
		
	
	def getMenu(self, url):
		data = self.api.getAPI(url)
		
		for item in data['feeds']:
			if item['type'] != 'account':
				params = {'service': SERVICE, 'url': item['url'], 'category': item['type'], 'title': item['caption'].encode('UTF-8'), 'icon': THUMB_SERVICE}
				self.gui.addDir(params)
		self.gui.endDir(True)
	
	
	def getPlaylist(self, url):
		data = self.api.getAPI(url)
		for item in data['feeds']:
			if item['license'] == 'FREE':
				params = {'service': SERVICE, 'url': item['url'], 'category': item['type'], 'title': item['title'].encode('UTF-8'), 'icon': item['img'].replace('61x80','199x286')}
				v = item.get('duration',None )
				if v != None:
					params.update({'duration': v})
				if item['type'] == 'movie_card':
					self.gui.playVideo(params)
				else:
					self.gui.addDir(params)
		self.gui.endDir(True)


	def getSeries(self, url):
		data = self.api.getAPI(url)
		self.getPlaylist(data['series'])

		
	def getVideoUrl(self, url):
		data = self.api.getAPI(url)
		
		#lector
		if 'lector' in data:
			details = self.api.getAPI(data['lector'])
		#subtitles
		else:
			details = self.api.getAPI(data['subtitles'])

		return self.api._decodeUrl(details['movie']['url'])


	def handleService(self):
		params = self.parser.getParams()
		title = str(self.parser.getParam(params, "title"))
		category = str(self.parser.getParam(params, "category"))
		url = str(self.parser.getParam(params, "url"))
		
		#MAINMENU
		if category == 'None':
			if self.api.geoCheck():
				self.getMenu(MAINURL + '/tv/main.menu?api=v4')
	
		#PLAYLIST
		if category == 'playlist':
			self.getPlaylist(url)
			
		#SERIES
		if category == 'series_card':
			self.getSeries(url)
			
		#CATEGORIES
		if category == 'category':
			self.getMenu(url)
			
		#VIDEO
		if category == 'movie_card':
			videoUrl = self.getVideoUrl(url)
			self.common.LOAD_AND_PLAY_VIDEO(videoUrl, title)
			
			
class API:
	def __init__(self):
		self.exception = sdErrors.Exception()
		self.common = sdCommon.common()
		self.proxy = sdCommon.proxy()
	
	
	def geoCheck(self):
		#{u'country': None, u'valid': False}
		#{u'country': u'POLAND', u'valid': True}
		ret = True
		if iplex_proxy != 'true':
			data = self.getAPI('http://samsung.iplex.pl/tv/geoblock?api=v4')
			if data['valid'] == False:
				d = xbmcgui.Dialog()
				d.ok(SERVICE, 'Serwis niedostepny na terenie twojego kraju.', 'Odwiedz sd-xbmc.org w celu uzyskania dostepu.')
			ret = data['valid']	
		return ret
			
	
	def getAPI(self, url):
		if iplex_proxy == 'true':
			url = self.proxy.useProxy(url)			
		
		query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
		try:
			data = self.common.getURLRequestData(query_data)
			if (iplex_proxy == 'true' and self.proxy.isAuthorized(data) != False) or iplex_proxy == 'false':
				result = _json.loads(data)

		except Exception, exception:
			traceback.print_exc()
			self.exception.getError(str(exception))
			exit()
		return result


	def _decodeUrl(self, url, key='-S75dbb-QB?<nE_['):
		ret = ''

        #-------- decoding -----------
		match = re.search('(http:\/\/.*)\/(\d{1,5}|pre_adv|post_adv)\/(.*)\.mp4', url)

        #check if valid url
		if match:
			url_path = match.group(1) + '/' + match.group(2) + '/'
			s1 = codecs.encode(match.group(3), 'rot_13') 
			s2 = base64.b64decode(s1)
			s3 = ''
			cipher = blowfish.Blowfish(key)
			for index in range(0, len(s2)/16):
				chunk = s2[index*16:index*16+16]
				s3 += cipher.decrypt(chunk.decode("hex"))
			s4 = s3.replace("$","")
			ret = url_path + s4 + '.mp4'
		return ret