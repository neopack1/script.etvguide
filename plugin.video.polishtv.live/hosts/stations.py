# -*- coding: utf-8 -*-
import sys, os
import xbmcaddon

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json 

scriptID = 'plugin.video.polishtv.live'
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join(ptv.getAddonInfo('path'), "../resources")
sys.path.append(os.path.join(BASE_RESOURCE_PATH, "lib"))
IMAGE_URL = 'http://sd-xbmc.org/repository/xbmc-addons/'
SERVICE_URL = 'http://sd-xbmc.org/support/stations/'

import sdLog, sdSettings, sdParser, sdServiceInfo, sdNavigation, sdCommon

log = sdLog.pLog()


class StreamStations:
    def __init__(self):
        self.parser = sdParser.Parser()
        self.gui = sdNavigation.sdGUI()
        self.cm = sdCommon.common()

        
    def setCategoriesMenu(self):
        result = self.cm.getURLRequestData({ 'url': SERVICE_URL + 'tv_categories.json', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })     
        result = _json.loads(result)

        for item in result:
            self.gui.addDir({'service': 'stations', 'name': str(item['id']), 'title': item['name'].encode('UTF-8'), 'icon': IMAGE_URL + item['icon']})
        self.gui.endDir()


    def setStations(self, categoryID):
        result = self.cm.getURLRequestData({ 'url': SERVICE_URL + 'tv_stations.json', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })     
        result = _json.loads(result)

        for item in result:
            if str(item['category']) == categoryID and item['active']:
                self.gui.addDir({'service': 'stations', 'name': 'playSelectedVideo', 'title': item['name'].encode('UTF-8'), 'description': item['desc'].encode('UTF-8'), 'url': item['stream'] + ' live=true', 'icon': IMAGE_URL + 'tv/' + item['desc'].encode('UTF-8') + '.png'})
        self.gui.endDir()


    def handleService(self):
        params = self.parser.getParams()
        name = str(self.parser.getParam(params, "name"))
        title = str(self.parser.getParam(params, "title"))
        url = str(self.parser.getParam(params, "url"))

        if name == 'None':
            self.setCategoriesMenu()
        elif name == 'playSelectedVideo':
            self.cm.LOAD_AND_PLAY_VIDEO(url, title)
        else:
            self.setStations(name)
