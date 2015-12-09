# -*- coding: utf-8 -*-
import os, re, sys, math
import xbmcaddon, traceback, xbmcgui
import xml.etree.ElementTree as ET

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = sys.modules[ "__main__" ].scriptID
scriptname   = sys.modules[ "__main__" ].scriptname
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, urlparser, sdCommon, sdNavigation, sdErrors, downloader

log = sdLog.pLog()
dstpath = ptv.getSetting('default_dstpath')
dbg = sys.modules[ "__main__" ].dbg
proxy = ptv.getSetting('tvp_proxy')
videoQuality = ptv.getSetting('tvp_quality')

SERVICE = 'tvp'
ICONURL = 'http://sd-xbmc.org/repository/xbmc-addons/'
THUMB_SERVICE = ICONURL + SERVICE + '.png'
LOGOURL = ICONURL + SERVICE + '.png'
THUMB_NEXT = ICONURL + 'dalej.png'
PAGE_MOVIES = ptv.getSetting('tvp_perpage')
MAINURL = "http://www.tvp.pl/pub/stat"
API = '/videolisting?object_type=video&child_mode=SIMPLE&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE'
TOKENIZER = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?platform=mobile-app&object_id='
#TOKENIZER = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?object_id='
FORMATS = {"video/mp4":"mp4"}


CATEGORIES = {
    "Teleexpress": 8811603,
    "Wiadomości": 7405772,
    "Panorama": 5513139,
    "Kronika Krakowska": 1277349,
    "Sport": 1775930,
    "Panorama Dnia": 12275918,
    "Serwis Info": 1484,
#   "Przegapiłes": "/missed?src_id=1885&object_id=-1&offset=-1&dayoffset=-1&rec_count=",
#   "Kultura": 883, #with with_subdirs=true instead of object_type=video&child_mode=SIMPLE
#   "Teleexpress": "/videolisting?object_id=8811603&object_type=video&child_mode=SIMPLE&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=",
#   "Wiadomości": "/videolisting?object_id=7405772&object_type=video&child_mode=SIMPLE&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=",
#   "Panorama": "/videolisting?object_id=5513139&object_type=video&child_mode=SIMPLE&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=",
#   "Kronika": "/videolisting?object_id=1277349&object_type=video&child_mode=SIMPLE&sort_desc=true&sort_by=RELEASE_DATE&sort_desc=true&rec_count=",
#   "Sport": "/videolisting?object_id=1775930&object_type=video&child_mode=SIMPLE&sort_desc=true&sort_by=RELEASE_DATE&sort_desc=true&rec_count=",
#   "Kultura": "/videolisting?object_id=883&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=",
#wylaczone - materialy dostepne w serwisach IPLA, TVPVOD
#   "Przegapiłes": "/missed?src_id=1885&object_id=-1&offset=-1&dayoffset=-1&rec_count=" + str(PAGE_MOVIES),
#   "Najcześciej oglądane": "/videolisting?src_id=1885&object_id=929547&object_type=video&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
#   "Makłowicz w podróży": MAINURL + "/videolisting?object_id=1364&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
#   "Kraków - najczęściej oglądane": MAINURL + "/videolisting?src_id=1885&object_id=929711&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
#   "Kabarety": MAINURL + "/videolisting?object_id=883&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
#   "Sport teraz oglądane": MAINURL + "/videolisting?object_id=928060&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
#   "Sport najwyżej oceniane": MAINURL + "/videolisting?object_id=928062&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
#   "Sport najczęściej oglądane": MAINURL + "/videolisting?object_id=928059&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
#   "Kultura teraz oglądane": MAINURL + "/listing?src_id=2&object_id=929222&object_type=video&child_mode=SIMPLE&list_mode=CURRENT&play_mode=VOD%3ALIVE&rec_count=" + str(PAGE_MOVIES),
#   "Kultura najwyżej oceniane": MAINURL + "/listing?src_id=2&object_id=929223&object_type=video&child_mode=SIMPLE&list_mode=VOTES&play_mode=VOD&rec_count=" + str(PAGE_MOVIES),
#   "Kultura najczęściej oglądane": MAINURL + "/listing?src_id=2&object_id=929221&object_type=video&child_mode=SIMPLE&list_mode=TOPLIST&play_mode=VOD&rec_count=" + str(PAGE_MOVIES),
#   "Rozrywka teraz oglądane": MAINURL + "/listing?src_id=2&object_id=929212&object_type=video&child_mode=SIMPLE&list_mode=CURRENT&play_mode=VOD%3ALIVE&rec_count=" + str(PAGE_MOVIES),
#   "Rozrywka najwyżej oceniane": MAINURL + "/listing?src_id=2&object_id=929213&object_type=video&child_mode=SIMPLE&list_mode=VOTES&play_mode=VOD&rec_count=" + str(PAGE_MOVIES),
#   "Rozrywka najczęściej oglądane": MAINURL + "/listing?src_id=2&object_id=929211&object_type=video&child_mode=SIMPLE&list_mode=TOPLIST&play_mode=VOD&rec_count=" + str(PAGE_MOVIES)
}

