# -*- coding: utf-8 -*-
import os,sys,xbmcaddon

ptv=xbmcaddon.Addon(sys.modules["__main__"].scriptID)

BASE_RESOURCE_PATH=os.path.join(ptv.getAddonInfo('path'),"../resources")
sys.path.append(os.path.join(BASE_RESOURCE_PATH,"lib"))

import yt_channels,sdParser

SERVICE='youtube_klipy'
MENU_TAB=[
	["ArmadaTV", "armadatv.png", 'UCGZXYc32ri4D0gSLPf2pZXQ'],
	["Asfalt Records", "asfaltrecords.png", 'UCa1UYrU2QHwfNihohSoMyAw'],
	["DIIL.TV", "diiltv.png", 'UCJRT8RpG8V7XDOAWgH41hhA'],
	["KontorTV", "kontortv.png", 'UCb3tJ5NKw7mDxyaQ73mwbRg'],
 	["MyMusic Group", "mymusicgroup.png", 'UCpIzF8rw6XK_z27HBW7tvUQ'],
	["Peja-Slums Attack", "pejaslumsattack.png", 'UCizuLqxCCa5kED4eBpXZHyw'],
	["PROSTOtv", "prostotv.png", 'UCQuSMKcwirmoLvzR4qlKjoQ'],
	["Step Records", "steprecords.png", 'UC0kLTLosqh6GH6L19I-3EgA'],
	["StoprocentTV", "stoprocenttv.png", 'UCunfpuYm_bM4FykPGyVXNRg'],
	["UrbanRecTv", "urbanrectv.png", 'UCgvtcyd8Cc_46jxu4Ejc6dA'],
	["VEVO", "vevo.png", 'UC2pmfLm7iq6Ov1UwYrWYkZA']
]

class YouTubeKlipy:
    def __init__(self):
        self.yt=yt_channels.youtubeChannels(SERVICE,MENU_TAB)
    def handleService(self):
        parser=sdParser.Parser()
        self.yt.handleService(parser.getParams())