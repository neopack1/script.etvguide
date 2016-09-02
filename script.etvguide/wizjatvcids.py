#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
from strings import *
from serviceLib import *

serviceName         = 'WizjaTV'
wizjaUrl            = 'http://wizja.tv/'
COOKIE_FILE         = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')) , 'wizjatv.cookie')
wizjatvChannelList  = None

class WizjaTVUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.serviceName        = serviceName
        self.serviceEnabled     = ADDON.getSetting('wizjatv_enabled')
        self.login              = ADDON.getSetting('wizjatv_username').strip()
        self.password           = ADDON.getSetting('wizjatv_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_wizjatv'))
        self.onlineMapFile      = 'http://epg.feenk.net/maps/wizjatvmap.xml'
        self.localMapFile       = 'wizjatvmap.xml'
        self.serviceRegex       = "service=" + self.serviceName + "&cid=%"
        self.rstrm              = self.serviceRegex + 's'
        self.url                = wizjaUrl
        self.maxAllowedStreams  = 1

    def getChannelList(self):
        global wizjatvChannelList
        if wizjatvChannelList is not None:
            return copy.deepcopy(wizjatvChannelList)

        result = list()
        self.log('\n\n')
        self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-IMG-'))

        try:
            post = {}
            post['login']='zaloguj'
            post['user_name'] = self.login
            post['user_password'] = self.password
            data = self.sl.getJsonFromExtendedAPI(self.url + 'users/index.php', post_data = post, cookieFile = COOKIE_FILE, save_cookie = True)
            if 'Zarejestruj nowe konto' in data or 'Brak premium' in data:
                xbmcgui.Dialog().ok(strings(SERVICE_ERROR),"\n" + strings(SERVICE_NO_PREMIUM) + ' ' + self.serviceName)
                return result
            data = self.sl.getJsonFromExtendedAPI(self.url, cookieFile = COOKIE_FILE, load_cookie = True) #, cookieFile = COOKIE_FILE, load_cookie = True
            data = self.sl.parseDOM(data, 'td')
            for i in data:
                try:
                    try:
                        res = [(self.sl.parseDOM(i, 'a', ret='href')[0], self.sl.parseDOM(i, 'img', ret='src')[0])]
                    except:
                        continue
                    img = (self.url + res[0][1]).encode('utf-8')
                    cid = (res[0][0].replace('watch.php?id=','')).encode('utf-8')
                    name = (res[0][1].replace('ch_logo/','').replace('.png','')).encode('utf-8').replace('_black', '')
                    self.log('[UPD] %-10s %-35s %-35s' % (cid, name, img))
                    program = TvCid(cid, name, name, img=img)
                    result.append(program)
                except Exception, e:
                    self.log('getChannelList exception while looping: %s' % str(e))

            if len(result) > 0:
                wizjatvChannelList = copy.deepcopy(result)

        except Exception, e:
            self.log('getChannelList exception: %s' % str(e))
        return result

    def getChannel(self, cid):
        try:
            channels = self.getChannelList()
            for chann in channels:
                if chann.cid == cid:
                    url = self.url + 'watch.php?id=%s' % cid
                    self.sl.getJsonFromExtendedAPI(url, cookieFile = COOKIE_FILE, load_cookie = True)
                    headers = { 'User-Agent' : HOST, 'Referer' : url }
                    url2 = self.url + 'porter.php?ch=%s' % cid
                    data = self.sl.getJsonFromExtendedAPI(url2, customHeaders=headers, cookieFile = COOKIE_FILE, load_cookie = True)
                    if 'killme.php' in data:
                        # Need to release stream
                        self.log('killme.php visible in data - killing old streams!')
                        self.sl.getJsonFromExtendedAPI(self.url + 'killme.php?id=%s' % cid, cookieFile = COOKIE_FILE, load_cookie = True)
                        data = self.sl.getJsonFromExtendedAPI(url2, customHeaders=headers, cookieFile = COOKIE_FILE, load_cookie = True)

                    link = re.compile('src: "(.*?)"').findall(data)
                    if len(link) > 0:
                        tmpRTMP = urllib.unquote(link[0]).decode('utf8')
                        tmpRTMP = re.compile('rtmp://(.*?)/(.*?)/(.*?)\?(.*?)\&streamType').findall(tmpRTMP)
                        rtmp = 'rtmp://' + tmpRTMP[0][0] + '/' + tmpRTMP[0][1] +'/' +tmpRTMP[0][2]+ '?'+ tmpRTMP[0][3]+ ' app=' + tmpRTMP[0][1] + '?' +tmpRTMP[0][3]+' swfVfy=1 flashver=WIN\\2020,0,0,306 timeout=25 swfUrl=http://wizja.tv/player/StrobeMediaPlayback.swf live=true pageUrl='+url
                        chann.strm = rtmp
                        self.log('getChannel found matching channel: cid: %s, name: %s, rtmp: %s' % (chann.cid, chann.name, chann.strm))
                        return chann
                    else:
                        self.log('getChannel error could not find video URL in: %s' % data)
        except Exception, e:
            self.log('getChannel exception while looping: %s' % str(e))
        return None
