#      Copyright (C) 2014 Krzysztof Cebulski
#      Copyright (C) 2013 Szakalit

# -*- coding: utf-8 -*-
import urllib, urllib2, httplib
import re, sys, os, cgi
import xbmcplugin, xbmcgui, xbmcaddon, xbmc, gui
import threading
import time
import simplejson as json
import weebtvcids
import datetime
from strings import *
import telewizjadacids


t = ADDON.getLocalizedString
os.path.join( ADDON.getAddonInfo('path'), "resources" )

mainUrl = 'http://weeb.tv'
playerUrl = mainUrl + '/api/setplayer'
apiUrl = mainUrl + '/api/getChannelList'
iconUrl = 'http://static2.weeb.tv/static2/ci/'
HOST = 'XBMC'
login = ADDON.getSetting('username')
password = ADDON.getSetting('userpassword')
goldVODLogin = ADDON.getSetting('usernameGoldVOD')
goldVODPassword = ADDON.getSetting('userpasswordGoldVOD')
multi = ADDON.getSetting('video_quality')

goldVODChannelList = None
goldVODLastUpdate = None

class ShowList:
    def __init__(self):
        pass

    def decode(self, string):
        json_ustr = json.dumps(string, ensure_ascii=False)
        return json_ustr.encode('utf-8')

    def getJsonFromAPI(self, url):
        result_json = { "0": "Null" }
        try:
            headers = { 'User-Agent' : HOST, 'ContentType' : 'application/x-www-form-urlencoded' }
            post = { 'username': login, 'userpassword': password }
            data = urllib.urlencode(post)
            failedCounter = 0
            while failedCounter < 5:
                try:
                    reqUrl = urllib2.Request(url, data, headers)
                    raw_json = urllib2.urlopen(reqUrl)
                    content_json = raw_json.read()
                    result_json = json.loads(content_json)
                    break
                except httplib.IncompleteRead:
                    failedCounter = failedCounter + 1
                    deb('getJsonFromAPI IncompleteRead exception - retrying')
                    time.sleep(.300)
        except urllib2.URLError, urlerr:
            msg = Messages()
            result_json = { "0": "Error" }
            print urlerr
            msg.Error(t(57001).encode('utf-8'), t(57002).encode('utf-8'), t(57003).encode('utf-8'))
        except NameError, namerr:
            msg = Messages()
            result_json = { "0": "Error" }
            print namerr
            msg.Error(t(57009).encode('utf-8'), t(57010).encode('utf-8'))
        except ValueError, valerr:
            msg = Messages()
            result_json = { "0": "Error" }
            print valerr
            msg.Error(t(57001).encode('utf-8'), t(57011).encode('utf-8'), t(57012).encode('utf-8'), t(57013).encode('utf-8'))
        except httplib.BadStatusLine, statuserr:
            msg = Messages()
            result_json = { "0": "Error" }
            print statuserr
            msg.Error(t(57001).encode('utf-8'), t(57002).encode('utf-8'), t(57003).encode('utf-8'))
        return result_json


class UrlParser:
    def __init__(self):
        pass

    def getParam(self, params, name):
        try:
            result = params[name]
            result = urllib.unquote_plus(result)
            return result
        except:
            return None

    def getIntParam (self, params, name):
        try:
            param = self.getParam(params, name)
            return int(param)
        except:
            return None

    def getBoolParam (self, params, name):
        try:
            param = self.getParam(params,name)
            return 'True' == param
        except:
            return None

    def getParams2(self, paramstring = ''):
        param=[]
        if len(paramstring) >= 2:
            params = paramstring
            cleanedparams = params.replace('?', '')
            if (params[len(params)-1] == '/'):
                params = params[0:len(params)-2]
            pairsofparams = cleanedparams.split('&')
            param = {}
            for i in range(len(pairsofparams)):
                splitparams = {}
                splitparams = pairsofparams[i].split('=')
                if (len(splitparams)) == 2:
                    param[splitparams[0]] = splitparams[1]
        return param

    def getParams(self):
        try:
			paramstring = sys.argv[1]
        except:
			return
        param=[]
        if len(paramstring) >= 2:
            params = paramstring
            cleanedparams = params.replace('?', '')
            if (params[len(params)-1] == '/'):
                params = params[0:len(params)-2]
            pairsofparams = cleanedparams.split('&')
            param = {}
            for i in range(len(pairsofparams)):
                splitparams = {}
                splitparams = pairsofparams[i].split('=')
                if (len(splitparams)) == 2:
                    param[splitparams[0]] = splitparams[1]
        return param

class RTMP:
    def __init__(self):
        pass

    def ConnectionParams(self, channel):
        data = None
        if login == '' and password == '':
            values = { 'cid': channel, 'platform': 'XBMC' }
        else:
            values = { 'cid': channel, 'platform': 'XBMC', 'username': login, 'userpassword': password }
        try:
            parser = UrlParser()
            headers = { 'User-Agent' : HOST }
            data = urllib.urlencode(values)
            reqUrl = urllib2.Request(playerUrl, data, headers)
            failedCounter = 0
            while failedCounter < 5:
                try:
                    response = urllib2.urlopen(reqUrl)
                    break
                except urllib2.URLError:
                    failedCounter = failedCounter + 1
                    deb('ConnectionParams URLError exception - retrying opening url')
                    time.sleep(.300)
            resLink = response.read()
            params = parser.getParams2(resLink)
            status = parser.getParam(params, "0")
            premium = parser.getIntParam(params, "5")
            rtmpLink = parser.getParam(params, "10")
            playPath = parser.getParam(params, "11")
            ticket = parser.getParam(params, "73")

            data = { 'rtmp': rtmpLink, 'ticket': ticket, 'playpath': playPath, 'premium': premium, 'status': status }
        except urllib2.URLError, urlerr:
            msg = Messages()
            data = { 'rtmp': None, 'ticket': None, 'playpath': None, 'premium': premium, 'status': status }
            print urlerr
            msg.Error(t(57014).encode('utf-8'), t(57015).encode('utf-8'), t(57003).encode('utf-8'))
        return data

    def GetLinkParameters(self, channel, bitrate):
        dataLink = {}
        valTabA = self.ConnectionParams(channel)
        rtmpLink = valTabA['rtmp']
        ticket = valTabA['ticket']
        playpath = valTabA['playpath']
        premium = valTabA['premium']
        status = valTabA['status']
        if bitrate == '1' and multi == 'true':
            playpath = playpath + 'HI'
        rtmp = str(rtmpLink) + '/' + str(playpath)
        rtmp += ' swfUrl='  + str(ticket)
        rtmp += ' pageUrl=token'
        rtmp += ' live=true'
        print 'Output rtmp link: %s' % (rtmp)
        return { 'rtmp': rtmp, 'premium': premium, 'status': status }

class VideoPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        self.is_active = True
        deb ( "#Starting control VideoPlayer events#" )

    def setPremium(self, premium):
        self.premium = premium

    def getPremium(self):
        return self.premium

    def onPlayBackPaused(self):
        deb ( "#Im paused#" )
        ThreadPlayerControl("Stop").start()
        self.is_active = False

    def onPlayBackResumed(self):
        deb ( "#Im Resumed #" )

    def onPlayBackStarted(self):
        deb ( "#Playback Started#" )
        try:
            deb ( "#Im playing :: " + self.getPlayingFile())
        except:
            deb("#I failed get what Im playing#")

    def onPlayBackEnded(self):
        msg = Messages()
        deb ("#Playback Ended#")
        self.is_active = False
        if self.getPremium() == 0:
            msg.Warning(t(57018).encode('utf-8'), t(57019).encode('utf-8'), t(57020).encode('utf-8'))
        else:
            msg.Warning(t(57018).encode('utf-8'), t(57027).encode('utf-8'))

    def onPlayBackStopped(self):
        deb( "## Playback Stopped ##")
        self.is_active = False

    def sleep(self, s):
        xbmc.sleep(s)

