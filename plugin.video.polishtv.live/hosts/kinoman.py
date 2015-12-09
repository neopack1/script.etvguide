# -*- coding: utf-8 -*-
import os, string, StringIO
import urllib, urllib2, re, sys
import xbmcaddon, xbmcgui, xbmcplugin
import xbmc, traceback

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()

dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg

username = ptv.getSetting('kinoman_login')
password = ptv.getSetting('kinoman_password')

SERVICE = 'kinoman'
MAINURL = 'http://www.kinoman.tv'
MAINURLS = 'https://www.kinoman.tv'
LOGOURL = BASE_IMAGE_PATH + SERVICE + '.png'
COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + SERVICE + ".cookie"
THUMB_NEXT = BASE_IMAGE_PATH + "dalej.png"

SEARCH_URL = MAINURL + '/szukaj?query='
LIST_URL = MAINURL + '/filmy?'
SERIAL_URL = MAINURL + '/seriale'

SERVICE_MENU_TABLE = {
    1: "Kategorie filmowe",
    2: "Typy filmów",
    3: "Ostatnio dodane",
    4: "Najwyżej ocenione",
    5: "Najczęściej oceniane",
    6: "Najczęściej oglądane",
    7: "Ulubione",
    8: "Najnowsze",
    9: "Seriale",
    10: "Wyszukaj",
    11: "Historia wyszukiwania"
}

