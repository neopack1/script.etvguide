# -*- coding: utf-8 -*-
import os, re, sys
import xbmcgui, xbmcaddon
import traceback

scriptID = sys.modules[ "__main__" ].scriptID
ptv = xbmcaddon.Addon(scriptID)

import sdLog, sdParser, sdCommon, sdNavigation, sdErrors, downloader, urlparser

log = sdLog.pLog()

dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

#ToDo:
#  Obsługa playlist

SERVICE = 'animeshinden'
MAINURL = 'http://www.anime-shinden.info'

SERVICE_MENU_TABLE = {
    1: "Lista anime (alfabetycznie)",
    2: "Lista anime (wg. gatunku)",
}

class AnimeShinden:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.parser = sdParser.Parser()
	self.up = urlparser.urlparser()
	self.cm = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()
	
	self.LOGOURL = self.gui.getLogoImage(SERVICE)

    def setTable(self):
	return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': self.LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsABCMenu(self, table):
	for i in range(len(table)):
	    params = {'service': SERVICE, 'name': 'abc-menu','category': table[i], 'title': table[i], 'icon': self.LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsGenre(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	r = re.compile('<input id=".+?"  type="checkbox" name="genre.." value="(.+?)">\n(.+?)</label').findall(data)
	if len(r)>0:
	    for i in range(len(r)):
		params = {'service': SERVICE, 'name': 'genset', 'title': r[i][1].strip(), 'page':r[i][0], 'icon': self.LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def getAnimeList(self, url):
	query_data = { 'url': MAINURL+url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	r = re.compile('<dl class="sub-nav">(.+?)</body>', re.DOTALL).findall(data)
	if len(r)>0:
	    r2 = re.compile('<a href="'+MAINURL+'/(.+?.html)">(.+?) </a>').findall(r[0])
	    if len(r2)>0:
		for i in range(len(r2)):
		    value = r2[i]
		    title = self.cm.html_entity_decode(value[1])
		    params = {'service': SERVICE, 'name': 'episodelist', 'title': title, 'page': value[0], 'icon': self.LOGOURL}
		    self.gui.addDir(params)
	self.gui.endDir()

    def getEpisodeList(self, url, series):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('><div id="news-id(.+?)</div>', re.DOTALL).findall(data)
	if len(match) > 0:
	    #match2 = re.compile('<a href=".+?(/.+?.html)".+?>(?:<b>)*((?:Odcinek.+?)|(?:OVA.*?)|(?:Special.*?)|(?:Movie.*?)|(?:Film.*?)|(?:Zobacz.*?)|(?:Obejrzyj Online))(?:</b>)*</a>').findall(match[0])
	    match2 = re.compile('<a href=".+?(/.+?.html)".+?>(?:<b>)*(.+?)(?:</b>)*</a>').findall(match[0])
	    if len(match2) > 0:
		for i in range(len(match2)):
		    value = match2[i]
		    if '<!--' not in value[1]:
			params = {'service': SERVICE,'dstpath': dstpath, 'title': value[1], 'page': 'http:' + value[0], 'icon': self.LOGOURL, 'series': series}
			self.gui.playVideo(params)
	self.gui.endDir()

    def getLinkParts(self,data):
	valTab = []
	src = re.compile("flashvars=.+?hd\.file=(.+?)&").findall(data)
	if len(src) < 1:
	    src = re.compile('flashvars="streamer=(.+?)"').findall(data)
	if len(src) < 1:
	    src = re.compile('src="(.+?)"').findall(data)
	for i in range(len(src)):
	    linkVideo = src[i]
	    valTab.append(self.cm.setLinkTable(linkVideo, 'Część '+str(i+1)))
	return valTab

    def getHostingTable(self,url):
	valTab = []
	videoID = ''
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('class="video_tabs".+?>(.+?)</div>\n', re.DOTALL).findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		linkVideos = self.getLinkParts(match[i])
		if linkVideos != []:
		    valTab.append(self.cm.setLinkTable(linkVideos, self.up.getHostName(str(linkVideos),True)))
	    d = xbmcgui.Dialog()
	    item = d.select("Wybór hostingu", self.cm.getItemTitles(valTab))
	    print str(item)
	    if item != -1:
		linkVideo = valTab[item][0]
		return linkVideo
	    else:
		exit()
	else:
	    d = xbmcgui.Dialog()
	    d.ok('Brak hostingu', SERVICE + ' - nie dodano jeszcze tego wideo.', 'Zapraszamy w innym terminie.')
	    exit()

    def getVideoPart(self,link):
	if len(link) == 1:
	    return (link[0][0], 0)
	elif len(link) > 1:
	    d = xbmcgui.Dialog()
	    item = d.select("Wybierz część", self.cm.getItemTitles(link))
	    print str(item)
	    if item != -1:
		linkVideo = str(link[item][0])
		log.info("final link: " + linkVideo)
		return (linkVideo, item)
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

	if page==None or page=='': page = '0'

    #MAIN MENU
	if name == None:
	    self.listsMainMenu(SERVICE_MENU_TABLE)
    #LISTA ANIME (Alfabetycznie)
	if category == self.setTable()[1]:
	    self.listsABCMenu(self.cm.makeABCList())

	if name == 'abc-menu':
	    self.getAnimeList('/animelist/index.php?letter=' + category)
    #LISTA ANIME (wg. Gatunku)
	if category == self.setTable()[2]:
	    self.listsGenre(MAINURL+'/animelist/index.php')

	if name == 'genset':
	    self.getAnimeList('/animelist/index.php?genre[]=' + page)
    #LISTA ODCINKÓW
	if name == 'episodelist':
	    url = MAINURL + '/' + page
	    self.getEpisodeList(url, title)
    #WYBIERZ SERWER. CZĘŚĆ I ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    linkVideo = self.up.getVideoLink(self.getVideoPart(self.getHostingTable(page))[0])
	    self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)
    #POBIERZ
	if action == 'download' and link != '':
	    if link.startswith('http://'):
		(link, link_id) = self.getVideoPart(self.getHostingTable(link))
		linkVideo = self.up.getVideoLink(link)
		if linkVideo != False:
		    self.cm.checkDir(os.path.join(dstpath, SERVICE))
		    dwnl = downloader.Downloader()
		    dwnl.getFile({ 'title': "%s_%s" % (title, link_id), 'url': linkVideo, 'path': path })
