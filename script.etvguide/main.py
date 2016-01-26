#      Copyright (C) 2016 Andrzej Mleczko
#      Copyright (C) 2014 Krzysztof Cebulski
#      Copyright (C) 2013 Szakalit

# -*- coding: utf-8 -*-
import re, sys, os, cgi
import xbmcplugin, xbmcgui, xbmcaddon, xbmc, gui
from strings import *
import weebtvcids
import telewizjadacids
import goldvodcids

t = ADDON.getLocalizedString

class InitPlayer:
    def __init__(self):
        pass

    def LoadVideoLink(self, channel, service):
        deb('LoadVideoLink %s service' % service)
        res = False
        channels = None
        channelInfo = None
        startWindowed = False
        if ADDON.getSetting('start_video_minimalized') == 'true':
            startWindowed = True

        if service == "weebtv":
            weebTv = weebtvcids.WebbTvStrmUpdater()
            channelInfo = weebTv.getChannel(channel)
        elif service == "goldvod":
            goldVodTv = goldvodcids.GoldVodUpdater()
            channelInfo = goldVodTv.getChannel(channel)
        elif service == "telewizjada":
            telewizja = telewizjadacids.TelewizjaDaUpdater()
            channelInfo = telewizja.getChannel(channel)

        if channelInfo is not None:
            liz = xbmcgui.ListItem(channelInfo.title, iconImage = channelInfo.img, thumbnailImage = channelInfo.img)
            liz.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
            try:
                if channelInfo.premium == 0:
                    msg = Messages()
                    msg.Warning(t(57034).encode('utf-8'), t(57036).encode('utf-8'), t(57037).encode('utf-8'), 'service: %s' % service.encode('utf-8')) # zmienic nazwe serwisu z weeb na service
                xbmc.Player().play(channelInfo.strm, liz, windowed=startWindowed)
                res = True
            except Exception, ex:
                msg = Messages()
                msg.Error(t(57018).encode('utf-8'), t(57021).encode('utf-8'), t(57028).encode('utf-8'), str(ex))

        return res

class Messages:
    def __init__(self):
        pass

    def Error(self, title, text1, text2 = "", text3 = ""):
        dialog = xbmcgui.Dialog()
        dialog.ok(title,"\n\t" +text1 + "\n\t" + text2 + "\n\t" + text3)


    def Warning(self, title, text1, text2 = "", text3 = ""):
        dialog = xbmcgui.Dialog()
        dialog.ok(title,"\n\t" +text1 + "\n\t" + text2 + "\n\t" + text3)
