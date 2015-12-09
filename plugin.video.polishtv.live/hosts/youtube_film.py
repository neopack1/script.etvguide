# -*- coding: utf-8 -*-
import os,sys,xbmcaddon
ptv=xbmcaddon.Addon(sys.modules["__main__"].scriptID)
BASE_RESOURCE_PATH=os.path.join(ptv.getAddonInfo('path'),"../resources")
sys.path.append(os.path.join(BASE_RESOURCE_PATH,"lib"))
import yt_channels,sdParser

SERVICE='youtube_film'
MENU_TAB=[
	["BB Docs", "yt_bbdocs.png", 'UCKwZBaGSGXV1qXKG0lzRUvw'],
	["BB Films", "yt_bbfilms.png", 'UCFdbsw1nIfRAlM8P6OWxANA'],
	["BB Media", "yt_bbmedia.png", 'UCFh_8rlN5NDm98XyYO_oF4g'],
	["Filmoteka", "youtube.png", 'UC3zN76GUZklizARdhVd-jYQ'],
	["Filmowisko", "yt_filmowisko.png", 'UCnCqkAxYvZJVy3vxws_pdgg'],
	["Media Distribution - Bajki dla dzieci", "yt_mediad_bajki.png", 'UCQ2YO3snlAQhdk9NS5_cl2A'],
	["Media Distribution - Filmy", "yt_mediad.png", 'UCpqFtaACYWbQo55tNcEyQ6Q'],
	["Mega Content", "yt_megacontent.png", 'UCoJ3SGh7dhJfB7CIIzQyJ8g'],	
	["Poland Movie Free", "youtube.png", 'UC_uMNN9-B-oFE95fvHUMtbQ'],		
	["Polska Kronika Filmowa", "yt_kronikafilmowa.png", 'UCqH0cdN4omTBTB-8gNJlWNA'],
	["Polski Dokument", "yt_dokumentpolski.jpg", 'UCEfR6Sb5Og6sn_7Cyv4vu5Q'],
	["Polski Film", "yt_filmpolski.jpg", 'UCINDbxkB0AF3lAQV2b_tFVQ'],
#	["Polski Serial", "yt_serialpolski.jpg", 'UCfnSZmJpIhJIjrxX-22yPrA'],
	["PolskiFilmFabularny", "yt_polskifilmfab.png", 'UCe_tR_ZUnM8yTQlXnIIQazw'],
	["Sala kinowa", "yt_salakinowa.png", 'UCMy42eSUu30ULX_VmnxiQLA'],
	["Se-Ma-For", "yt_semafor.png", 'UCl4zoXowxFjf8Bzs4ICruFQ'],
	["Studio Filmowe KADR", "yt_studiokadr.png", 'UCAskl5pFqXmRv33qLaiXR7Q'],
	["Studio Filmowe TOR", "yt_studiotor.png", 'UCalRj86akc7Jr2wLUlOHnqw'],
	["Studio Filmów Rysunkowych", "yt_studiorysunkowych.png", 'UCfXtDCs237pyDFCBIQR46yw'],
	["Studio Miniatur Filmowych", "yt_studiominiatur.png", 'UCCd_I2mXkZ5LcP02cDx1ryw'],
	["Superfilm.pl", "superfilm.png", 'UC7A5iwFhh5dLvo49geBhQ_Q'],
	["[COLOR blue]Język angielski[/COLOR] AmPOP Films", "youtube.png", 'UCRrpZec8AV3R6FL51AvhzMQ'],
	["[COLOR blue]Język angielski[/COLOR] CiNENET", "youtube.png", 'UCfjp6_4aAvhDGzvSkkAo0Jg'],
	["[COLOR blue]Język angielski[/COLOR] Viewster TV", "youtube.png", 'UCSUMyPPmunaDKk0YHxCK-cw'],
	["[COLOR blue]Język niemiecki[/COLOR] History Films TV", "youtube.png", 'UC7zrRpXr4TLfcIPrMIvZtPQ']
#	["Filmy w języku angielskim", "youtube.png", 'SBae7jiISxYlc']
]

class YouTubeFilm:
    def __init__(self):
        self.yt=yt_channels.youtubeChannels(SERVICE,MENU_TAB)
    def handleService(self):
        parser=sdParser.Parser()
        self.yt.handleService(parser.getParams())