class tvp:
    def __init__(self):
	log.info('Loading ' + SERVICE)
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.cm = sdCommon.common()
        self.proxy = sdCommon.proxy()
	self.exception = sdErrors.Exception()
	self.gui = sdNavigation.sdGUI()

    def getVideoUrl(self, videoID):
        
            if proxy == 'true':
                try:
                    result = self.cm.getURLRequestData({ 'url': self.proxy.useProxy(TOKENIZER + videoID), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
                except Exception, exception:
                    traceback.print_exc()
                    self.exception.getError(str(exception))
                    exit()                
            else:
                try:
                    result = self.cm.getURLRequestData({ 'url': TOKENIZER + videoID, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
                except Exception, exception:
                    traceback.print_exc()
                    self.exception.getError(str(exception))
                    exit()
            
            videoTab = []
            data = _json.loads(result)
            if (isinstance(data['formats'],list)):
                for item in data['formats']:
                    if item['mimeType'] == 'unknown':
                        return item['url']
                    if item['mimeType'] in FORMATS.keys():
                        videoTab.append( {'bitrate': str(item['totalBitrate']), 'url' : item['url'].encode('utf-8') })
                videoTab.sort(key = lambda x: int(x['bitrate']), reverse=True)
                videoUrl = videoTab[0]['url']
            
                if videoQuality == 'Niska': videoUrl = videoTab[-1]['url']
                if videoQuality == 'Wysoka': videoUrl = videoTab[0]['url']
                if videoQuality == 'Średnia':
                    length = len(videoTab)            
                    i = int(math.ceil(float(length/2)))
                    videoUrl = videoTab[i]['url']
            else:
                videoUrl =  data['formats']['url']

	    if proxy == 'true':
		try:
		    data = self.cm.getURLRequestData({ 'url': self.proxy.useProxy(videoUrl), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
		except Exception, exception:
		    traceback.print_exc()
		    self.exception.getError(str(exception))
		    exit() 
		videoUrl = data
	    
	    return videoUrl
		

    def listsCategories(self, table):
	for num, val in table.items():
	    params = {'service': SERVICE, 'name': 'video', 'category': val, 'title': num, 'icon': LOGOURL}
	    self.gui.addDir(params)
	self.gui.endDir(True)

    def getVideoList(self, url, page):
	description = ''
	time = 0
	aired = ''
	episode = 0
        
        if self.cm.isNumeric(url):
            url = MAINURL + API + '&object_id=' + str(url) + '&rec_count=' + str(PAGE_MOVIES)
	else:
            url = MAINURL + url + str(PAGE_MOVIES)
            
        paginationUrl = ''
	if page > 0:
	    paginationUrl = "&start_rec=" + str(page * PAGE_MOVIES)
	query_data = { 'url': url+paginationUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
	try:
	    data = self.cm.getURLRequestData(query_data)
	except Exception, exception:
	    traceback.print_exc()
	    self.exception.getError(str(exception))
	    exit()

	elems = ET.fromstring(data)
	epgItems = elems.findall("directory_video/video")

        if not epgItems:
	    epgItems = elems.findall("directory_stats/video")
	if not epgItems:
	    epgItems = elems.findall("directory_standard/video")
	listsize = len(epgItems)
        
	for epgItem in epgItems:
	    title =  epgItem.find("title").text.encode('utf-8')
            videoID = epgItem.attrib['video_id']

	    if epgItem.attrib['release_date']:
		aired = epgItem.attrib['release_date']
	    if epgItem.get('episode_number'):
		episode = epgItem.attrib['episode_number']
	    textNode = epgItem.find('text_paragraph_standard/text')
	    if ET.iselement(textNode):
		description = textNode.text.encode('utf-8').replace("<BR/>", "")
	    iconUrl = ''
	    iconFileNode = epgItem.find('video/image')
	    if not iconFileNode:
		iconFileNode = epgItem.find('image')
	    if iconFileNode:
		iconFileName = iconFileNode.attrib['file_name']
		iconFileName = iconFileName.split('.')
		iconUrl = 'http://s.v3.tvp.pl/images/6/2/4/uid_%s_width_700.jpg' % iconFileName[0]

	    params = {'service': SERVICE, 'dstpath': dstpath, 'title': title, 'page': videoID, 'icon': iconUrl, "plot": description, "duration": str(time/60), "premiered": aired, "episode": int(episode)}
	    self.gui.playVideo(params)

	if listsize == PAGE_MOVIES:
	    params = {'service': SERVICE, 'name': 'video', 'category': url, 'title': 'Następna strona', 'page': str(page+1), 'icon': THUMB_NEXT}
	    self.gui.addDir(params)

	self.gui.endDir(False, 'episodes')


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

	if page == None: page = '0'

	if name == None:
	    self.listsCategories(CATEGORIES)
	elif name == 'video':
	    self.getVideoList(category, int(page))
	elif name == 'playSelectedVideo':
            videoUrl = self.getVideoUrl(page)
	    self.gui.LOAD_AND_PLAY_VIDEO(videoUrl, title)    
