#      Copyright (C) 2016 Andrzej Mleczko

import re, sys, os, cgi
import xbmcplugin, xbmcgui, xbmcaddon, xbmc
from strings import *
import weebtvcids
import telewizjadacids
import goldvodcids
import playlistcids
import threading
import time

SERVICES = {
'weebtv': weebtvcids.WebbTvStrmUpdater(),
'goldvod': goldvodcids.GoldVodUpdater(),
'telewizjada': telewizjadacids.TelewizjaDaUpdater(),
'playlist': playlistcids.PlaylistUpdater()
}

SERVICE_AVAILABILITY = {
'weebtv': ADDON.getSetting('WeebTV_enabled'),
'goldvod': ADDON.getSetting('GoldVOD_enabled'),
'telewizjada': ADDON.getSetting('telewizjada_enabled'),
'playlist': ADDON.getSetting('playlist_enabled')
}

class BasePlayService:
    lockMap = {}
    maxAllowedStreams = {}
    lock = threading.Lock()
    for service in SERVICES:
        lockMap[service] = 0
        maxAllowedStreams[service] = SERVICES[service].maxAllowedStreams

    def __init__(self):
        self.thread = None
        self.terminating = False

    def parseUrl(self, url):
        cid = 0
        service = None
        try:
            params = url[8:].split('&')
            service = params[0]
            cid = params[1].split('=')[1]
            deb(self.__class__.__name__ + ' parseUrl: cid %s, service %s' % (cid, service))
        except:
            pass
        return [cid, service]

    def isWorking(self):
        if self.thread is not None:
            return self.thread.is_alive()
        return False

    def getChannel(self, cid, service, currentlyPlayedService = None):
        BasePlayService.lock.acquire() # make this function thread safe
        channelInfo = None
        if self.isServiceLocked(service) == True and service != currentlyPlayedService: #if issued by playservice and th's the same as played then allow using the same service - it will be release anyway
            debug(self.__class__.__name__ + ' getChannel service %s is locked - aborting' % service)
            BasePlayService.lock.release()
            return None
        try:
            serviceHandler = SERVICES[service]
        except KeyError:
            serviceHandler = None

        if serviceHandler is not None:
            channelInfo = serviceHandler.getChannel(cid)

        if channelInfo is not None and service != currentlyPlayedService:
            self.lockService(service)
        BasePlayService.lock.release()
        return channelInfo

    def lockService(self, service):
        try:
            BasePlayService.lockMap[service] = BasePlayService.lockMap[service] + 1
            deb(self.__class__.__name__ + ' lockService: %d streams handled by service: %s, max is: %d' % (BasePlayService.lockMap[service], service, BasePlayService.maxAllowedStreams[service]))
        except:
            pass

    def unlockService(self, service):
        try:
            BasePlayService.lockMap[service] = BasePlayService.lockMap[service] - 1
            deb(self.__class__.__name__ + ' unlockService: still %d streams handled by service: %s, max is: %d' % (BasePlayService.lockMap[service], service, BasePlayService.maxAllowedStreams[service]))
            if BasePlayService.lockMap[service] < 0:
                deb(self.__class__.__name__ + ' error while unlocking service, nr less than 0, something went wrong!')
                raise
        except:
            pass

    def isServiceLocked(self, service):
        try:
            if BasePlayService.lockMap[service] >= BasePlayService.maxAllowedStreams[service]:
                return True
        except:
            pass
        return False

class PlayService(xbmc.Player, BasePlayService):
    def __init__(self, *args, **kwargs):
        BasePlayService.__init__(self)
        self.playbackStopped = False
        self.playbackStarted = False
        self.currentlyPlayedService = None
        self.player = xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER)

    def playUrlList(self, urlList):
        if self.thread is not None and self.thread.is_alive():
            deb('PlayService playUrlList waiting for thread to terminate')
            self.terminating = True
            self.thread.join()

        self.thread = threading.Thread(name='playUrlList Loop', target = self._playUrlList, args=[urlList])
        self.thread.start()

    def _playUrlList(self, urlList):
        self.terminating = False

        for url in urlList:
            playStarted = self.playUrl(url)

            for i in range(150):

                if self.terminating == True or xbmc.abortRequested == True:
                    self.player.stop()
                    self.unlockService(self.currentlyPlayedService)
                    self.currentlyPlayedService = None
                    deb('PlayService _playUrlList abort requested - terminating')
                    return

                if self.playbackStarted == True:
                    deb('PlayService _playUrlList detected stream start!')
                    return

                if self.playbackStopped == True or playStarted == False:
                    break

                time.sleep(.100)

            deb('PlayService _playUrlList detected faulty stream!')
            self.player.stop()
            self.unlockService(self.currentlyPlayedService)
            self.currentlyPlayedService = None

    def playUrl(self, url):
        self.playbackStopped = False
        self.playbackStarted = False
        success = True

        if url[-5:] == '.strm':
            try:
                f = open(url)
                content = f.read()
                f.close()
                if content[0:9] == 'plugin://':
                    url = content.strip()
            except:
                pass

        if url[0:9] == 'plugin://':
            xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
        elif url[0:7] == 'service':
            cid, service = self.parseUrl(url)
            success = self.LoadVideoLink(cid, service)
        else:
            self.player.play(url)
        return success

    def close(self):
        self.terminating = True
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(10)

    def LoadVideoLink(self, channel, service):
        deb('LoadVideoLink %s service' % service)
        res = False
        channels = None
        startWindowed = False
        if ADDON.getSetting('start_video_minimalized') == 'true':
            startWindowed = True

        channelInfo = self.getChannel(channel, service, self.currentlyPlayedService)

        if channelInfo is not None:
            if self.currentlyPlayedService != service:
                self.unlockService(self.currentlyPlayedService)
            self.currentlyPlayedService = service
            liz = xbmcgui.ListItem(channelInfo.title, iconImage = channelInfo.img, thumbnailImage = channelInfo.img)
            liz.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
            try:
                if channelInfo.premium == 0:
                    xbmcgui.Dialog().ok(strings(57034).encode('utf-8'), strings(57036).encode('utf-8') + '\n' + strings(57037).encode('utf-8') + '\n' + 'service: %s' % service.encode('utf-8'))
                self.player.play(channelInfo.strm, liz, windowed=startWindowed)
                res = True
            except Exception, ex:
                self.unlockService(self.currentlyPlayedService)
                self.currentlyPlayedService = None
                xbmcgui.Dialog().ok(strings(57018).encode('utf-8'), strings(57021).encode('utf-8') + '\n' + strings(57028).encode('utf-8') + '\n' + str(ex))
        return res

    def onPlayBackStopped(self):
        self.playbackStopped = True
        self.unlockService(self.currentlyPlayedService)
        self.currentlyPlayedService = None
        self.player.stop()

    def onPlayBackStarted(self):
        self.playbackStarted = True
