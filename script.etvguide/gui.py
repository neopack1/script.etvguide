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
import platform
import xbmc
import xbmcgui
from xbmcgui import Dialog, WindowXMLDialog
from time import mktime
import source as src
from notification import Notification
from strings import *
import strings as strings2
import re, sys, os
import streaming
import vosd
from vosd import VideoOSD
from playService import PlayService
from recordService import RecordService

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

KEY_CODEC_INFO = 0

config = ConfigParser.RawConfigParser()
config.read(os.path.join(ADDON.getAddonInfo('path'), 'resources', 'skins',ADDON.getSetting('Skin'), 'settings.ini'))
ini_chan = config.getint("Skin", "CHANNELS_PER_PAGE")
ini_info = config.getboolean("Skin", "USE_INFO_DIALOG")


try:
    skin_separate_category = config.getboolean("Skin", "program_category_separated")
except:
    skin_separate_category = False
try:
    skin_separate_episode = config.getboolean("Skin", "program_episode_separated")
except:
    skin_separate_episode = False
try:
    skin_separate_allowed_age_icon = config.getboolean("Skin", "program_allowed_age_icon")
except:
    skin_separate_allowed_age_icon = False
try:
    skin_separate_director = config.getboolean("Skin", "program_director_separated")
except:
    skin_separate_director = False
try:
    skin_separate_year_of_production = config.getboolean("Skin", "program_year_of_production_separated")
except:
    skin_separate_year_of_production = False
try:
    skin_separate_program_progress = config.getboolean("Skin", "program_show_progress_bar")
except:
    skin_separate_program_progress = False
try:
    skin_separate_program_actors = config.getboolean("Skin", "program_show_actors")
except:
    skin_separate_program_actors = False

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
     KEY_VOL_UP = int(ADDON.getSetting('volume_up_key'))
except:
     KEY_VOL_UP = -1
try:
     KEY_VOL_DOWN = int(ADDON.getSetting('volume_down_key'))
except:
     KEY_VOL_DOWN = -1
try:
     KEY_HOME2 = int(ADDON.getSetting('home_key'))
except:
     KEY_HOME2 = 0

try:
     KEY_CONTEXT = int(ADDON.getSetting('context_key'))
except:
     KEY_CONTEXT = -1

try:
     KEY_RECORD = int(ADDON.getSetting('record_key'))
except:
     KEY_RECORD = -1


CHANNELS_PER_PAGE = ini_chan

HALF_HOUR = datetime.timedelta(minutes = 30)
AUTO_OSD = 666

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
        self.updatePositionTimerData = {}
        self.recordedFilesPositions = {}
        self.updatePositionTimer = None

    def setPlaylistPositionFile(self, recordedFilesPositions):
        self.recordedFilesPlaylistPositions = recordedFilesPositions

    def stopplaying(self):
        self.updatePositionTimerData['stop'] = True
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
        self.updatePositionTimerData['stop'] = True
        self.sleepSupervisor.Start()
        self.onStateChange("Started")
        try:
            playedFile = xbmc.Player().getPlayingFile()
            if os.path.isfile(playedFile):
                try:
                    playlistFileName = re.sub('_part_\d*.flv', '.flv', playedFile)
                    currentPositionInPlaylist = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                    self.recordedFilesPlaylistPositions[playlistFileName] = currentPositionInPlaylist
                    deb('onPlayBackStarted updating playlist position to: %d file: %s' % (currentPositionInPlaylist, playlistFileName))
                except:
                    pass
                try:
                    seek = int(self.recordedFilesPositions[playedFile])
                    deb('onPlayBackStarted seeking file: %s, for %d seconds' % (playedFile, seek))
                    time.sleep(1)
                    xbmc.Player().seekTime(seek)
                except:
                    pass
                self.updatePositionTimerData = {'filename' : playedFile, 'stop' : False}
                self.updatePositionTimer = threading.Timer(10, self.updatePosition, [self.updatePositionTimerData])
                self.updatePositionTimer.start()
        except:
            pass

    def onPlayBackEnded(self):
        deb ("################# Playback Ended")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("Ended")

    def onPlayBackStopped(self):
        deb( "################# Playback Stopped")
        self.updatePositionTimerData['stop'] = True
        self.sleepSupervisor.Stop()
        self.onStateChange("Stopped")

    def updatePosition(self, updatePositionTimerData):
        try:
            fileName = updatePositionTimerData['filename']
            while updatePositionTimerData['stop'] == False:
                self.recordedFilesPositions[fileName] = xbmc.Player().getTime()
                for sleepTime in range(5):
                    if updatePositionTimerData['stop'] == True:
                        break
                    time.sleep(1)
        except:
            pass

    def close(self):
        self.updatePositionTimerData['stop'] = True
        if self.updatePositionTimer is not None:
            self.updatePositionTimer.cancel()

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
        deb('eTVGuide __init__ System: %s, ARH: %s' % (platform.system(), platform.machine()))
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
        self.playService = PlayService()
        self.recordService = RecordService(self)
        self.database = None
        self.redrawagain = False
        self.info = False
        self.infoDialog = None
        self.oldchan = 0
        self.a = {}
        self.urlList = None
        self.mode = MODE_EPG
        self.currentChannel = None
        self.recordedFilesPlaylistPositions = {}
        self.playingRecordedProgram = False
        self.program = None
        self.dontBlockOnAction = False
        self.onFocusTimer = None
        self.blockInputDueToRedrawing = False

        # find nearest half hour
        self.viewStartDate = datetime.datetime.today()
        self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)

        # monitorowanie zmiany stanu odtwarzacza
        threading.Timer(0.3, self.playerstate).start()
        self.updateTimebarTimer = None
        self.lastKeystroke = datetime.datetime.now()

    def playerstate(self):
        vp = VideoPlayerStateChange()
        vp.setPlaylistPositionFile(self.recordedFilesPlaylistPositions)
        vp.playerStateChanged += self.onPlayerStateChanged
        while not self.isClosing:
            xbmc.sleep(300)
        vp.close()
        return

    def onPlayerStateChanged(self, pstate):
        deb("########### onPlayerStateChanged %s %s" % (pstate, ADDON.getSetting('info.osd')))
        if self.isClosing:
            return
        if (pstate == "Stopped" or pstate == "Ended"):  #or pstate == "Paused" or pstate == "Resumed"
            if ADDON.getSetting('start_video_minimalized') == 'false' and ADDON.getSetting('pokazpanel') == 'true': #workaroud for dissapearing mouse panel when start_video_minimalized disabled
                self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
            if (pstate == "Stopped" or pstate == "Ended") and self.playService.isWorking():
                while self.playService.isWorking() == True:
                    time.sleep(0.1)
                time.sleep(0.1)
                if xbmc.Player().isPlaying():
                    debug('onPlayerStateChanged - was able to recover playback - dont show EPG!')
                    return

            self._showEPG()
            if pstate == "Ended" and self.playingRecordedProgram and self.recordService.isProgramScheduled(self.program) == False:
                time.sleep(0.1)
                if xbmc.Player().isPlaying() == False:
                    deleteFiles = False
                    if ADDON.getSetting('ask_to_delete_watched') == '1':
                        deleteFiles = xbmcgui.Dialog().yesno(heading=strings(69026).encode('utf-8', 'replace'), line1='%s?' % strings(69027).encode('utf-8', 'replace'))
                    elif ADDON.getSetting('ask_to_delete_watched') == '2':
                        deleteFiles = True
                    if deleteFiles == True:
                        self.recordService.removeRecordedProgram(self.program)
        else:
            self._hideEpg()

    def getControl(self, controlId):
        #debug('getControl')
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
            if self.recordService.isRecordOngoing():
                ret = xbmcgui.Dialog().yesno(heading=strings(69000).encode('utf-8', 'replace'), line1='%s' % strings(69011).encode('utf-8', 'replace'), autoclose=60000)
                if ret == False:
                    return
            elif self.recordService.isRecordScheduled():
                ret = xbmcgui.Dialog().yesno(heading=strings(69000).encode('utf-8', 'replace'), line1='%s' % strings(69015).encode('utf-8', 'replace'), autoclose=60000)
                if ret == False:
                    return

            self.isClosing = True
            strings2.M_TVGUIDE_CLOSING = True
            xbmc.Player().stop()
            self.playService.close()
            self.recordService.close()
            if self.notification:
                self.notification.close()
            if self.updateTimebarTimer:
                self.updateTimebarTimer.cancel()
            self._clearEpg()
            if self.database:
                self.database.close(super(eTVGuide, self).close)
            else:
                super(eTVGuide, self).close()

    def onInit(self):
        deb('onInit')
        if self.initialized:
            # onInit(..) is invoked again by XBMC after a video addon exits after being invoked by XBMC.RunPlugin(..)
            deb("[%s] TVGuide.onInit(..) invoked, but we're already initialized!" % ADDON_ID)
            self.redrawagain = True
            #self._showEPG()
            #self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)
            #deb('redrawagain')
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
        self.infoDialog = InfoDialog(program)
        self.infoDialog.setChannel(program)
        self.infoDialog.doModal()
        del self.infoDialog
        self.infoDialog = None

    def onAction(self, action):
        if not self.isClosing:
            self.lastKeystroke = datetime.datetime.now()
            if self.mode == MODE_TV:
                self.onActionTVMode(action)
            elif self.mode == MODE_EPG:
                self.onActionEPGMode(action)

    def onActionTVMode(self, action):
        debug('onActionTVMode actId %d, buttonCode %d' % (action.getId(), action.getButtonCode()))
        if action.getId() == ACTION_PAGE_UP:
            self._channelUp()

        elif action.getId() == ACTION_PAGE_DOWN:
            self._channelDown()

