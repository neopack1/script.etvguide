# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, traceback, xbmcgui

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
LOGOURL = ptv.getAddonInfo('path') + os.path.sep + "images" + os.path.sep + "telpol.png"
HOST = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_2 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8H7 Safari/6533.18.5'

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg

SERVICE = 'telpol'
MAINURL = 'http://joytv.telpol.net.pl/live'

class Telpol:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def listsChannels(self, url):
	query_data = { 'url': url, 'use_host': True, 'host': HOST, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	log.info("Test1 "+str(data))
	r = re.compile('<a href="(.+?)"><h4>(.+?)</h4></a>').findall(data)
	if len(r)>0:
	    for i in range(len(r)):
		params = {'service': SERVICE, 'title': string.capwords(r[i][1]), 'page': r[i][0].replace('index.m3', '03.m3'), 'icon': LOGOURL}
		self.gui.playVideo(params)
	    self.gui.endDir(True)
	else:
	    d = xbmcgui.Dialog()
	    d.ok('Blad odtwarzania', 'Serwis tylko dla abonentow Telpol,','lub chwilowo niedostępny.')        


    def handleService(self):
	params = self.parser.getParams()
	name = self.parser.getParam(params, "name")
	title = self.parser.getParam(params, "title")
	category = self.parser.getParam(params, "category")
	page = self.parser.getParam(params, "page")
	icon = self.parser.getParam(params, "icon")

	self.parser.debugParams(params, dbg)

    #LISTA KANAŁÓW
	if name == None:
	    self.listsChannels(MAINURL)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    self.gui.LOAD_AND_PLAY_VIDEO(page, title)
