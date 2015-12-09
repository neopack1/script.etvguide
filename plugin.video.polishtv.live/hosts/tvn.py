# -*- coding: utf-8 -*-

#NOTES:
# - pomija ULUBIONE i KONTYNUUJ,
# - uzywa settings: quality i proxy


import os, sys, time
import xbmcaddon, xbmcgui
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

from hashlib import sha1
import crypto.cipher.aes_cbc
import crypto.cipher.base, base64
import binascii

scriptID = 'plugin.video.polishtv.live'
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()

SERVICE = 'tvn'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'

platform = {
    'Samsung': {
        'platform' : 'ConnectedTV',
        'terminal' : 'Samsung',
        'authKey' : 'ba786b315508f0920eca1c34d65534cd',
        'host' : 'Mozilla/5.0 (SmartHub; SMART-TV; U; Linux/SmartTV; Maple2012) AppleWebKit/534.7 (KHTML, like Gecko) SmartTV Safari/534.7'
    },
    'Android': {
        'platform' : 'Mobile',
        'terminal' : 'Android',
        'authKey' : 'b4bc971840de63d105b3166403aa1bea',
        'host' : 'Apache-HttpClient/UNAVAILABLE (java 1.4)'
    }         
}

qualities = [
            'HD',
            'Bardzo wysoka',
            'Wysoka',
            'Standard',
            'Średnia'
            'Niska',
            'Bardzo niska'
            ]

tvn_proxy = ptv.getSetting('tvn_proxy')
tvn_quality = ptv.getSetting('tvn_quality')
tvn_sort = ptv.getSetting('tvn_sort')
tvn_platform = ptv.getSetting('tvn_platform')

tvn_url_keys = ("service","id","seriesId","category")

MAINURL =  'https://api.tvnplayer.pl'
IMAGEURL = 'http://dcs-193-111-38-250.atmcdn.pl/scale/o2/tvn/web-content/m/'
APIURL = MAINURL + '/api/?platform=%s&terminal=%s&format=json&v=3.0&authKey=%s&' % (platform[tvn_platform]['platform'], platform[tvn_platform]['terminal'], platform[tvn_platform]['authKey'])
HOST = platform[tvn_platform]['host']

class tvn:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()
        self.api = API()
    
    
    def getMenu(self, args):
        data = self.api.getAPI(args)
        for item in data['categories']:
            #pomin ULUBIONE i KONTYNUUJ
            if item['type'] != 'favorites' and  item['type'] != 'pauses':                
                if item['thumbnail'] != None:
                    icon =self.api.getImage(item['thumbnail'][0]['url'])
                else:
                    icon = THUMB_SERVICE
                params = {'service': SERVICE, 'category': item['type'], 'id': item['id'], 'title': item['name'].encode('UTF-8'), 'icon': icon}
                self.gui.addDir(params, params_keys_needed = tvn_url_keys)
        self.gui.endDir()
        
        
    def getItems(self, args):
        sort = True
        data = self.api.getAPI(args)

        if (not 'seasons' in data) or (len(data['seasons']) == 0) or ('season=' in args): #bez sezonow albo odcinki w sezonie
            for item in data['items']:
                try:
                    icon =self.api.getImage(item['thumbnail'][0]['url'])
                except Exception, exception:
                    icon = THUMB_SERVICE
                    
                title = item['title'].encode('UTF-8')
   
                if item['type'] == 'episode':
                    sort = False
                    if item['season'] != 0 and item['season'] != None:
                        title = title + ', sezon ' + str(item['season'])
                    if item['episode'] != 0 and item['episode'] != None:
                        title = title + ', odcinek ' + str(item['episode'])

                    #'preview_catchup' or 'preview_prepremier'
                    if ('preview_' in item['type_episode']):
                        title = title + ' [COLOR FFFF0000](' + item['start_date'].encode('UTF-8') + ')[/COLOR]'

                if item['type'] == 'series':
                    #tu wsadzic wlaczanie/wylaczanie sortowania
                    if tvn_sort == "Alfabetycznie": sort = True
                    else: sort = False
                    
                    if item['season'] != 0 and item['season'] != None:
                        title = title + ', sezon ' + str(item['season'])

                subtitle = item.get('sub_title', None)
                if subtitle != None and len(subtitle) > 0:
                    title = title + ' - ' + subtitle.encode('UTF-8')
                    
                params = {'service': SERVICE, 'category': item['type'], 'id': item['id'], 'title': title.strip(), 'icon': icon, 'fanart': icon}

                duration = item.get('end_credits_start', None) # Czas trwania to |end_credits_start| lub |run_time|
                if duration != None and len(duration) == 8:    #format 00:23:34
                    l = duration.split(':')
                    min = int(l[0])*60 + int(l[1]) + 1 
                    params.update({'duration': str(min)})

                rating = item.get('rating', None)
                if rating != None and len(rating) > 0:
                    if rating != '0' :
                        params.update({'mpaa': 'Od '+rating+ ' lat'})
                    else:
                        params.update({'mpaa': 'Bez ograniczeń'})

                plot = item.get('lead', None)
                if plot != None:
                    params.update({'plot': plot.replace('&quot;', '"').encode('UTF-8')})
                if item['type'] == 'episode':
                    self.gui.playVideo(params,isPlayable = True,params_keys_needed = tvn_url_keys)
                else:
                    self.gui.addDir(params, params_keys_needed = tvn_url_keys)
        else: #listuj sezony
            for item in data['seasons']:
                if item['thumbnail'] != None:
                    icon =self.api.getImage(item['thumbnail'][0]['url'])
                else:
                    icon = THUMB_SERVICE
                t = data['items'][0]['title'].encode('UTF-8')
                params = {'service': SERVICE, 'category': item['type'], 'id': item['id'], 'title': t + ' - ' + item['name'].encode('UTF-8'), 'icon': icon, 'fanart': icon, 'seriesId': item['vdp_id']}
                self.gui.addDir(params, params_keys_needed = tvn_url_keys)
        self.gui.endDir(sort)
    
    
    def getVideoUrl(self, args):
        ret = ''
        
        if tvn_proxy == 'true':
            useProxy = True
        else:
            useProxy = False
    
        data = self.api.getAPI(args, useProxy)
        
        #znajdz jakosc z settings wtyczki      
        if data['item']['videos']['main']['video_content'] != None and len(data['item']['videos']['main']['video_content']) != 0:
            url = ''
            for item in data['item']['videos']['main']['video_content']:
                if item['profile_name'].encode('UTF-8') == tvn_quality:
                    url = item['url'] #znalazlem wybrana jakosc
                    break;
            #jesli jakosc nie znaleziona (lub Maksymalna) znajdz pierwsza najwyzsza jakosc
            if url == '':
                for q in qualities:
                    for item in data['item']['videos']['main']['video_content']:
                        if item['profile_name'].encode('UTF-8') == q:
                            url = item['url']
                            break
                    if url != '':
                        break
            
            #dodaj token tylko do Androida
            if tvn_platform == 'Android':
                ret = self.api.generateToken(url).encode('UTF-8')
            else:
                query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
                try:
                    ret = self.common.getURLRequestData(query_data)
                except Exception, exception:
                    traceback.print_exc()
                    self.exception.getError(str(exception))
                    exit()                        
        return ret
    
    
    def handleService(self):
        params = self.parser.getParams()
        category = str(self.parser.getParam(params, "category"))
        id = str(self.parser.getParam(params, "id"))
        seriesId = str(self.parser.getParam(params, "seriesId"))

        #MAINMENU
        if category == 'None':
            if self.api.geoCheck():
                self.getMenu('m=mainInfo')
        
        #WSZYSTKO
        if category != 'None' and category != 'episode' and seriesId == 'None':
            self.getItems('m=getItems&sort=newest&limit=500&type=' + category + '&id=' + id)
        
        #ODCINKI W SEZONIE
        if seriesId != 'None':
            self.getItems('m=getItems&sort=newest&limit=500&type=series&id=' + seriesId + '&season=' + id)
        
        #VIDEO
        if category == 'episode':
            videoUrl = self.getVideoUrl('m=getItem&type=' + category + '&id=' + id)
            self.gui.LOAD_AND_PLAY_VIDEO_WATCHED(videoUrl)
            
            