#        elif action.getId() == KEY_CONTEXT_MENU or action.getButtonCode() == KEY_CONTEXT:
#            if self.urlList is not None and len(self.urlList) > 1 and not self.playingRecordedProgram:
#                tmpUrl = self.urlList.pop(0)
#                self.urlList.append(tmpUrl)
#                self.playService.playUrlList(self.urlList)
#                time.sleep(0.3)

        elif action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)


    def onActionEPGMode(self, action):
        debug('onActionEPGMode keyId %d, buttonCode %d' % (action.getId(), action.getButtonCode()))
        if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            self.close()
            return

        elif action.getId() == ACTION_MOUSE_MOVE:
            if ADDON.getSetting('pokazpanel') == 'true':
                self._showControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
            return

        if not self.dontBlockOnAction and self.blockInputDueToRedrawing : #Workaround for occasional gui freeze caused by muliple buttons pressed
            debug('Ignoring action')
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

        elif action.getId() == KEY_CONTEXT_MENU or action.getButtonCode() == KEY_CONTEXT:
            if xbmc.Player().isPlaying():

                if ADDON.getSetting('start_video_minimalized') == 'false' or self.playingRecordedProgram:
                    xbmc.executebuiltin("Action(FullScreen)")
                self._hideEpg()
                if ADDON.getSetting('info.osd') == "true" and not self.playingRecordedProgram:
                    osd = Pla(None, self.database, None, self)
                    osd.doModal()
                    osd.close()
                    del osd
                return

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
        elif (action.getId() in [KEY_CONTEXT_MENU] or action.getButtonCode() in [KEY_CONTEXT]) and controlInFocus is not None:
            program = self._getProgramFromControl(controlInFocus)
            if program is not None:
                self._showContextMenu(program)
                return
        elif action.getButtonCode() == KEY_RECORD:
            program = self._getProgramFromControl(controlInFocus)
            self.recordProgram(program)
            return

    def onClick(self, controlId):
        debug('onClick')
        if self.isClosing:
            return
        self.lastKeystroke = datetime.datetime.now()
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
            try:
                channel = self.a[o]
            except Exception, ex:
                deb('RecordAppImporter Error: %s' % str(ex))

        program = self._getProgramFromControl(self.getControl(controlId))
        if channel is not None:
            if not self.playChannel(channel, program):
                result = self.streamingService.detectStream(channel)
                if not result:
                    return
                elif type(result) == str:
                    # one single stream detected, save it and start streaming
                    self.database.setCustomStreamUrl(channel, result)
                    self.playChannel(channel, program)

                else:
                    # multiple matches, let user decide

                    d = ChooseStreamAddonDialog(result)
                    d.doModal()
                    if d.stream is not None:
                        self.database.setCustomStreamUrl(channel, d.stream)
                        self.playChannel(channel, program)
            return

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
            if not self.playChannel(program.channel, program):
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
        debug('setFocusId')
        control = self.getControl(controlId)
        if control:
            self.setFocus(control)

    def setFocus(self, control):
        debug('setFocus %d' % control.getId())
        if control in [elem.control for elem in self.controlAndProgramList]:
            #deb('Focus before %s' % self.focusPoint)
            (left, top) = control.getPosition()
            if left > self.focusPoint.x or left + control.getWidth() < self.focusPoint.x:
                self.focusPoint.x = left
            self.focusPoint.y = top + (control.getHeight() / 2)
            #deb('New focus at %s' % self.focusPoint)
        super(eTVGuide, self).setFocus(control)

    def onFocus(self, controlId):
        #Call filling all program data was delayed, because of Kodi internal error which may lead to Kodi freeze when scrolling
        try:
            if self.onFocusTimer:
                self.onFocusTimer.cancel()
            self.onFocusTimer = threading.Timer(0.20, self.delayedOnFocus, [controlId])
            self.onFocusTimer.start()
        except:
            pass

    def delayedOnFocus(self, controlId):
        debug('onFocus controlId : %s' % controlId)
        try:
            controlInFocus = self.getControl(controlId)
        except Exception, ex:
            deb('onFocus Exception str: %s' % str(ex))
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

        if skin_separate_category or skin_separate_year_of_production or skin_separate_director or skin_separate_episode or skin_separate_allowed_age_icon or skin_separate_program_progress or skin_separate_program_actors:
            #This mean we'll need to parse program description
            descriptionParser = src.ProgramDescriptionParser(description)
            if skin_separate_category:
                category = descriptionParser.extractCategory()
                self.setControlText(C_PROGRAM_CATEGORY, category)
            if skin_separate_year_of_production:
                year = descriptionParser.extractProductionDate()
                self.setControlText(C_PROGRAM_PRODUCTION_DATE, year)
            if skin_separate_director:
                director = descriptionParser.extractDirector()
                self.setControlText(C_PROGRAM_DIRECTOR, director)
            if skin_separate_episode:
                episode = descriptionParser.extractEpisode()
                self.setControlText(C_PROGRAM_EPISODE, episode)
            if skin_separate_allowed_age_icon:
                icon = descriptionParser.extractAllowedAge()
                self.setControlImage(C_PROGRAM_AGE_ICON, icon)
            if skin_separate_program_actors:
                actors = descriptionParser.extractActors()
                self.setControlText(C_PROGRAM_ACTORS, actors)
            if skin_separate_program_progress:
                try:
                    programProgressControl = self.getControl(C_MAIN_PROGRAM_PROGRESS)
                    stdat = time.mktime(program.startDate.timetuple())
                    endat = time.mktime(program.endDate.timetuple())
                    nodat = time.mktime(datetime.datetime.now().timetuple())
                    percent =  100 -  ((endat - nodat)/ ((endat - stdat)/100))
                    if percent > 0 and percent < 100:
                        programProgressControl.setVisible(True)
                        programProgressControl.setPercent(percent)
                    else:
                        programProgressControl.setVisible(False)
                except:
                    pass

            description = descriptionParser.description

        self.setControlText(C_MAIN_DESCRIPTION, description)

        xbmc.sleep(10)
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
        debug('_left')
        control = self._findControlOnLeft(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.viewStartDate -= datetime.timedelta(hours = 2)
            self.focusPoint.x = self.epgView.right
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnLeft)

    def _right(self, currentFocus):
        debug('_right')
        control = self._findControlOnRight(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.viewStartDate += datetime.timedelta(hours = 2)
            self.focusPoint.x = self.epgView.left
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnRight)

    def _up(self, currentFocus):
        debug('_up')
        currentFocus.x = self.focusPoint.x
        control = self._findControlAbove(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx - CHANNELS_PER_PAGE, self.viewStartDate, focusFunction=self._findControlAbove)

    def _down(self, currentFocus):
        debug('_down')
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
        debug('_moveUp')
        if scrollEvent:
            self.dontBlockOnAction = True
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate)
            self.dontBlockOnAction = False
        else:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate, focusFunction = self._findControlAbove)

    def _moveDown(self, count = 1, scrollEvent = False):
        debug('_moveDown')
        if scrollEvent:
            self.dontBlockOnAction = True
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate)
            self.dontBlockOnAction = False
        else:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate, focusFunction=self._findControlBelow)

    def _channelUp(self):
        channel = self.database.getNextChannel(self.currentChannel)
        self.playChannel2(self.database.getCurrentProgram(channel))

    def _channelDown(self):
        channel = self.database.getPreviousChannel(self.currentChannel)
        self.playChannel2(self.database.getCurrentProgram(channel))

    def playRecordedProgram(self, program):
        self.playingRecordedProgram = False
        recordedProgram = self.recordService.isProgramRecorded(program)
        if recordedProgram is not None:
            ret = xbmcgui.Dialog().yesno(heading=strings(RECORDED_FILE_POPUP).encode('utf-8', 'replace'), line1='%s %s?' % (strings(RECORDED_FILE_QUESTION).encode('utf-8', 'replace'), program.title.encode('utf-8', 'replace')), autoclose=60000)
            if ret == True:
                #if ADDON.getSetting('start_video_minimalized') == 'true':
                    #startWindowed = True
                #else:
                    #startWindowed = False
                try:
                    firstFileInPlaylist = recordedProgram[0].getfilename()
                    playlistIndex = int(self.recordedFilesPlaylistPositions[firstFileInPlaylist])
                except:
                    playlistIndex = -1

                deb('playRecordedProgram starting play of recorded program %s from index %d' % (program.title.encode('utf-8', 'replace'), playlistIndex))
                xbmc.Player().play(item=recordedProgram, windowed=False, startpos=playlistIndex)
                self.playingRecordedProgram = True
                return True
        return False

    def playChannel2(self, program):
        deb('playChannel2')
        self.program = program
        self.currentChannel = program.channel
        if self.playRecordedProgram(program):
            return True

        self.urlList = self.database.getStreamUrlList(program.channel)
        if len(self.urlList) > 0:
            self.oldchan = self.database.getCurrentChannelIdx(program.channel)
            osd = Pla(self.program, self.database, self.urlList, self)
            #debug('GUI playChannel2 started Pla, pointer: %s' % (osd))
            osd.doModal()
            osd.close()
            #debug('GUI playChannel2 stopped Pla, pointer: %s' % (osd))
            del osd
            currentChannelIndex = self.database.getCurrentChannelIdx(self.currentChannel)
            if self.oldchan != currentChannelIndex:
                if not xbmc.Player().isPlaying() and not self.isClosing:
                    newStartIndex = (currentChannelIndex // CHANNELS_PER_PAGE) * CHANNELS_PER_PAGE
                    self.viewStartDate = datetime.datetime.today()
                    self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)
                    self.onRedrawEPG(newStartIndex, self.viewStartDate, self._getCurrentProgramFocus)
        #self.onPlayBackStopped()
        return len(self.urlList) > 0


    def playChannel(self, channel, program = None):
        deb('playChannel')
        self.currentChannel = channel
        wasPlaying = xbmc.Player().isPlaying()
        if program is not None:
            self.program = program
            if self.playRecordedProgram(program):
                return True
        self.urlList = self.database.getStreamUrlList(channel)
        if len(self.urlList) > 0:
            self.playService.playUrlList(self.urlList)
            #if not wasPlaying:
                #self._hideEpg()

        #threading.Timer(1, self.waitForPlayBackStopped).start()

        return len(self.urlList) > 0

    def recordProgram(self, program):
        deb('recordProgram')
        databaseUpdated = False
        timeToProgramEnd = program.endDate - datetime.datetime.now()
        if ((timeToProgramEnd.days * 86400) + timeToProgramEnd.seconds) <= 0:
            return

        if self.recordService.isProgramScheduled(program):
            ret = xbmcgui.Dialog().yesno(heading=strings(69000).encode('utf-8'), line1=strings(69009).encode('utf-8'), autoclose=60000)
            if ret == True:
                self.database.removeRecording(program)
                self.recordService.cancelProgramRecord(program)
                databaseUpdated = True
        elif program.recordingScheduled != 1:
            ret = xbmcgui.Dialog().yesno(heading=strings(69000).encode('utf-8'), line1='%s %s?' % (strings(69010).encode('utf-8', 'replace'), program.title.encode('utf-8', 'replace')), autoclose=60000)
            if ret == True:
                self.database.addRecording(program)
                self.recordService.scheduleRecording(program)
                databaseUpdated = True
        else:
            self.database.removeRecording(program)
            databaseUpdated = True

        if databaseUpdated == True:
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)


    def waitForPlayBackStopped(self):
        debug('waitForPlayBackStopped')
        while self.epg.playService.isWorking() == True:
            time.sleep(0.2)
        while (xbmc.Player().isPlaying() or self.epg.playService.isWorking() == True) and not strings2.M_TVGUIDE_CLOSING and not self.isClosing:
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
        if self.currentChannel is not None:
            currentChannelIndex = self.database.getCurrentChannelIdx(self.currentChannel)
            self.channelIdx = (currentChannelIndex // CHANNELS_PER_PAGE) * CHANNELS_PER_PAGE

        #przerysuj tylko wtedy gdy nie bylo epg! jak jest to nie przerysowuj - nie ustawi sie wtedy na aktualnej godzienie!
        if (self.mode == MODE_TV):
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus) #przerysuj

    def onRedrawEPG(self, channelStart, startTime, focusFunction = None):
        deb('onRedrawEPG')
        if self.redrawingEPG or (self.database is not None and self.database.updateInProgress) or self.isClosing:
            deb('onRedrawEPG - already redrawing')
            return # ignore redraw request while redrawing
        self.redrawingEPG = True
        self.blockInputDueToRedrawing = True
        self.redrawagain = False
        self.mode = MODE_EPG

        if self.onFocusTimer:
            self.onFocusTimer.cancel()
        if self.infoDialog is not None:
            self.infoDialog.close()

        self._showControl(self.C_MAIN_EPG)
        self.updateTimebar(scheduleTimer = False)

        # show Loading screen
        self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(CALCULATING_REMAINING_TIME))
        self._showControl(self.C_MAIN_LOADING)
        self.setFocusId(self.C_MAIN_LOADING_CANCEL)

        # remove existing controls
        self._clearEpg()
        try:
            self.channelIdx, channels, programs, cacheExpired = self.database.getEPGView(channelStart, startTime, self.onSourceProgressUpdate, clearExistingProgramList = True)
        except src.SourceException:
            self.blockInputDueToRedrawing = False
            debug('onRedrawEPG onEPGLoadError')
            self.onEPGLoadError()
            return

        if cacheExpired == True and ADDON.getSetting('notifications.enabled') == 'true':
            #make sure notifications are scheduled for newly downloaded programs
            self.notification.scheduleNotifications()

        # date and time row
        self.setControlLabel(self.C_MAIN_DATE, self.formatDate(self.viewStartDate))
        for col in range(1, 5):
            self.setControlLabel(4000 + col, self.formatTime(startTime))
            startTime += HALF_HOUR

        if programs is None:
            debug('onRedrawEPG onEPGLoadError2')
            self.onEPGLoadError()
            return

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

                if program.recordingScheduled:
                    noFocusTexture = ADDON.getSetting('kolor.recording')+'.png'

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
        if focusControl is None:
            focusControl = self._findControlAt(self.focusPoint)
        controls = [elem.control for elem in self.controlAndProgramList]
        self.addControls(controls)
        if focusControl is not None:
            self.setFocus(focusControl)
        self.ignoreMissingControlIds.extend([elem.control.getId() for elem in self.controlAndProgramList])
        if focusControl is None and len(self.controlAndProgramList) > 0:
            self.setFocus(self.controlAndProgramList[0].control)

        self._hideControl(self.C_MAIN_LOADING)
        self.blockInputDueToRedrawing = False
        # set channel logo or text
        for idx in range(0, CHANNELS_PER_PAGE):
            if idx >= len(channels):
                if idx % 2 == 0 and not self.dontBlockOnAction:
                    xbmc.sleep(20) #Fix for ocasional gui freeze during quick scrolling
                self.setControlImage(4110 + idx, ' ')
                self.setControlLabel(4010 + idx, ' ')
            else:
                channel = channels[idx]
                self.setControlLabel(4010 + idx, channel.title)
                if idx % 2 == 0 and not self.dontBlockOnAction:
                    xbmc.sleep(20) #Fix for ocasional gui freeze during quick scrolling
                if channel.logo is not None:
                    self.setControlImage(4110 + idx, channel.logo)
                else:
                    self.setControlImage(4110 + idx, ' ')

                self.a[idx] = channel


        self.redrawingEPG = False
        if self.redrawagain:
            debug('onRedrawEPG redrawing again')
            self.redrawagain = False
            self.onRedrawEPG(channelStart, self.viewStartDate, focusFunction)
        debug('onRedrawEPG done')

    def _clearEpg(self):
        deb('_clearEpg')
        controls = [elem.control for elem in self.controlAndProgramList]
        try:
            self.removeControls(controls)
        except:
            debug('_clearEpg failed to delete all controls, deleting one by one')
            for elem in self.controlAndProgramList:
                try:
                    self.removeControl(elem.control)
                except RuntimeError, ex:
                    debug('_clearEpg RuntimeError: %s' % str(ex))
                    pass # happens if we try to remove a control that doesn't exist
                except Exception, ex:
                    deb('_clearEpg unhandled exception: %s' % str(ex))
        del self.controlAndProgramList[:]
        debug('_clearEpg end')

    def onEPGLoadError(self):
        deb('onEPGLoadError, M_TVGUIDE_CLOSING: %s' % strings2.M_TVGUIDE_CLOSING)
        self.redrawingEPG = False
        self._hideControl(self.C_MAIN_LOADING)
        if not strings2.M_TVGUIDE_CLOSING:
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
        return strings2.M_TVGUIDE_CLOSING or self.isClosing

    def onSourceInitialized(self, success):
        deb('onSourceInitialized')
        if success:
            self.notification = Notification(self.database, ADDON.getAddonInfo('path'), self)
            if ADDON.getSetting('notifications.enabled') == 'true':
                self.notification.scheduleNotifications()
            self.recordService.scheduleAllRecordings()
            if strings2.M_TVGUIDE_CLOSING == False:
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

        return not strings2.M_TVGUIDE_CLOSING and not self.isClosing

    def onPlayBackStopped(self):
        deb('onPlayBackStopped')
        if not xbmc.Player().isPlaying() and not self.isClosing:
            self.viewStartDate = datetime.datetime.today()
            self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

    def _secondsToXposition(self, seconds):
        #deb('_secondsToXposition')
        return self.epgView.left + (seconds * self.epgView.width / 7200)

    def _findControlOnRight(self, point):
        debug('_findControlOnRight')
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
        debug('_findControlOnLeft')
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
        debug('_findControlBelow')
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
        debug('_findControlAbove')
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
        debug('_findControlAt')
        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            bottom = top + control.getHeight()
            right = left + control.getWidth()

            if left <= point.x <= right and  top <= point.y <= bottom:
                return control

        return None

    def _getProgramFromControl(self, control):
        #deb('_getProgramFromControl')
        try:
            for elem in self.controlAndProgramList:
                if elem.control == control:
                    return elem.program
        except Exception, ex:
            deb('_getProgramFromControl Error: %s' % str(ex))
            raise
        return None

    def _getCurrentProgramFocus(self, point = None):
        try:
            if self.currentChannel:
                program = self.database.getCurrentProgram(self.currentChannel)
                if program is not None:
                    for elem in self.controlAndProgramList:
                        if elem.program.channel.id == program.channel.id and elem.program.startDate == program.startDate:
                            return elem.control
        except:
            pass
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
        debug('_showControl')
        """
        Visibility is inverted in skin
        """
        for controlId in controlIds:
            control = self.getControl(controlId)
            if control:
                control.setVisible(False)

    def formatTime(self, timestamp):
        debug('formatTime')
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def formatDate(self, timestamp):
        debug('formatDate')
        format = xbmc.getRegion('dateshort')
        return timestamp.strftime(format)

    def setControlImage(self, controlId, image):
        debug('setControlImage')
        control = self.getControl(controlId)
        if control:
            control.setImage(image.encode('utf-8'))

    def setControlLabel(self, controlId, label):
        debug('setControlLabel')
        control = self.getControl(controlId)
        if control:
            control.setLabel(label)

    def setControlText(self, controlId, text):
        debug('setControlText')
        control = self.getControl(controlId)
        if control:
            control.setText(text)


    def updateTimebar(self, scheduleTimer = True):
        #debug('updateTimebar')
        if xbmc.Player().isPlaying():
            self.lastKeystroke = datetime.datetime.now()
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

                xPositionBar = self._secondsToXposition(timeDelta.seconds)
                control.setPosition(xPositionBar, y)

                if xPositionBar > self.epgView.right:
                    #Time bar exceeded EPG
                    #Check how long was since EPG was used
                    diff = datetime.datetime.now() - self.lastKeystroke
                    diffSeconds = (diff.days * 86400) + diff.seconds
                    debug('updateTimebar seconds since last user action %s' % diffSeconds)
                    if diffSeconds > 300:
                        debug('updateTimebar redrawing EPG start')
                        self.lastKeystroke = datetime.datetime.now()
                        self.viewStartDate = datetime.datetime.today()
                        self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30, seconds = self.viewStartDate.second)
                        self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)
                        debug('updateTimebar redrawing EPG end')

            if scheduleTimer and not strings2.M_TVGUIDE_CLOSING and not self.isClosing:
                if self.updateTimebarTimer is not None:
                    self.updateTimebarTimer.cancel()
                self.updateTimebarTimer = threading.Timer(20, self.updateTimebar)
                self.updateTimebarTimer.start()
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
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU] or action.getButtonCode() in [KEY_CONTEXT]:
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
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU] or action.getButtonCode() in [KEY_CONTEXT]:
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
        self.previousAddonId = None
        self.strmFile = None
        self.streamingService = streaming.StreamsService()

    def close(self):
        if xbmc.Player().isPlaying():
            xbmc.Player().stop()
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
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU] or action.getButtonCode() in [KEY_CONTEXT]:
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
            if xbmc.Player().isPlaying():
                xbmc.Player().stop()
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
                xbmc.Player().play(item = stream, windowed = True)
                if xbmc.Player().isPlaying():
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
    def __new__(cls, program):
        return super(InfoDialog, cls).__new__(cls, 'DialogInfo.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), "720p")

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


        if skin_separate_category or skin_separate_year_of_production or skin_separate_director or skin_separate_episode or skin_separate_allowed_age_icon or skin_separate_program_progress or skin_separate_program_actors:
            #This mean we'll need to parse program description
            descriptionParser = src.ProgramDescriptionParser(description)
            if skin_separate_category:
                try:
                    categoryControl = self.getControl(C_PROGRAM_CATEGORY)
                    category = descriptionParser.extractCategory()
                    categoryControl.setText(category)
                except:
                    pass
            if skin_separate_year_of_production:
                try:
                    productionDateControl = self.getControl(C_PROGRAM_PRODUCTION_DATE)
                    year = descriptionParser.extractProductionDate()
                    productionDateControl.setText(year)
                except:
                    pass
            if skin_separate_director:
                try:
                    directorControl = self.getControl(C_PROGRAM_DIRECTOR)
                    director = descriptionParser.extractDirector()
                    directorControl.setText(director)
                except:
                    pass
            if skin_separate_episode:
                try:
                    episodeControl = self.getControl(C_PROGRAM_EPISODE)
                    episode = descriptionParser.extractEpisode()
                    episodeControl.setText(episode)
                except:
                    pass
            if skin_separate_allowed_age_icon:
                try:
                    ageImageControl = self.getControl(C_PROGRAM_AGE_ICON)
                    icon = descriptionParser.extractAllowedAge()
                    ageImageControl.setImage(icon)
                except:
                    pass
            if skin_separate_program_actors:
                try:
                    actorsControl = self.getControl(C_PROGRAM_ACTORS)
                    actors = descriptionParser.extractActors()
                    actorsControl.setText(actors)
                except:
                    pass

            description = descriptionParser.description


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
        if action.getId() in [ACTION_SHOW_INFO, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, ACTION_PARENT_DIR] or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0) or action.getButtonCode() == KEY_STOP:
            self.close()

    def onClick(self, controlId):
        if controlId == 1000:
            self.close()


