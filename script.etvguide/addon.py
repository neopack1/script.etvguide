#
#      Copyright (C) 2014 Krzysztof Cebulski
#      Copyright (C) 2013 Szakalit
#
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import gui
import urllib, urllib2
import re, sys, os
import xbmcaddon, xbmcgui, xbmcplugin, xbmc
from strings import *
import main

class Start:
    def __init__(self):
        self.Run()

    def Play(self, cid, service):
        run = main.InitPlayer()
        run.LoadVideoLink(cid, service)


    def Run(self):
        parser = main.UrlParser()
        params = parser.getParams()
        service = parser.getParam(params, "service")
        cid = parser.getParam(params, "cid")
        if service == None or service == '':
            try:
                w = gui.eTVGuide()
                w.doModal()
                w.close()
                del w
                del xbmc.Player
            except Exception, ex:
                deb('addon.py exception: %s' % str(ex))
        elif service == "weebtv" or service == "goldvod":
            #self.Play(cid, service)
            pass



init = Start()



