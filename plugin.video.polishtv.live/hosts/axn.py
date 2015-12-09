# -*- coding: utf-8 -*-
import os, re, sys
import xbmcaddon, traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
LOGOURL = ptv.getAddonInfo('path') + os.path.sep + "images" + os.path.sep + "axn.png"
THUMB_NEXT = os.path.join(ptv.getAddonInfo('path'), "images/") + 'dalej.png'

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()
dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

PLONLY = ptv.getSetting('axn_version') in ('true')
SERVICE = 'axn'
MAINURL = 'http://api.brightcove.com/services/library?'
TOKEN = 'JHmtFzwbUevUituBImybmBNA490FN0M6gfvVU9Ccv30.'

PLFILTER = '&playlist_fields=id,name,thumbnailURL,filterTags,videoIds'
VFILTER = '&playlist_fields=id,name,thumbnailURL,filterTags,videos&video_fields=id,name,shortDescription,videoStillURL,videoFullLength'
MAINQUERY = 'token='+TOKEN+'&get_item_count=true&media_delivery=http&page_size=1000&page_number=0'

POLQUERY = MAINURL+MAINQUERY+PLFILTER+'&command=find_playlists_for_player_id&player_id=1423840913001'
PLAYQUERY = MAINURL+MAINQUERY+PLFILTER+'&command=find_all_playlists'
VQUERY = MAINURL+MAINQUERY+VFILTER+'&command=find_playlist_by_id&playlist_id='

SERVICE_MENU_TABLE = {
    1: "Polecane",
    2: "Playlisty"#~ ,
    #~ 3: "Wyszukaj",
    #~ 4: "Historia Wyszukiwania"
}

class AXNPlayer:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.history = sdCommon.history()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return SERVICE_MENU_TABLE
	
    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsPlaylists(self, url):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	    result = _json.loads(data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
            
        print str(result)
        exit()
	for item in result['items']:
	    if len(item['videoIds']) != 0:
		if (PLONLY and ('poland' in item['filterTags'] or 'pl' in item['filterTags'] or 'pol' in item['filterTags'])) or not PLONLY:
		    title = item['name'].encode('UTF-8')
		    if item['thumbnailURL'] == None: img = LOGOURL
		    else: img = item['thumbnailURL']
		    params = {'service': SERVICE, 'name': 'sub-menu', 'category':str(item['id']), 'title': title, 'icon': img}
		    self.gui.addDir(params)
	if (result['page_number']+1)*result['page_size'] < result['total_count']:
	    pager = url.replace('&page_number=' + str(result['page_number']),'&page_number=' + str(result['page_number']+1))
	    params = {'service': SERVICE, 'name': 'nextpage', 'title': 'Następna strona', 'page': pager, 'icon': THUMB_NEXT}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsItems(self, url):
	query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	    result = _json.loads(data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	for item in result['videos']:
	    params = {'service': SERVICE, 'dstpath': dstpath, 'title': item['name'].encode('UTF-8'), 'page': item['videoFullLength']['url'].encode('UTF-8'), 'icon': item['videoStillURL'].encode('UTF-8'), 'plot': item['shortDescription'].encode('UTF-8')}
	    self.gui.playVideo(params)
	self.gui.endDir()

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
	icon = self.parser.getParam(params, "icon")
	link = self.parser.getParam(params, "url")
	service = self.parser.getParam(params, "service")
	action = self.parser.getParam(params, "action")
	path = self.parser.getParam(params, "path")

	self.parser.debugParams(params, dbg)

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(SERVICE_MENU_TABLE)
    #POLECANE
	if category == self.setTable()[1]:
	    self.listsPlaylists(POLQUERY)
    #PLAYLISTY
	if category == self.setTable()[2]:
	    self.listsPlaylists(PLAYQUERY)
    #~ #WYSZUKAJ
	#~ if category == self.setTable()[3]:
	    #~ text = self.gui.searchInput(SERVICE)
	    #~ if text != None:
		#~ self.listsItems(MAINURL + "/search?queryType=2&query=" + urllib.quote(text))
    #~ #HISTORIA WYSZUKIWANIA
	#~ if category == self.setTable()[4]:
	    #~ t = self.history.loadHistoryFile(SERVICE)
	    #~ self.listsHistory(t)
#~ 
	#~ if name == 'history':
	    #~ self.listsItems(MAINURL + "/search?queryType=2&query=" + urllib.quote(title))
    #LISTA ITEMS W KATEGORII/SERIE
	if name == 'sub-menu':
	    self.listsItems(VQUERY + category)
    #NASTEPNA STRONA
	if name == 'nextpage':
	    self.listsPlaylists(page)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    self.gui.LOAD_AND_PLAY_VIDEO(page, title)
    #POBIERZ
	if action == 'download' and link != '':
	    self.cm.checkDir(os.path.join(dstpath, SERVICE))
	    if link.startswith('http://'):
		dwnl = downloader.Downloader()
		dwnl.getFile({ 'title': title, 'url': link, 'path': path })
