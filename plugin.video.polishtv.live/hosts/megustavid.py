# -*- coding: utf-8 -*-
import os, string, cookielib, StringIO
import time, base64, logging, calendar
import urllib, urllib2, re, sys, math
import xbmcgui, xbmc, xbmcaddon, xbmcplugin
import xml.etree.ElementTree as ET

scriptID = 'plugin.video.polishtv.live'
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon

log = sdLog.pLog()

SERVICE = 'megustavid'
THUMB_SERVICE = os.path.join(ptv.getAddonInfo('path'), "images/") + SERVICE + '.png'
THUMB_NEXT = os.path.join(ptv.getAddonInfo('path'), "images/") + 'dalej.png'
THUMB_PREV = os.path.join(ptv.getAddonInfo('path'), "images/") + 'wroc.png'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE +".cookie"

MAINURL = 'http://megustavid.com'
SEARCHURL = MAINURL + '/search?search_type=videos&search_query='
NEW_LINK = MAINURL + '/videos?o=mr'
HOT_LINK = MAINURL + '/videos?o=tr'

SERVICE_MENU_TABLE = {
			1: "Najnowsze",
			2: "Popularne",
			3: "Wyszukaj",
			4: "Historia wyszukiwania"
		     }

			
dbg = ptv.getSetting('default_debug')

class megustavid:
  def __init__(self):
    log.info('Loading ' + SERVICE)
    self.settings = sdSettings.TVSettings()
    self.parser = sdParser.Parser()
    self.common = sdCommon.common()
    self.history = sdCommon.history()
    self.megustavid = serviceParser()
 
 
  def setTable(self):
    return SERVICE_MENU_TABLE
    
    
  def getMenuTable(self):
    nTab = []
    for num, val in SERVICE_MENU_TABLE.items():
      nTab.append(val)
    return nTab
   
    
  def searchInputText(self):
    text = None
    k = xbmc.Keyboard()
    k.doModal()
    if (k.isConfirmed()):
      text = k.getText()
    return text  
    
  
  def getMovieTab(self, url):
    strTab = []
    valTab = []
    query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
    data = self.common.getURLRequestData(query_data)   
    match = re.compile('<div class="video_box">.+?<a href="v=(.+?)">.+?<img src="(.+?)" title="(.+?)"', re.DOTALL).findall(data)
    if len(match) > 0:
      for i in range(len(match)):
	value = match[i]
	if 'megustavid.com' in value[1]: icon = value[1]
	else: icon = MAINURL + value[1]
	strTab.append(self.common.html_entity_decode(value[2]))
	strTab.append(value[0])
	strTab.append(icon)	
	valTab.append(strTab)
	strTab = []
      match = re.search('<span class="currentpage">.+?</span></li><li><a href="(.+?)">',data)
    if match:
      strTab.append("pokaz wiecej")
      strTab.append(match.group(1))
      strTab.append(THUMB_NEXT)
      valTab.append(strTab)
    #title,url,icon
    return valTab
  
   
  def listsAddLinkMovie(self, table):
    #name,url,icon
    for i in range(len(table)):
      if table[i][0] == 'pokaz wiecej':
	self.add(SERVICE, table[i][0], 'movie', 'None', table[i][0], table[i][2], table[i][1], True, False)
      else:
	self.add(SERVICE, 'playSelectedMovie', 'movie', 'None', table[i][0], table[i][2], table[i][1], True, False)	
    #zmien view na "Thumbnail"
    xbmcplugin.setContent(int(sys.argv[1]),'movies')
    xbmc.executebuiltin("Container.SetViewMode(500)")    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
  
  def listsAddDirMenu(self, table):
    for i in range(len(table)):
      self.add(SERVICE, table[i], 'None', 'None', table[i], THUMB_SERVICE, 'None', True, False)
    #zmien view na "List"
    xbmcplugin.setContent(int(sys.argv[1]),'movies')
    xbmc.executebuiltin("Container.SetViewMode(502)")    	
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


  def listsHistory(self, table):
    for i in range(len(table)):
      if table[i] <> '':
	self.add(SERVICE, table[i], 'history', 'None', 'None', THUMB_SERVICE, 'None', True, False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    

  def add(self, service, name, category, page, title, iconimage, url, folder = True, isPlayable = True):
    u=sys.argv[0] + "?service=" + service + "&name=" + urllib.quote_plus(name) + "&category=" + urllib.quote_plus(category) + "&page=" + urllib.quote_plus(page) + "&title=" + urllib.quote_plus(title) + "&url=" + urllib.quote_plus(url)
    if name == 'playSelectedMovie':
    	name = title
    if iconimage == '':
    	iconimage = "DefaultVideo.png"
    liz=xbmcgui.ListItem(name.decode('utf-8'), iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if isPlayable:
	liz.setProperty("IsPlayable", "true")
    liz.setInfo('video', {'title' : title.decode('utf-8')} )
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=folder)


  def handleService(self):
    params = self.parser.getParams()
    name = str(self.parser.getParam(params, "name"))
    title = str(self.parser.getParam(params, "title"))
    category = str(self.parser.getParam(params, "category"))
    url = str(self.parser.getParam(params, "url"))
    name = name.replace("+", " ")
    title = title.replace("+", " ")
    category = category.replace("+", " ")

    if name == 'None':
      self.listsAddDirMenu(self.getMenuTable()) 
    #Najnowsze
    if name == self.setTable()[1]:
      self.listsAddLinkMovie(self.getMovieTab(NEW_LINK))
    #Popularne	
    if name == self.setTable()[2]:
      self.listsAddLinkMovie(self.getMovieTab(HOT_LINK))      
    #lista tytulow w kategorii
    if category != 'None' and url != 'None' and name != 'playSelectedMovie':
      self.listsAddLinkMovie(self.getMovieTab(url))
    #Wyszukaj
    if name == self.setTable()[3]:
      text = self.searchInputText()
      if text != None:
	self.history.addHistoryItem(SERVICE, text)
	self.listsAddLinkMovie(self.getMovieTab(SEARCHURL + urllib.quote_plus(text)))
    #Historia wyszukiwania
    if name == self.setTable()[4]:
      self.listsHistory(self.history.loadHistoryFile(SERVICE))
    if category == 'history':
      self.listsAddLinkMovie(self.getMovieTab(SEARCHURL + urllib.quote_plus(name)))
    
    #odtwarzaj video
    if name == 'playSelectedMovie':
      videoUrl = self.megustavid.getVideoUrl(url)
      if videoUrl != False:
	log.info("videoUrl: "+ videoUrl)
	self.common.LOAD_AND_PLAY_VIDEO(videoUrl, title)
	

class serviceParser:
    def __init__(self):
      self.common = sdCommon.common()
    
    def getVideoUrl(self, h):
      videoUrl = ""
      url = MAINURL + "/e=" + h
      query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
      data = self.common.getURLRequestData(query_data)    
      match = re.compile('<a href="/download.php\?id=(.+?)" .+?>').findall(data)
      if len(match) > 0:
	url = MAINURL + '/media/nuevo/player/playlist.php?id=' + match[0]
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        data = self.common.getURLRequestData(query_data)
	root = ET.fromstring(data)
	for g in root.findall('.//*'):
	  #print g.tag + " : " + g.text.encode('utf-8')
	  if 'file' in g.tag: videoUrl = g.text.encode('utf-8')
	return videoUrl
      return False


