# -*- coding: utf-8 -*-
import os, sys
import xbmcaddon, traceback
import re, urllib

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json 

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdNavigation, sdErrors

log = sdLog.pLog()

SERVICE = 'filmbox'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL  + SERVICE + '.png'
HOST = 'Mozilla/5.0 (SmartHub; SMART-TV; U; Linux/SmartTV+2013; Maple2012) AppleWebKit/535.20+ (KHTML, like Gecko) SmartTV Safari/535.20'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE +".cookie"

CATEGORYURL =  'http://www.filmboxliveapp.net/sms/tvappV2/ScriptService.aspx?GetScript=0&lang=pl'             
LIVEURL = 'http://filmboxliveapp.net/android/android_service_V2/services.aspx?method=GetMovieTicket&mov_url=%s&mov_id=%s&pub_id=5842&is_live=1&session_id=%s'
LIVEURL ='http://www.filmboxliveapp.net/tvservice/Services.aspx?method=gettickettv&session_id=%s&mov_id=%s&pub_id=5842&is_live=1&mov_url=%s'
CHANNELSURL = ''

APIURL = 'http://api.invideous.com/plugin/get_package_videos?package_id=12&publisher_id=5842&records_per_page=50&custom_order_by_order_priority=asc&filter_by_live=%s%s&page=%s'
APILOGIN = 'http://api.invideous.com/plugin/login?username=%s&password=%s&platform=spi_android_pl_2.0&publisher_id=5842'

THUMB_NEXT = ICONURL + 'dalej.png'

username = ptv.getSetting('filmbox_login')
password = ptv.getSetting('filmbox_password')

class filmbox:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.parser = sdParser.Parser()
	self.gui = sdNavigation.sdGUI()
	self.common = sdCommon.common()
	self.api = API()


    def getMenu(self):
	query_data = {'url': CATEGORYURL, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': True}
	data = self.common.getURLRequestData(query_data)

	match = re.compile('genres\[0\].push\("(.+?)"\);').findall(data)
	matchNames = re.compile('genresname\[0\].push\("(.+?)"\);').findall(data)

	if len(match) > 0 and (len(match) == len(matchNames)):
	    
	    if self.common.getCookieItem(COOKIEFILE, 'session_id') != '':
		params = {'service': SERVICE, 'title': 'Telewizja na zywo', 'name': 'LIVE', 'page': '', 'icon': THUMB_SERVICE}
		self.gui.addDir(params)	    
	
	    for i in range(len(match)):
		params = {'service': SERVICE, 'title': matchNames[i], 'name': match[i], 'page': '', 'icon': THUMB_SERVICE}
		self.gui.addDir(params)
            self.gui.endDir()


    def getVideoUrl(self, url):
	query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.common.getURLRequestData(query_data)
	    result = _json.loads(data)
	    if result['status'].encode('UTF-8') == 'success':
		videoUrl = result['data'].encode('UTF-8')
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	return videoUrl


    def getPlaylist(self, live, name, page):
	data = self.api.getAPI(live, name, page)
	for item in data['response']['result']['videos']:
	    if live == 0:
		title = item['title'].encode('UTF-8') + ' (' + item['custom_attributes']['title_en'].encode('UTF-8') +')'
		url = item['custom_attributes']['samsung_source_url']
		icon = item['custom_attributes']['largeImage']
	    else:
		url = LIVEURL % (self.common.getCookieItem(COOKIEFILE, 'session_id'), item['id'].encode('UTF-8'), item['custom_attributes']['samsung_url'].encode('UTF-8'))
		title = item['title'].encode('UTF-8')
		icon = item['custom_attributes']['thumbnail']
	    params = {'service': SERVICE, 'url': url, 'title': title.strip(), 'icon': icon}
	    self.gui.playVideo(params)
	
	if data['response']['result']['total_pages'] > page:
	    params = {'service': SERVICE, 'name': name, 'title': 'Następna strona', 'page': str(page+1), 'icon': THUMB_NEXT}
	    self.gui.addDir(params)  
	self.gui.endDir(False)


    def handleService(self):
	params = self.parser.getParams()
	title = self.parser.getParam(params, "title")
	page = self.parser.getIntParam(params, "page")
	name = self.parser.getParam(params, "name")
	url = self.parser.getParam(params, "url")

	if name == None:
	    #login
	    if (username!='' and password!=''):
		self.api.getAPILogin(username,password)
	    self.getMenu()
	
	if (name != 'playSelectedVideo' and name != None):
	    if page == None: page = 1
	    if name != 'LIVE': self.getPlaylist(0, name, page)
	    else: self.getPlaylist(1, '', page)

	if name == 'playSelectedVideo':
	    if 'session_id' in url:
		#do orignalnego url jest dokladany jeszcze &userID=XXXXXX&domain=filmbox
		videoUrl = self.getVideoUrl(url)
	    else:
		#User-Agent pozyczony on MrKnow, http://filmkodi.com
		videoUrl = url + '|User-Agent=Mozilla%2f5.0+(iPad%3b+CPU+OS+6_0+like+Mac+OS+X)+AppleWebKit%2f536.26+(KHTML%2c+​like+Gecko)+Version%2f6.0+Mobile%2f10A5355d+Safari%2f8536.25'
	    self.gui.LOAD_AND_PLAY_VIDEO(videoUrl, title)
	    
	    
class API:
    def __init__(self):
	self.exception = sdErrors.Exception()
	self.common = sdCommon.common()


    def getAPI(self, live, genre, page):
	if genre != '': genre = '&custom_filter_by_genre=' + genre
	url = APIURL % (live, genre, page)
	query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.common.getURLRequestData(query_data)
	    result = _json.loads(data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	return result


    def getAPILogin(self, username, password):
	url = APILOGIN % (username, password)
	query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_header': False, 'use_cookie': True, 'save_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True}
	
	ret = False
	try:
	    data = self.common.getURLRequestData(query_data)
	    result = _json.loads(data)
	    if result['response']['status'] == 'success': ret = True
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	return ret

