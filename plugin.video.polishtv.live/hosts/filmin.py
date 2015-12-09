# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon
import xbmc, traceback

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)
language = ptv.getLocalizedString
t = sys.modules[ "__main__" ].language

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, urlparser, sdNavigation, sdErrors, downloader

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

SERVICE = 'filmin'
LOGOURL = os.path.join(ptv.getAddonInfo('path'), "images/") + SERVICE + '.png'
THUMB_NEXT = os.path.join(ptv.getAddonInfo('path'), "images/") + 'dalej.png'

MAINURL = 'http://filmin.pl/videos'

class filmin:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.common = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.up = urlparser.urlparser()
	self.gui = sdNavigation.sdGUI()

    def listMainCategories(self):
	query_data = { 'url': MAINURL, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    response = self.common.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    quit()
	match = re.compile('<div class="categories">(.+?)</div>', re.DOTALL).findall(response)
	if len(match) > 0:
	    match = re.compile('<li.+?><a href="(.+?)">(.+?)</a></li>').findall(match[0])
	    if len(match) > 0:
		for i in range(len(match)):
		    params = {'service': SERVICE, 'name': 'categories','page': match[i][0], 'title': match[i][1], 'icon': LOGOURL}
		    self.gui.addDir(params)
		self.gui.endDir(True)

    def listMovies(self, url):
	query_data = { 'url': url, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    response = self.common.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    quit()
	match = re.compile('<a href="(.+?)"><img src="(.+?)" alt="(.+?)"  /></a>').findall(response)
	match_page = re.compile('Strony :.+?<a href="(.+?)">&raquo;</a></div>').findall(response)
	if len(match) > 0:
	    for i in range(len(match)):
		params = {'service': SERVICE, 'dstpath': dstpath, 'title': match[i][2], 'page': match[i][0], 'icon': match[i][1]}
		self.gui.playVideo(params)
	    if len(match_page) > 0:
		    params = {'service': SERVICE, 'name': 'nextpage', 'title': t(55115).encode("utf-8"), 'page': self.getNextPageUrl(url), 'icon': THUMB_NEXT}
		    self.gui.addDir(params)
	    self.gui.endDir()

    def getMovieUrl(self, url, download = ''):
	movieUrl = ''
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    response = self.common.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    quit()
	match = re.compile('<param (.+?)></param>').findall(response)
	if len(match) > 0:
	    movieUrl = match[0].split('value=')[1].replace("\\", "").replace("\"", "")
	    if movieUrl.startswith("http://www.youtube.com"):
		tab = movieUrl.split("?")[0].split("&")[0].split("/")
		id = tab[len(tab) - 1]
		if download != '':
		    movieUrl = 'plugin://plugin.video.youtube?path=%s&action=download&videoid=%s' % ('/root/video', id)
		else:
		    movieUrl = 'plugin://plugin.video.youtube?path=%s&action=play_video&videoid=%s' % ('/root/video', id)
	    else:
		movieUrl = self.up.getVideoLink(movieUrl)
	return movieUrl

    def getNextPageUrl(self, url):
	n_url = url
	urlTab = url.split("/")
	id = urlTab[len(urlTab) - 1]
	len_id = len(str(id))
	if self.common.isNumeric(id):
	    id = int(id) + 1
	return n_url[:-len_id] + str(id)

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
	    self.listMainCategories()
    #KATEGORIE
	elif name == 'categories':
	    self.listMovies(page)

	elif name == 'nextpage':
	    self.listMovies(page)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    self.gui.LOAD_AND_PLAY_VIDEO(self.getMovieUrl(page), title)
    #POBIERZ
	if action == 'download' and link != '':
	    linkVideo = self.getMovieUrl(link, path)
	    if linkVideo.startswith("plugin://plugin.video.youtube"):
		xbmc.executebuiltin('XBMC.RunPlugin(%s)' % (linkVideo))
	    elif linkVideo.startswith('http://'):
		self.cm.checkDir(os.path.join(dstpath, SERVICE))
		dwnl = downloader.Downloader()
		dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })
