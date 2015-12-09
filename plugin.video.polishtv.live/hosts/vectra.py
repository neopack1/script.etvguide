# -*- coding: utf-8 -*-
import os, string, cookielib, StringIO
import time, base64, logging, calendar
import urllib, urllib2, re, sys, math
import xbmcgui, xbmc, xbmcaddon, xbmcplugin
import traceback
from xml.dom.minidom import parseString, parse

scriptID = 'plugin.video.polishtv.live'
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append (os.path.join(BASE_RESOURCE_PATH, "lib"))

import sdLog, sdSettings, sdParser, sdCommon, sdErrors

log = sdLog.pLog()

SERVICE ='vectra'
THUM_SERVICE = os.path.join(ptv.getAddonInfo('path'), "images/") + SERVICE + '.png'


class vectra:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.exception = sdErrors.Exception()
	self.common = sdCommon.common()
        self.channels = XMLchannels('http://sd-xbmc.org/support/tvvectra.xml')
        
    
    def showStations(self):
	for i in range(len(self.channels.list)):
	    self.add(SERVICE, self.channels.list.keys()[i], self.channels.list[self.channels.list.keys()[i]][2])
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
    

    def add(self, service, name, image):
	u=sys.argv[0] + "?service=" + service + "&name=" + name
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=image)
        liz.setProperty("isPlayable","true")
        liz.setInfo(type="Video", infoLabels={"Title": name})
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)


    def getToken(self, url):
        query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        data = self.common.getURLRequestData(query_data)
        if 'token=' in data and 'salt=' in data: return data
        else: return False


    def getVideoUrl(self, name):
        nUrl = ''
        token = self.getToken(self.channels.list[name][0])
        if token != False: nUrl = self.channels.list[name][1] + token
        return nUrl


    def handleService(self):
        params = self.parser.getParams()
	name = str(self.parser.getParam(params, "name"))
	
	if name == 'None':
	    self.showStations()
	else:
	    videoUrl = self.getVideoUrl(name)
	    if videoUrl != '':
		self.common.LOAD_AND_PLAY_VIDEO(videoUrl, name)
	    else:
		d = xbmcgui.Dialog()
		d.ok('Blad odtwarzania', 'Serwis tylko dla abonentow TV Vectra.','')        


#name : [url, tokenUrl, image]
class XMLchannels:
    def __init__(self, url):
        self.common = sdCommon.common()
        self.list = self.readFile(url)

    
    def readFile(self, url):
        strTab = []
        outTab = {}
        query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        data = self.common.getURLRequestData(query_data)

        if len(data) > 0:
            d = parseString(data)
            for node in d.getElementsByTagName('channel'):
                name = node.getElementsByTagName('name')[0]
                url = node.getElementsByTagName('url')[0]
                token = node.getElementsByTagName('token')[0]
                image = node.getElementsByTagName('image')[0]

                strTab.append(self.getText(url.childNodes))
                strTab.append(self.getText(token.childNodes))
                strTab.append(self.getText(image.childNodes))
                
                outTab[self.getText(name.childNodes)] = strTab
                strTab = []
        return outTab
 
   
    def getText(self, nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)
    
