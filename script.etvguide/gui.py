#
#      Copyright (C) 2014 Krzysztof Cebulski
#      Copyright (C) 2013 Szakalit
#
#      Copyright (C) 2013 Tommy Winther

#      http://tommy.winther.nu
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
import vosd
import main
from vosd import VideoOSD

MODE_EPG = 'EPG'
MODE_TV = 'TV'


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

ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_MOVE = 107

KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117
KEY_HOME = 159

config = ConfigParser.RawConfigParser()
config.read(os.path.join(ADDON.getAddonInfo('path'), 'resources', 'skins',ADDON.getSetting('Skin'), 'settings.ini'))
ini_chan = config.getint("Skin", "CHANNELS_PER_PAGE")
ini_info = config.getboolean("Skin", "USE_INFO_DIALOG")

try:
     KEY_INFO = int(ADDON.getSetting('info_key'))
except:
     KEY_INFO = 0
try:
     KEY_STOP = int(ADDON.getSetting('stop_key'))
except:
     KEY_STOP = 0
try:
     KEY_PP = int(ADDON.getSetting('pp_key'))
except:
     KEY_PP = 0
try:
     KEY_PM = int(ADDON.getSetting('pm_key'))
except:
     KEY_PM = 0
try:
     KEY_HOME2 = int(ADDON.getSetting('home_key'))
except:
     KEY_HOME2 = 0

CHANNELS_PER_PAGE = ini_chan

HALF_HOUR = datetime.timedelta(minutes = 30)

class Point(object):
    def __init__(self):
        self.x = self.y = 0

    def __repr__(self):
        return 'Point(x=%d, y=%d)' % (self.x, self.y)

class EPGView(object):
    def __init__(self):
        self.top = self.left = self.right = self.bottom = self.width = self.cellHeight = 0

class ControlAndProgram(object):
    def __init__(self, control, program):
        self.control = control
        self.program = program

