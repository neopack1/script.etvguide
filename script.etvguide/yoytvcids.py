#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
import urlparse
from strings import *
from serviceLib import *

serviceName         = 'YoyTV'
yoyUrl              = 'http://yoy.tv/'
COOKIE_FILE         = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')) , 'yoytv.cookie')
yoytvChannelList    = None

class YoyTVUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.serviceName        = serviceName
        self.serviceEnabled     = ADDON.getSetting('yoytv_enabled')
        self.login              = ADDON.getSetting('yoytv_username').strip()
        self.password           = ADDON.getSetting('yoytv_password').strip()
        self.useFreeAccount     = ADDON.getSetting('yoytv_use_free_account')
        self.servicePriority    = int(ADDON.getSetting('priority_yoytv'))
        self.onlineMapFile      = 'http://epg.feenk.net/maps/yoytvmap.xml'
        self.localMapFile       = 'yoytvmap.xml'
        self.serviceRegex       = "service=" + self.serviceName + "&cid=%"
        self.rstrm              = self.serviceRegex + 's'
        self.url                = yoyUrl
        self.maxAllowedStreams  = 1
        self.nrOfPagesToParse   = 10


    def downloadThread(self, url, threadData):
        data = self.sl.getJsonFromExtendedAPI(url, cookieFile = COOKIE_FILE, load_cookie = True)
        if data is not None:
            threadData.append(data)

    def getChannelList(self):
        global yoytvChannelList
        if yoytvChannelList is not None:
            return copy.deepcopy(yoytvChannelList)

        result = list()
        self.log('\n\n')
        self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-IMG-'))

        try:
            post = {}
            data = self.sl.getJsonFromExtendedAPI(self.url + 'signin', cookieFile = COOKIE_FILE, save_cookie = True)
            if self.useFreeAccount == 'false' and len(self.login) > 0:
                post['remember_me']='1'
                post['email'] = self.login
                post['password'] = self.password
                post['_token'] = self.sl.parseDOM(data, 'input', ret='value', attrs={'name' : '_token'})[0]
                data = self.sl.getJsonFromExtendedAPI(self.url + 'signin', post_data = post, cookieFile = COOKIE_FILE, load_cookie = True, max_conn_time=7)

                #if data is not None and not 'http://yoy.tv/signout' in data:
                    #xbmcgui.Dialog().ok(strings(SERVICE_ERROR), "\n" + strings(SERVICE_NO_PREMIUM) + ' ' + self.serviceName)
                    #return result

            threadList = list()
            threadData = list()
            for page in range(1, self.nrOfPagesToParse):
                thread = threading.Thread(name='downloadThread', target = self.downloadThread, args=[self.url + 'channels?live=1&country=140&page=%s' % page, threadData])
                threadList.append(thread)
                thread.start()

            for thread in threadList:
                while thread.is_alive():
                    xbmc.sleep(300)

            del threadList[:]

            for data in threadData:
                if data is not None:
                    data = self.sl.parseDOM(data, 'a', attrs={'class' : 'thumb-info team'})
                    parsedData = list()
                    for i in data:
                        try:
                            row = i.replace('>>', '')
                            img  = self.sl.parseDOM(row, 'img', ret='src')[0]
                            name = self.sl.parseDOM(row, 'img', ret='alt')[0]
                            parsedData.append([img, name])
                        except Exception, e:
                            self.log('getChannelList exception: %s, while parsing data: %s' % (str(e), row) )

                    for item in parsedData:
                        cid = item[0].replace('http://yoy.tv/channel/covers/','').replace('.jpg?cache=32','').encode('utf-8')
                        name = item[1].upper().encode('utf-8')
                        img = item[0].replace('?cache=32', '').encode('utf-8')
                        self.log('[UPD] %-10s %-35s %-35s' % (cid, name, img))
                        program = TvCid(cid, name, name, img=img)
                        result.append(program)

                    del parsedData[:]

            del threadData[:]
            if len(result) > 0:
                yoytvChannelList = copy.deepcopy(result)

        except Exception, e:
            self.log('getChannelList exception: %s' % str(e))
        return result

    def getChannel(self, cid):
        try:
            channels = self.getChannelList()
            for chann in channels:
                if chann.cid == cid:
                    url = self.url + 'channels/%s' % cid
                    data = self.sl.getJsonFromExtendedAPI(url, cookieFile = COOKIE_FILE, load_cookie = True)
                    if '<title>Kup konto premium w portalu yoy.tv</title>' in data:
                        xbmcgui.Dialog().notification(strings(SERVICE_ERROR), strings(SERVICE_NO_PREMIUM) + ' ' + self.serviceName, time=10000, sound=False)
                        return None
                    data = self.sl.parseDOM(data, 'param', ret='value', attrs={'name' : 'FlashVars'})[0].encode('utf-8')

                    # Decoded by MrKnow - thanks!
                    lpi = data.index("s=") + data.index("=") * 3
                    rpi = data.index("&", lpi) - data.index("d") * 2
                    dp=[]
                    cp=data[lpi:rpi].split('.')
                    for i, item in enumerate(cp):
                        j = 2 ^ i ^ ((i ^ 3) >> 1)
                        k = 255 - int(cp[j])
                        dp.append(k)
                    myip = '.'.join(map(str, dp))
                    data = dict(urlparse.parse_qsl(data))

                    playpath = '%s?email=%s&secret=%s&hash=%s' % (data['cid'], data['email'], data['secret'], data['hash'])
                    rtmp = 'rtmp://' + myip + ' app=yoy/_definst_ playpath=' + playpath + ' swfUrl=http://yoy.tv/playerv3a.swf' + ' swfVfy=true tcUrl=' + 'rtmp://' + myip + '/yoy/_definst_ live=true pageUrl=' + url
                    chann.strm = rtmp
                    self.log('getChannel found matching channel: cid: %s, name: %s, rtmp: %s' % (str(chann.cid), str(chann.name), str(chann.strm)) )
                    return chann

        except Exception, e:
            self.log('getChannel exception while looping: %s' % str(e))
        return None
