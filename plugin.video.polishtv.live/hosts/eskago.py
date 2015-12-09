# -*- coding: utf-8 -*-

#todo:
# - video format (HLS|mp4) setting,
# - check proxy authorization 

import os, sys
import xbmcaddon, xbmcgui
import traceback
from xml.dom.minidom import parseString, parse

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = 'plugin.video.polishtv.live'
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors, sdNavigation

log = sdLog.pLog()

SERVICE = 'eskago'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'
MAINURL =  'http://www.eskago.pl/indexajax.php?action=SamsungSmartTvV1&start=channelsGroups'
MAINURLVOD = 'http://www.eskago.pl/indexajax.php?action=MobileApi'

eskago_proxy = ptv.getSetting('eskago_proxy')

class eskago:
    def __init__(self):
        log.info('Loading ' + SERVICE)
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.common = sdCommon.common()
        self.proxy = sdCommon.proxy()  
        self.api = API()

        
        
    def getMenu(self):
        data = self.api.getAPI()
        for item in data['result']:
            params = {'service': SERVICE, 'id': item['id'], 'title': item['title'].encode('UTF-8'), 'icon': item['image']}
            self.gui.addDir(params)
        #add VOD 
        params = {'service': SERVICE, 'category': 'vod', 'title': 'VOD', 'icon': THUMB_SERVICE}
        self.gui.addDir(params)
        self.gui.endDir(True)
    
    
    def getChannels(self, id):
        data = self.api.getAPI()
        for item in data['result']:
            if str(item['id']) == id:
                for channel in item['channels']:
                    if 'streamUrls' in channel:
                        url = channel['streamUrls']['hd']
                    else:
                        url = channel['streamUrl']
                        
                    if channel['type'] == 'TV':
                        title = '[COLOR FF00FF00]'  + channel['name'].encode('UTF-8').replace('\r\n','') + '[/COLOR]'
                    else:
                        title = channel['name'].encode('UTF-8').replace('\r\n','')
                    
                    params = {'service': SERVICE, 'url': url, 'title': title, 'icon': item['image']}
                    self.gui.addDir(params)
        self.gui.endDir(True)


    def getChannelsVOD(self):
        if self.proxy.geoCheck() == False and eskago_proxy == 'false':
            d = xbmcgui.Dialog()
            d.ok(SERVICE, 'Serwis niedostepny na terenie twojego kraju.', 'Odwiedz sd-xbmc.org w celu uzyskania dostepu.')            
        
        data = self.api.getAPIVOD()
        for node in data.getElementsByTagName('Group'):
            params = {'service': SERVICE, 'category': 'vod', 'url': node.getElementsByTagName('itemsUrl')[0].firstChild.wholeText.encode('UTF-8'), 'title': node.getElementsByTagName('name')[0].firstChild.wholeText.encode('UTF-8'), 'icon': THUMB_SERVICE}
            self.gui.addDir(params)
        self.gui.endDir(True)
        
        
    def getVODList(self, url):
        data = self.api.getAPIVOD(url.replace('[OFFSET]','0').replace('[LIMIT]','100'))
        for node in data.getElementsByTagName('Movie'):
           params = {'service': SERVICE, 'category': 'vod', 'id': node.getElementsByTagName('id')[0].firstChild.wholeText, 'title': node.getElementsByTagName('name')[0].firstChild.wholeText.encode('UTF-8'), 'icon': node.getElementsByTagName('cover')[0].firstChild.wholeText.replace('[WIDTH]','260')}
           self.gui.addDir(params)
        self.gui.endDir(True)
        
    def getVODDetails(self, id):
        if eskago_proxy == 'true':
            useProxy = True
        else:
            useProxy = False
        data = self.api.getAPIVOD('http://www.eskago.pl/indexajax.php?action=MobileApi&start=movie&id=' + id, useProxy)
        for node in data.getElementsByTagName('Stream'):
            return node.getElementsByTagName('url')[0].firstChild.wholeText
        return ''
    
    def handleService(self):
        params = self.parser.getParams()
        title = str(self.parser.getParam(params, "title"))
        id = str(self.parser.getParam(params, "id"))
        url = str(self.parser.getParam(params, "url"))
        category = str(self.parser.getParam(params, "category"))
        
        #MAINMENU
        if id == 'None' and url == 'None' and category == 'None':
            self.getMenu()
        
        #KANALY
        if id != 'None' and url == 'None' and category == 'None':
            self.getChannels(id)
        
        #KANALY VOD
        if category == 'vod' and url == 'None' and id == 'None':
            self.getChannelsVOD()
            
        #KATEGORIA VOD
        if category == 'vod' and url != 'None':
            self.getVODList(url)
            
        #PLAY
        if (category == 'vod' and id != 'None') or (category == 'None' and url != 'None'):
            if id != 'None':
                url = self.getVODDetails(id)
            self.common.LOAD_AND_PLAY_VIDEO(url, title)

			
			
class API:
    def __init__(self):
        self.exception = sdErrors.Exception()
        self.common = sdCommon.common()
        self.proxy = sdCommon.proxy()    
    
        
    def getAPIVOD(self, url = MAINURLVOD + '&start=vodCategories&type=movies', useProxy = False):
        if useProxy:
            url = self.proxy.useProxy(url)
        query_data = {'url': url, 'use_host': False, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.common.getURLRequestData(query_data)
            result = parseString(data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        return result
    
    
    def getAPI(self):
        query_data = {'url': MAINURL, 'use_host': False, 'use_header': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.common.getURLRequestData(query_data)
            result = _json.loads(data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        return result