class Event:
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    def getHandlerCount(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__  = getHandlerCount

class VideoPlayerStateChange(xbmc.Player):

    def __init__(self, *args, **kwargs):
        deb ( "################ Starting control VideoPlayer events" )
        self.playerStateChanged = Event()
        self.sleepSupervisor = SleepSupervisor()
        #threading.Timer(0.3, self.fixstop).start()

    def stopplaying(self):
        self.Stop()

    def onStateChange(self, state):
        self.playerStateChanged(state)

    def onPlayBackPaused(self):
        deb ( "################ Im paused" )
        self.playerStateChanged("Paused")
        #threading.Timer(0.3, self.stopplaying).start()

    def onPlayBackResumed(self):
        deb ( "################ Im Resumed" )
        self.onStateChange("Resumed")

    def onPlayBackStarted(self):
        deb ( "################ Playback Started" )
        self.sleepSupervisor.Start()
        self.onStateChange("Started")

    def onPlayBackEnded(self):
        deb ("################# Playback Ended")
        self.onStateChange("Ended")

    def onPlayBackStopped(self):
        deb( "################# Playback Stopped")
        self.sleepSupervisor.Stop()
        self.onStateChange("Stopped")

class eTVGuide(xbmcgui.WindowXML):
    C_MAIN_DATE = 4000

    C_MAIN_TIMEBAR = 4100
    C_MAIN_LOADING = 4200
    C_MAIN_LOADING_PROGRESS = 4201
    C_MAIN_LOADING_TIME_LEFT = 4202
    C_MAIN_LOADING_CANCEL = 4203
    C_MAIN_MOUSEPANEL_CONTROLS = 4300
    C_MAIN_MOUSEPANEL_HOME = 4301
    C_MAIN_MOUSEPANEL_EPG_PAGE_LEFT = 4302
    C_MAIN_MOUSEPANEL_EPG_PAGE_UP = 4303
    C_MAIN_MOUSEPANEL_EPG_PAGE_DOWN = 4304
    C_MAIN_MOUSEPANEL_EPG_PAGE_RIGHT = 4305
    C_MAIN_MOUSEPANEL_EXIT = 4306
    C_MAIN_MOUSEPANEL_CURSOR_UP = 4307
    C_MAIN_MOUSEPANEL_CURSOR_DOWN = 4308
    C_MAIN_MOUSEPANEL_CURSOR_LEFT = 4309
    C_MAIN_MOUSEPANEL_CURSOR_RIGHT = 4310
    C_MAIN_MOUSEPANEL_SETTINGS = 4311

    C_MAIN_BACKGROUND = 4600
    C_MAIN_EPG = 5000
    C_MAIN_EPG_VIEW_MARKER = 5001
    C_MAIN_INFO = 7000
    C_MAIN_LIVE = 4944

    def __new__(cls):
        return super(eTVGuide, cls).__new__(cls, 'script-tvguide-main.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

    def __init__(self):
        deb('eTVGuide __init__')
        super(eTVGuide, self).__init__()
        self.initialized = False
        self.notification = None
        self.redrawingEPG = False
        self.isClosing = False
        self.controlAndProgramList = list()
        self.ignoreMissingControlIds = list()
        self.channelIdx = 0
        self.focusPoint = Point()
        self.epgView = EPGView()
        self.streamingService = streaming.StreamsService()
        self.player = xbmc.Player()
        self.database = None
        self.redrawagain = False
        self.info = False
        self.oldchan = 0
        self.a = {}


        self.mode = MODE_EPG
        self.currentChannel = None

        # find nearest half hour
        self.viewStartDate = datetime.datetime.today()
        self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)

        # monitorowanie zmiany stanu odtwarzacza
        threading.Timer(0.3, self.playerstate).start()

    def playerstate(self):
        vp = VideoPlayerStateChange()
        vp.playerStateChanged += self.onPlayerStateChanged
        while not self.isClosing:
            xbmc.sleep(300)
        return

    def onPlayerStateChanged(self, pstate):
        deb("########### onPlayerStateChanged %s %s" % (pstate, ADDON.getSetting('info.osd')))
        if (pstate == "Stopped" or pstate == "Ended" or pstate == "Paused" or pstate == "Resumed"):
            self._showEPG()
        else:
            self._hideEpg()

    def getControl(self, controlId):
        #deb('getControl')
        try:
            return super(eTVGuide, self).getControl(controlId)
        except:
            if controlId in self.ignoreMissingControlIds:
                return None
            if not self.isClosing:
                self.close()
        return None

    def close(self):
        deb('close')
        if not self.isClosing:
            self.isClosing = True
            if self.player.isPlaying():
                self.player.stop()
            if self.database:
                self.database.close(super(eTVGuide, self).close)
            else:
                super(eTVGuide, self).close()
            self._clearEpg()

    def onInit(self):
        deb('onInit')
        if self.initialized:
            # onInit(..) is invoked again by XBMC after a video addon exits after being invoked by XBMC.RunPlugin(..)
            deb("[%s] TVGuide.onInit(..) invoked, but we're already initialized!" % ADDON_ID)
            self.redrawagain = True
            deb('redrawagain')
            #if self.redrawingEPG == False:
                #self.redrawagain = False
                #xbmc.log('redrawagain 2 channel %s' % self.channelIdx )
                #self.onRedrawEPG(self.channelIdx, self.viewStartDate)


            return
        self.initialized = True
        self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
        self._showControl(self.C_MAIN_EPG, self.C_MAIN_LOADING)
        self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(BACKGROUND_UPDATE_IN_PROGRESS))
        self.setFocusId(self.C_MAIN_LOADING_CANCEL)

        control = self.getControl(self.C_MAIN_EPG_VIEW_MARKER)
        if control:
            left, top = control.getPosition()
            self.focusPoint.x = left
            self.focusPoint.y = top
            self.epgView.left = left
            self.epgView.top = top
            self.epgView.right = left + control.getWidth()
            self.epgView.bottom = top + control.getHeight()
            self.epgView.width = control.getWidth()
            self.epgView.cellHeight = control.getHeight() / CHANNELS_PER_PAGE

        try:
            self.database = src.Database()
        except src.SourceNotConfiguredException:
            self.onSourceNotConfigured()
            self.close()
            return
        self.database.initialize(self.onSourceInitialized, self.isSourceInitializationCancelled)
        self.updateTimebar()

    def Info(self, program):
        deb('Info')
        info = InfoDialog(program)
        info.setChannel(program)
        info.doModal()
        del info

    def onAction(self, action):
        #deb('onAction')
        #deb('Mode is: %s' % self.mode)

        if self.mode == MODE_TV:
            self.onActionTVMode(action)
        elif self.mode == MODE_EPG:
            self.onActionEPGMode(action)

    def onActionTVMode(self, action):
        deb('onActionTVMode')
        if action.getId() == ACTION_PAGE_UP:
            self._channelUp()

        elif action.getId() == ACTION_PAGE_DOWN:
            self._channelDown()

        elif action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, KEY_CONTEXT_MENU, ACTION_PREVIOUS_MENU]:
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)


    def onActionEPGMode(self, action):
        #deb('onActionEPGMode')
        if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            self.close()
            return

        elif action.getId() == ACTION_MOUSE_MOVE:
            if ADDON.getSetting('pokazpanel') == 'true':
                self._showControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
            return

        elif action.getId() == ACTION_SHOW_INFO or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0) or (action.getId() == KEY_INFO and KEY_INFO != 0):
            if not ini_info:
                return
            try:
                controlInFocus = self.getFocus()
                program = self._getProgramFromControl(controlInFocus)
                if program is not None:
                    self.Info(program)
            except:
                pass
            return

        elif action.getId() == KEY_CONTEXT_MENU:
            if self.player.isPlaying():
                self._hideEpg()

        controlInFocus = None
        currentFocus = self.focusPoint
        try:
            controlInFocus = self.getFocus()
            if controlInFocus in [elem.control for elem in self.controlAndProgramList]:
                (left, top) = controlInFocus.getPosition()
                currentFocus = Point()
                currentFocus.x = left + (controlInFocus.getWidth() / 2)
                currentFocus.y = top + (controlInFocus.getHeight() / 2)
        except Exception:
            control = self._findControlAt(self.focusPoint)
            if control is None and len(self.controlAndProgramList) > 0:
                control = self.controlAndProgramList[0].control
            if control is not None:
                self.setFocus(control)
                if action.getId() == ACTION_MOUSE_WHEEL_UP:
                    pass
                elif action.getId() == ACTION_MOUSE_WHEEL_DOWN:
                    pass
                else:
                    return

        if action.getId() == ACTION_LEFT:
            self._left(currentFocus)
        elif action.getId() == ACTION_RIGHT:
            self._right(currentFocus)
        elif action.getId() == ACTION_UP:
            self._up(currentFocus)
        elif action.getId() == ACTION_DOWN:
            self._down(currentFocus)
        elif action.getId() == ACTION_NEXT_ITEM:
            self._nextDay()
        elif action.getId() == ACTION_PREV_ITEM:
            self._previousDay()
        elif action.getId() == ACTION_PAGE_UP:
            self._moveUp(CHANNELS_PER_PAGE)
        elif action.getId() == ACTION_PAGE_DOWN:
            self._moveDown(CHANNELS_PER_PAGE)
        elif action.getId() == ACTION_MOUSE_WHEEL_UP:
            self._moveUp(scrollEvent = True)
        elif action.getId() == ACTION_MOUSE_WHEEL_DOWN:
            self._moveDown(scrollEvent = True)
        elif action.getId() == KEY_HOME or (action.getButtonCode() == KEY_HOME2 and KEY_HOME2 != 0) or (action.getId() == KEY_HOME2 and KEY_HOME2 != 0):
            self.viewStartDate = datetime.datetime.today()
            self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        elif action.getId() in [KEY_CONTEXT_MENU] and controlInFocus is not None:
            program = self._getProgramFromControl(controlInFocus)
            if program is not None:
                self._showContextMenu(program)



    def onClick(self, controlId):
        deb('onClick')
        channel = None
        if controlId in [self.C_MAIN_LOADING_CANCEL, self.C_MAIN_MOUSEPANEL_EXIT]:
            self.close()
            return

        if self.isClosing:
            return

        if controlId == self.C_MAIN_MOUSEPANEL_HOME:
            self.viewStartDate = datetime.datetime.today()
            self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_LEFT:
            self.viewStartDate -= datetime.timedelta(hours = 2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_UP:
            self._moveUp(count = CHANNELS_PER_PAGE)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_DOWN:
            self._moveDown(count = CHANNELS_PER_PAGE)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_RIGHT:
            self.viewStartDate += datetime.timedelta(hours = 2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_UP:
            self._moveUp(scrollEvent = True)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_DOWN:
            self._moveDown(scrollEvent = True)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_RIGHT:
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_LEFT:
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_SETTINGS:
             xbmcaddon.Addon(id=ADDON_ID).openSettings()
             return
        elif controlId >= 9010 and controlId <= 9021:
            o = controlId - 9010
            channel = self.a[o]

        if channel is not None:
            if not self.playChannel(channel):
                result = self.streamingService.detectStream(channel)
                if not result:
                    return
                elif type(result) == str:
                    # one single stream detected, save it and start streaming
                    self.database.setCustomStreamUrl(channel, result)
                    self.playChannel(channel)

                else:
                    # multiple matches, let user decide

                    d = ChooseStreamAddonDialog(result)
                    d.doModal()
                    if d.stream is not None:
                        self.database.setCustomStreamUrl(channel, d.stream)
                        self.playChannel(channel)
            return


        program = self._getProgramFromControl(self.getControl(controlId))
        if program is None:

            return

        #self.channelIdx = program.channel
        if ADDON.getSetting('info.osd') == "true":

            if not self.playChannel2(program):
                result = self.streamingService.detectStream(program.channel)
                if not result:
                    # could not detect stream, show context menu
                    self._showContextMenu(program)
                elif type(result) == str:
                    # one single stream detected, save it and start streaming
                    self.database.setCustomStreamUrl(program.channel, result)
                    self.playChannel2(program)

                else:
                    # multiple matches, let user decide

                    d = ChooseStreamAddonDialog(result)
                    d.doModal()
                    if d.stream is not None:
                        self.database.setCustomStreamUrl(program.channel, d.stream)
                        self.playChannel2(program)

        else:
            if not self.playChannel(program.channel):
                result = self.streamingService.detectStream(program.channel)
                if not result:
                    # could not detect stream, show context menu
                    self._showContextMenu(program)
                elif type(result) == str:
                    # one single stream detected, save it and start streaming
                    self.database.setCustomStreamUrl(program.channel, result)
                    self.playChannel(program.channel)

                else:
                    # multiple matches, let user decide

                    d = ChooseStreamAddonDialog(result)
                    d.doModal()
                    if d.stream is not None:
                        self.database.setCustomStreamUrl(program.channel, d.stream)
                        self.playChannel(program.channel)







    def _showContextMenu(self, program):
        deb('_showContextMenu')
        self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
        d = PopupMenu(self.database, program, not program.notificationScheduled)
        d.doModal()
        buttonClicked = d.buttonClicked
        del d

        if buttonClicked == PopupMenu.C_POPUP_REMIND:
            if program.notificationScheduled:
                self.notification.removeNotification(program)
            else:
                self.notification.addNotification(program)

            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

        elif buttonClicked == PopupMenu.C_POPUP_CHOOSE_STREAM:
            d = StreamSetupDialog(self.database, program.channel)
            d.doModal()
            del d

        elif buttonClicked == PopupMenu.C_POPUP_PLAY:
            self.playChannel(program.channel)

        elif buttonClicked == PopupMenu.C_POPUP_CHANNELS:
            d = ChannelsMenu(self.database)
            d.doModal()
            del d
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

        elif buttonClicked == PopupMenu.C_POPUP_QUIT:
            self.close()

        elif buttonClicked == PopupMenu.C_POPUP_ADDON_SETTINGS:
            xbmcaddon.Addon(id=ADDON_ID).openSettings()

    def setFocusId(self, controlId):
        deb('setFocusId')
        control = self.getControl(controlId)
        if control:
            self.setFocus(control)

    def setFocus(self, control):
        deb('setFocus')
        deb('setFocus %d' % control.getId())
        if control in [elem.control for elem in self.controlAndProgramList]:
            deb('Focus before %s' % self.focusPoint)
            (left, top) = control.getPosition()
            if left > self.focusPoint.x or left + control.getWidth() < self.focusPoint.x:
                self.focusPoint.x = left
            self.focusPoint.y = top + (control.getHeight() / 2)
            deb('New focus at %s' % self.focusPoint)

        super(eTVGuide, self).setFocus(control)


    def onFocus(self, controlId):
        deb('onFocus controlId : %s' % controlId)
        try:
            controlInFocus = self.getControl(controlId)
        except Exception:
            return

        program = self._getProgramFromControl(controlInFocus)
        if program is None:
            return

        self.setControlLabel(C_MAIN_TITLE, '[B]%s[/B]' % (program.title))
        self.setControlLabel(C_MAIN_TIME, '[B]%s - %s[/B]' % (self.formatTime(program.startDate), self.formatTime(program.endDate)))
        if program.description:
            description = program.description
        else:
            description = strings(NO_DESCRIPTION)
        self.setControlText(C_MAIN_DESCRIPTION, description)

        if program.channel.logo is not None:
            self.setControlImage(C_MAIN_LOGO, program.channel.logo)
        if program.imageSmall is not None:
            self.setControlImage(C_MAIN_IMAGE, program.imageSmall)
        if program.imageSmall is None:
            self.setControlImage(C_MAIN_IMAGE, 'tvguide-logo-epg.png')
        if program.imageLarge == 'live':
            self.setControlImage(C_MAIN_LIVE, 'live.png')
        else:
            self.setControlImage(C_MAIN_LIVE, '')

    def _left(self, currentFocus):
        deb('_left')
        control = self._findControlOnLeft(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.viewStartDate -= datetime.timedelta(hours = 2)
            self.focusPoint.x = self.epgView.right
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnLeft)

    def _right(self, currentFocus):
        deb('_right')
        control = self._findControlOnRight(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.viewStartDate += datetime.timedelta(hours = 2)
            self.focusPoint.x = self.epgView.left
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnRight)

    def _up(self, currentFocus):
        deb('_up')
        currentFocus.x = self.focusPoint.x
        control = self._findControlAbove(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx - CHANNELS_PER_PAGE, self.viewStartDate, focusFunction=self._findControlAbove)

    def _down(self, currentFocus):
        deb('_down')
        currentFocus.x = self.focusPoint.x
        control = self._findControlBelow(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx + CHANNELS_PER_PAGE, self.viewStartDate, focusFunction=self._findControlBelow)

    def _nextDay(self):
        deb('_nextDay')
        self.viewStartDate += datetime.timedelta(days = 1)
        self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def _previousDay(self):
        deb('_previousDay')
        self.viewStartDate -= datetime.timedelta(days = 1)
        self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def _moveUp(self, count = 1, scrollEvent = False):
        deb('_moveUp')
        if scrollEvent:
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate)
        else:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate, focusFunction = self._findControlAbove)

    def _moveDown(self, count = 1, scrollEvent = False):
        deb('_moveDown')
        if scrollEvent:
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate)
        else:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate, focusFunction=self._findControlBelow)

    def _channelUp(self):
        channel = self.database.getNextChannel(self.currentChannel)
        self.playChannel2(self.database.getCurrentProgram(channel))

    def _channelDown(self):
        channel = self.database.getPreviousChannel(self.currentChannel)
        self.playChannel2(self.database.getCurrentProgram(channel))

    def playChannel2(self, program):
        deb('playChannel2')
        self.program = program
        self.currentChannel = program.channel
        url = self.database.getStreamUrl(program.channel)
        self.oldchan = self.database.getCurrentChannelIdx(program.channel)
        if url:
            if url[-5:] == '.strm':
                try:
                    f = open(url)
                    content = f.read()
                    f.close()

                    if content[0:9] == 'plugin://':
                        url = content.strip()
                except:
                    pass
            lo = Pla(self.program, self.database, url, self)
            lo.doModal()
            lo.close()
            del lo
            if self.oldchan != self.database.getCurrentChannelIdx(self.currentChannel):
                if not self.player.isPlaying() and not self.isClosing:
                    self.viewStartDate = datetime.datetime.today()
                    self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)
                    self.onRedrawEPG(self.database.getCurrentChannelIdx(self.currentChannel), self.viewStartDate)
        #self.onPlayBackStopped()
        return url is not None


    def playChannel(self, channel):
        deb('playChannel')
        self.currentChannel = channel
        wasPlaying = self.player.isPlaying()
        url = self.database.getStreamUrl(channel)
        if url:
            if url[-5:] == '.strm':
                try:
                    f = open(url)
                    content = f.read()
                    f.close()

                    if content[0:9] == 'plugin://':
                        url = content.strip()
                except:
                    pass

            if url[0:9] == 'plugin://':
                xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
            elif url[0:7] == 'service':
                playService(url)
                #xbmc.executebuiltin('XBMC.RunScript(%s,%s,0)' % (ADDON_ID, url))
            else:
                self.player.play(item = url)



            #if not wasPlaying:
                #self._hideEpg()

        #threading.Timer(1, self.waitForPlayBackStopped).start()


        return url is not None

    def waitForPlayBackStopped(self):
        deb('waitForPlayBackStopped')
        for retry in range(0, 100):
            time.sleep(0.1)
            if self.player.isPlaying():
                break

        while self.player.isPlaying() and not xbmc.abortRequested and not self.isClosing:
            time.sleep(0.5)

        self.onPlayBackStopped()

    def _hideEpg(self):
        deb('_hideEpg')
        self._hideControl(self.C_MAIN_EPG)
        self.mode = MODE_TV
        self._clearEpg()

    def _showEPG(self):
        deb('_showEpg')

        #aktualna godzina!
        self.viewStartDate = datetime.datetime.today()
        self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)

        #przerysuj tylko wtedy gdy nie bylo epg! jak jest to nie przerysowuj - nie ustawi sie wtedy na aktualnej godzienie!
        if (self.mode == MODE_TV):
            self.onRedrawEPG(self.channelIdx, self.viewStartDate) #przerysuj

    def onRedrawEPG(self, channelStart, startTime, focusFunction = None):
        deb('onRedrawEPG')
        if self.redrawingEPG or (self.database is not None and self.database.updateInProgress) or self.isClosing:
            deb('onRedrawEPG - already redrawing')
            return # ignore redraw request while redrawing

        self.redrawingEPG = True
        self.mode = MODE_EPG
        self._showControl(self.C_MAIN_EPG)
        self.updateTimebar(scheduleTimer = False)

        # show Loading screen
        self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(CALCULATING_REMAINING_TIME))
        self._showControl(self.C_MAIN_LOADING)
        self.setFocusId(self.C_MAIN_LOADING_CANCEL)

        # remove existing controls
        self._clearEpg()
        try:
            self.channelIdx, channels, programs = self.database.getEPGView(channelStart, startTime, self.onSourceProgressUpdate, clearExistingProgramList = True)
        except src.SourceException:
            self.onEPGLoadError()
            return

        # date and time row
        self.setControlLabel(self.C_MAIN_DATE, self.formatDate(self.viewStartDate))
        for col in range(1, 5):
            self.setControlLabel(4000 + col, self.formatTime(startTime))
            startTime += HALF_HOUR

        if programs is None:
            self.onEPGLoadError()
            return

        # set channel logo or text
        for idx in range(0, CHANNELS_PER_PAGE):
            if idx >= len(channels):
                self.setControlImage(4110 + idx, ' ')
                self.setControlLabel(4010 + idx, ' ')
            else:
                channel = channels[idx]
                self.setControlLabel(4010 + idx, channel.title)
                if channel.logo is not None:
                    self.setControlImage(4110 + idx, channel.logo)
                else:
                    self.setControlImage(4110 + idx, ' ')

                self.a[idx] = channel

        for program in programs:
            idx = channels.index(program.channel)

            startDelta = program.startDate - self.viewStartDate
            stopDelta = program.endDate - self.viewStartDate

            cellStart = self._secondsToXposition(startDelta.seconds)
            if startDelta.days < 0:
                cellStart = self.epgView.left
            cellWidth = self._secondsToXposition(stopDelta.seconds) - cellStart
            if cellStart + cellWidth > self.epgView.right:
                cellWidth = self.epgView.right - cellStart
            if cellWidth > 1:

                if program.categoryA == "Filmy":
                    if ADDON.getSetting('kolor.Filmy') == '':
						noFocusTexture = "default.png"
                    else:
						noFocusTexture = ADDON.getSetting('kolor.Filmy')+'.png'
                elif program.categoryA == "Seriale":
                    if ADDON.getSetting('kolor.Seriale') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.Seriale')+'.png'
                elif program.categoryA == "Informacja":
                    if ADDON.getSetting('kolor.Informacja') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.Informacja')+'.png'
                elif program.categoryA == "Rozrywka":
                    if ADDON.getSetting('kolor.Rozrywka') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.Rozrywka')+'.png'
                elif program.categoryA == "Dokument":
                    if ADDON.getSetting('kolor.Dokument') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.Dokument')+'.png'
                elif program.categoryA == "Dla dzieci":
                    if ADDON.getSetting('kolor.Dladzieci') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.Dladzieci')+'.png'
                elif program.categoryA == "Sport":
                    if ADDON.getSetting('kolor.Sport') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.Sport')+'.png'
                elif program.categoryA == "Interaktywny Program Rozrywkowy":
                    if ADDON.getSetting('kolor.InteraktywnyProgramRozrywkowy') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.InteraktywnyProgramRozrywkowy')+'.png'
                else:
                    if ADDON.getSetting('kolor.default') == '':
						noFocusTexture = 'default.png'
                    else:
						noFocusTexture = ADDON.getSetting('kolor.default')+'.png'


                if program.notificationScheduled:
                    noFocusTexture = ADDON.getSetting('kolor.notification')+'.png'

                focusTexture = ADDON.getSetting('kolor.defaultfocus')+'.png'

                if cellWidth < 25:
                    title = '' # Text will overflow outside the button if it is too narrow
                else:
                    title = program.title

                control = xbmcgui.ControlButton(
                    cellStart,
                    self.epgView.top + self.epgView.cellHeight * idx,
                    cellWidth - 2,
                    self.epgView.cellHeight - 2,
                    title,
                    noFocusTexture = noFocusTexture,
                    focusTexture = focusTexture
                )

                self.controlAndProgramList.append(ControlAndProgram(control, program))
        # add program controls
        if focusFunction is None:
            focusFunction = self._findControlAt
        focusControl = focusFunction(self.focusPoint)
        controls = [elem.control for elem in self.controlAndProgramList]
        self.addControls(controls)
        if focusControl is not None:
            deb('onRedrawEPG - setFocus %d' % focusControl.getId())
            self.setFocus(focusControl)
        self.ignoreMissingControlIds.extend([elem.control.getId() for elem in self.controlAndProgramList])
        if focusControl is None and len(self.controlAndProgramList) > 0:
            self.setFocus(self.controlAndProgramList[0].control)
        self._hideControl(self.C_MAIN_LOADING)
        self.redrawingEPG = False
        if self.redrawagain:
            self.redrawagain = False
            self.onRedrawEPG(channelStart, self.viewStartDate, focusFunction)

    def _clearEpg(self):
        deb('_clearEpg')
        controls = [elem.control for elem in self.controlAndProgramList]
        try:
            self.removeControls(controls)
        except RuntimeError:
            for elem in self.controlAndProgramList:
                try:
                    self.removeControl(elem.control)
                except RuntimeError:
                    pass # happens if we try to remove a control that doesn't exist
        del self.controlAndProgramList[:]

    def onEPGLoadError(self):
        deb('')
        self.redrawingEPG = False
        self._hideControl(self.C_MAIN_LOADING)
        xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1), strings(LOAD_ERROR_LINE2))
        self.close()

    def onSourceNotConfigured(self):
        deb('onSourceNotConfigured')
        self.redrawingEPG = False
        self._hideControl(self.C_MAIN_LOADING)
        xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1), strings(CONFIGURATION_ERROR_LINE2))
        self.close()

    def isSourceInitializationCancelled(self):
        deb('isSourceInitializationCancelled')
        return xbmc.abortRequested or self.isClosing

    def onSourceInitialized(self, success):
        deb('onSourceInitialized')
        if success:
            self.notification = Notification(self.database, ADDON.getAddonInfo('path'))
            self.onRedrawEPG(0, self.viewStartDate)

    def onSourceProgressUpdate(self, percentageComplete):
        deb('onSourceProgressUpdate')
        control = self.getControl(self.C_MAIN_LOADING_PROGRESS)
        if percentageComplete < 1:
            if control:
                control.setPercent(1)
            self.progressStartTime = datetime.datetime.now()
            self.progressPreviousPercentage = percentageComplete
        elif percentageComplete != self.progressPreviousPercentage:
            if control:
                control.setPercent(percentageComplete)
            self.progressPreviousPercentage = percentageComplete
            delta = datetime.datetime.now() - self.progressStartTime

            if percentageComplete < 20:
                self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(CALCULATING_REMAINING_TIME))
            else:
                secondsLeft = int(delta.seconds) / float(percentageComplete) * (100.0 - percentageComplete)
                if secondsLeft > 30:
                    secondsLeft -= secondsLeft % 10
                self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(TIME_LEFT) % secondsLeft)

        return not xbmc.abortRequested and not self.isClosing

    def onPlayBackStopped(self):
        deb('onPlayBackStopped')
        if not self.player.isPlaying() and not self.isClosing:
            self.viewStartDate = datetime.datetime.today()
            self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def _secondsToXposition(self, seconds):
        #deb('_secondsToXposition')
        return self.epgView.left + (seconds * self.epgView.width / 7200)

    def _findControlOnRight(self, point):
        deb('_findControlOnRight')
        distanceToNearest = 10000
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            x = left + (control.getWidth() / 2)
            y = top + (control.getHeight() / 2)

            if point.x < x and point.y == y:
                distance = abs(point.x - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        return nearestControl


    def _findControlOnLeft(self, point):
        deb('_findControlOnLeft')
        distanceToNearest = 10000
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            x = left + (control.getWidth() / 2)
            y = top + (control.getHeight() / 2)

            if point.x > x and point.y == y:
                distance = abs(point.x - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        return nearestControl

    def _findControlBelow(self, point):
        deb('_findControlBelow')
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if point.y < y:
                rightEdge = leftEdge + control.getWidth()
                if(leftEdge <= point.x < rightEdge
                   and (nearestControl is None or nearestControl.getPosition()[1] > top)):
                    nearestControl = control

        return nearestControl

    def _findControlAbove(self, point):
        deb('_findControlAbove')
        nearestControl = None
        for elem in self.controlAndProgramList:
            control = elem.control
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if point.y > y:
                rightEdge = leftEdge + control.getWidth()
                if(leftEdge <= point.x < rightEdge
                   and (nearestControl is None or nearestControl.getPosition()[1] < top)):
                    nearestControl = control

        return nearestControl

    def _findControlAt(self, point):
        deb('_findControlAt')
        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            bottom = top + control.getHeight()
            right = left + control.getWidth()

            if left <= point.x <= right and  top <= point.y <= bottom:
                return control

        return None

    def _getProgramFromControl(self, control):
        deb('_getProgramFromControl')
        try:
            for elem in self.controlAndProgramList:
                if elem.control == control:
                    return elem.program
        except Exception, ex:
            deb('_getProgramFromControl Error: %s' % str(ex))
            raise
        return None

    def _hideControl(self, *controlIds):
        deb('_hideControl')
        """
        Visibility is inverted in skin
        """
        for controlId in controlIds:
            control = self.getControl(controlId)
            if control:
                control.setVisible(True)

    def _showControl(self, *controlIds):
        deb('_showControl')
        """
        Visibility is inverted in skin
        """
        for controlId in controlIds:
            control = self.getControl(controlId)
            if control:
                control.setVisible(False)

    def formatTime(self, timestamp):
        deb('formatTime')
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def formatDate(self, timestamp):
        deb('formatDate')
        format = xbmc.getRegion('dateshort')
        return timestamp.strftime(format)

    def setControlImage(self, controlId, image):
        deb('setControlImage')
        control = self.getControl(controlId)
        if control:
            control.setImage(image.encode('utf-8'))

    def setControlLabel(self, controlId, label):
        deb('setControlLabel')
        control = self.getControl(controlId)
        if control:
            control.setLabel(label)

    def setControlText(self, controlId, text):
        deb('setControlText')
        control = self.getControl(controlId)
        if control:
            control.setText(text)


    def updateTimebar(self, scheduleTimer = True):
        #deb('updateTimebar')
        try:
            # move timebar to current time
            timeDelta = datetime.datetime.today() - self.viewStartDate
            control = self.getControl(self.C_MAIN_TIMEBAR)
            if control:
                (x, y) = control.getPosition()
                try:
                    # Sometimes raises:
                    # exceptions.RuntimeError: Unknown exception thrown from the call "setVisible"
                    control.setVisible(timeDelta.days == 0)
                except:
                    pass
                control.setPosition(self._secondsToXposition(timeDelta.seconds), y)

            if scheduleTimer and not xbmc.abortRequested and not self.isClosing:
                threading.Timer(1, self.updateTimebar).start()
        except Exception:
            pass


class PopupMenu(xbmcgui.WindowXMLDialog):
    C_POPUP_PLAY = 4000
    C_POPUP_CHOOSE_STREAM = 4001
    C_POPUP_REMIND = 4002
    C_POPUP_CHANNELS = 4003
    C_POPUP_QUIT = 4004
    C_POPUP_CHANNEL_LOGO = 4100
    C_POPUP_CHANNEL_TITLE = 4101
    C_POPUP_PROGRAM_TITLE = 4102
    C_POPUP_PROGRAM_TIME_RANGE = 4103
    C_POPUP_ADDON_SETTINGS = 4110

    LABEL_CHOOSE_STRM = CHOOSE_STRM_FILE

    def __new__(cls, database, program, showRemind):
        return super(PopupMenu, cls).__new__(cls, 'script-tvguide-menu.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

    def __init__(self, database, program, showRemind):
        """

        @type database: source.Database
        @param program:
        @type program: source.Program
        @param showRemind:
        """
        super(PopupMenu, self).__init__()
        self.database = database
        self.program = program
        self.showRemind = showRemind
        self.buttonClicked = None


    def onInit(self):
        playControl = self.getControl(self.C_POPUP_PLAY)
        remindControl = self.getControl(self.C_POPUP_REMIND)
        channelLogoControl = self.getControl(self.C_POPUP_CHANNEL_LOGO)
        channelTitleControl = self.getControl(self.C_POPUP_CHANNEL_TITLE)
        programTitleControl = self.getControl(self.C_POPUP_PROGRAM_TITLE)
        chooseStrmControl = self.getControl(self.C_POPUP_CHOOSE_STREAM)
        programTimeRangeControl = self.getControl(self.C_POPUP_PROGRAM_TIME_RANGE)

        playControl.setLabel(strings(WATCH_CHANNEL, self.program.channel.title))
        if not self.program.channel.isPlayable():
            playControl.setEnabled(False)
            self.setFocusId(self.C_POPUP_CHOOSE_STREAM)

        self.LABEL_CHOOSE_STRM = getStateLabel(chooseStrmControl, 0, CHOOSE_STRM_FILE)
        LABEL_REMOVE_STRM = getStateLabel(chooseStrmControl, 1, REMOVE_STRM_FILE)
        LABEL_REMIND      = getStateLabel(remindControl,     0, REMIND_PROGRAM)
        LABEL_DONT_REMIND = getStateLabel(remindControl,     1, DONT_REMIND_PROGRAM)

        if self.database.getCustomStreamUrl(self.program.channel):
            chooseStrmControl.setLabel(strings(LABEL_REMOVE_STRM))
        else:
            chooseStrmControl.setLabel(strings(self.LABEL_CHOOSE_STRM))

        if self.program.channel.logo is not None:
            channelLogoControl.setImage(self.program.channel.logo)
            channelTitleControl.setVisible(False)
        else:
            channelTitleControl.setLabel(self.program.channel.title)
            channelLogoControl.setVisible(False)

        programTitleControl.setLabel(self.program.title)

        if self.showRemind:
            remindControl.setLabel(strings(LABEL_REMIND))
        else:
            remindControl.setLabel(strings(LABEL_DONT_REMIND))

        if programTimeRangeControl is not None:
            programTimeRangeControl.setLabel('[B]%s - %s[/B]' % (self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))

    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU]:
            self.close()
            return


    def onClick(self, controlId):
        if controlId == self.C_POPUP_CHOOSE_STREAM and self.database.getCustomStreamUrl(self.program.channel):
            self.database.deleteCustomStreamUrl(self.program.channel)
            chooseStrmControl = self.getControl(self.C_POPUP_CHOOSE_STREAM)
            chooseStrmControl.setLabel(strings(self.LABEL_CHOOSE_STRM))

            if not self.program.channel.isPlayable():
                playControl = self.getControl(self.C_POPUP_PLAY)
                playControl.setEnabled(False)

        else:
            self.buttonClicked = controlId
            self.close()

    def onFocus(self, controlId):
        pass

    def formatTime(self, timestamp):
        deb('formatTime')
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def getControl(self, controlId):
        try:
            return super(PopupMenu, self).getControl(controlId)
        except:
            pass
        return None

class ChannelsMenu(xbmcgui.WindowXMLDialog):
    C_CHANNELS_LIST = 6000
    C_CHANNELS_SELECTION_VISIBLE = 6001
    C_CHANNELS_SELECTION = 6002
    C_CHANNELS_SAVE = 6003
    C_CHANNELS_CANCEL = 6004

    def __new__(cls, database):
        return super(ChannelsMenu, cls).__new__(cls, 'script-tvguide-channels.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

    def __init__(self, database):
        """

        @type database: source.Database
        """
        super(ChannelsMenu, self).__init__()
        self.database = database
        self.channelList = database.getChannelList(onlyVisible = False)
        self.swapInProgress = False


    def onInit(self):
        self.updateChannelList()
        self.setFocusId(self.C_CHANNELS_LIST)


    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU]:
            self.close()
            return

        if self.getFocusId() == self.C_CHANNELS_LIST and action.getId() == ACTION_LEFT:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            idx = listControl.getSelectedPosition()
            buttonControl = self.getControl(self.C_CHANNELS_SELECTION)
            buttonControl.setLabel('[B]%s[/B]' % self.channelList[idx].title)

            self.getControl(self.C_CHANNELS_SELECTION_VISIBLE).setVisible(False)
            self.setFocusId(self.C_CHANNELS_SELECTION)

        elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() in [ACTION_RIGHT, ACTION_SELECT_ITEM]:
            self.getControl(self.C_CHANNELS_SELECTION_VISIBLE).setVisible(True)
            xbmc.sleep(350)
            self.setFocusId(self.C_CHANNELS_LIST)

        elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() == ACTION_UP:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            idx = listControl.getSelectedPosition()
            if idx > 0:
                self.swapChannels(idx, idx - 1)

        elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() == ACTION_DOWN:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            idx = listControl.getSelectedPosition()
            if idx < listControl.size() - 1:
                self.swapChannels(idx, idx + 1)


    def onClick(self, controlId):
        if controlId == self.C_CHANNELS_LIST:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            item = listControl.getSelectedItem()
            channel = self.channelList[int(item.getProperty('idx'))]
            channel.visible = not channel.visible

            if channel.visible:
                iconImage = 'tvguide-channel-visible.png'
            else:
                iconImage = 'tvguide-channel-hidden.png'
            item.setIconImage(iconImage)

        elif controlId == self.C_CHANNELS_SAVE:
            self.database.saveChannelList(self.close, self.channelList)

        elif controlId == self.C_CHANNELS_CANCEL:
            self.close()


    def onFocus(self, controlId):
        pass

    def updateChannelList(self):
        listControl = self.getControl(self.C_CHANNELS_LIST)
        listControl.reset()
        for idx, channel in enumerate(self.channelList):
            if channel.visible:
                iconImage = 'tvguide-channel-visible.png'
            else:
                iconImage = 'tvguide-channel-hidden.png'

            item = xbmcgui.ListItem('%3d. %s' % (idx+1, channel.title), iconImage = iconImage)
            item.setProperty('idx', str(idx))
            listControl.addItem(item)

    def updateListItem(self, idx, item):
        channel = self.channelList[idx]
        item.setLabel('%3d. %s' % (idx+1, channel.title))

        if channel.visible:
            iconImage = 'tvguide-channel-visible.png'
        else:
            iconImage = 'tvguide-channel-hidden.png'
        item.setIconImage(iconImage)
        item.setProperty('idx', str(idx))

    def swapChannels(self, fromIdx, toIdx):
        if self.swapInProgress:
            return
        self.swapInProgress = True

        c = self.channelList[fromIdx]
        self.channelList[fromIdx] = self.channelList[toIdx]
        self.channelList[toIdx] = c

        # recalculate weight
        for idx, channel in enumerate(self.channelList):
            channel.weight = idx

        listControl = self.getControl(self.C_CHANNELS_LIST)
        self.updateListItem(fromIdx, listControl.getListItem(fromIdx))
        self.updateListItem(toIdx, listControl.getListItem(toIdx))

        listControl.selectItem(toIdx)
        xbmc.sleep(50)
        self.swapInProgress = False



class StreamSetupDialog(xbmcgui.WindowXMLDialog):
    C_STREAM_STRM_TAB = 101
    C_STREAM_FAVOURITES_TAB = 102
    C_STREAM_ADDONS_TAB = 103
    C_STREAM_STRM_BROWSE = 1001
    C_STREAM_STRM_FILE_LABEL = 1005
    C_STREAM_STRM_PREVIEW = 1002
    C_STREAM_STRM_OK = 1003
    C_STREAM_STRM_CANCEL = 1004
    C_STREAM_FAVOURITES = 2001
    C_STREAM_FAVOURITES_PREVIEW = 2002
    C_STREAM_FAVOURITES_OK = 2003
    C_STREAM_FAVOURITES_CANCEL = 2004
    C_STREAM_ADDONS = 3001
    C_STREAM_ADDONS_STREAMS = 3002
    C_STREAM_ADDONS_NAME = 3003
    C_STREAM_ADDONS_DESCRIPTION = 3004
    C_STREAM_ADDONS_PREVIEW = 3005
    C_STREAM_ADDONS_OK = 3006
    C_STREAM_ADDONS_CANCEL = 3007

    C_STREAM_VISIBILITY_MARKER = 100

    VISIBLE_STRM = 'strm'
    VISIBLE_FAVOURITES = 'favourites'
    VISIBLE_ADDONS = 'addons'

    def __new__(cls, database, channel):
        return super(StreamSetupDialog, cls).__new__(cls, 'script-tvguide-streamsetup.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

    def __init__(self, database, channel):
        """
        @type database: source.Database
        @type channel:source.Channel
        """
        super(StreamSetupDialog, self).__init__()
        self.database = database
        self.channel = channel

        self.player = xbmc.Player()
        self.previousAddonId = None
        self.strmFile = None
        self.streamingService = streaming.StreamsService()

    def close(self):
        if self.player.isPlaying():
            self.player.stop()
        super(StreamSetupDialog, self).close()


    def onInit(self):
        self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_STRM)

        favourites = self.streamingService.loadFavourites()
        items = list()
        for label, value in favourites:
            item = xbmcgui.ListItem(label)
            item.setProperty('stream', value)
            items.append(item)

        listControl = self.getControl(StreamSetupDialog.C_STREAM_FAVOURITES)
        listControl.addItems(items)

        items = list()
        for id in self.streamingService.getAddons():
            try:
                addon = xbmcaddon.Addon(id) # raises Exception if addon is not installed
                item = xbmcgui.ListItem(addon.getAddonInfo('name'), iconImage=addon.getAddonInfo('icon'))
                item.setProperty('addon_id', id)
                items.append(item)
            except Exception:
                pass
        listControl = self.getControl(StreamSetupDialog.C_STREAM_ADDONS)
        listControl.addItems(items)
        self.updateAddonInfo()



    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU]:
            self.close()
            return

        elif self.getFocusId() == self.C_STREAM_ADDONS:
            self.updateAddonInfo()



    def onClick(self, controlId):
        if controlId == self.C_STREAM_STRM_BROWSE:
            stream = xbmcgui.Dialog().browse(1, ADDON.getLocalizedString(30304), 'video', '.strm')
            if stream:
                self.database.setCustomStreamUrl(self.channel, stream)
                self.getControl(self.C_STREAM_STRM_FILE_LABEL).setText(stream)
                self.strmFile = stream

        elif controlId == self.C_STREAM_ADDONS_OK:
            listControl = self.getControl(self.C_STREAM_ADDONS_STREAMS)
            item = listControl.getSelectedItem()
            if item:
                stream = item.getProperty('stream')
                self.database.setCustomStreamUrl(self.channel, stream)
            self.close()

        elif controlId == self.C_STREAM_FAVOURITES_OK:
            listControl = self.getControl(self.C_STREAM_FAVOURITES)
            item = listControl.getSelectedItem()
            if item:
                stream = item.getProperty('stream')
                self.database.setCustomStreamUrl(self.channel, stream)
            self.close()

        elif controlId == self.C_STREAM_STRM_OK:
            self.database.setCustomStreamUrl(self.channel, self.strmFile)
            self.close()

        elif controlId in [self.C_STREAM_ADDONS_CANCEL, self.C_STREAM_FAVOURITES_CANCEL, self.C_STREAM_STRM_CANCEL]:
            self.close()

        elif controlId in [self.C_STREAM_ADDONS_PREVIEW, self.C_STREAM_FAVOURITES_PREVIEW, self.C_STREAM_STRM_PREVIEW]:
            if self.player.isPlaying():
                self.player.stop()
                self.getControl(self.C_STREAM_ADDONS_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                self.getControl(self.C_STREAM_FAVOURITES_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                self.getControl(self.C_STREAM_STRM_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                return

            stream = None
            visible = self.getControl(self.C_STREAM_VISIBILITY_MARKER).getLabel()
            if visible == self.VISIBLE_ADDONS:
                listControl = self.getControl(self.C_STREAM_ADDONS_STREAMS)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
            elif visible == self.VISIBLE_FAVOURITES:
                listControl = self.getControl(self.C_STREAM_FAVOURITES)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
            elif visible == self.VISIBLE_STRM:
                stream = self.strmFile

            if stream is not None:
                self.player.play(item = stream, windowed = True)
                if self.player.isPlaying():
                    self.getControl(self.C_STREAM_ADDONS_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_FAVOURITES_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_STRM_PREVIEW).setLabel(strings(STOP_PREVIEW))


    def onFocus(self, controlId):
        if controlId == self.C_STREAM_STRM_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_STRM)
        elif controlId == self.C_STREAM_FAVOURITES_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_FAVOURITES)
        elif controlId == self.C_STREAM_ADDONS_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_ADDONS)


    def updateAddonInfo(self):
        listControl = self.getControl(self.C_STREAM_ADDONS)
        item = listControl.getSelectedItem()
        if item is None:
            return

        if item.getProperty('addon_id') == self.previousAddonId:
            return

        self.previousAddonId = item.getProperty('addon_id')
        addon = xbmcaddon.Addon(id = item.getProperty('addon_id'))
        self.getControl(self.C_STREAM_ADDONS_NAME).setLabel('[B]%s[/B]' % addon.getAddonInfo('name'))
        self.getControl(self.C_STREAM_ADDONS_DESCRIPTION).setText(addon.getAddonInfo('description'))

        streams = self.streamingService.getAddonStreams(item.getProperty('addon_id'))
        items = list()
        for (label, stream) in streams:
            item = xbmcgui.ListItem(label)
            item.setProperty('stream', stream)
            items.append(item)
        listControl = self.getControl(StreamSetupDialog.C_STREAM_ADDONS_STREAMS)
        listControl.reset()
        listControl.addItems(items)





class ChooseStreamAddonDialog(xbmcgui.WindowXMLDialog):
    C_SELECTION_LIST = 1000

    def __new__(cls, addons):
        return super(ChooseStreamAddonDialog, cls).__new__(cls, 'script-tvguide-streamaddon.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

    def __init__(self, addons):
        super(ChooseStreamAddonDialog, self).__init__()
        self.addons = addons
        self.stream = None


    def onInit(self):
        items = list()
        for id, label, url in self.addons:
            addon = xbmcaddon.Addon(id)

            item = xbmcgui.ListItem(label, addon.getAddonInfo('name'), addon.getAddonInfo('icon'))
            item.setProperty('stream', url)
            items.append(item)

        listControl = self.getControl(ChooseStreamAddonDialog.C_SELECTION_LIST)
        listControl.addItems(items)

        self.setFocus(listControl)


    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK]:
            self.close()


    def onClick(self, controlId):
        if controlId == ChooseStreamAddonDialog.C_SELECTION_LIST:
            listControl = self.getControl(ChooseStreamAddonDialog.C_SELECTION_LIST)
            self.stream = listControl.getSelectedItem().getProperty('stream')
            self.close()


    def onFocus(self, controlId):
        pass

class InfoDialog(xbmcgui.WindowXMLDialog):

    def __new__(cls, program ):
        return super(InfoDialog, cls).__new__(cls, 'DialogInfo.xml', ADDON.getAddonInfo('path'), "Default", "720p")

    def __init__(self, program):
        super(InfoDialog, self).__init__()
        self.program = program

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
        if self.program is None:
            return

        self.setControlLabel(C_MAIN_TITLE, '[B]%s[/B]' % self.program.title)
        self.setControlLabel(C_MAIN_TIME, '[B]%s - %s[/B]' % (self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))
        if self.program.description:
            description = self.program.description
        else:
            description = strings("")
        self.setControlText(C_MAIN_DESCRIPTION, description)

        if self.program.channel.logo is not None:
            self.setControlImage(C_MAIN_LOGO, self.program.channel.logo)
        if self.program.imageSmall is not None:
            self.setControlImage(C_MAIN_IMAGE, self.program.imageSmall)
        if self.program.imageSmall is None:
            self.setControlImage(C_MAIN_IMAGE, 'tvguide-logo-epg.png')
        if self.program.imageLarge == 'live':
            self.setControlImage(C_MAIN_LIVE, 'live.png')
        else:
            self.setControlImage(C_MAIN_LIVE, '')

        self.stdat = time.mktime(self.program.startDate.timetuple())
        self.endat = time.mktime(self.program.endDate.timetuple())
        self.nodat = time.mktime(datetime.datetime.now().timetuple())
        self.per =  100 -  ((self.endat - self.nodat)/ ((self.endat - self.stdat)/100))
        if self.per > 0 and self.per < 100:
            self.getControl(C_PROGRAM_PROGRESS).setVisible(True)
            self.getControl(C_PROGRAM_PROGRESS).setPercent(self.per)
        else:
            self.getControl(C_PROGRAM_PROGRESS).setVisible(False)

    def setChannel(self, channel):
        self.channel = channel


    def getChannel(self):
        return self.channel


    def onAction(self, action):
        if action.getId() == ACTION_SHOW_INFO or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0):
            self.close()

    def onClick(self, controlId):
        if controlId == 1000:
            self.close()