class Kinoman:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.parser = sdParser.Parser()
	self.up = urlparser.urlparser()
	self.cm = sdCommon.common()
	self.history = sdCommon.history()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def setTable(self):
	return SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu', 'title': val, 'category': val, 'icon':LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsFiltersMenu(self, filter):
	query_data = { 'url': MAINURL + '/filmy', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	
	match = re.findall('<a[^>]+data-value="([^"]*)"[^>]*data-filter="' + filter + '[^"]*"[^>]*>(.*?)</a>\s*(?:<span[^>]*>(.*?)</span>)?', data, re.S)
	if len(match) > 0:
	    for i in range(len(match)):
		title = match[i][1]
		if (len(match[i]) > 2):
			title = title + ' [COLOR=white]' + match[i][2] + '[/COLOR]'
		params = {'service': SERVICE, 'name': 'category', 'title': title, 'category': filter + '%5b0%5d=' + match[i][0], 'icon':LOGOURL}
		self.gui.addDir(params)

	self.gui.endDir(True)

    def formatMatch(self, match):
	
	result = {}
	
	reClean = re.compile('<[^>]+>|^\s*|\s*$', re.S)
	reSpace = re.compile('\s+', re.S)
	reComma = re.compile('\s+,\s*', re.S)
	
	for (name, value) in match.items():
		if value:
			if name == 'title' or name == 'plot' or name == 'genre':
				value = reSpace.sub(' ', reClean.sub('', value))
				if name == 'genre':
					value = reComma.sub(', ', value)
			if name == 'icon':
				value = value.replace('m.jpg', 'o.jpg')
			if  name == 'page':
				value = MAINURL + value
			if name == 'code':
				if value == 'PL':
					color = 'lime'
				elif value == 'Dubbing':
					color = 'blue'
				elif value == 'Lektor':
					color = 'green'
				elif value == 'Napisy':
					color = 'yellow'
				else:
					color = 'red'
				value = '[COLOR=' + color + ']' + value + '[/COLOR]';
			
			result[name] = self.cm.html_entity_decode(value)
		
	return result

    def endDir(self, type):
    
	if type == 'movies':
		listMask = '%P [[COLOR=white]%Y[/COLOR]] %R'
		viewMode = 'MediaInfo'
	elif type == 'episodes':
		listMask = '[[COLOR=white]%H [/COLOR]]%Z'
		viewMode = 'List'
	else:
		listMask = None
		viewMode = None 
	
	if listMask:
		xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE, label2Mask = listMask )
	
	self.gui.endDir(False, type, viewMode)

    def getFilmTab(self, url, category, pager):
        #xbmcgui.Dialog().ok('url', url)
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	
	matches = re.compile('<div[^>]+class="[^"]*movie-item[^"]*"[^>]*>.*?<img[^>]+src="(?P<icon>[^"]*)"[^>]*>.*?<a[^>]+class="[^"]*title[^"]*"[^>]*href="(?P<page>[^"]+)"[^>]*>\s*(?P<title>.+?)(?:\((?P<year>\d{4})\).*?)?\s*(?:\[\s*(?P<code>\w+)\s*\].*?)?\s*</a>.*?<p[^>]+class="[^"]*cats[^"]*"[^>]*>\s*(?P<genre>[^\|]+)\|\s*Ocena:\s*(?P<rating>[0-9\.]+).*?</p>.*?<p[^>]+class="[^"]*desc[^"]*"[^>]*>\s*(?P<plot>.+?)\s*</p>.*?<div[^>]+class="[^"]*clearfix[^"]*"[^>]*>', re.S)
	
	for match in matches.finditer(data):
		params = self.formatMatch(match.groupdict())
		params.update({ 'service': SERVICE, 'dstpath': dstpath })
		
		self.gui.playVideo(params)
	
	if re.search('<li><a href="/filmy[^"]*" rel="next">&raquo;</a></li>', data, re.S):
	    params = {'service': SERVICE, 'name': 'nextpage', 'category': category, 'title': 'Następna strona', 'page': str(int(pager) + 1), 'icon': THUMB_NEXT }
	    self.gui.addDir(params)
	
	self.endDir('movies')

    def getSerialCategories(self, url, category):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	if category == '0 - 9':
	    matchAll = re.compile('id="letter_0-9"(.+?)<div class="offset1', re.S).findall(data);
	else:
	    matchAll = re.compile('id="letter_' + category + '"(.+?)<div class="offset1', re.S).findall(data);
	if len(matchAll) > 0:
	    match = re.compile('<a href="(.+?)" class="pl-corners">(.+?)<span class="subtitle".+?</span></a>').findall(matchAll[0]);
	    if len(matchAll) > 0:
		for i in range(len(match)):
		    title = match[i][1].replace('<span class="label label-important">NOWE</span> ', '')
		    params = { 'service': SERVICE, 'name': 'getSeason', 'tvshowtitle': title, 'title': self.cm.html_entity_decode(title), 'page': MAINURL + match[i][0], 'icon': LOGOURL }
		    self.gui.addDir(params)
	self.gui.endDir(False, 'tvshows')

    def listsABCMenu(self, table):
	for i in range(len(table)):
	    params = {'service': SERVICE, 'name': 'abc-menu','category': table[i], 'title': table[i], 'icon':'' }
	    self.gui.addDir(params)
	self.gui.endDir()

    def listsHistory(self, table, ser):
	for i in range(len(table)):
	    if table[i] <> '':
		params = {'service': SERVICE, 'name': 'history', 'category': ser, 'title': table[i],'icon':'' }
		self.gui.addDir(params)
	self.gui.endDir()

    def searchTab(self, url, sType):
        print url
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	
	if sType == 'movies':
		reLabel = 'Filmy'
		reTitle = '(?P<title>.+?)(?:\((?P<year>\d{4}(?:-\d{4})?)\).*?)?\s*(?:\[\s*(?P<code>\w+)\s*\].*?)?'
	elif sType == 'tvshows':
		reLabel = 'Seriale'
		reTitle = '(?P<title>.+?)'
	else:
		exit()

	matchIn = re.findall('<div[^>]+class="[^"]*results_title[^"]*"[^>]*>[^<]*' + reLabel + '[^<]*</div>.*?<div[^>]+class="[^"]*results_title[^"]*"[^>]*>', data, re.S)[0]
	matches = re.compile('<div[^>]+class="[^"]*result box[^"]*"[^>]*>.*?<img[^>]+src="(?P<icon>[^"]*)"[^>]*>.*?<a[^>]+href="(?P<page>[^"]+)"[^>]*class="[^"]*pl-white[^"]*"[^>]*>\s*' + reTitle + '\s*</a>.*?<span[^>]+class="[^"]*small-bread[^"]*"[^>]*>\s*(?P<genre>[^<]+).*?Ocena[^\d]+(?P<rating>[\d\.]+).*?<p[^>]*>\s*(?P<plot>.+?)\s*</p>.*?</button>', re.S)
	
	for match in matches.finditer(matchIn):
		params = self.formatMatch(match.groupdict())
		if sType == 'movies':
			params.update({'service': SERVICE, 'dstpath': dstpath })
			self.gui.playVideo(params)
		elif sType == 'tvshows':
			params.update({ 'service': SERVICE, 'name': 'getSeason', 'tvshowtitle': params['title'] })
			self.gui.addDir(params)
	
	self.endDir(sType)

    def getSeasonTab(self, url, serial):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	icon = re.compile('<img src="(.+?)" alt=""/>').findall(data)
	img = icon[0].replace('m.jpg', 'o.jpg')
	match = re.compile('<button data-action="scrollTo" data-scroll="(.+?)"').findall(data)
	if len(match) > 0:
	    for i in range(len(match)):
                title = match[i].replace('_', ' ').capitalize()
		params = {'service': SERVICE, 'name': 'getEpisodes', 'season': match[i], 'tvshowtitle': serial, 'title': title, 'page': url, 'icon': img}
		self.gui.addDir(params)
	self.gui.endDir(True)

    def getEpisodesTab(self, url, serial, sezon, icon):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	matchAll = re.compile('style="margin:0;margin-top:10px;" id="'+sezon+'">(.+?)<div class="p10"></div>', re.DOTALL).findall(data)
	if len(matchAll) > 0:
	    match = re.compile('<a class="o" href="(.+?)/(.+?)/(.+?)">[^(]+\(([^)]+).*?</a>').findall(matchAll[0])
	    if len(match) > 0:
		for i in range(len(match)):
		    page = MAINURL + match[i][0]+'/'+match[i][1]+'/'+match[i][2]
		    print page
		    #title = '%s - %s - %s' % (serial, match[i][1], self.cm.html_entity_decode(match[i][3]))
		    title = self.cm.html_entity_decode(match[i][3])
		    temp = re.findall('\w0*(\d+)', match[i][1])
		    print title
		    params = {'service': SERVICE, 'dstpath': dstpath, 'season': temp[0], 'episode': temp[1], 'tvshowtitle': serial, 'title': title, 'page': page, 'icon': icon}
		    self.gui.playVideo(params)
	self.endDir('episodes')

    def getHostTable(self,url):
	videoID = ''
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
	try:
	    link = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('class="player-wrapper" id="player_(.+?)"').findall(link)
	if len(match) > 0:
	    for i in range(len(match)):
		query_data = { 'url': MAINURL+'/players/init/' + match[i], 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
		try:
		    link = self.cm.getURLRequestData(query_data)
		except Exception, exception:
		    traceback.print_exc()
		    self.exception.getError(str(exception))
		    exit()
		data = link.replace('\\', '')
		match = re.compile('"data":"(.+?)"').findall(data)
		if len(match) > 0:
                    query_data = { 'url': MAINURL+'/players/get', 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True}
                    post_data = { 'hash' : match[0] }
                    try:
                        link = self.cm.getURLRequestData(query_data, post_data)
                    except Exception, exception:
                        traceback.print_exc()
                        self.exception.getError(str(exception))
                        exit()
                    #ShowNormalPlayer('http://static-kinoman.tv:8989/balancer/vip/123088',
                    #match = re.compile('src="(.+?)"').findall(link)
                    #<iframe src="http://www.vidzer.net/e/902b9f6ff61fb13e8768aa1a65d760a1?w=631&h=425&name=Elle.s'en.va" width="631" height="425" scrolling="no" frameborder="0"></iframe>
                    match = re.search('src="([^"]+?)"', link)
	
                    if match:
                        videoID = self.getResolvedURL( match.group(1) )
                    else:
                        match = re.search("""ShowNormalPlayer\('([^']+?)',""", link)
                        if match:
                            videoID = match.group(1)
                            log.info("final url: " + videoID)
                            break
        return videoID

	
    def getResolvedURL(self, url):
        url = self.up.getVideoLink( url )
        if isinstance(url, basestring):
            return url
        else:
            return ""
        

    def getHostingTable(self,url):
	videoID = ''
	query_data = { 'url': url, 'use_host': False, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True}
	try:
	    link = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('class="player-wrapper" id="player_(.+?)"').findall(link)
	if len(match) > 0:
	    for i in range(len(match)):
                query_data = { 'url': MAINURL+'/players/init/' + match[i], 'use_host': False, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True}
		try:
		    link = self.cm.getURLRequestData(query_data)
		except Exception, exception:
		    traceback.print_exc()
		    self.exception.getError(str(exception))
		    exit()
		data = link.replace('\\', '')
		match = re.compile('"data":"(.+?)"').findall(data)
		if len(match) > 0:
                    query_data = { 'url': MAINURL+'/players/get', 'use_host': False, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': True, 'return_data': True}
                    post_data = { 'hash' : match[0], 'type' : 'vip' }
                    try:
                        link = self.cm.getURLRequestData(query_data, post_data)
                    except Exception, exception:
                        traceback.print_exc()
                        self.exception.getError(str(exception))
                        exit()
                    match = re.compile("ShowNormalPlayer.+?'(.+?)',").findall(link)
                    if len(match) > 0:
                        videoID = match[0] + '|Referer=http://www.kinoman.tv/assets/kinoman.tv/swf/flowplayer-3.2.7.swf'
                        log.info("final link: " + videoID)
                        return videoID

    def mobileAuth(self):
        if username == '' or password == '':
            return False
        
        try:
            data = { 'use_host': False, 'use_post': False, 'return_data': True, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE }
            
            data['url'] = 'http://m.kinoman.tv/account/login'
            form = self.cm.getURLRequestData(data)
            vals = re.compile('<input.*?name=".*?time.*?".*?value="(\d+)"[^>]*?>.*?<input.*?name=".*?hash.*?".*?value="(\w+)"[^>]*?>', re.S).findall(form)
            
            data['url'] = 'http://www.kinoman.tv/auth/mobileLogin?time=' + vals[0][0] + '&hash=' + vals[0][1] + '&login=' + username + '&password=' + password
            init = self.cm.getURLRequestData(data)
            
            data['url'] = 'http://www.kinoman.tv/tool/getUser?time=' + vals[0][0]
            user = self.cm.getURLRequestData(data)
            code = re.compile('"(\w+)"', re.S).findall(user)
            
            data['url'] = 'http://m.kinoman.tv/account/login'
            data['use_post'] = True
            auth = self.cm.getURLRequestData(data, { 'hash': code[0] })
            
            return auth.index('success') > 0
            
        except Exception, exception:
            return False

    def getHostingMobile(self, page):
        try:
            data = { 'use_host': False, 'use_post': False, 'return_data': True, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE }
            
            data['url'] = 'http://m.kinoman.tv/filmy' + page[page.rindex('/'):]
            init = self.cm.getURLRequestData(data)
            base = re.compile('<div[^>]*?role="[^"]*?main[^"]*?"[^>]*?class="[^"]*?ui-content[^"]*?jqm-content[^"]*?"[^>]*?>.*?<a.*?href="([^"]+)"[^>]*?>', re.S).findall(init)
            
            data['url'] = base[0]
            show = self.cm.getURLRequestData(data)
            link = re.compile('<a.*?href="([^"]+)"[^>]*?id="player"[^>]*?>', re.S).findall(show)
            
            return link[0]
            
        except Exception, exception:
            return ''

    def getMediaType(self):
	mediaTypes = { 'movies': 'Filmy', 'tvshows': 'Seriale' }
	typeIndex = xbmcgui.Dialog().select("Co chcesz znaleść?", mediaTypes.values())
	if typeIndex >= 0:
		return mediaTypes.keys()[typeIndex]
	return None

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
	sezon = self.parser.getParam(params, "season")
	epizod = self.parser.getParam(params, "episode")
	serial = self.parser.getParam(params, "tvshowtitle")

	self.parser.debugParams(params, dbg)

	if str(page) == 'None' or page == '': page = '1'

    #MAIN MENU
	if name == None:
	    #logowanie
	    if username == '' or password == '': loginData = {}
	    else: loginData = { 'username': username, 'password': password, "submit_login": "login", "submit": "" }
	    self.cm.requestLoginData(MAINURL + "/auth/login", '<a href="/auth/logout">wyloguj', COOKIEFILE, loginData)
	    self.mobileAuth()
	    self.listsMainMenu(SERVICE_MENU_TABLE)
    #KATEGORIE FILMOWE
	elif category == self.setTable()[1]:
	    self.listsFiltersMenu('genres')
    #TYPY FILMÓW
	elif category == self.setTable()[2]:
	    self.listsFiltersMenu('types')
    #OSTATNIO DODANE
	elif category == self.setTable()[3]:
	    url = LIST_URL + 'p=' + page
	    self.getFilmTab(url, category, page)
    #NAJWYŻEJ OCENIONE
	elif category == self.setTable()[4]:
	    url = LIST_URL + 'sorting=movie.rate&p=' + page
	    self.getFilmTab(url, category, page)
    #NAJCZĘŚCIEJ OCENIANE
	elif category == self.setTable()[5]:
	    url = LIST_URL + 'sorting=total_rates&p=' + page
	    self.getFilmTab(url, category, page)
    #NAJCZĘŚCIEJ OGLĄDANE
	elif category == self.setTable()[6]:
	    url = LIST_URL + 'sorting=movie.views&p=' + page
	    self.getFilmTab(url, category, page)
    #ULUBIONE
	elif category == self.setTable()[7]:
	    url = LIST_URL + 'sorting=total_favs&p=' + page
	    self.getFilmTab(url, category, page)
    #NAJNOWSZE
	elif category == self.setTable()[8]:
	    url = LIST_URL + 'sorting=movie.created&p=' + page
	    self.getFilmTab(url, category, page)
    #SERIALE
	elif category == self.setTable()[9]:
	    self.listsABCMenu(self.cm.makeABCList())
    #WYSZUKAJ
	elif category == self.setTable()[10]:
	    sType = self.getMediaType()
	    if sType:
			sText = self.gui.searchInput(SERVICE + sType)
			if sText:
				self.searchTab(SEARCH_URL + sText, sType)
    #HISTORIA WYSZUKIWANIA
	elif category == self.setTable()[11]:
	    sType = self.getMediaType()
	    if sType:
			sText = self.history.loadHistoryFile(SERVICE + sType)
			self.listsHistory(sText, sType)
	if name == 'history':
	    self.searchTab(SEARCH_URL + title, category)
    #LISTA SERIALI
	if name == 'abc-menu':
	    self.getSerialCategories(SERIAL_URL, category)
	if name == 'getSeason':
	    self.getSeasonTab(page, title)
	if name == 'getEpisodes':
	    self.getEpisodesTab(page, serial, sezon, icon)
    #LISTA FILMÓW
	if name == 'category' or name == 'nextpage':
	    if category not in self.setTable().values():
		self.getFilmTab(LIST_URL + category + '&p=' + page, category, page)
    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    linkVideo = None
	    if username != '' and password != '':
		linkVideo = self.getHostingTable(page)
	    if linkVideo == None:
		videoID = self.getHostTable(page)
		if videoID != False:
                    linkVideo = videoID                   
                    #linkVideo = self.up.getVideoLink(videoID)
		else:
                    d = xbmcgui.Dialog()
		    d.ok(SERVICE + ' - przepraszamy', 'Ten materiał nie został jeszcze dodany,', 'albo jest dostępny tylko dla konta Standard lub Premium', 'Zapraszamy w innym terminie.')
		    return False
	    if linkVideo == None or linkVideo == '':
	        linkVideo = self.getHostingMobile(page)
	    self.gui.LOAD_AND_PLAY_VIDEO(linkVideo, title)
    #POBIERZ
	if action == 'download' and link != '':
	    self.cm.checkDir(os.path.join(dstpath, SERVICE))
	    if link.startswith('http://'):
		linkVideo = None
		if username != '' and password != '':
		    linkVideo = self.getHostingTable(link)
		if linkVideo == None:
		    linkVideo = self.up.getVideoLink(self.getHostTable(link))
		if linkVideo != False:
		    dwnl = downloader.Downloader()
		    dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })
