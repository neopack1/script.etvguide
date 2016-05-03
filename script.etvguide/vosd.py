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
ACTION_SHOW_UP = 16
ACTION_SHOW_DOWN = 17

C_MAIN_TITLE = 4920
C_MAIN_TIME = 4921
C_MAIN_DESCRIPTION = 4922
C_MAIN_IMAGE = 4923
C_STOP = 101
C_SHOW_INFO = 102
C_PAGE_DOWN = 103
C_PAGE_UP = 104
C_PLAY = 105
C_SETUP = 106
C_SCHEDULE = 107
C_UNSCHEDULE = 108
C_CLOSE_WINDOW = 1000

ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_MOVE = 107

KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117
KEY_HOME = 159
try:
     KEY_STOP = int(ADDON.getSetting('stop_key'))
except:
     KEY_STOP = -1
AUTO_OSD = 666

class VideoOSD(xbmcgui.WindowXMLDialog):
    def __new__(cls, gu, controlledByMouse = True, action = None):
        return super(VideoOSD, cls).__new__(cls, 'VidOSD.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

    def __init__(self, gu, controlledByMouse = True, action = None):
        self.gu = gu
        self.playService = self.gu.epg.playService
        self.isClosing = False
        self.mouseCount = 0
        self.program = self.gu.program
        self.controlledByMouse = controlledByMouse
        self.keyRightLeftChangeProgram = False
        self.showConfigButtons = False
        self.initialized = False
        self.osdDisplayTime = int(ADDON.getSetting('osd_time'))
        if ADDON.getSetting('show_osd_buttons') == 'true':
            self.showConfigButtons = True
        if not self.showConfigButtons and ADDON.getSetting('key_right_left_show_next') == 'true':
            self.keyRightLeftChangeProgram = True

        if action is not None:
            if action == ACTION_UP:
                self.program = self.gu.getProgramUp(self.program)
            elif action == ACTION_DOWN:
                self.program = self.gu.getProgramDown(self.program)
            elif action == ACTION_LEFT:
                self.showPreviousProgram()
            elif action == ACTION_RIGHT:
                self.showNextProgram()
            elif action == AUTO_OSD:
                self.osdDisplayTime = int(ADDON.getSetting('osd_on_play_time'))
            if not self.program:
                self.program = self.gu.getCurrentProgram()
        super(VideoOSD, self).__init__()

    def onInit(self):
        if not self.controlledByMouse:
            closeWindowControl = self.getControl(C_CLOSE_WINDOW)
            closeWindowControl.setVisible(False)
            closeWindowControl.setEnabled(False)
            threading.Timer(1, self.waitForKeyboard).start()
        else:
            threading.Timer(1, self.waitForMouse).start()

        self.playControl = self.getControl(C_PLAY)
        self.stopPlaybackControl = self.getControl(C_STOP)
        self.pageUpControl = self.getControl(C_PAGE_UP)
        self.pageDownControl = self.getControl(C_PAGE_DOWN)
        self.infoControl = self.getControl(C_SHOW_INFO)
        self.setupControl = self.getControl(C_SETUP)
        self.scheduleControl = self.getControl(C_SCHEDULE)
        self.unscheduleControl = self.getControl(C_UNSCHEDULE)

        if self.controlledByMouse or self.showConfigButtons:
            self.infoControl.controlRight(self.setupControl)
            self.setupControl.controlLeft(self.infoControl)
            self.setupControl.controlRight(self.pageDownControl)
            self.pageDownControl.controlLeft(self.setupControl)
            self.pageDownControl.controlRight(self.pageUpControl)
            self.pageUpControl.controlLeft(self.pageDownControl)
            self.stopPlaybackControl.controlLeft(self.pageUpControl)
            self.stopPlaybackControl.controlRight(self.infoControl)
            self.playControl.controlRight(self.infoControl)
            self.playControl.controlLeft(self.pageUpControl)
            self.scheduleControl.controlRight(self.infoControl)
            self.scheduleControl.controlLeft(self.pageUpControl)
            self.unscheduleControl.controlRight(self.infoControl)
            self.unscheduleControl.controlLeft(self.pageUpControl)
        else:
            self.pageUpControl.setVisible(False)
            self.pageDownControl.setVisible(False)
            self.infoControl.setVisible(False)
            self.setupControl.setVisible(False)
            self.pageUpControl.setEnabled(False)
            self.pageDownControl.setEnabled(False)
            self.infoControl.setEnabled(False)
            self.setupControl.setEnabled(False)

        self.playControl.setVisible(False)
        self.stopPlaybackControl.setVisible(False)
        self.scheduleControl.setVisible(False)
        self.stopPlaybackControl.setEnabled(False)
        self.playControl.setEnabled(False)
        self.scheduleControl.setEnabled(False)
        self.unscheduleControl.setVisible(False)
        self.unscheduleControl.setEnabled(False)


        self.ctrlMainTitle = self.getControl(C_MAIN_TITLE)
        self.ctrlProgramTitle = self.getControl(C_MAIN_TITLE)
        self.ctrlProgramTime = self.getControl(C_MAIN_TIME)
        self.ctrlProgramDesc = self.getControl(C_MAIN_DESCRIPTION)
        self.ctrlProgramLogo = self.getControl(C_MAIN_LOGO)
        self.ctrlProgramImg = self.getControl(C_MAIN_IMAGE)
        self.ctrlMainLive = self.getControl(C_MAIN_LIVE)
        self.ctrlProgramProgress = self.getControl(C_PROGRAM_PROGRESS)

        self.mousetime = time.mktime(datetime.datetime.now().timetuple())
        self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())
        threading.Timer(1, self.waitForPlayBackStopped).start()
        self.initialized = True
        self.refreshControls()

    def setControlVisibility(self):
        currentlyPlayedProgram = self.gu.getCurrentProgram()
        timeDiff = self.program.startDate - datetime.datetime.now()
        secToStartProg = (timeDiff.days * 86400) + timeDiff.seconds

        self.playControl.setVisible(False)
        self.stopPlaybackControl.setVisible(False)
        self.scheduleControl.setVisible(False)
        self.unscheduleControl.setVisible(False)
        self.playControl.setEnabled(False)
        self.stopPlaybackControl.setEnabled(False)
        self.scheduleControl.setEnabled(False)
        self.unscheduleControl.setEnabled(False)

        if secToStartProg > 0:
            #Future program, not started yet
            if ADDON.getSetting('notifications.enabled') == 'true':
                if not self.gu.epg.notification.isScheduled(self.program):
                    self.scheduleControl.setVisible(True)
                    self.scheduleControl.setEnabled(True)
                    self.infoControl.controlLeft(self.scheduleControl)
                    self.pageUpControl.controlRight(self.scheduleControl)
                    self.setFocusId(C_SCHEDULE)
                else:
                    self.infoControl.controlLeft(self.unscheduleControl)
                    self.pageUpControl.controlRight(self.unscheduleControl)
                    self.unscheduleControl.setVisible(True)
                    self.unscheduleControl.setEnabled(True)
                    self.setFocusId(C_UNSCHEDULE)
            else:
                self.infoControl.controlLeft(self.pageUpControl)
                self.pageUpControl.controlRight(self.infoControl)
                self.setFocusId(C_PLAY)

        elif not self.controlledByMouse and not (currentlyPlayedProgram.channel.id == self.program.channel.id and currentlyPlayedProgram.startDate == self.program.startDate):
            #Program executed on different channel than currently is on, False if mouse controlled
            self.playControl.setEnabled(True)
            self.playControl.setVisible(True)
            self.infoControl.controlLeft(self.playControl)
            self.pageUpControl.controlRight(self.playControl)
            self.setFocusId(C_PLAY)

        elif self.controlledByMouse or self.showConfigButtons:
            self.stopPlaybackControl.setEnabled(True)
            self.stopPlaybackControl.setVisible(True)
            self.infoControl.controlLeft(self.stopPlaybackControl)
            self.pageUpControl.controlRight(self.stopPlaybackControl)
            self.setFocusId(C_STOP)


    def onAction(self, action):
        self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())

        if action.getId() in [ACTION_PREVIOUS_MENU, KEY_NAV_BACK, ACTION_PARENT_DIR, 100, 101, ACTION_STOP] or action.getButtonCode() == KEY_STOP:
            self.isClosing = True

        elif action.getId() == ACTION_MOUSE_MOVE:
            self.mouseCount = self.mouseCount + 1
            if self.mouseCount > 3:
                self.mouseCount =  0
                self.mousetime = time.mktime(datetime.datetime.now().timetuple())
                self.refreshControls()

        elif self.controlledByMouse:
            return #remaining are for keyboard

        elif (action.getId() == ACTION_UP):
            self.program = self.gu.getProgramUp(self.program)
            self.refreshControls()

        elif (action.getId() == ACTION_DOWN):
            self.program = self.gu.getProgramDown(self.program)
            self.refreshControls()

        elif (action.getId() == ACTION_LEFT):
            if not self.showConfigButtons:
                self.showPreviousProgram()

        elif (action.getId() == ACTION_RIGHT):
            if not self.showConfigButtons:
                self.showNextProgram()

        elif (action.getId() == ACTION_SELECT_ITEM):
            currentlyPlayedProgram = self.gu.getCurrentProgram()
            if not self.showConfigButtons and currentlyPlayedProgram.channel.id == self.program.channel.id and currentlyPlayedProgram.startDate == self.program.startDate:
                self.isClosing = True

    def showNextProgram(self):
        program = self.gu.getProgramRight(self.program)
        if program is not None:
            self.program = program
            self.refreshControls()

    def showPreviousProgram(self):
        program = self.gu.getProgramLeft(self.program)
        if program is not None:
            timeDiff = program.endDate - datetime.datetime.now()
            diffSec = (timeDiff.days * 86400) + timeDiff.seconds
            if diffSec > 0:
                self.program = program
                self.refreshControls()


    def onClick(self, controlId):
        self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())

        if controlId == 1000:
            self.isClosing = True
        elif controlId == C_STOP:
            self.isClosing = True
            self.gu.onAction2(ACTION_STOP)
        elif controlId == C_PLAY:
            self.isClosing = True
            self.gu.playChannel(self.program.channel)
        elif controlId == C_SHOW_INFO:
            #self.isClosing = True
            self.gu.onAction2(ACTION_SHOW_INFO, self.program)
        elif controlId == C_SETUP:
            self.isClosing = True
            xbmc.executebuiltin('ActivateWindow(videoosd)')
        else:
            if self.controlledByMouse:
                self.onClickMouse(controlId)
            else:
                self.onClickKeyboard(controlId)

    def onClickMouse(self, controlId):
        if controlId == C_PAGE_DOWN:
            self.isClosing = True
            self.gu.onAction2(ACTION_PAGE_DOWN)
        elif controlId == C_PAGE_UP:
            self.isClosing = True
            self.gu.onAction2(ACTION_PAGE_UP)

    def onClickKeyboard(self, controlId):
        if controlId == C_PAGE_DOWN:
            self.showPreviousProgram()
            self.setFocusId(C_PAGE_DOWN)
        elif controlId == C_PAGE_UP:
            self.showNextProgram()
            self.setFocusId(C_PAGE_UP)
        elif controlId == C_SCHEDULE:
            if self.gu.epg.notification:
                self.gu.epg.notification.addNotification(self.program, onlyOnce = True)
                self.refreshControls()
        elif controlId == C_UNSCHEDULE:
            if self.gu.epg.notification:
                self.gu.epg.notification.removeNotification(self.program)
                self.refreshControls()

    def refreshControls(self):
        if not self.initialized:
            return
        if self.ctrlMainTitle is not None:
            self.ctrlMainTitle.setLabel('[B]%s[/B]' % (self.program.title))
        if self.ctrlProgramTime is not None:
            self.ctrlProgramTime.setLabel('[B]%s - %s[/B]' % (self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))
        if self.ctrlProgramDesc is not None:
            if self.program.description and self.ctrlProgramDesc:
                self.ctrlProgramDesc.setText(self.program.description)
            else:
                self.ctrlProgramDesc.setText(strings(NO_DESCRIPTION))

        if self.program.channel.logo and self.ctrlProgramLogo:
            self.ctrlProgramLogo.setImage(self.program.channel.logo.encode('utf-8'))

        if self.program.imageSmall is not None and self.ctrlProgramImg:
            self.ctrlProgramImg.setImage(self.program.imageSmall.encode('utf-8'))
        else:
            if self.ctrlProgramImg is not None:
                self.ctrlProgramImg.setImage('tvguide-logo-epg.png')

        if self.program.imageLarge == 'live' and self.ctrlMainLive:
            self.ctrlMainLive.setImage('live.png')
        else:
            if self.ctrlMainLive is not None:
                self.ctrlMainLive.setImage('')

        if self.ctrlProgramProgress:
            self.stdat = time.mktime(self.program.startDate.timetuple())
            self.endat = time.mktime(self.program.endDate.timetuple())
            self.nodat = time.mktime(datetime.datetime.now().timetuple())
            try:
                self.per =  100 -  ((self.endat - self.nodat)/ ((self.endat - self.stdat)/100))
            except:
                self.per = 0
            if self.per > 0 and self.per < 100:
                self.ctrlProgramProgress.setVisible(True)
                self.ctrlProgramProgress.setPercent(self.per)
            else:
                self.ctrlProgramProgress.setVisible(False)

        self.setControlVisibility()

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
        while time.mktime(datetime.datetime.now().timetuple()) < self.mousetime + 2 and not self.isClosing:
            time.sleep(0.1)
        self.isClosing = True

    def waitForKeyboard(self):
        while time.mktime(datetime.datetime.now().timetuple()) < self.keyboardTime + self.osdDisplayTime and not self.isClosing:
            time.sleep(0.1)
        self.isClosing = True

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
