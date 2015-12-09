# -*- coding: utf-8 -*-
import os, string, StringIO
import re, sys
import xbmcaddon, xbmcgui
import traceback, xbmc

scriptID = sys.modules[ "__main__" ].scriptID
ptv = xbmcaddon.Addon(scriptID)

BASE_IMAGE_PATH = 'http://sd-xbmc.org/repository/xbmc-addons/'
BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader
import maxvideo

log = sdLog.pLog()

dbg = sys.modules[ "__main__" ].dbg
dstpath = ptv.getSetting('default_dstpath')

HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
SERVICE = 'zalukajtv'
LOGOURL = BASE_IMAGE_PATH + SERVICE + '.png'
THUMB_NEXT = BASE_IMAGE_PATH + 'dalej.png'

MAINURL = 'http://zalukaj.tv/'
SEARCHURL = 'http://zalukaj.tv/szukaj'
TOP_LINK = MAINURL + 'top100/'
HOT_LINK = MAINURL + 'hot/'

MENU_TAB = {
    1: "Filmy",
    2: "Seriale",
    3: "Wyszukaj",
    4: "Historia wyszukiwania"
}

class ZalukajTV:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.parser = sdParser.Parser()
	self.up = urlparser.urlparser()
	self.cm = sdCommon.common()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()
	self.history = sdCommon.history()
	log.setLevel(7)

    def setTable(self):
    	return MENU_TAB


    def listsMainMenu(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'main-menu','category': val, 'title': val, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir()


    def listsCategoriesMenu(self, category, url):
	query_data = { 'url': MAINURL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True, 'use_header': False}
	try:
	    data = self.cm.getURLRequestData(query_data)
	    log.info("CATEGORY: "+category)
	    log.info("DATA: "+data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	if category == 'filmy':
	    match = re.compile('<td class="wef32f"><a href="/gatunek/([0-9]+?)">(.+?)</a></td>').findall(data)
	    log.info(match)
	    link = "gatunek/"
	elif category == 'seriale':
	    match = re.compile('<td class="wef32f"><a href="/sezon-serialu/(.+?)" title="(.+?)">(.+?)</a>').findall(data)
	    log.info(match)
	    link = 'sezon-serialu/'
	if len(match) > 0:
	    for i in range(len(match)):
		params = {'service': SERVICE, 'name': category, 'title': match[i][1], 'page': url + link + match[i][0], 'icon': LOGOURL}
		self.gui.addDir(params)
	self.gui.endDir()


    def listsSearchResults (self, text):
	query_data = { 'url': SEARCHURL, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True, 'use_header': False}     
        try:
            content = self.cm.getURLRequestData(query_data, {'searchinput' : text})   
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        match = re.compile('<h3><a href="(.+?)" title="(.+?)">(.+?)</a></h3>').findall(content)
        if len(match) > 0:
            for i in range(len(match)):
                try:
                    params = {'service': SERVICE, 'title':match[i][1], 'page':match[i][0][0:], 'icon':'http://static.zalukaj.tv/image/'+match[i][0].split('/')[4]+'.jpg', 'plot':plot_match[i]}
                except:
                    params = {'service': SERVICE, 'title':match[i][1], 'page':match[i][0][0:], 'icon':'http://static.zalukaj.tv/image/'+match[i][0].split('/')[4]+'.jpg'}
                self.gui.playVideo(params)
        self.gui.endDir(False, 'movies', 'MediaInfo')


    def listsMovies(self, url, current_page=1, lang = -1, sort_type = -1):
	# print url
   	typeTab = [(0,'Lektor'),(1,'Napisy PL'),(2,'Oryginał')]
   	sortTab = [(0,'Ostatnio dodane'),(1,'Ostatnio oglądane'),(2,'Ilość odsłon'),(3,'Ulubione'),(4,'Ocena')]
	if lang!=-1:
	    langType = lang
	else:
	    d = xbmcgui.Dialog()
   	    langType = d.select("Wybierz wersję", self.cm.getItemTitles(typeTab))
	if langType == 0:
	    match = re.compile(MAINURL+'gatunek/(.+?)$').findall(url)
	    url_page = MAINURL+'gatunek,'+match[0]+'/TYPE,tlumaczone,strona-'+str(current_page)
	elif langType == 1:
	    match = re.compile(MAINURL+'gatunek/(.+?)$').findall(url)
	    url_page = MAINURL+'gatunek,'+match[0]+'/TYPE,napisy-pl,strona-'+str(current_page)
	elif langType == 2:
	    match = re.compile(MAINURL+'gatunek/(.+?)$').findall(url)
	    url_page = MAINURL+'gatunek,'+match[0]+'/TYPE,nie-tlumaczone,strona-'+str(current_page)
	if sort_type!=-1:
	    sortType = sort_type
	else:
	    d = xbmcgui.Dialog()
   	    sortType = d.select("Sortowanie", self.cm.getItemTitles(sortTab))
	if sortType == 0:
	    url_page = url_page.replace('TYPE','ostatnio-dodane')
	elif sortType == 1:
	    url_page = url_page.replace('TYPE','ostatnio-ogladane')
	elif sortType == 2:
	    url_page = url_page.replace('TYPE','odslon')
	elif sortType == 3:
	    url_page = url_page.replace('TYPE','ulubione')
	elif sortType == 4:
	    url_page = url_page.replace('TYPE','oceny')
	    
	query_data = { 'url': url_page, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True, 'use_header': False}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<h3><a href="(.+?)" title=".+?">(.+?)</a></h3>').findall(data)
	plot_match = re.compile('<div style="min-height:110px">(.+?)<a href=".+?">.+?</a></div>').findall(data)
	pages = re.compile('<div class="categories_page">(.+?)</a></div>').findall(data)
	max_page=1
	try:
	    max_page = int(pages[0].split('>')[-1])
	except:
	    pass
	if len(match) > 0:
	    for i in range(len(match)):
		try:
		    params = {'service': SERVICE, 'title':match[i][1], 'page':match[i][0], 'icon':'http://static.zalukaj.tv/image/'+match[i][0].split('/')[2]+'.jpg', 'plot':plot_match[i]}
		except:
		    params = {'service': SERVICE, 'title':match[i][1], 'page':match[i][0], 'icon':'http://static.zalukaj.tv/image/'+match[i][0].split('/')[2]+'.jpg'}
		self.gui.playVideo(params)
	if current_page < max_page:
		params = {'service': SERVICE, 'name': 'nextpage', 'title': 'Następna strona', 'page': url, 'icon': THUMB_NEXT, 'page_num':current_page, 'lang':langType, 'sort':sortType}
		self.gui.addDir(params)
	self.gui.endDir(False, 'movies', 'MediaInfo')

    
    def listsSeasons(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True, 'use_header': False}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	#match = re.compile('<div align="center" id="sezony"><a class="sezon" href="(.+?)" >(.+?)</a></div>').findall(data)
	match = re.compile('<div align="center" id="sezony"><a class="sezon" href="(.+?)">(.+?)</a></div>').findall(data)
	if match > 0:
	    for i in range(len(match)):
		params = {'service':SERVICE, 'name': 'season', 'title':match[i][1], 'page':MAINURL+match[i][0][1:]}
	        self.gui.addDir(params)
	self.gui.endDir()


    def listsEpisodes(self, url):
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True, 'use_header': False}
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	#match = re.compile('<div align="left" id="sezony".+?>(.+?) <a href="(.+?)" title=".+?">(.+?)</a></div>').findall(data)
	match = re.compile('<div align="left" id="sezony".*?>(.+?) <a href="(.+?)" title=".+?">(.+?)</a></div>').findall(data)

	if match > 0:
	    for i in range(len(match)):
		params = {'service':SERVICE, 'name': 'episode', 'title':match[i][0]+" "+match[i][2], 'page':match[i][1]}
	        self.gui.playVideo(params)
	self.gui.endDir(False,'movies')


    def getVideoID(self,url):
        print "kups"
	videoID = ''
	query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True, 'use_header': False}
	try:
	    link = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()
	match = re.compile('<iframe allowTransparency="true" src="(.+?)" width="490" height="370" scrolling="no" frameborder="0"><img src="http://static.zalukaj.tv/images/loading.gif" alt="Loading"/></iframe>').findall(link)
	print str(match)
        if len(match) > 0:
	    player = MAINURL + match[0][1:]
	    url = player.split('&')[0]+'&x=1&'+player.split('&')[1]
            query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True, 'use_header': False}
            response = self.cm.getURLRequestData(query_data)         
	    match=re.compile('<iframe src="(.+?)" .+?></iframe>').findall(response)
            print "bar"
            print str(match)
	    if len(match) > 0:
                query_data = { 'url': match[0], 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True, 'use_header': False}
                response = self.cm.getURLRequestData(query_data)
	        match = re.compile('var so = new SWFObject\(\'(.+?)\'').findall(response)
                print "match"
                print str(match)
		match_vshare=re.compile('url: \'(.+?)\'').findall(response)
                print str(match_vshare)
	        if len(match) > 0:
	            return match[0]
	        if len(match_vshare) > 0:
	            return match_vshare[0]
	return videoID
    
    def listsHistory(self, table):
        print "here"
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
	link = self.parser.getParam(params, "url")
	service = self.parser.getParam(params, "service")
	action = self.parser.getParam(params, "action")
	path = self.parser.getParam(params, "path")
	page_num = self.parser.getParam(params,"page_num")
	lang = self.parser.getParam(params,"lang")
	sort_type = self.parser.getParam(params,"sort")
	self.parser.debugParams(params, dbg)
    #MAIN MENU
	if name == None:
	    self.listsMainMenu(MENU_TAB)
    #FILMY
	elif category == self.setTable()[1]:
	    self.listsCategoriesMenu('filmy', MAINURL)
    #SERIALE
	elif category == self.setTable()[2]:
	    self.listsCategoriesMenu('seriale', MAINURL)
    #SZUKAJ
	elif category == self.setTable()[3]:
            text = self.gui.searchInput(SERVICE)
            if text != None:
                self.listsSearchResults(text)
    
    #HISTORIA WYSZUKIWANIA
	elif category == self.setTable()[4]:
	    t = self.history.loadHistoryFile(SERVICE)
	    self.listsHistory(t)
	if name == 'history':
	    self.listsSearchResults(title)


    #LISTA TYTULOW
	if name == 'filmy':
	    self.listsMovies(page)
	elif name == "seriale":
	    self.listsSeasons(page)
	elif name == "season":
	    self.listsEpisodes(page)
	elif name== "nextpage":
	    pn = int(page_num)
	    pn+=1
	    self.listsMovies(page, pn, int(lang), int(sort_type))
        elif name== "szukaj":
            self.listsSearchResults(page)



    #ODTWÓRZ VIDEO
	if name == 'playSelectedVideo':
	    videoUrl = ''
	    ID = self.getVideoID(page)
	    if ID != '':
                if 'vshare.io' in ID:
                    videoUrl = ID
                else:
                    videoUrl = self.up.getVideoLink(ID)
            self.gui.LOAD_AND_PLAY_VIDEO(videoUrl, title)
    #POBIERZ
	if action == 'download' and link != '':
	    if link.startswith('http'):
		linkVideo = self.up.getVideoLink(self.getVideoID(link))
		if linkVideo != False:
		    self.cm.checkDir(os.path.join(dstpath, SERVICE))
		    dwnl = downloader.Downloader()
		    dwnl.getFile({ 'title': title, 'url': linkVideo, 'path': path })
