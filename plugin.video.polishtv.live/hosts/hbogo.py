# -*- coding: utf-8 -*-
import urllib, urllib2, sys, re, os
import xbmcgui, xbmc, xbmcplugin, xbmcaddon
import xml.etree.ElementTree as ET 
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

import sdLog, sdSettings, sdParser, sdNavigation, sdCommon, sdErrors, smth

log = sdLog.sdLog()
HANDLE = int(sys.argv[1])

scriptID = 'plugin.video.polishtv.live'
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

SERVICE = 'hbogo'
userAgent = 'Apache-HttpClient/UNAVAILABLE (java 1.4)'
TMP = os.path.join( ptv.getAddonInfo('path'), "smth" )

token_free = 'n%2FFQqeAY5JVOLVPRtWovoMTW6Psuzc81MppqxE7hrLM4jsN2efvHl5HQb2zSnHyHmcabf24c1xumMfpD1h2d25vV%2B7c5g8SWOzgLmHfolVCjK4bjRFtE%2F0ukfYs5GnACOrVii17LrtWStDtDHGaVScDN4zBWO078XGXHXuf%2FCvc%3D'
operatorId = '806f7409-ca46-4525-a48c-91269f53b952'

COOKIEFILE = ptv.getAddonInfo('path') + os.path.sep + "cookies" + os.path.sep + "hbogo.cookie"

webUrl = 'http://www.hbogo.pl'
plapiUrl = 'http://plapi.hbogo.eu'
ploriginUrl = 'http://plorigin.hbogo.eu'
drmUrl = 'http://sl.licensekeyserver.com'
configUrl = plapiUrl + '/Player26.svc/Configuration/JSON/POL/TABL'
categoryPlayer = '/Player26.svc/Category/JSON/POL/'
mediaPlayer = '/Player26.svc/Media/JSON/POL/'
emptyMediaIdPlayer = '/00000000-0000-0000-0000-000000000000/TABL'
lgBaseUrl = webUrl + '/lg'
lgGetUrl = webUrl + '/tvservice/services/GetMediaUrl.aspx'
lgFreePurchase = webUrl + '/tvservice/services/FreePurchase.aspx'
lgLicenseUrl = webUrl +'/tvservice/services/License.aspx'

HEADER = { 'Accept-Language': 'pl, en;q=0.8', 'User-Agent': 'Mozilla/5.0 (DirectFB; Linux armv7l) AppleWebKit/534.26+ (KHTML, like Gecko) Version/5.0 Safari/534.26+ LG Browser/5.00.00(+mouse+3D+SCREEN+TUNER; LGE; 55LM670S-ZA; 04.40.19; 0x00000001;); LG NetCast.TV-2012', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate', 'Cookie': 'HBOApplicationLanguage=POL; HBOApplicationCustomerId=e3af6cc4-c2f5-4c4c-b512-4a9c9c1e300f' }

dstpath = ptv.getSetting('default_dstpath')
dbg = ptv.getSetting('default_debug')


class Movies:
    def __init__(self):
        self.common = sdCommon.common()
        self.chars = sdCommon.Chars()
        self.manifest_path = os.path.join(TMP, 'manifest')
        self.exception = sdErrors.Exception()
        self.sm = smth.Manifest()

    def enc(self, string):
        json_ustr = _json.dumps(string, ensure_ascii=False)
        return json_ustr.encode('utf-8')
    
    def dec(self, json):
        string = self.enc('u\'' + json + '\'').replace("\"", "").replace("u'", "").replace("'", "")
        return string 
        
    def getStatus(self, url):
        status = True
        query_data = { 'url': url, 'use_host': True, 'host': userAgent, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        if response.strip() != 'OK':
            status = False
        if dbg == 'true':
           log.info("HBOGO - getStatus() -> response: " + str(response.strip()))
           log.info("HBOGO - getStatus() -> status: " + str(status))
        return status

    def getLGCookie(self, url):
        status = False
        query_data = {'url': url, 'use_host': False, 'use_header': True, 'header': HEADER, 'use_cookie': True, 'load_cookie': False, 'save_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True}
        #query_data  = { 'url': url, 'use_host': True, 'host': userAgent, 'use_cookie': True,  'load_cookie': False, 'save_cookie': True, 'cookiefile': COOKIEFILE, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
        if response != None:
            status = True
        return status
    
    def hbogoAPI(self, url, method = 'get', cookie = False, return_data = True):
        use_post = False
        json_data = {}
        if method == 'post':
            use_post = True
        query_data = { 'url': url, 'use_host': True, 'host': userAgent, 'use_cookie': cookie, 'use_post': use_post, 'return_data': return_data }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            response = None
        if response != None:
            json_data = _json.loads(response)
        return json_data

    def listCategories(self, url):
        api = self.hbogoAPI(url)
        categories = api['Categories']
        for i in range(len(categories)):
            img = self.dec(categories[i]['NormalIconUrl'])
            title = self.dec(categories[i]['Name'])
            id = self.dec(categories[i]['Id'])
            n_url = plapiUrl + categoryPlayer + id + emptyMediaIdPlayer
            if dbg == 'true':
                log.info("HBOGO - listCategories() -> title: " + str(title))
                log.info("HBOGO - listCategories() -> img link: " + img)
                log.info("HBOGO - listCategories() -> url: " + n_url)
            self.addDir(SERVICE, 'categories', title, img, '', n_url)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def listContent(self, url):
        api = self.hbogoAPI(url)
        items = api['Collections'][0]['MediaItems']
        for i in range(len(items)):
            desc = self.dec(items[i]['Abstract'])
            img = self.dec(items[i]['ThumbnailUrl'])
            title = self.dec(items[i]['Name'])
            id = self.dec(items[i]['Id'])
            materialId = self.dec(items[i]['MaterialId'])
            materialItemId = self.dec(items[i]['MaterialItemId'])
            origTitle = self.dec(items[i]['OriginalName'])
            content = items[i]['ContentType']
            n_url = plapiUrl + mediaPlayer + id + '/' + materialId + '/' + materialItemId + '/TABL'
            if dbg == 'true':
                log.info("HBOGO - listSeasons() -> title: " + str(title))
                log.info("HBOGO - listSeasons() -> img link: " + img)
                log.info("HBOGO - listSeasons() -> url: " + n_url)
                log.info("HBOGO - listSeasons() -> content: " + str(content))
            if content == 1:
                self.addDir(SERVICE, 'movie', title, img, desc, n_url)
            elif content == 2:
                self.addDir(SERVICE, 'episode', title, img, desc, n_url)
            elif content == 5:
                self.addDir(SERVICE, 'season', title, img, desc, n_url)
            #self.addDir(SERVICE, 'series', '', '', '', '')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def listEpisodes(self, url):
        api = self.hbogoAPI(url)
        items = api['Episodes']
        for i in range(len(items)):
            allowfreepreview = items[i]['AllowFreePreview'] #true
            allowplay = items[i]['AllowPlay'] #true
            allowFreePreview = items[i]['AllowFreePreview']
            episode = items[i]['EpisodeNumber']
            ispublic = items[i]['IsPublic']
            duration = items[i]['MovieDuration']
            desc = self.dec(items[i]['Abstract'])
            img = self.dec(items[i]['ThumbnailUrl'])
            title = self.dec(items[i]['Name'])
            id = self.dec(items[i]['Id'])
            materialId = self.dec(items[i]['MaterialId'])
            materialItemId = self.dec(items[i]['MaterialItemId'])
            origTitle = self.dec(items[i]['OriginalName'])
            content = items[i]['ContentType']
            n_url = plapiUrl + mediaPlayer + id + '/' + materialId + '/' + materialItemId + '/TABL'
            if allowFreePreview:
                title = '%s%s - %s%s' % ('[COLOR green]', title, 'darmowy', '[/COLOR]')
            if dbg == 'true':
                log.info("HBOGO - listEpisodes() -> title: " + str(title))
                log.info("HBOGO - listEpisodes() -> img link: " + img)
                log.info("HBOGO - listEpisodes() -> url: " + n_url)
                log.info("HBOGO - listEpisodes() -> content: " + str(content))
                log.info("HBOGO - listEpisodes() -> freePreview: " + str(allowFreePreview))
            if content == 3:
                self.addDir(SERVICE, 'info-movie', title, img, desc, n_url)
            #self.addDir(SERVICE, 'series', '', '', '', '')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def infoMovie(self, url):
        api = self.hbogoAPI(url)
        audio = api['AudioTracks']
        desc = self.dec(api['Description'])
        ispublic = api['IsPublic']
        duration = api['Duration']
        id = api['Id']
        materialId = api['MaterialId']
        materialItemId = api['MaterialItemId']
        name = self.dec(api['Name'])
        #operatorId = api['OperatorId']
        #customerId = api['customerId']
        img = api['ThumbnailUrl']
        background = api['BackgroundUrl']
        hasTrailer = api['HasTrailer']
        allowFreePreview = api['AllowFreePreview']
        n_url = ploriginUrl + '//' + id + '/' + self.getIdFromURL(background) + '/MOBI/Movie/mux.ism/Manifest'
        if dbg == 'true':
            log.info("HBOGO - infoMovie() -> n_url[0]: " + str(n_url))
        if allowFreePreview:
            n_url = self.getMovieUrl({ 'allowfreepreview': allowFreePreview, 'machineId': '00-11-22-33-44-55', 'systemType': 'lg',  'mediaId': id, 'materialId': materialId, 'materialItemId': materialItemId, 'customerId': operatorId, 'operatorId': operatorId, 'credit': '0', 'creditRoleId': '00000000-0000-0000-0000-000000000000' })
        if dbg == 'true':
            log.info("HBOGO - infoMovie() -> audio: " + str(audio))
            log.info("HBOGO - infoMovie() -> desc: " + desc)
            log.info("HBOGO - infoMovie() -> name: " + str(name))
            log.info("HBOGO - infoMovie() -> n_url: " + str(n_url))
            log.info("HBOGO - infoMovie() -> hasTrailer: " + str(hasTrailer))
            log.info("HBOGO - infoMovie() -> freePreview: " + str(allowFreePreview))
        self.addDir(SERVICE, 'playSelectedMovie', 'PLAY: ' + name, img, desc, n_url)
        if hasTrailer == True:
            t_url = self.getDataUrl({ 'mediaId': id, 'materialId': materialId, 'materialItemId': materialItemId, 'customerId': operatorId, 'operatorId': operatorId })
            #t_url = '%s/%s/%s/COTV/trailer/mux.wmv' % (ploriginUrl, id, self.getIdFromURL(background))
            if dbg == 'true':
                log.info("HBOGO - infoMovie() -> t_url: " + str(t_url))
            if t_url != None:
                self.addDir(SERVICE, 'playSelectedTrailer', 'PLAY: TRAILER', img, desc, t_url)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def getDataUrl(self, opts = {}):
        url = '%s?mediaId=%s&materialId=%s&materialItemId=%s&customerId=%s&operatorId=%s' % (lgGetUrl, opts['mediaId'], opts['materialId'], opts['materialItemId'], opts['customerId'], operatorId)
        query_data = { 'url': url, 'use_host': True, 'host': userAgent, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            response = None
        if dbg == 'true':
            log.info("HBOGO - getDataUrl() -> response: " + str(response))
        if response != None:
            match = re.compile('"Data":"(.+?)"').findall(response)
            if len(match) > 0:
                return match[0]

    def getMovieUrl(self, opts = {}):
        url = ''
        token = ''
        if opts['allowfreepreview']:
            token = token_free
            url = lgFreePurchase
        post_data = { 'token': token, 'machineId': opts['machineId'], 'systemType': opts['systemType'], 'mediaId': opts['mediaId'], 'materialItemId': opts['materialItemId'], 'credit': opts['credit'], 'creditRoleId': opts['creditRoleId'], 'customerId': opts['customerId'], 'operatorId': operatorId, 'language': 'POL', 'platform': 'COTV' }
        query_data = { 'url': url, 'use_host': True, 'host': userAgent, 'use_cookie': False, 'use_post': True, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data, post_data)
        except Exception, exception:
            traceback.print_exc()
            response = None
        if dbg == 'true':
            log.info("HBOGO - getMovieUrl() -> response: " + str(response))
        if response != None:
            match = re.compile('"Data":"(.+?)"').findall(response)
            if len(match) > 0:
                return match[0]

    def saveTmpManifest(self, response):
        self.common.checkDir(TMP)
        f = open(self.manifest_path, "w")
        f.write(response)
        f.close()

    def getIdFromURL(self, url):
        return url.split("/")[5]
    
    def addDir(self, service, type, title, img, desc, link):
        folder = True
        if type == 'playSelectedMovie':
            folder = False
        liz = xbmcgui.ListItem(title, iconImage = "DefaultFolder.png", thumbnailImage = img)
        liz.setProperty("IsPlayable", "false")
        liz.setInfo(type = "Video", infoLabels={ "Title": title,
                                                "Plot": desc })
                                                #"Studio": "WEEB.TV",
                                                #"Tagline": tags,
                                                #"Aired": user } )
        u = '%s?service=%s&type=%s&title=%s&icon=%s&url=%s' % (sys.argv[0], SERVICE, type, str(title), urllib.quote_plus(img), urllib.quote_plus(link))
        xbmcplugin.addDirectoryItem(HANDLE, url = u, listitem = liz, isFolder = folder)


class DRM:
    def __init__(self):
        self.sm = smth.Manifest()

    def getProtectionHeader(self, manifest):
        query_data = { 'url': manifest, 'use_host': True, 'host': userAgent, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            response = None
        if response != None:
            protection = self.sm.getProtectionHeader(manifest)
            prot_id = protection['systemId']
            prot_value = protection['value']


class HBOGO:
    def __init__(self):
        self.common = sdCommon.common()
        self.chars = sdCommon.Chars()
        self.movie = Movies()
        self.parser = sdParser.Parser()
        
    def handleService(self):
        self.common.checkDir(ptv.getAddonInfo('path') + os.path.sep + "cookies")
        
        params = self.parser.getParams()
        title = str(self.parser.getParam(params, "title"))
        name = self.parser.getParam(params, "name")
        type = self.parser.getParam(params, "type")
        service = self.parser.getParam(params, "service")
        image = self.parser.getParam(params, "image")
        #url = urllib.unquote_plus(self.parser.getParam(params, "url"))
        url = str(self.parser.getParam(params, "url"))
        #content = self.parser.getParam(params, "content")
        
        if dbg == 'true':
            log.info('HBOGO - handleService()[0] -> title: ' + str(title))
            log.info('HBOGO - handleService()[0] -> type: ' + str(type))
            log.info('HBOGO - handleService()[0] -> service: ' + str(service))
            log.info('HBOGO - handleService()[0] -> image: ' + str(image))
            log.info('HBOGO - handleService()[0] -> url: ' + str(url))
            log.info('HBOGO - handleService()[0] -> name: ' + str(name))
        
        if self.movie.getStatus(webUrl + '/servicestatus.aspx'):
            if dbg == 'true':
                log.info("HBOGO - handleService()[0] -> getStatus is TRUE")
            if name == None and type == None:
                self.movie.getLGCookie(lgBaseUrl)
                self.movie.listCategories(configUrl)
            elif title != 'None' and url.startswith("http://") and type == 'categories':
                self.movie.listContent(url)
            elif title != 'None' and url.startswith("http://") and type == 'season':
                self.movie.listEpisodes(url)
            elif title != 'None' and url.startswith("http://") and type == 'info-movie':
                self.movie.infoMovie(url)
            
        if type == 'playSelectedMovie' and url.startswith("http://"):
            self.movie.getMovieInformationAndPlay(url)
        elif type == 'playSelectedTrailer' and url.startswith("http://"):
            self.common.LOAD_AND_PLAY_VIDEO(url, title)
            
            