class Pla(xbmcgui.WindowXMLDialog):

    def __new__(cls, program, database, url, epg):
        return super(Pla, cls).__new__(cls, 'Vid.xml', ADDON.getAddonInfo('path'), "Default", "720p")



    def play(self, url):
        if url[0:9] == 'plugin://':
            xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
        elif url[0:7] == 'service':
            playService(url)
            #xbmc.executebuiltin('XBMC.RunScript(%s,%s,0)' % (ADDON_ID, url))
        else:
            xbmc.Player().play(url)

        threading.Timer(1, self.waitForPlayBackStopped).start()


    def __init__(self, program, database, url, epg):
        super(Pla, self).__init__()
        self.epg = epg
        self.url = url
        self.program = program
        self.currentChannel = program.channel
        self.database = database
        self.controlAndProgramList = list()
        self.play(url)
        self.ChannelChanged = 0
        self.mouseCount = 0

    def onAction(self, action):
        #deb(str(action.getId()))
        if action.getId() == ACTION_PREVIOUS_MENU or action.getId() == ACTION_STOP or (action.getButtonCode() == KEY_STOP and KEY_STOP != 0) or (action.getId() == KEY_STOP and KEY_STOP != 0):
            xbmc.Player().stop()
            self.close()


        if action.getId() == ACTION_SHOW_INFO or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0) or (action.getId() == KEY_INFO and KEY_INFO != 0):
            try:
                self.program = self.database.getCurrentProgram(self.currentChannel)
                self.epg.Info(self.program)
            except:
                pass
            return
        if action.getId() == ACTION_PAGE_UP or (action.getButtonCode() == KEY_PP and KEY_PP != 0) or (action.getId() == KEY_PP and KEY_PP != 0):
            self.ChannelChanged = 1
            self._channelUp()

        if action.getId() == ACTION_PAGE_DOWN or (action.getButtonCode() == KEY_PM and KEY_PM != 0) or (action.getId() == KEY_PM and KEY_PM != 0):
            self.ChannelChanged = 1
            self._channelDown()
#
        if (action.getId() == 3):
            xbmc.executebuiltin("Action(VolumeUp)")
        if (action.getId() == 4):
            xbmc.executebuiltin("Action(VolumeDown)")
        if (action.getId() == 7):
            try:
                self.program = self.database.getCurrentProgram(self.currentChannel)
                self.epg.Info(self.program)
            except:
                pass
            return
#

        if (action.getButtonCode() == KEY_HOME2 and KEY_HOME2 != 0) or (action.getId() == KEY_HOME2 and KEY_HOME2 != 0):
            #xbmc.executebuiltin("Action(PreviousMenu)")
            xbmc.executebuiltin("SendClick(VideoLibrary)")
            #self.setFocus('video')

        if action.getId() == ACTION_MOUSE_MOVE and xbmc.Player().isPlaying():
            self.mouseCount = self.mouseCount + 1
            if self.mouseCount > 15:
                self.mouseCount = 0
                osd = VideoOSD(self)
                osd.doModal()
                del osd


    def onAction2(self, action):
        if action == ACTION_STOP:
            xbmc.Player().stop()
            self.close()
        if action == ACTION_SHOW_INFO:
            try:
                self.program = self.database.getCurrentProgram(self.currentChannel)
                self.epg.Info(self.program)
            except:
                pass
            return
        if action == ACTION_PAGE_UP:
            self.ChannelChanged = 1
            self._channelUp()

        if action == ACTION_PAGE_DOWN:
            self.ChannelChanged = 1
            self._channelDown()



