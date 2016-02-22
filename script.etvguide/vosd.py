#
#      Copyright (C) 2013 Szakalit
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
import datetime
import threading
import time
import ConfigParser

import xbmc
import xbmcgui
from xbmcgui import Dialog, WindowXMLDialog
from time import mktime
import source as src
from notification import Notification
from strings import *
import re, sys, os
import streaming



ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_UP = 3
ACTION_DOWN = 4
ACTION_PAGE_UP = 5
ACTION_PAGE_DOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ACTION_SHOW_INFO = 11
ACTION_STOP = 13
ACTION_NEXT_ITEM = 14
ACTION_PREV_ITEM = 15


C_MAIN_TITLE = 4920
C_MAIN_TIME = 4921
C_MAIN_DESCRIPTION = 4922
C_MAIN_IMAGE = 4923

ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_MOVE = 107

KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117
KEY_HOME = 159
class VideoOSD(xbmcgui.WindowXMLDialog):


    def __new__(cls, gu):
        return super(VideoOSD, cls).__new__(cls, 'VidOSD.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

    def __init__(self,gu):
        self.gu = gu
        self.isClosing = False
        self.mouseCount = 0
        super(VideoOSD, self).__init__()

    def setControlLabel(self, controlId, label):
        control = self.getControl(controlId)
        if control:
            control.setLabel(label)

    def formatTime(self, timestamp):
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def setControlText(self, controlId, text):
        control = self.getControl(controlId)
        if control:
            control.setText(text)

    def setControlImage(self, controlId, image):
        control = self.getControl(controlId)
        if control:
            control.setImage(image)

    def onInit(self):
        self.mousetime = time.mktime(datetime.datetime.now().timetuple())
        threading.Timer(1, self.waitForPlayBackStopped).start()
        threading.Timer(1, self.waitForMouse).start()

        self.ctrlMainTitle = self.getControl(C_MAIN_TITLE)
        self.ctrlProgramTitle = self.getControl(C_MAIN_TITLE)
        self.ctrlProgramTime = self.getControl(C_MAIN_TIME)
        self.ctrlProgramDesc = self.getControl(C_MAIN_DESCRIPTION)
        self.ctrlProgramLogo = self.getControl(C_MAIN_LOGO)
        self.ctrlProgramImg = self.getControl(C_MAIN_IMAGE)
        self.ctrlMainLive = self.getControl(C_MAIN_LIVE)
        self.ctrlProgramProgress = self.getControl(C_PROGRAM_PROGRESS)

    def setChannel(self, channel):
        self.channel = channel


    def getChannel(self):
        return self.channel


    def onAction(self, action):
        if action.getId() == ACTION_PREVIOUS_MENU:
            self.isClosing = True
            #self.close()

        if action.getId() == 100 or action.getId() == 101 :
            self.isClosing = True

        if action.getId() == ACTION_MOUSE_MOVE:
            self.mouseCount = self.mouseCount + 1
            if self.mouseCount > 4:
                self.mouseCount =  0
                self.mousetime = time.mktime(datetime.datetime.now().timetuple())
                self.refreshControls()


    def refreshControls(self):
        if self.ctrlMainTitle is not None:
            self.ctrlMainTitle.setLabel('[B]%s[/B]' % (self.gu.program.title))
        if self.ctrlProgramTime is not None:
            self.ctrlProgramTime.setLabel('[B]%s - %s[/B]' % (self.formatTime(self.gu.program.startDate), self.formatTime(self.gu.program.endDate)))
        if self.ctrlProgramDesc is not None:
            if self.gu.program.description and self.ctrlProgramDesc:
                self.ctrlProgramDesc.setText(self.gu.program.description)
            else:
                self.ctrlProgramDesc.setText(strings(NO_DESCRIPTION))

        if self.gu.program.channel.logo and self.ctrlProgramLogo:
            self.ctrlProgramLogo.setImage(self.gu.program.channel.logo.encode('utf-8'))

        if self.gu.program.imageSmall is not None and self.ctrlProgramImg:
            self.ctrlProgramImg.setImage(self.gu.program.imageSmall.encode('utf-8'))
        else:
            if self.ctrlProgramImg is not None:
                self.ctrlProgramImg.setImage('tvguide-logo-epg.png')

        if self.gu.program.imageLarge == 'live' and self.ctrlMainLive:
            self.ctrlMainLive.setImage('live.png')
        else:
            if self.ctrlMainLive is not None:
                self.ctrlMainLive.setImage('')

        if self.ctrlProgramProgress:
            self.stdat = time.mktime(self.gu.program.startDate.timetuple())
            self.endat = time.mktime(self.gu.program.endDate.timetuple())
            self.nodat = time.mktime(datetime.datetime.now().timetuple())
            self.per =  100 -  ((self.endat - self.nodat)/ ((self.endat - self.stdat)/100))
            if self.per > 0 and self.per < 100:
                self.ctrlProgramProgress.setVisible(True)
                self.ctrlProgramProgress.setPercent(self.per)
            else:
                self.ctrlProgramProgress.setVisible(False)

    def onClick(self, controlId):
        if controlId == 1000:
            self.isClosing = True
        if controlId == 101:
            self.isClosing = True
            self.gu.onAction2(ACTION_STOP)
        if controlId == 102:
            self.isClosing = True
            self.gu.onAction2(ACTION_SHOW_INFO)
        if controlId == 103:
            self.isClosing = True
            self.gu.onAction2(ACTION_PAGE_DOWN)
        if controlId == 104:
            self.isClosing = True
            self.gu.onAction2(ACTION_PAGE_UP)

    def getControl(self, controlId):
        try:
            return super(VideoOSD, self).getControl(controlId)
        except:
            pass
        return None

    def onPlayBackStopped(self):
        self.close()

    def waitForPlayBackStopped(self):
        while xbmc.Player().isPlaying() and not self.isClosing:
            time.sleep(0.1)

        self.onPlayBackStopped()

    def waitForMouse(self):
        while time.mktime(datetime.datetime.now().timetuple()) < self.mousetime + 2:
            time.sleep(0.1)
        self.isClosing = True

