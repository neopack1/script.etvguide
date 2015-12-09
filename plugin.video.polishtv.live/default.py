# -*- coding: utf-8 -*-
import sys, os, xbmcaddon, xbmcgui, StorageServer

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json 

ptv = xbmcaddon.Addon()
scriptID = ptv.getAddonInfo('id')
scriptname = ptv.getAddonInfo('name')
language = ptv.getLocalizedString
dbg = ptv.getSetting('default_debug') in ('true')

BASE_RESOURCE_PATH = os.path.join(ptv.getAddonInfo('path'), 'resources')
sys.path.append(os.path.join(BASE_RESOURCE_PATH, 'lib'))
sys.path.append(os.path.join(ptv.getAddonInfo('path'), 'hosts'))
IMAGE_URL = 'http://sd-xbmc.org/repository/xbmc-addons/'
SERVICE_URL = 'http://sd-xbmc.org/support/services/'

import sdLog, sdSettings, sdParser, sdServiceInfo, sdNavigation, sdCommon

log = sdLog.pLog()

MENU_TAB = {
        1: ['Telewizja', 'tv', True],
        2: ['Filmy, Seriale', 'vod', True],
        4: ['Rozrywka', 'rozrywka', True],
        5: ['Kultura/Nauka', 'kultura', True],
        3: ['Zarządzanie nagrywaniem/ściąganiem', 'record', True],
        21: ['Informacje o serwisach', 'info', False],
        20: ['Ustawienia', 'ustawienia', False]
}

class PolishLiveTV:
    def __init__(self):
	log.info('Starting: ' + scriptname + ', version: ' + ptv.getAddonInfo('version'))
	self.settings = sdSettings.TVSettings()
	self.parser = sdParser.Parser()
	self.gui = sdNavigation.sdGUI()
	self.cm = sdCommon.common()
	self.cache = StorageServer.StorageServer('SDXBMC1', 1)
	self.serviceObj = self.cache.cacheFunction(self.getServices)

    def showMainMenu(self):
	params = self.parser.getParams()
	mode = self.parser.getIntParam(params, 'mode')
	name = self.parser.getParam(params, 'name')
	service = self.parser.getParam(params, 'service')
	record = self.parser.getParam(params, 'record')
	self.parser.debugParams(params, dbg)

        if mode != None:
            details = self.getServiceDetails('id', mode)
        elif service != None:
            details = self.getServiceDetails('name', service)

	if mode == None and name == None and service == None:
	    log.info('Wyświetlam menu główne')
	    self.setMainMenu()

        elif mode in MENU_TAB and MENU_TAB[mode][2] == True:
            log.info('Wyświetlam kategorie: ' + MENU_TAB[mode][0])
            self.setMenuItems(MENU_TAB[mode][1])

	elif mode == 20:
	    log.info('Wyświetlam ' + MENU_TAB[mode][0])
	    self.settings.showSettings()
	elif mode == 21:
	    log.info('Wyświetlam ' + MENU_TAB[mode][0])
	    si = sdServiceInfo.ServiceInfo()
	    si.getWindow()

        elif (mode != None or service != None) and details != False:
	    vod = getattr(__import__(details['name']), details['init'])()
	    if record == 'True':
                vod.handleRecords()
            else:
                if not details['active']:
                    d = xbmcgui.Dialog()
                    res = d.yesno("Serwis nieczynny", "Serwis [B]" + self.cm.html_entity_decode(details['displayName']) + "[/B] jest oznaczony jako nieaktywny.\nCzy na pewno chcesz kontynuować?","","","Nie","Tak")
		    if res == 0:
		        exit()
	        vod.handleService()

    def setMainMenu(self):
        if ptv.getSetting('default_lite') == 'true':
            self.setMenuItems('core')
        else:
            for num, val in MENU_TAB.items():
                 params = {'mode': num, 'title': val[0], 'icon': IMAGE_URL + val[1] + '.png'}
                 self.gui.addDir(params, val[2])
            self.gui.endDir()
 
    def setMenuItems(self, serviceType):
        lite_list=[]
        for i in range(1,13):  
                lite_list.append(int(ptv.getSetting('lite_pos'+str(i))))
        for service in self.serviceObj['services']:
            try:
                if service['active']:
                    icon = IMAGE_URL + service['name'] + '.png'
                else:
                    icon = IMAGE_URL + 'no-entry.png'
            except:
                icon = 'DefaultVideoPlaylists.png'

            #lite or record or regular
            if (dbg):
                 service['active'] = True

            if  ((service['id'] in lite_list ) and service['active'] and serviceType == 'core') or \
                      (serviceType == 'record' and 'record' in service and service['record'] and service['active']) or \
                      (service['type'] == serviceType and service['active']):
                if serviceType == 'record' and 'record' in service:
                    record = True
                else:
                    record = False

                self.gui.addDir({'mode': service['id'], 'title': self.cm.html_entity_decode(service['displayName']), 'icon': icon, 'record': record})
        self.gui.endDir(True)

    def getServices(self):
	result = self.cm.getURLRequestData({'url': SERVICE_URL, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
        return _json.loads(result)

    def getServiceDetails(self, node, value):
        for service in self.serviceObj['services']:
            if service[node] == value:
                return service
        return False

init = PolishLiveTV()
init.showMainMenu()