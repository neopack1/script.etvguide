# -*- coding: utf-8 -*-
import os, sys
import xbmcgui, xbmc, xbmcaddon, xbmcplugin
import sdCommon, sdParser, sdLog

pmod = xbmcaddon.Addon(id='script.module.sd-xbmc')
t = lambda x: pmod.getLocalizedString(x).encode('utf-8')

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg

class sdGUI:
	def __init__(self):
		self.cm = sdCommon.common()
		self.history = sdCommon.history()
		self.parser = sdParser.Parser()
		
	def searchInput(self, SERVICE, heading='Wyszukaj'):
		keyboard = xbmc.Keyboard('', heading, False)
		keyboard.doModal()
		if keyboard.isConfirmed():
			text = keyboard.getText()
			self.history.addHistoryItem(SERVICE, text)
			return text
		
	def dialog(self):
		return xbmcgui.Dialog()
		
	def percentDialog(self):
		return xbmcgui.DialogProgress()
	
	def notification(self, title=" ", msg=" ", time=5000):
		xbmc.executebuiltin("XBMC.Notification("+title+","+msg+","+str(time)+")")

	def getBaseImagePath(self):
		return 'http://sd-xbmc.org/repository/xbmc-addons/'

	def getThumbNext(self):
		return self.getBaseImagePath() + "dalej.png"
	
	def getLogoImage(self, title, ext="png"):
		return self.getBaseImagePath() + title + "." + ext

	def __setInfoLabels(self, params, pType):
		InfoLabels = {}
		if pType=="video":
				infoLabelsKeys = ["genre", "year", "episode", "season", "top250", "tracknumber", "rating", "playcount", "overlay",
					"cast", "castandrole", "director", "mpaa", "plot", "plotoutline", "title", "originaltitle", "sorttitle",
					"duration", "studio", "tagline", "writer", "tvshowtitle", "premiered", "status", "code", "aired", "credits",
					"lastplayed", "album", "artist", "votes", "trailer", "dateadded"]
		elif pType=="music":
				infoLabelsKeys = ["tracknumber", "duration", "year", "genre", "album", "artist", "title", "rating",
						"lyrics", "playcount", "lastplayed"]

		for key, value in params.items():
			if key in infoLabelsKeys:
				InfoLabels[key] = value
		return InfoLabels

	def __play(self, params, isPlayable=False, isFolders=False, pType="video", params_keys_needed = None ):
		if pType=="video":
			params['name'] = 'playSelectedVideo'
		elif pType=="music":
			params['name'] = 'playSelectedAudio'
# uproszczenie urli / niezbedne żeby dobrze działał status "watched"
		if params_keys_needed == None:
			u=sys.argv[0] + self.parser.setParam(params)
		else:
			needed_params = {}
			for k in params_keys_needed:
				if params.has_key(k):
					needed_params[k]=params[k]
			u=sys.argv[0] + self.parser.setParam(needed_params)

		pType = pType.replace("dir_","")

		params['icon'] = params.get('icon') or "DefaultVideo.png"

		if dbg == True:
			log.info(" - "+pType+": ")
			self.parser.debugParams(params, True)

		params['title'] = params.get('title') or None
		if params['title'] == None: return False
		params['series'] = params.get('series') or None
		params['file_name'] = params['title']
		if params['series'] != None:
			params['file_name'] = "%s - %s" % (params['series'], params['title'])

		liz=xbmcgui.ListItem(params['title'], iconImage="DefaultFolder.png", thumbnailImage=params['icon'])
		if isPlayable:
			liz.setProperty("IsPlayable", "true")

		params['fanart'] = params.get('fanart') or "http://sd-xbmc.org/repository/repository.sd-xbmc.org/fanart.jpg"

		params['banner'] = params.get('banner') or params['icon']

		meta = self.__setInfoLabels(params, pType)
		meta.update({'art(banner)': params['banner'], 'art(poster)': params['icon']})

		liz.setProperty("fanart_image", params['fanart'])
		liz.setInfo( type=pType, infoLabels=meta )
		if isPlayable and params_keys_needed != None:  #uproszone url = wsparcje dla "watched"
			liz.addContextMenuItems([(t(55805), 'Action(ToggleWatched)')])