class InitPlayer:
    def __init__(self):
        pass

    def getChannelInfoFromJSON(self, channel):
        chan = ShowList()
        dataInfo = { 'title': '', 'image': '', 'bitrate': '' }
        try:
            channelsArray = chan.getJsonFromAPI(apiUrl)
            for v,k in channelsArray.items():
                if int(channel) == int(k['cid']):
                    cid = k['cid']
                    title = chan.decode(k['channel_title']).replace("\"", "")
                    bitrate = k['multibitrate']
                    img = k['channel_image']
                    image = iconUrl + "no_video.png"
                    if img == '1':
                        image = iconUrl + cid + ".jpg"
                    dataInfo = { 'title': title, 'image': image, 'bitrate': bitrate }
                    break
        except TypeError, typerr:
            print typerr
        return dataInfo

    def LoadVideoLink(self, channel, service):
        deb('LoadVideoLink %s service' % service)
        res = True
        channels = None
        channelInfo = None
        if service == "weebtv":
            rtmp = RTMP()
            val = self.getChannelInfoFromJSON(channel)
            videoLink =  rtmp.GetLinkParameters(channel, val['bitrate'])
            if videoLink['status'] == '1':
                if videoLink['rtmp'].startswith('rtmp'):
                    liz = xbmcgui.ListItem(val['title'], iconImage = val['image'], thumbnailImage = val['image'])
                    liz.setInfo( type="Video", infoLabels={ "Title": val['title'], } )
                    try:
                        player = VideoPlayer()
                        player.setPremium(int(videoLink['premium']))
                        if videoLink['premium'] == 0:
                            msg = Messages()
                            msg.Warning(t(57034).encode('utf-8'), t(57036).encode('utf-8'), t(57037).encode('utf-8'), t(57038).encode('utf-8'))
                        player.play(videoLink['rtmp'], liz, windowed=True)
                    except:
                        msg = Messages()
                        msg.Error(t(57018).encode('utf-8'), t(57021).encode('utf-8'), t(57028).encode('utf-8'))
                else:
                    msg = Messages()
                    msg.Error(t(57018).encode('utf-8'), t(57022).encode('utf-8'))
            elif videoLink['status'] == '-1':
                msg = Messages()
                msg.Warning(t(57018).encode('utf-8'), t(57043).encode('utf-8'))
            elif videoLink['status'] == '-2':
                msg = Messages()
                msg.Warning(t(57018).encode('utf-8'), t(57044).encode('utf-8'))
            elif videoLink['status'] == '-3':
                msg = Messages()
                msg.Warning(t(57018).encode('utf-8'), t(57045).encode('utf-8'))
            elif videoLink['status'] == '-4':
                msg = Messages()
                msg.Warning(t(57018).encode('utf-8'), t(57046).encode('utf-8'), t(57047).encode('utf-8'))
            else:
                msg = Messages()
                msg.Warning(t(57018).encode('utf-8'), t(57042).encode('utf-8'))
        elif service == "goldvod":            
            global goldVODChannelList
            global goldVODLastUpdate
            if goldVODLastUpdate is not None and goldVODChannelList is not None:
                try:
                    secSinceLastUpdate = (datetime.datetime.now() - goldVODLastUpdate).total_seconds()
                    deb('LoadVideoLink channels were updated %s seconds ago' % secSinceLastUpdate )
                    if secSinceLastUpdate < 600:
                        channels = goldVODChannelList
                except:
                    pass

            if channels is None:
                deb('LoadVideoLink downloading channel list')
                sl = weebtvcids.ShowList()
                sl.setLoginData(goldVODLogin, goldVODPassword)
                channels = sl.loadChannelsGoldVod('http://goldvod.tv/api/getTvChannels.php', 'url', 'password', True)

                if len(channels) > 0:
                    goldVODChannelList = channels
                    goldVODLastUpdate = datetime.datetime.now()
            else:
                deb('LoadVideoLink using cached list')
            
            for chann in channels:
                if channel == chann.cid:
                    deb('LoadVideoLink: service %s found matching channel: cid %s, name %s, rtmp %s' % (service, chann.cid, chann.name, chann.strm))
                    channelInfo = chann
                    break
            if channelInfo is not None:
                liz = xbmcgui.ListItem(channelInfo.name, iconImage = channelInfo.img, thumbnailImage = channelInfo.img)
                liz.setInfo( type="Video", infoLabels={ "Title": channelInfo.name, } )
                try:
                    player = VideoPlayer()
                    player.setPremium(1)
                    player.play(channelInfo.strm, liz, windowed=True)
                except Exception, ex:
                    msg = Messages()
                    msg.Error(t(57018).encode('utf-8'), t(57021).encode('utf-8'), t(57028).encode('utf-8'), str(ex))
        elif service == "telewizjada":
            telewizja = telewizjadacids.TelewizjaDaUpdater()
            channels = telewizja.getChannelList()
            if len(channels) > 0:
                url = telewizja.getChannelUrl(channel)
                for chann in channels:
                    if channel == chann.cid:
                        deb('LoadVideoLink: service %s found matching channel: cid %s, name %s, rtmp %s ' % (service, chann.cid, chann.name, chann.strm))
                        channelInfo = chann
                        break
                if channelInfo is not None:
                    liz = xbmcgui.ListItem(channelInfo.name, iconImage = channelInfo.img, thumbnailImage = channelInfo.img)
                    liz.setInfo( type="Video", infoLabels={ "Title": channelInfo.name, } )
                try:
                    player = VideoPlayer()
                    player.setPremium(1)
                    player.play(url, liz, windowed=True)
                except Exception, ex:
                    msg = Messages()
                    msg.Error(t(57018).encode('utf-8'), t(57021).encode('utf-8'), t(57028).encode('utf-8'), str(ex))
        return res

class ThreadPlayerControl(threading.Thread):
    def __init__(self, command):
        self.command = command
        threading.Thread.__init__ (self)

    def run(self):
        xbmc.executebuiltin('PlayerControl(' + self.command + ')')

class Messages:
    def __init__(self):
        pass

    def Error(self, title, text1, text2 = "", text3 = ""):
        dialog = xbmcgui.Dialog()
        dialog.ok(title,"\n\t" +text1 + "\n\t" + text2 + "\n\t" + text3)


    def Warning(self, title, text1, text2 = "", text3 = ""):
        dialog = xbmcgui.Dialog()
        dialog.ok(title,"\n\t" +text1 + "\n\t" + text2 + "\n\t" + text3)


