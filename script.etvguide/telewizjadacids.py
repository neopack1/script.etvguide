#      Copyright (C) 2014 Krzysztof Cebulski

import urllib, urllib2, httplib, sys, StringIO, cookielib, copy, re
from xml.etree import ElementTree
import simplejson as json #import json
import xbmc
import time
import os, xbmcaddon
from strings import *
import ConfigParser
import weebtvcids

telewizjadaMainUrl = 'http://www.telewizjada.net/'
COOKIE_FILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')) , 'telewizjada.cookie')

HOST       = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0'
#rstrm      = '%s'  #pobierany przepis z xml-a np.: 'service=weebtv&cid=%s'
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')

telewizjadaChannelList = None

class TelewizjaDaUpdater: 
    def __init__(self):
        self.sl = weebtvcids.ShowList()
        self.sl.setLoginData('', '')
        
    def loadChannelList(self):
        try:
            self.channels = self.getChannelList()
            pathMap = os.path.join(pathMapBase, 'telewizjadamap.xml')
            mapfile = weebtvcids.MapString.loadFile(pathMap)
            self.automap = weebtvcids.MapString.Parse(mapfile)

            deb('\n[UPD] Wyszykiwanie STRM')
            deb('-------------------------------------------------------------------------------------')
            deb('[UPD] %-30s %-30s %-20s %-35s' % ('-ID mTvGuide-', '-    Orig Name    -', '-    SRC   -', '-    STRM   -'))
            for x in self.automap:
                if x.strm != '':
                    x.src = 'CONST'  
                    deb('[UPD] %-30s %-15s %-35s' % (x.channelid, x.src, x.strm))
                    continue
                try:
                    error=""
                    p = re.compile(x.titleRegex, re.IGNORECASE)
                    for y in self.channels:
                        b=p.match(y.title)
                        if (b):
                            x.strm = weebtvcids.rstrm % y.cid
                            x.src  = 'telewizjada.net'
                            y.strm = x.strm
                            y.src = x.src
                            deb('[UPD] %-30s %-30s %-20s %-35s ' % (x.channelid, y.name, x.src, x.strm))
                except Exception, ex:
                    print '%s Error %s %s' % (x.channelid, x.titleRegex, str(ex))
            deb ('\n[UPD] Nie znaleziono/wykorzystano odpowiedników w telewizjada.net dla:')
            deb('-------------------------------------------------------------------------------------')
            for x in self.automap:
                if x.src!='telewizjada.net':
                    deb('[UPD] CH=%-30s SRC=%-15s STRM=%-35s' % (x.channelid, x.src, x.strm))
                    
            deb ('\n[UPD] Nie wykorzystano STRM nadawanych przez telewizjada.net programów:')
            deb('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != 'telewizjada.net':
                    deb ('[UPD] CID=%-10s NAME=%-40s STRM=%-45s' % (y.cid, y.name, str(y.strm)))

            deb("[UPD] Zakończono analizę...")
            
        except Exception, ex:
            print 'TelewizjaDaUpdater loadChannelList Error %s' % str(ex)
            
    def getChannelList(self):
        try:
            global telewizjadaChannelList
            if telewizjadaChannelList is not None:
                deb('TelewizjaDaUpdater getChannelList return cached channel list')
                return copy.deepcopy(telewizjadaChannelList)
            
            deb('TelewizjaDaUpdater getChannelList downloading channel list')
            
            channelsArray = list()
            result = list()
            failedCounter = 0
            while failedCounter < 50:
                try:
                    channelsArray = self.sl.getJsonFromAPI(telewizjadaMainUrl + 'get_channels.php', '')
                    break
                except httplib.IncompleteRead:
                    failedCounter = failedCounter + 1
                    time.sleep(.300)
                
            if len(channelsArray) > 0:
                
                for x in range(0, len(channelsArray['channels'])):
                    chann = self.sl.decode(channelsArray['channels'][x])
                    args = chann.split(",")
                    url = ''
                    ID = ''
                    img = ''
                    displayName = ''
                    description = ''
                    
                    for index in range(0, len(args)): 
                        arg = args[index].split(":")
                        if "id" in arg[0]:
                            ID = arg[1].replace('"', '').strip()
                        if "displayName" in arg[0]:
                            displayName = arg[1].replace('"', '').strip()
                        if "url" in arg[0]:
                            url = arg[1].replace('"', '').strip()
                        if "thumb" in arg[0]:
                            img = telewizjadaMainUrl + arg[1].replace('"', '').strip()
                        if "description" in arg[0]:
                            description = arg[1].replace('"', '').strip()

                    result.append(weebtvcids.WeebTvCid(ID, displayName, displayName, '2', url, img))                    
                telewizjadaChannelList = copy.deepcopy(result)
            
            return result

        except Exception, ex:
            print 'TelewizjaDaUpdater getChannelList Error %s' % str(ex)
            
    def getChannelUrl(self, cid):
        try:
            for chann in telewizjadaChannelList:
                if chann.cid == cid:
                    tmp_url = ''
                    failedCounter = 0
                    data = { 'url': chann.strm}
                    while failedCounter < 50:
                        try:
                            self.sl.getJsonFromExtendedAPI(telewizjadaMainUrl + 'set_cookie.php', post_data = data, cookieFile = COOKIE_FILE, save_cookie = True)
                            break
                        except:
                            failedCounter = failedCounter + 1
                            time.sleep(.100)

                    data = { 'cid': cid }
                    failedCounter = 0
                    while failedCounter < 50:
                        try:
                            tmp_url = self.sl.getJsonFromExtendedAPI(telewizjadaMainUrl + 'get_channel_url.php', post_data = data, cookieFile = COOKIE_FILE, load_cookie = True)
                            break
                        except:
                            failedCounter = failedCounter + 1
                            time.sleep(.100)

                    msec = self.sl.getCookieItem(COOKIE_FILE, 'msec')
                    sessid = self.sl.getCookieItem(COOKIE_FILE, 'sessid')
                    
                    final_url = tmp_url + '|Cookie='+ urllib.quote_plus('msec=' + msec + '; sessid=' + sessid )
                    return final_url
            
        except Exception, ex:
            print 'TelewizjaDaUpdater getChannelUrl Error %s' % str(ex)