#

    def onPlayBackStopped(self):
        xbmc.Player().stop()
        self.close()


    def waitForPlayBackStopped(self):
        self.wait = True
        for retry in range(0, 50):
            time.sleep(0.1)
            if xbmc.Player().isPlaying():
                break

        while self.wait == True:
            if xbmc.Player().isPlaying() and not xbmc.abortRequested:
                time.sleep(0.2)
            else:
                if self.ChannelChanged == 1:
                    for retry in range(0, 10):
                        time.sleep(0.1)
                    self.ChannelChanged = 0
                else:
                    self.wait = False


        self.onPlayBackStopped()


    def _channelUp(self):
        channel = self.database.getNextChannel(self.currentChannel)
        self.playChannel(channel)

    def _channelDown(self):
        channel = self.database.getPreviousChannel(self.currentChannel)
        self.playChannel(channel)

    def playChannel(self, channel):
        self.currentChannel = channel
        self.epg.currentChannel = channel
        url = self.database.getStreamUrl(channel)
        if url:
            if url[-5:] == '.strm':
                try:
                    f = open(url)
                    content = f.read()
                    f.close()

                    if content[0:9] == 'plugin://':
                        url = content.strip()
                except:
                    pass
        if url[0:9] == 'plugin://':
            xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
        elif url[0:7] == 'service':
            playService(url)
            #xbmc.executebuiltin('XBMC.RunScript(%s,%s,0)' % (ADDON_ID, url))
        else:
            xbmc.Player().play(url)
            
