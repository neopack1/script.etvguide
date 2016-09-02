#      Copyright (C) 2016 Andrzej Mleczko

import re, sys, os, cgi
import xbmcplugin, xbmcgui, xbmcaddon, xbmc
from strings import *
import strings as strings2
import datetime
import serviceLib
import weebtvcids
import telewizjadacids
import goldvodcids
import playlistcids
import mojefilmycids
import pierwszatvcids
import wizjatvcids
import yoytvcids
import threading
import time

SERVICES = {
    weebtvcids.serviceName      : weebtvcids.WebbTvStrmUpdater(),
    goldvodcids.serviceName     : goldvodcids.GoldVodUpdater(),
    telewizjadacids.serviceName : telewizjadacids.TelewizjaDaUpdater(),
    playlistcids.serviceName    : playlistcids.PlaylistUpdater(),
    mojefilmycids.serviceName   : mojefilmycids.MojeFilmyUpdater(),
    pierwszatvcids.serviceName  : pierwszatvcids.PierwszaTvUpdater(),
    wizjatvcids.serviceName     : wizjatvcids.WizjaTVUpdater(),
    yoytvcids.serviceName       : yoytvcids.YoyTVUpdater()
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
        self.starting = False

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
            return self.thread.is_alive() or self.starting
        return False

    def getChannel(self, cid, service, currentlyPlayedService = { 'service' : None }):
        BasePlayService.lock.acquire() # make this function thread safe
        channelInfo = None
        if self.isServiceLocked(service) == True and service != currentlyPlayedService['service']: #if issued by PlayService and it's the same as played then allow using the same service - it will be release anyway
            debug(self.__class__.__name__ + ' getChannel service %s is locked - aborting' % service)
            BasePlayService.lock.release()
            return None
        try:
            serviceHandler = SERVICES[service]
        except KeyError:
            serviceHandler = None

        if serviceHandler is not None:
            channelInfo = serviceHandler.getChannel(cid)

        if channelInfo is not None and service != currentlyPlayedService['service']:
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
            if service:
                BasePlayService.lockMap[service] = BasePlayService.lockMap[service] - 1
                SERVICES[service].unlockService()
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
        self.currentlyPlayedService = { 'service' : None }
        self.urlList = None
        self.playbackStartTime = None
        self.sleepSupervisor = serviceLib.SleepSupervisor(self.stopPlayback)
        self.streamQuality = ''
        self.userStoppedPlayback = True
        self.nrOfResumeAttempts = 0
        self.threadData = { 'terminate' : False }
        self.maxNrOfResumeAttempts = int(ADDON.getSetting('max_reconnect_attempts'))
        self.reconnectFailedStreams = ADDON.getSetting('reconnect_stream')
        self.reconnectDelay = int(ADDON.getSetting('reconnect_delay'))

    def playUrlList(self, urlList):
        if urlList is None or len(urlList) == 0:
            deb('playUrlList got empty list to play - aborting!')
            return
        self.starting = True
        self.threadData['terminate'] = True
        currentThreadData = self.threadData = { 'terminate' : False }

        if self.thread is not None and self.thread.is_alive():
            deb('PlayService playUrlList waiting for thread to terminate')
            self.terminating = True
            while self.thread is not None and self.thread.is_alive() and currentThreadData['terminate'] == False:
                xbmc.sleep(100)
            #self.thread.join()

        if currentThreadData['terminate'] == True:
            deb('playUrlList decided to terminate thread starting playback')
            return

        self.thread = threading.Thread(name='playUrlList Loop', target = self._playUrlList, args=[urlList])
        self.thread.start()
        self.starting = False

    def _playUrlList(self, urlList):
        self.terminating = False
        self.urlList = list(urlList)
        self.userStoppedPlayback = False

        for url in self.urlList[:]:
            playStarted = self.playUrl(url)

            for i in range(80):

                if self.terminating == True or strings2.M_TVGUIDE_CLOSING == True:
                    if strings2.M_TVGUIDE_CLOSING == True:
                        xbmc.Player().stop()
                    self.unlockService(self.currentlyPlayedService['service'])
                    self.currentlyPlayedService['service'] = None
                    deb('PlayService _playUrlList abort requested - terminating')
                    return

                if self.playbackStarted == True:
                    deb('PlayService _playUrlList detected stream start!')
                    self.playbackStartTime = datetime.datetime.now()
                    return

                if self.playbackStopped == True or playStarted == False:
                    break

                xbmc.sleep(100)

            deb('PlayService _playUrlList detected faulty stream! playbackStopped: %s, playStarted: %s' % (self.playbackStopped, playStarted) )
            xbmc.Player().stop()
            self.unlockService(self.currentlyPlayedService['service'])
            self.currentlyPlayedService['service'] = None
            try:
                #move stream to the end of list
                self.urlList.remove(url)
                self.urlList.append(url)
            except Exception, ex:
                deb('_playUrlList exception: %s' % str(ex))

    def playUrl(self, url):
        self.playbackStopped = False
        self.playbackStarted = False
        self.streamQuality = ''
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
            if success:
                self.getStreamQualityFromCid(cid)
        else:
            xbmc.Player().play(url)
        return success

    def playNextStream(self):
        if self.urlList and len(self.urlList) > 1:
            tmpUrl = self.urlList.pop(0)
            self.urlList.append(tmpUrl)
            debug('PlayService playNextStream skipping: %s, next: %s' % (tmpUrl, self.urlList[0]))
            self.playUrlList(self.urlList)

    def close(self):
        self.terminating = True
        self.stopPlayback()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(10)

    def LoadVideoLink(self, channel, service):
        #deb('LoadVideoLink %s service' % service)
        res = False
        channels = None
        startWindowed = False
        if ADDON.getSetting('start_video_minimalized') == 'true':
            startWindowed = True

        channelInfo = self.getChannel(channel, service, self.currentlyPlayedService)

        if channelInfo is not None:
            if self.currentlyPlayedService['service'] != service:
                self.unlockService(self.currentlyPlayedService['service'])
            self.currentlyPlayedService['service'] = service
            liz = xbmcgui.ListItem(channelInfo.title, iconImage = channelInfo.img, thumbnailImage = channelInfo.img)
            liz.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
            try:
                self.playbackStopped = False
                xbmc.Player().play(channelInfo.strm, liz, windowed=startWindowed)
                res = True
            except Exception, ex:
                deb('Exception while trying to play video: %s' % str(ex))
                self.unlockService(self.currentlyPlayedService['service'])
                self.currentlyPlayedService['service'] = None
                xbmcgui.Dialog().ok(strings(57018).encode('utf-8'), strings(57021).encode('utf-8') + '\n' + strings(57028).encode('utf-8') + '\n' + str(ex))
        else:
            deb('LoadVideoLink ERROR channelInfo is None! service: %s' % service)
        return res

    def onPlayBackStopped(self):
        self.playbackStopped = True
        self.unlockService(self.currentlyPlayedService['service'])
        self.currentlyPlayedService['service'] = None
        self.sleepSupervisor.Stop()
        self.tryResummingPlayback()

    def onPlayBackEnded(self):
        self.playbackStopped = True
        self.unlockService(self.currentlyPlayedService['service'])
        self.currentlyPlayedService['service'] = None
        self.sleepSupervisor.Stop()
        self.tryResummingPlayback()

    def onPlayBackStarted(self):
        self.playbackStarted = True
        self.sleepSupervisor.Start()

    def stopPlayback(self):
        debug('PlayService stopPlayback')
        self.urlList = None
        self.userStoppedPlayback = True
        self.nrOfResumeAttempts = 0
        self.terminating = True
        xbmc.Player().stop()

    def getStreamQualityFromCid(self, cid):
        #debug('getStreamQualityFromCid cid: %s' % cid)
        self.streamQuality = ''
        try:
            parts = cid.split("_")
            self.streamQuality = parts[1]
        except:
            pass

    def tryResummingPlayback(self):
        deb('PlayService tryResummingPlayback self.userStoppedPlayback: %s, self.isWorking(): %s, self.nrOfResumeAttempts: %s, self.maxNrOfResumeAttempts: %s' % (self.userStoppedPlayback, self.isWorking(), self.nrOfResumeAttempts, self.maxNrOfResumeAttempts))
        if self.reconnectFailedStreams == 'true' and not self.userStoppedPlayback and not self.isWorking() and self.urlList:
            if self.nrOfResumeAttempts < self.maxNrOfResumeAttempts:
                self.nrOfResumeAttempts += 1
                self.starting = True
                deb('PlayService reconnecting, nr of reattempts: %s' % self.nrOfResumeAttempts)
                if self.playbackStartTime is not None and (datetime.datetime.now() - self.playbackStartTime).seconds < 10:
                    try:
                        #Playback didn't last for 10s - move stream to the end of list
                        deb('Playback last for only %s seconds - moving to next one' % (datetime.datetime.now() - self.playbackStartTime).seconds)
                        tmpUrl = self.urlList.pop(0)
                        self.urlList.append(tmpUrl)
                    except Exception, ex:
                        deb('tryResummingPlayback exception: %s' % str(ex))
                if self.reconnectDelay > 0:
                    xbmc.sleep(self.reconnectDelay)
                self.playUrlList(self.urlList)
            else:
                deb('PlayService reached reconnection limit - aborting!')
                self.stopPlayback()
