#      Copyright (C) 2016 Andrzej Mleczko

import sys, re, copy
import xbmc
import datetime
import os, xbmcaddon, xbmcgui
from strings import *
from serviceLib import *
import base64

baseUrl = 'http://pierwsza.tv/'
onlineMapFile = 'http://epg.feenk.net/maps/pierwszatvmap.xml'
localMapFile = 'pierwszatvmap.xml'
serviceName = 'pierwsza.tv'
serviceRegex = "service=pierwszatv&cid=%"
servicePriority = int(ADDON.getSetting('priority_pierwszatv'))
pierwszaTVChannelList = None
lo = 'VzRaQS0+PC1iMGZjZTI4NzlhM2Q0MDYwNzQ2YTI1Zjc1ZDUwZGFkZQ=='

class PierwszaTvUpdater(baseServiceUpdater):
    def __init__(self):
        baseServiceUpdater.__init__(self)
        self.login    = ADDON.getSetting('pierwszatv_username').strip()
        self.password = ADDON.getSetting('pierwszatv_password').strip()
        self.serviceName = serviceName
        self.serviceRegex = serviceRegex
        self.servicePriority = servicePriority
        self.onlineMapFile = onlineMapFile
        self.localMapFile = localMapFile
        self.url = baseUrl
        self.refreshTimer = None
        self.timerData = {}

    def getChannelList(self, silent = False):
        global pierwszaTVChannelList
        if pierwszaTVChannelList is not None:
            return copy.deepcopy(pierwszaTVChannelList)

        if silent is not True:
            self.log('\n\n')
            self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
            self.log('[UPD] -------------------------------------------------------------------------------------')
            self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-RTMP-'))
        result = list()

        tmp_data = base64.b64decode(lo).split('-><-')
        self.apiId = tmp_data[0]
        self.apiChecksum = tmp_data[1]
        channelsArray = self.sl.getJsonFromExtendedAPI(self.url + 'api/channels?api_id=%s&checksum=%s' % (self.apiId, self.apiChecksum), jsonLoadsResult=True)

        try:
            if channelsArray['status'] != 'ok':
                self.log('getChannelList error while downloading channnel list, message: %s' % channelsArray['message'])
                return result
            else:
                channelsArray = channelsArray['channels']
        except Exception, ex:
            self.log('getChannelList Exception: %s' % str(ex))
            return result

        if channelsArray is None:
            self.log('Error while loading Json from URL: %s - aborting' % self.url)
            return result

        if len(channelsArray) > 0:
            try:
                for s in range(len(channelsArray)):
                    cid = self.sl.decode(channelsArray[s]['id']).replace("\"", '').strip()
                    ico = channelsArray[s]['thumbail']
                    if ico:
                        ico = baseUrl + self.sl.decode(ico).replace("\"", '').strip()
                    else:
                        ico = ''
                    name = self.sl.decode(channelsArray[s]['name']).replace("\"", '').strip()

                    self.log('[UPD] %-10s %-35s %-35s' % (cid, name, ''))

                    program = TvCid(cid, name, name, '', ico)
                    result.append(program)

                pierwszaTVChannelList = copy.deepcopy(result)
            except KeyError, keyerr:
                self.log('getChannelList exception while looping channelsArray, error: %s' % str(keyerr))
        else:
            self.log('getChannelList returned empty channel array!!!!!!!!!!!!!!!!')
            xbmcgui.Dialog().ok(strings(SERVICE_ERROR),"\n" + strings(SERVICE_NO_PREMIUM) + ' ' + self.serviceName)
        return result

    def getChannel(self, cid):
        channels = self.getChannelList()
        for chann in channels:
            if chann.cid == cid:
                channelData = self.sl.getJsonFromExtendedAPI(self.url + 'api/stream/create?api_id=%s&checksum=%s&id=%s&user=%s&password=%s' % (self.apiId, self.apiChecksum, cid, self.login, self.password), jsonLoadsResult=True)
                deb('XXXXXXX %sapi/stream/create?api_id=%s&checksum=%s&id=%s&user=%s&password=%s' % (self.url, self.apiId, self.apiChecksum, cid, self.login, self.password))
                debug('Mleczan stream/create URL returned: %s' % str(channelData))

                if not channelData or channelData['status'] != 'ok':
                    self.log('Error while trying to get channel data: %s' % str(channelData))
                    if channelData and channelData['message']:
                        xbmcgui.Dialog().ok(strings(SERVICE_ERROR),"\n" + channelData['message'] + ' ' + self.serviceName)
                    return None

                serverId = channelData['serverId']
                token = channelData['token']
                streamId = channelData['streamId']
                tokenExpireIn = int(channelData['tokenExpireIn'])

                startTime = datetime.datetime.now()
                while (datetime.datetime.now() - startTime).seconds < 25 and strings2.M_TVGUIDE_CLOSING == False:
                    serverStatus = self.sl.getJsonFromExtendedAPI(self.url + 'api/stream/status?api_id=%s&checksum=%s&serverId=%s&streamId=%s' % (self.apiId, self.apiChecksum, serverId, streamId), jsonLoadsResult=True)
                    debug('Mleczan stream/status URL returned: %s' % str(serverStatus))

                    if not serverStatus or serverStatus['status'] != 'ok' or serverStatus['sourceError'] == True:
                        self.log('Error while trying to get server status: %s' % str(serverStatus))
                        return None

                    if serverStatus['started'] == True:
                        self.unlockService()
                        timeDifference = (datetime.datetime.now() - startTime).seconds
                        refreshTokenIn = int(tokenExpireIn * 0.75) - timeDifference
                        if refreshTokenIn < 1:
                            refreshTokenIn = 1
                        self.log('getChannel cid: %s - stream ready after %d seconds! Refreshing token in %s seconds.' % (cid, timeDifference, refreshTokenIn))
                        self.timerData = { 'terminate' : False, 'serverId' : serverId, 'streamId' : streamId, 'token' : token }
                        self.refreshTimer = threading.Timer(refreshTokenIn, self.refreshToken, args=[self.timerData])
                        self.refreshTimer.start()
                        break
                    else:
                        self.log('getChannel cid: %s - waiting for server to start stream' % cid)
                        xbmc.sleep(150)

                if serverStatus['started'] == False:
                    self.log('getChannel cid: %s - stream not ready - aborting!' % cid)
                    return None

                channel = copy.deepcopy(chann)
                channel.strm = serverStatus['source'] + '?token=' + token
                self.log('getChannel found matching channel: cid: %s, name: %s, rtmp: %s' % (channel.cid, channel.name, channel.strm))
                return channel
        return None

    def refreshToken(self, timerData):
        if not timerData['terminate']:
            refreshData = self.sl.getJsonFromExtendedAPI(self.url + 'api/stream/refresh?api_id=%s&checksum=%s&serverId=%s&streamId=%s&token=%s' % (self.apiId, self.apiChecksum, timerData['serverId'], timerData['streamId'], timerData['token']), jsonLoadsResult=True)
            debug('Mleczan stream/refresh URL returned: %s' % str(refreshData))

            if not timerData['terminate'] and refreshData and refreshData['status'] == 'ok':
                refreshTokenIn = int(int(refreshData['tokenExpireIn']) * 0.75)
                self.refreshTimer = threading.Timer(refreshTokenIn, self.refreshToken, args=[timerData])
                self.refreshTimer.start()
            elif not timerData['terminate'] and refreshData:
                self.log('Problem while refreshing token, data sent is: %s' % str(timerData))

    def unlockService(self):
        self.log('unlockService')
        self.timerData['terminate'] = True
        if self.refreshTimer:
            self.refreshTimer.cancel()
