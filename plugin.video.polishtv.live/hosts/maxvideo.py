# -*- coding: utf-8 -*-
import os, re, sys
import xbmcaddon, xbmc, traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdNavigation, sdErrors

log = sdLog.pLog()

MAINURL = 'http://maxvideo.pl'
apiLogin = MAINURL + '/api/login.php'
apiFrontList = MAINURL + '/api/front_list.php'
apiVideoUrl = MAINURL + '/api/get_link.php'
apiLoggedIn = MAINURL + '/api/is_logged.php'
authKey = '8d00321f70b85a4fb0203a63d8c94f97'

SERVICE = 'maxvideo'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE +".cookie"
LOGOURL = os.path.join(ptv.getAddonInfo('path'), "images/") + SERVICE + '.png'

login = ptv.getSetting('maxvideo_login')
password = ptv.getSetting('maxvideo_password')
notification = ptv.getSetting('maxvideo_notify') in ('true')

class Maxvideo:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
	self.api = API()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()
	self.cm.checkDir(ptv.getAddonInfo('path') + os.path.sep + "cookies")

    def getFrontListTable(self):
	strTab = []
	valTab = []
	query_data = {'url': apiFrontList, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	result = _json.loads(data)
	for majorkey, value in result.iteritems():
	    for subkey, v in value.iteritems():
		strTab.append(v)
	    valTab.append(strTab)
	    strTab = []
	return valTab

    def getMenuTable(self):
	valTab = []
	nTab = self.getFrontListTable()
	log.info(str(nTab))
	for i in range(len(nTab)):
	    if not nTab[i][0] in valTab:
		valTab.append(nTab[i][0])
	return valTab

    def getMovieTab(self, name):
	valTab = []
	strTab = []
	nTab = self.getFrontListTable()
	for i in range(len(nTab)):
	    if nTab[i][0].encode('UTF-8') == name:
		strTab.append(nTab[i][1])
		strTab.append(nTab[i][2])
		valTab.append(strTab)
	    strTab = []
	return valTab

    def addList(self, table, category):
	if category == 'movie':
	    for i in range(len(table)):
		params = {'service': SERVICE, 'title': table[i][1].encode('UTF-8'), 'page': table[i][0], 'icon': LOGOURL}
		self.gui.playVideo(params)
	if category == 'main-menu':
	    for i in range(len(table)):
		val = table[i].encode('UTF-8')
		params = {'service': SERVICE, 'name': val, 'category': category, 'title': val, 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()

    def handleService(self):
	params = self.parser.getParams()
	name = self.parser.getParam(params, "name")
	title = self.parser.getParam(params, "title")
	category = self.parser.getParam(params, "category")
	page = self.parser.getParam(params, "page")

	if name == None:
	    self.api.Login(login, password, notification)
	    self.addList(self.getMenuTable(),'main-menu')
	if category == 'main-menu':
	    self.addList(self.getMovieTab(name),'movie')
	if name == 'playSelectedVideo':
	    #linkVideo = self.api.getVideoUrl(page, COOKIEFILE, notification)
	    linkVideo = self.api.getVideoUrl(page, '', notification)
	    self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title, Player())

class Player(xbmc.Player):
    def __init__(self, *args, **kwargs):
      self.is_active = True
      print "#Starting control events#"

    def getPremium(self):
      self.api = API()
      return self.api.Premium()

    def onPlayBackPaused(self):
      print "#Im paused#"
      ThreadPlayerControl("Stop").start()
      self.is_active = False

    def onPlayBackResumed(self):
      print "#Im Resumed #"

    def onPlayBackStarted(self):
      print "#Playback Started#"
      try:
        print "#Im playing : " + self.getPlayingFile()
      except:
	print "#I failed get what Im playing#"

    def onPlayBackEnded(self):
      msg = xbmcgui.Dialog()
      print "#Playback Ended#"
      self.is_active = False
      if self.getPremium() == 0:
        msg.ok("Błąd odtwarzania", "Wyczerpany limit lub zbyt duża liczba użytkowników.", "Wykup konto premium na maxvideo.pl aby oglądać bez przeszkód.")

    def onPlayBackStopped(self):
      print "## Playback Stopped ##"
      self.is_active = False

    def sleep(self, s):
      xbmc.sleep(s)

class API:
  def __init__(self):
    self.cm = sdCommon.common()

  def Premium(self):
    query_data = {'url': apiLoggedIn, 'use_host': False, 'use_cookie': True, 'load_cookie': True, 'save_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True}
    data = self.cm.getURLRequestData(query_data)
    result = _json.loads(data)
    print str(result)
    if 'error' in result:
      retVal = False
    else:
      retVal = result['premium']
    return retVal

  def Login(self, username, password, notification):
    self.cm.checkDir(ptv.getAddonInfo('path') + os.path.sep + "cookies")
    if login=='':
	uname = ''
	log_desc = 'Nie zalogowano'
	log_time = 10000
	retVal = False
    else:
	uname = username + ': '
	query_data = {'url': apiLogin, 'use_host': False, 'use_cookie': True, 'load_cookie': False, 'save_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': True, 'return_data': True}
	data = self.cm.getURLRequestData(query_data, {'login' : username, 'password' : password})
	result = _json.loads(data)
	if 'error' in result:
	    log_desc = result['error'].encode('UTF-8')
	    log_time = 20000
	    retVal = False
	else:
	    log_desc = result['ok']
	    log_time = 5000
	    retVal = True
    if notification:
      notification = '(maxvideo.pl,' + uname + log_desc + ',' + str(log_time) + ')'
      xbmc.executebuiltin("XBMC.Notification" + notification +'"')
    return retVal

  def getVideoUrl(self, videoHash, cookiefile, notification):
    if cookiefile == '': load_cookie = False
    else: load_cookie = True
    query_data = { 'url': apiVideoUrl, 'use_host': False, 'use_cookie': True, 'load_cookie': load_cookie, 'save_cookie': False, 'cookiefile': cookiefile, 'use_post': True, 'return_data': True }
    data = self.cm.getURLRequestData(query_data, {'v' : videoHash, 'key' : authKey})
    result = _json.loads(data)
    result = dict([(str(k), v) for k, v in result.items()])
    if 'error' in result: videoUrl = ''
    else:
      if (not result['premium']):
	if notification:
	  xbmc.executebuiltin("XBMC.Notification(maxvideo.pl,wykup konto premium by w pelni korzystac z serwisu,15000)")
      videoUrl = result['ok'].encode('UTF-8')
    return videoUrl
