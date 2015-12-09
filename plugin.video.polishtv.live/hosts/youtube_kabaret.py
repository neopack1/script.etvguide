# -*- coding: utf-8 -*-
import os,sys,xbmcaddon

ptv=xbmcaddon.Addon(sys.modules["__main__"].scriptID)

BASE_RESOURCE_PATH=os.path.join(ptv.getAddonInfo('path'),"../resources")
sys.path.append(os.path.join(BASE_RESOURCE_PATH,"lib"))

import yt_channels,sdParser

SERVICE='youtube_kabaret'
MENU_TAB=[
	["eKabaret", "yt_ekabaret.png", 'UC7Gq-DyRm0XiB3rXInVq8-g'],
	["Kabaret Ciach", "yt_ciach.png", 'UCh14i3U4QtIIEdX29zccCCA'],
	["Kabaret Czesuaf", "yt_czesuaf.png", 'UCXLt6fVEWculLyQcWH1H3QA'],
	["Kabaret Dno", "yt_kdno.png", 'UC3ETqU0KVhf0UjHV20v6G5g'],
	["Kabaret Jurki", "yt_jurki.png", 'UC27a18Z5SPzf71uueYhDmRw'],
	["Kabaret Neo-Nówka", "yt_neonowka.png", 'UCTrnBUzPGlOVSnCXzP-PhsA'],
	["Kabaret Paranienormalni", "yt_paranienormalni.png", 'UCmWTyuyqLrd_qs9z4g98UvQ'],
	["Kabaret pod Wyrwigroszem ", "yt_podwyrwigroszem.png", 'UCCdUUA1AWAaDJI0py3bDTaA'],
	["Kabaret Skeczów Męczących", "yt_ksm.png", 'UCSuu8FXGa6ahCQEodOhBQUg'],
	["Kabaret Smile", "yt_smile.png", 'UCp5Ce0BwgVGUp5qUDzBatKg'],
	["New Abra TV", "yt_newabra.png", 'UCNRkRe0QSUTJ-hN50FRjf6g'],
]

class YouTubeKabaret:
    def __init__(self):
        self.yt=yt_channels.youtubeChannels(SERVICE,MENU_TAB)
    def handleService(self):
        parser=sdParser.Parser()
        self.yt.handleService(parser.getParams())