class Pla(xbmcgui.WindowXMLDialog):
    def __new__(cls, program, database, urlList, epg):
        return super(Pla, cls).__new__(cls, 'Vid.xml', ADDON.getAddonInfo('path'), "Default", "720p")

    def play(self, urlList):
        #debug('Pla play %s' % self)
        self.epg.playService.playUrlList(urlList)

    def __init__(self, program, database, urlList, epg):
        #debug('Pla __init__ %s' % self)
        super(Pla, self).__init__()
        self.epg = epg
        self.database = database
        self.controlAndProgramList = list()
        self.ChannelChanged = 0
        self.mouseCount = 0
        self.isClosing = False
        self.playbackStarted = False
        self.key_right_left_show_next = ADDON.getSetting('key_right_left_show_next')
        self.showOsdOnPlay = False
        self.displayAutoOsd = False
        self.playButtonAsSchedule = False
        self.videoOSD = None
        if ADDON.getSetting('show_osd_on_play') == 'true':
            self.showOsdOnPlay = True
            self.displayAutoOsd = True
        if program is not None:
            self.program = program
            self.currentChannel = program.channel
            self.urlList = urlList
            self.play(urlList)
        else:
            self.currentChannel = self.epg.currentChannel
            self.program = self.database.getCurrentProgram(self.currentChannel)
            self.urlList = self.database.getStreamUrlList(self.currentChannel)
        threading.Timer(0, self.waitForPlayBackStopped).start()

    def onAction(self, action):
        debug('Pla onAction keyId %d, buttonCode %d' % (action.getId(), action.getButtonCode()))

        if action.getId() == ACTION_PREVIOUS_MENU or action.getId() == ACTION_STOP or (action.getButtonCode() == KEY_STOP and KEY_STOP != 0) or (action.getId() == KEY_STOP and KEY_STOP != 0):
            #debug('Pla before self.epg.player.stop()')
            xbmc.Player().stop()
            #debug('Pla before self.close()')
            self.closeOSD()
            #debug('Pla after self.close()')

