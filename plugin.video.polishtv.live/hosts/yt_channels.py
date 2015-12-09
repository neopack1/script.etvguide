# -*- coding: utf-8 -*-
import os, re, sys
import xbmcaddon, xbmc
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources")
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdCommon, sdErrors, sdParser, sdNavigation, urlparser

log = sdLog.pLog()

dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

NEXTURL = BASE_IMAGE_PATH + "dalej.png"

API = 'https://www.youtube.com/c4_browse_ajax?action_load_more_videos=1&sort=dd&live_view=500&flow=grid&view=0&fluid=True'
MAINURL = 'http://www.youtube.com'

class youtubeChannels:
    def __init__(self, service, menuTab):
        self.service = service
        self.menuTab = menuTab

	log.info('Loading ' + self.service)
	self.settings = sdSettings.TVSettings()
	self.cm = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.parser = sdParser.Parser()
	self.gui = sdNavigation.sdGUI()
	self.up = urlparser.urlparser()


    def listsMainMenu(self, table):
        for i in range(len(table)):
	    params = {'service': self.service, 'name': 'main-menu','category': i, 'title': table[i][0], 'icon': BASE_IMAGE_PATH +  table[i][1]}
	    self.gui.addDir(params)
	self.gui.endDir()


    def listsPlaylistMenu(self, url):
        if not 'paging' in url:
            url = API + '&channel_id=' + url + '&paging=1'
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
        
        data = _json.dumps(_json.loads(data), ensure_ascii=False).encode('utf-8').replace('&quot;', '').replace('\\', '').replace('[', '')
        match = re.compile('<a class="yt-uix-sessionlink .+?title="(.+?)".+?href="/watch\?v=(.+?)".+?</a>', re.DOTALL).findall(data)

	if len(match) > 0:
	    for i in range(len(match)):
		img = 'http://i.ytimg.com/vi/' + match[i][1] + '/mqdefault.jpg'
                link = MAINURL + '/' + match[i][1]
		params = {'service': self.service, 'name': 'playSelectedVideo', 'title': self.cm.html_entity_decode(match[i][0]), 'page': link, 'icon': img}
		self.gui.addDir(params)
        
        match = re.compile('<span class="load-more-text', re.DOTALL).findall(data)
	if len(match) > 0:
            link = url[:-1] + str(int(url[-1:]) + 1)
            params = {'service': self.service, 'name': 'next', 'title': 'Następna strona', 'page': link, 'icon': NEXTURL}
	    self.gui.addDir(params)
	self.gui.endDir()


    def handleService(self, params):
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
	    self.listsMainMenu(self.menuTab)
#LISTA KANALOW
        if name == 'main-menu':
            self.listsPlaylistMenu(self.menuTab[int(category)][2])
#NASTEPNA STRONA
	if name == 'next':
	    self.listsPlaylistMenu(page)
#ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
            linkVideo = self.up.getVideoLink(page)
            self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)
#POBIERZ
	if action == 'download' and link != '':
	    if link.startswith('http://'):
		linkVideo = self.up.getVideoLink(link).replace("action=play_video","action=download")
		if linkVideo != False:
		    xbmc.executebuiltin('XBMC.RunPlugin(%s)' % (linkVideo))