class API:
    def __init__(self):
        self.exception = sdErrors.Exception()
        self.common = sdCommon.common()
        self.proxy = sdCommon.proxy()
    
    
    def geoCheck(self):
        ret = True
        if tvn_proxy != 'true':
            data = self.getAPI('m=checkClientIp', False)
            if data['result'] == False:
                d = xbmcgui.Dialog()
                d.ok(SERVICE, 'Serwis niedostepny na terenie twojego kraju.', 'Odwiedz sd-xbmc.org w celu uzyskania dostepu.')
            ret = data['result']
        return ret


    def getAPI(self, args, useProxy = False):
        if useProxy:
            url = self.proxy.useProxy(APIURL + args)
        else:
            url = APIURL + args
            
        query_data = {'url': url, 'use_host': True, 'host': HOST, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.common.getURLRequestData(query_data)
            if (useProxy and self.proxy.isAuthorized(data)) or useProxy == False:
                result = _json.loads(data)
                if not 'status' in result or result['status'] != 'success':
                    d = xbmcgui.Dialog()
                    d.ok(SERVICE, 'Blad API', '')
                    exit()
                return result
            else:
                exit()

        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
            
    
    def getImage(self, path):
        return IMAGEURL + path + '?quality=85&dstw=870&dsth=560&type=1'


    def generateToken(self, url):
        url = url.replace('http://redir.atmcdn.pl/http/','')
        SecretKey = 'AB9843DSAIUDHW87Y3874Q903409QEWA'
        iv = 'ab5ef983454a21bd'
        KeyStr = '0f12f35aa0c542e45926c43a39ee2a7b38ec2f26975c00a30e1292f7e137e120e5ae9d1cfe10dd682834e3754efc1733'
        salt = sha1()
        salt.update(os.urandom(16))
        salt = salt.hexdigest()[:32]

        tvncrypt = crypto.cipher.aes_cbc.AES_CBC(SecretKey, padding=crypto.cipher.base.noPadding(), keySize=32)
        key = tvncrypt.decrypt(binascii.unhexlify(KeyStr), iv=iv)[:32]

        expire = 3600000L + long(time.time()*1000) - 946684800000L

        unencryptedToken = "name=%s&expire=%s\0" % (url, expire)

        pkcs5_pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
        pkcs5_unpad = lambda s : s[0:-ord(s[-1])]

        unencryptedToken = pkcs5_pad(unencryptedToken)

        tvncrypt = crypto.cipher.aes_cbc.AES_CBC(binascii.unhexlify(key), padding=crypto.cipher.base.noPadding(), keySize=16)
        encryptedToken = tvncrypt.encrypt(unencryptedToken, iv=binascii.unhexlify(salt))
        encryptedTokenHEX = binascii.hexlify(encryptedToken).upper()

        return "http://redir.atmcdn.pl/http/%s?salt=%s&token=%s" % (url, salt, encryptedTokenHEX)