#        elif action.getId() == KEY_NAV_BACK:
#            if ADDON.getSetting('start_video_minimalized') == 'true' and ADDON.getSetting('navi_back_stop_play') == 'false':
#                self.closeOSD()
#                self.epg._showEPG()
#            else:
#                xbmc.Player().stop()
#                self.closeOSD()

        #if action.getId() == KEY_CODEC_INFO: #przysik O
            #xbmc.executebuiltin("Action(CodecInfo)")

        elif action.getId() == ACTION_PAGE_UP or (action.getButtonCode() == KEY_PP and KEY_PP != 0) or (action.getId() == KEY_PP and KEY_PP != 0):
            self.ChannelChanged = 1
            self._channelUp()
            return

        elif action.getId() == ACTION_PAGE_DOWN or (action.getButtonCode() == KEY_PM and KEY_PM != 0) or (action.getId() == KEY_PM and KEY_PM != 0):
            self.ChannelChanged = 1
            self._channelDown()
            return

#        elif action.getId() == KEY_CONTEXT_MENU or action.getButtonCode() == KEY_CONTEXT:
#            self.changeStream()

        elif self.playbackStarted == False:
            debug('Playback has not started yet, canceling all key requests')
            return

        elif action.getId() == ACTION_SHOW_INFO or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0) or (action.getId() == KEY_INFO and KEY_INFO != 0):
            try:
                self.program = self.database.getCurrentProgram(self.currentChannel)
                self.epg.Info(self.program)
            except:
                pass
            return

        elif action.getButtonCode() == KEY_VOL_DOWN or (action.getId() == ACTION_LEFT and self.key_right_left_show_next == 'false'):
            xbmc.executebuiltin("Action(VolumeDown)")

        elif action.getButtonCode() == KEY_VOL_UP or (action.getId() == ACTION_RIGHT and self.key_right_left_show_next == 'false'):
            xbmc.executebuiltin("Action(VolumeUp)")

        elif (action.getId() == ACTION_LEFT and self.key_right_left_show_next == 'true'):
            self.showVidOsd(ACTION_LEFT)

        elif (action.getId() == ACTION_RIGHT and self.key_right_left_show_next == 'true'):
            self.showVidOsd(ACTION_RIGHT)

        elif (action.getId() == ACTION_UP):
            self.showVidOsd(ACTION_UP)

        elif (action.getId() == ACTION_DOWN):
            self.showVidOsd(ACTION_DOWN)

        elif (action.getId() == ACTION_SELECT_ITEM):
            try:
                if ADDON.getSetting('VidOSD_on_select') == 'true':
                    self.showVidOsd()
                else:
                    self.program = self.database.getCurrentProgram(self.currentChannel)
                    self.epg.Info(self.program)
            except:
                pass
            return

        elif (action.getButtonCode() == KEY_HOME2 and KEY_HOME2 != 0) or (action.getId() == KEY_HOME2 and KEY_HOME2 != 0):
            xbmc.executebuiltin("SendClick(VideoLibrary)")

        elif action.getId() == ACTION_MOUSE_MOVE and xbmc.Player().isPlaying():
            self.mouseCount = self.mouseCount + 1
            if self.mouseCount > 15:
                self.mouseCount = 0
                osd = VideoOSD(self)
                osd.doModal()
                del osd


    def onAction2(self, action, program = None):
        debug('Pla onAction2 %s' % self)
        if action in [ACTION_STOP, KEY_NAV_BACK]:
            xbmc.Player().stop()
            self.closeOSD()

        elif action == ACTION_SHOW_INFO:
            try:
                if program is None:
                    program = self.database.getCurrentProgram(self.currentChannel)
                self.epg.Info(program)
            except:
                pass
            return

        elif action == ACTION_PAGE_UP:
            self.ChannelChanged = 1
            self._channelUp()

        elif action == ACTION_PAGE_DOWN:
            self.ChannelChanged = 1
            self._channelDown()

    def onPlayBackStopped(self):
        debug('Pla onPlayBackStopped %s' % self)
        self.closeOSD()

    def waitForPlayBackStopped(self):
        self.wait = True

        while self.epg.playService.isWorking() == True and not self.isClosing:
            time.sleep(0.1)

        while self.wait == True and not self.isClosing:
            if xbmc.Player().isPlaying() and not strings2.M_TVGUIDE_CLOSING and not self.isClosing and not self.epg.playService.isWorking():
                self.playbackStarted = True
                if self.displayAutoOsd and self.showOsdOnPlay:
                    self.displayAutoOsd = False
                    self.showVidOsd(AUTO_OSD)
                else:
                    time.sleep(0.2)
            else:
                self.playbackStarted = False
                if not self.isClosing and (self.ChannelChanged == 1 or self.epg.playService.isWorking() == True):
                    while self.epg.playService.isWorking() == True and not self.isClosing:
                        time.sleep(0.1)
                    self.ChannelChanged = 0
                    self.show()
                else:
                    debug('Pla waitForPlayBackStopped not waiting anymore %s' % self)
                    self.wait = False

        self.onPlayBackStopped()

    def _channelUp(self):
        #debug('Pla _channelUp %s' % self)
        channel = self.database.getNextChannel(self.currentChannel)
        self.playChannel(channel)

    def _channelDown(self):
        #debug('Pla _channelDown %s' % self)
        channel = self.database.getPreviousChannel(self.currentChannel)
        self.playChannel(channel)

    def playChannel(self, channel):
        debug('Pla playChannel %s' % self)
        if channel.id != self.currentChannel.id:
            self.ChannelChanged = 1
            self.currentChannel = channel
            self.epg.currentChannel = channel
            self.program = self.database.getCurrentProgram(self.currentChannel)
            self.epg.program = self.program
            self.urlList = self.database.getStreamUrlList(channel)
            if len(self.urlList) > 0:
                self.epg.playService.playUrlList(self.urlList)
                if self.showOsdOnPlay:
                    self.displayAutoOsd = True

    def changeStream(self):
        deb('Changing stream for channel %s' % self.currentChannel.id)
        if len(self.urlList) > 1:
            tmpUrl = self.urlList.pop(0)
            self.urlList.append(tmpUrl)
            self.ChannelChanged = 1
            self.epg.playService.playUrlList(self.urlList)
            time.sleep(0.3)

    def getProgramUp(self, program):
        channel = self.database.getPreviousChannel(program.channel)
        return self.database.getCurrentProgram(channel)

    def getProgramDown(self, program):
        channel = self.database.getNextChannel(program.channel)
        return self.database.getCurrentProgram(channel)

    def getProgramLeft(self, program):
        return self.database.getPreviousProgram(program)

    def getProgramRight(self, program):
        return self.database.getNextProgram(program)

    def getCurrentProgram(self):
        return self.database.getCurrentProgram(self.currentChannel)

    def showVidOsd(self, action = None):
        self.program = self.database.getCurrentProgram(self.currentChannel)
        self.videoOSD = VideoOSD(self, False, action)
        self.videoOSD.doModal()
        del self.videoOSD
        self.videoOSD = None

    def closeOSD(self):
        #debug('Pla closeOSD %s' % self)
        if self.videoOSD:
            self.videoOSD.isClosing = True
            self.videoOSD.close()
        self.isClosing = True
        self.close()

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
