# -*- coding: utf-8 -*-
import os,sys,xbmcaddon
ptv=xbmcaddon.Addon(sys.modules["__main__"].scriptID)
BASE_RESOURCE_PATH=os.path.join(ptv.getAddonInfo('path'),"../resources")
sys.path.append(os.path.join(BASE_RESOURCE_PATH,"lib"))
import yt_channels,sdParser

SERVICE='youtube_hit'
MENU_TAB=[
	["5 Sposobów na...", "yt_5sposobow.png", 'UCLcxQ8h1PX3WgLdgnJHcCxg'],
	["Abstrachuje TV", "yt_abstrachuje.png", 'UCTISYi9ABujrrI1Slg3ZDBA'],
	["AdBuster", "yt_adbuster.png", 'UCXoBDsK4B75au2YTC1aLVpg'],
	["Chwytak TV", "yt_chwytak.png", 'UC3AqXmyeOPUPxDchLJ1_BpA'],
	["Cyber Marian", "yt_cyber.png", 'UC2g3uS_ac-9xZr-nZTzPwkA'],
	["Historia Bez Cenzury", "yt_historiabc.png", 'UCRWskElXZvb3q0W5JopPTnQ'],	
	["Matura To Bzdura", "yt_mtb.png", 'UCgwIfE7xkql7bIBRMZNZYLg'],
	["Niekryty Krytyk", "yt_niekryty.png", 'UCura5JPb8QkzXrMfAxq4Ssw'],
	["Polimaty", "yt_polimaty.png", 'UCCRXm_ENFXkMl7_iwERqlrQ'],	
	["Pyta.pl", "yt_pyta.png", 'UCsJ4t5oP5ALRtZq_kweZ2lg'],
	["Ravgor.tv", "yt_ravgor.png", 'UCaK-eFcgZZq3MV31D9gUq5Q'],
	["SA Wardega", "yt_sawardega.png", 'UCdZwMpK-iWqCos46xPscDeg'],	
	["SciFun", "yt_scifun.png", 'UCWTA5Yd0rAkQt5-9etIFoBA'],
	["Fail Army", "yt_failarmy.png", 'UCPDis9pjXuqyI7RYLJ-TTSA'],
	["Simon's Cat", "yt_simonscat.png", 'UCH6vXjt-BA7QHl0KnfL-7RQ']
]

class YouTubeHit:
    def __init__(self):
        self.yt=yt_channels.youtubeChannels(SERVICE,MENU_TAB)
    def handleService(self):
        parser=sdParser.Parser()
        self.yt.handleService(parser.getParams())