# -*- coding: utf-8 -*-

#todo:

import os, sys
import xbmcaddon, xbmcgui
import traceback
import re

scriptID = 'plugin.video.polishtv.live'
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()

SERVICE = 'eleven'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL =  'http://www.elevensports.pl/'


class eleven:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()
    
    
    def getChannels(self):
        query_data = {'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	data = self.common.getURLRequestData(query_data)
	
	match = re.compile("stream=(.+?)' frameborder").findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
		if 'ch01' in match[i]:
		    title = 'Eleven'
		else:
		    title = 'Eleven Sports'
		    		    
                params = {'service': SERVICE, 'url': match[i].replace('~','='), 'title': title, 'icon': ''}
                self.gui.addDir(params)
        self.gui.endDir(True)        
    
    
    def handleService(self):
        params = self.parser.getParams()
        url = str(self.parser.getParam(params, "url"))
	title = str(self.parser.getParam(params, "title"))
                
        #KANALY
        if url == 'None':
            self.getChannels()
                    
        #PLAY
        if url != 'None':
            self.common.LOAD_AND_PLAY_VIDEO(url, title)