def playService(url):
    params = url[8:].split('&')
    service = params[0]
    cid = params[1].split('=')[1]
    deb('playService playing cid %s, service %s' % (cid, service))
    run = main.InitPlayer().LoadVideoLink(cid, service)

class SleepSupervisor(object):
    def __init__(self):
        self.sleepEnabled = ADDON.getSetting('sleep_enabled')
        self.sleepAction = ADDON.getSetting('sleep_action')
        self.sleepTimer = ADDON.getSetting('sleep_timer')
        self.actions = {
                        'Zatrzymaj odtw.': 'PlayerControl(Stop)',
                        'Wylacz Xbmc': 'Quit',
                        'Wylacz komputer': 'Powerdown',
                        'Uspij komputer': 'Suspend'
        }
        deb('Supervisor timer init: sleepEnabled %s, sleepAction: %s, sleepTimer: %s' % (self.sleepEnabled, self.sleepAction, self.sleepTimer))
            
    def Start(self):
        if self.sleepEnabled == 'Tak':
            self.Stop()
            try:
                action = self.actions[self.sleepAction]
            except KeyError:
                action = self.sleepAction
            
            deb('Supervisor timer Start, action = %s' % action)
            xbmc.executebuiltin('AlarmClock(Stopper,%s,%s,True)' % (action, self.sleepTimer))
        
    def Stop(self):
        if self.sleepEnabled == 'Tak':
            deb('Supervisor timer Stop')
            xbmc.executebuiltin('CancelAlarm(Stopper,True)')