#			liz.addStreamInfo('video', { 'codec': 'h264', 'aspect': 1.78, 'width': 1280,'height': 720})
		if self.cm.isEmptyDict(params, 'page'): params['page'] = ''
		if (not self.cm.isEmptyDict(params, 'dstpath')) and pType=="video":
			cm = self.__addDownloadContextMenu({ 'service': params['service'], 'title': params['file_name'], 'url': params['page'], 'path': os.path.join(params['dstpath'], params['service']) })
			liz.addContextMenuItems(cm, replaceItems=False)
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolders)

	def __addDownloadContextMenu(self, params={}):
		params['action'] = 'download'
		param = self.parser.setParam(params)
		cm = []
		cm.append((t(55801), "XBMC.RunPlugin(%s%s)" % (sys.argv[0], param)))
		cm.append((t(55804), "XBMC.Action(Info)",))
		return cm

	def playVideo(self, params, isPlayable=False, isFolders=False, params_keys_needed = None ):
		self.__play(params, isPlayable, isFolders, "video" , params_keys_needed )

	def playAudio(self, params, isPlayable=False, isFolders=False, params_keys_needed = None):
		self.__play(params, isPlayable, isFolders, "music" , params_keys_needed )

	def addDir(self, params, isFolders=True, params_keys_needed = None):
		self.__play(params, False, isFolders, "dir_video", params_keys_needed)

	def endDir(self, sort=False, content=None, viewMode=None, ps=None):
		'''
		ToDo:
		Check is Confluence, not? other View Mode
		Confluence View Modes:
		http://www.xbmchub.com/forums/general-python-development/717-how-set-default-view-type-xbmc-lists.html#post4683
		https://github.com/xbmc/xbmc/blob/master/addons/skin.confluence/720p/MyVideoNav.xml
		'''
		if ps==None:
			ps=int(sys.argv[1])
		if sort==True:
			xbmcplugin.addSortMethod(ps, xbmcplugin.SORT_METHOD_LABEL)
		canBeContent = ["files", "songs", "artists", "albums", "movies", "tvshows", "episodes", "musicvideos"]
		if content in canBeContent:
			xbmcplugin.setContent(ps,content)
		if viewMode!=None:
			viewList = {}
			if 'confluence' in xbmc.getSkinDir():
				viewList = {
					'List':						'50',
					'Big List':					'51',
					'ThumbnailView':			'500',
					'PosterWrapView':			'501',
					'PosterWrapView2_Fanart':	'508',
					'MediaInfo':				'504',
					'MediaInfo2':				'503',
					'MediaInfo3':				'515',
					'WideIconView':				'505',
					'MusicVideoInfoListView':	'511',
					'AddonInfoListView1':		'550',
					'AddonInfoThumbView1':		'551',
					'LiveTVView1':				'560'
				}
			if viewMode in viewList:
				view = viewList[viewMode]
			else:
				view='None'
			xbmc.executebuiltin("Container.SetViewMode(%s)" % (view))
		xbmcplugin.endOfDirectory(ps)

	def new_playlist(self, playlist='audio'):
		playlists = {'audio': 0, 'video': 1}
		if playlist not in playlists.keys():
			log.info('Playlista "%s" jest inwalidą ;).' % playlist)
		selected_playlist = xbmc.PlayList(playlists[playlist])
		selected_playlist.clear()
		return selected_playlist

	def add_to_playlist(self, playlist, items):
		if isinstance(items, list):
			for item in items:
				playlist.add(item)
		elif isinstance(items, str):
			playlist.add(items)

	def __LOAD_AND_PLAY(self, url, title, player = True, pType='video'):
		if url == '':
			d = xbmcgui.Dialog()
			d.ok('Nie znaleziono streamingu', 'Może to chwilowa awaria.', 'Spróbuj ponownie za jakiś czas')
			return False
		thumbnail = xbmc.getInfoImage("ListItem.Thumb")
		liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
		liz.setInfo( type="pType", infoLabels={ "Title": title } )
		try:
			if player != True:
				print "custom player pCommon"
				xbmcPlayer = player
			else:
				print "default player pCommon"
				xbmcPlayer = xbmc.Player()
			xbmcPlayer.play(url, liz)
		except:
			d = self.dialog()
			if pType=="video":
					d.ok('Wystąpił błąd!', 'Błąd przy przetwarzaniu, lub wyczerpany limit czasowy oglądania.', 'Zarejestruj się i opłać abonament.', 'Aby oglądać za darmo spróbuj ponownie za jakiś czas.')
			elif pType=="music":
					d.ok('Wystąpił błąd!', 'Błąd przy przetwarzaniu.', 'Aby wysłuchać spróbuj ponownie za jakiś czas.')
			return False
		return True

	def __LOAD_AND_PLAY_WATCHED(self, url, pType='video'): # NOWE wersja używa xbmcplugin.setResolvedUrl wspiera status "watched"
		if url == '':
			d = xbmcgui.Dialog()
			d.ok('Nie znaleziono streamingu', 'Może to chwilowa awaria.', 'Spróbuj ponownie za jakiś czas')
			return False
		liz=xbmcgui.ListItem(path=url)
		try:
			return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
		except:
			d = self.dialog()
			if pType=="video":
				d.ok('Wystąpił błąd!', 'Błąd przy przetwarzaniu, lub wyczerpany limit czasowy oglądania.', 'Zarejestruj się i opłać abonament.', 'Aby oglądać za darmo spróbuj ponownie za jakiś czas.')
			elif pType=="music":
				d.ok('Wystąpił błąd!', 'Błąd przy przetwarzaniu.', 'Aby wysłuchać spróbuj ponownie za jakiś czas.')
			return False

	def LOAD_AND_PLAY_VIDEO(self, url, title, player = True):
		if url != False:
			self.__LOAD_AND_PLAY(url, title, player, "video")
		else:
			d = xbmcgui.Dialog()
			d.ok('Brak linku!', 'Przepraszamy, chwilowa awaria.', 'Zapraszamy w innym terminie.')

	def LOAD_AND_PLAY_VIDEO_WATCHED(self, url): # NOWE wersja używa xbmcplugin.setResolvedUrl wspiera status "watched"
		if url != False:
			return self.__LOAD_AND_PLAY_WATCHED(url,'video')
		else:
			d = xbmcgui.Dialog()
			d.ok('Brak linku!', 'Przepraszamy, chwilowa awaria.', 'Zapraszamy w innym terminie.')
			return False

	def LOAD_AND_PLAY_AUDIO(self, url, title, player = True):
		if url != False:
			self.__LOAD_AND_PLAY(url, title, player, "music")
		else:
			d = xbmcgui.Dialog()
			d.ok('Brak linku!', 'Przepraszamy, chwilowa awaria.', 'Zapraszamy w innym terminie.')

	def LOAD_AND_PLAY_AUDIO_WATCHED(self, url): # NOWE wersja używa xbmcplugin.setResolvedUrl wspiera status "watched"
		if url != False:
			return self.__LOAD_AND_PLAY_WATCHED(url,'audio')
		else:
			d = xbmcgui.Dialog()
			d.ok('Brak linku!', 'Przepraszamy, chwilowa awaria.', 'Zapraszamy w innym terminie.')
			return False