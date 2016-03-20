#      Copyright (C) 2016 Andrzej Mleczko

import re, sys, os, cgi
import xbmcplugin, xbmcgui, xbmcaddon, xbmc, gui
from strings import *
import threading
import datetime
import subprocess
import signal
from playService import BasePlayService
import unicodedata
import time

recordIcon = 'recordIcon.png'
recordNotificationName = strings(69004).encode('utf-8')
finishedRecordNotificationName = strings(69005).encode('utf-8')
nonExistingRecordDirName = strings(69006).encode('utf-8')
failedRecordDialogName = strings(69007).encode('utf-8')
missingRecordBinaryString = strings(69008).encode('utf-8')

maxNrOfReattempts = int(ADDON.getSetting('max_reattempts'))

class RecordService(BasePlayService):
    def __init__(self, epg):
        BasePlayService.__init__(self)
        self.rtmpdumpExe = xbmc.translatePath(ADDON.getSetting('rtmpdumpExe'))
        self.ffmpegdumpExe = xbmc.translatePath(ADDON.getSetting('ffmpegExe'))
        self.useOnlyFFmpeg = ADDON.getSetting('use_only_ffmpeg')
        self.recordDestinationPath = xbmc.translatePath(ADDON.getSetting('record.folder'))
        self.icon = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), recordIcon)
        self.epg = epg
        self.threadList = list()
        self.timers = list()
        self.cleanupTimer = None

    def scheduleAllRecordings(self):
        deb('scheduleAllRecordings')
        channels = self.epg.database.getChannelList(True)
        for channel_name, program_title, start_date, end_date in self.epg.database.getRecordings():
            timeDelta = end_date - datetime.datetime.now()
            timeToProgramEnd = timeDelta.seconds + timeDelta.days * 86400
            if timeToProgramEnd < 0:
                debug('scheduleAllRecordings %s has already finished' % program_title)
                continue
            for channel in channels:
                if channel.id == channel_name:
                    program = self.epg.database.getProgramStartingAt(channel, start_date)
                    if program is not None and self.isProgramScheduled(program) == False:
                        self.scheduleRecording(program, 30)
                    break
        debug('scheduleAllRecordings completed!')

    def scheduleRecording(self, program, delayRecording = 0):
        deb('RecordService scheduling record for program %s, starting at %s' % (program.title.encode('utf-8'), program.startDate))
        timeDiff = program.startDate - datetime.datetime.now()
        timeToProgramEnd = program.endDate - datetime.datetime.now()
        secToRecording  = ((timeDiff.days * 86400) + timeDiff.seconds) + 5  #make sure old recordins will finish before
        secToFinishRecording = ((timeToProgramEnd.days * 86400) + timeToProgramEnd.seconds) - 5
        if secToRecording < 0:
            secToRecording = 0 + delayRecording #start now
        if secToFinishRecording <= 0:
            #Program already ended! exit
            return
        element = self.getScheduledRecordingsForThisTime(program.startDate)
        if element is not None:
            programList = element[2]    #Fetch already scheduled list of programs
            for prog in programList:
                if program.channel == prog.channel and program.startDate == prog.startDate:
                    return #already on list
            programList.append(program) #And add one more
        else:
            programList = list()
            programList.append(program)
            timer = threading.Timer(secToRecording, self.recordChannel, [program.startDate])
            self.timers.append([program.startDate, timer, programList])
            timer.start()

    def recordChannel(self, startTime):
        deb('RecordService recordChannel startTime %s' % startTime)
        element = self.getScheduledRecordingsForThisTime(startTime)
        if element is None:
            deb('RecordService recordChannel couldnt find scheduled program for time %s' % startTime)
            return
        programList = element[2]
        self.timers.remove(element)
        for program in programList:
            urlList = self.epg.database.getStreamUrlList(program.channel)
            threadData = {'urlList' : urlList, 'program' : program, 'recordHandle' : None, 'stopRecordTimer' : None, 'terminateThread' : False}
            thread = threading.Thread(name='recordLoop', target = self.recordLoop, args=[threadData])
            self.threadList.append([thread, threadData])
            thread.start()

    def recordLoop(self, threadData):
        if self.recordDestinationPath == '' or os.path.isdir(self.recordDestinationPath) == False:
            xbmcgui.Dialog().ok(failedRecordDialogName,"\n" + nonExistingRecordDirName + "\n" + self.recordDestinationPath)
            return
        missingRtmpdumpBinary = False
        missingFfmpegumpBinary = False
        success = False
        notificationDisplayed = False
        outputFileName = self.getOutputFilename(threadData['program'])
        destinationFile = os.path.join(self.recordDestinationPath, outputFileName)
        partNumber = 1
        nrOfReattempts = 0

        while success == False and nrOfReattempts <= maxNrOfReattempts and self.terminating == False and threadData['terminateThread'] == False and M_TVGUIDE_CLOSING == False:
            for url in threadData['urlList']:
                if success == True or self.terminating == True or threadData['terminateThread'] == True or nrOfReattempts > maxNrOfReattempts or M_TVGUIDE_CLOSING == True:
                    break

                recordCommand = None
                timeDiff = threadData['program'].endDate - datetime.datetime.now()
                programDuration = ((timeDiff.days * 86400) + timeDiff.seconds) - 5
                if programDuration <= 0:
                    deb('RecordService recordLoop aborting record for program %s, starting at: %s because program has already ended!' % (threadData['program'].title.encode('utf-8'), threadData['program'].startDate))
                    return

                cid, service = self.parseUrl(url)
                channelInfo = self.getChannel(cid, service)
                if channelInfo is None:
                    nrOfReattempts = nrOfReattempts + 1
                    deb('RecordService recordLoop - locked service %s - trying next, nrOfReattempts: %d, max: %d' % (service, nrOfReattempts, maxNrOfReattempts))
                    continue #go to next stream - this one seems to be locked

                while os.path.isfile(destinationFile): #Generate output filename which is not used
                    partNumber = partNumber + 1
                    outputFileName = self.getOutputFilename(threadData['program'], partNumber)
                    destinationFile = os.path.join(self.recordDestinationPath, outputFileName)

                if self.useOnlyFFmpeg == 'false' and channelInfo.rtmpdumpLink is not None:
                    if os.path.isfile(self.rtmpdumpExe):
                        recordCommand = list()
                        recordCommand.append(self.rtmpdumpExe)
                        recordCommand.extend(channelInfo.rtmpdumpLink)
                        recordCommand.append("--realtime")
                        recordCommand.append("--timeout")
                        recordCommand.append("5")
                        recordCommand.append("--hashes")
                        recordCommand.append("--live")
                        recordCommand.append("-B")
                        recordCommand.append("%d" % programDuration)
                        recordCommand.append("-o")
                        recordCommand.append(destinationFile)
                    else:
                        missingRtmpdumpBinary = True

                elif channelInfo.ffmpegdumpLink is not None:
                    if os.path.isfile(self.ffmpegdumpExe):
                        recordCommand = list()
                        recordCommand.append(self.ffmpegdumpExe)
                        recordCommand.extend(channelInfo.ffmpegdumpLink)
                        recordCommand.append("-c")
                        recordCommand.append("copy")
                        recordCommand.append("-f")
                        recordCommand.append("%s" % ADDON.getSetting('ffmpeg_format'))
                        recordCommand.append("-t")
                        recordCommand.append("%d" % programDuration)
                        recordCommand.append("-loglevel")
                        recordCommand.append("info")
                        recordCommand.append("-n")
                        recordCommand.append("-bsf:a")
                        recordCommand.append("aac_adtstoasc")
                        recordCommand.append("%s%s" % (self.recordDestinationPath, outputFileName))
                    else:
                        missingFfmpegumpBinary = True

                else:
                    if os.path.isfile(self.ffmpegdumpExe):
                        recordCommand = list()
                        recordCommand.append(self.ffmpegdumpExe)
                        recordCommand.append("-i")
                        recordCommand.append("%s" % channelInfo.strm)
                        recordCommand.append("-c")
                        recordCommand.append("copy")
                        recordCommand.append("-f")
                        recordCommand.append("%s" % ADDON.getSetting('ffmpeg_format'))
                        recordCommand.append("-t")
                        recordCommand.append("%d" % programDuration)
                        recordCommand.append("-loglevel")
                        recordCommand.append("info")
                        recordCommand.append("-n")
                        recordCommand.append("-bsf:a")
                        recordCommand.append("aac_adtstoasc")
                        recordCommand.append("%s%s" % (self.recordDestinationPath, outputFileName))
                    else:
                        missingFfmpegumpBinary = True

                if recordCommand is None:
                    nrOfReattempts = nrOfReattempts + 1
                else:
                    if notificationDisplayed == False:
                        xbmc.executebuiltin('Notification(%s,%s,10000,%s)' % (recordNotificationName, self.normalizeString(threadData['program'].title), self.icon))
                        notificationDisplayed = True #show only once
                    recordStartTime = datetime.datetime.now()
                    output = self.record(recordCommand, programDuration, threadData)
                    recordedSecs = (datetime.datetime.now() - recordStartTime).seconds
                    if(programDuration - recordedSecs < 60):
                        deb('RecordService recordLoop successfully recored program: %s, started at: %s, ended at: %s, duration %d, now: %s' % (threadData['program'].title.encode('utf-8', 'ignore'), threadData['program'].startDate, threadData['program'].endDate, programDuration, datetime.datetime.now()))
                        success = True
                    else:
                        deb('RecordService recordLoop ERROR: too short recording, got: %d sec, should be: %d, program: %s, start at: %s, end at: %s, nrOfReattempts: %d, max: %d' % (recordedSecs, programDuration, threadData['program'].title.encode('utf-8', 'ignore'), threadData['program'].startDate, threadData['program'].endDate, nrOfReattempts, maxNrOfReattempts))
                        nrOfReattempts = nrOfReattempts + 1
                        if os.path.isfile(destinationFile) and os.path.getsize(destinationFile) < 2097152: #Less then 2MB, remove downloaded data
                            try:
                                deb('RecordService recordLoop deleting incomplete record file %s, recorded for %d s, size %d KB' % (destinationFile, recordedSecs, os.path.getsize(destinationFile)/1024))
                                os.remove(destinationFile)
                            except:
                                pass

                self.unlockService(service)
                if self.terminating == True or M_TVGUIDE_CLOSING == True or threadData['terminateThread'] == True:
                    deb('RecordService recordLoop abort requested - terminating')

            if missingRtmpdumpBinary or missingFfmpegumpBinary:
                binaryname = 'RTMPDUMP'
                if missingFfmpegumpBinary == True and missingRtmpdumpBinary == False:
                    binaryname = 'FFMPEG'
                xbmcgui.Dialog().ok(failedRecordDialogName, "\n" + missingRecordBinaryString + binaryname)
                break

            if success == False:
                if nrOfReattempts <= maxNrOfReattempts:
                    for sleepTime in range(5):
                        if self.terminating == True or threadData['terminateThread'] == True or M_TVGUIDE_CLOSING:
                            break
                        time.sleep(1) #Go to sleep, maybe after that any service will be free to use
        deb('RecordService - end of recording program: %s' % threadData['program'].title.encode('utf-8', 'ignore'))
        if notificationDisplayed == True:
            xbmc.executebuiltin('Notification(%s,%s,10000,%s)' % (finishedRecordNotificationName, self.normalizeString(threadData['program'].title), self.icon))

        if self.cleanupTimer is not None:
            self.cleanupTimer.cancel()
        self.cleanupTimer = threading.Timer(0.2, self.cleanupFinishedThreads)
        self.cleanupTimer.start()

    def record(self, recordCommand, programDuration, threadData):
        deb('RecordService record command: %s' % str(recordCommand))
        output = ''
        si = None
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        recordEnviron = os.environ.copy()
        oldLdPath = recordEnviron.get("LD_LIBRARY_PATH", '')
        recordEnviron["LD_LIBRARY_PATH"] = os.path.join(os.path.dirname(recordCommand[0]), 'lib') + ':/lib:/usr/lib:/usr/local/lib'
        if oldLdPath != '':
            recordEnviron["LD_LIBRARY_PATH"] = recordEnviron["LD_LIBRARY_PATH"] + ":" + oldLdPath
        try:
            threadData['stopRecordTimer'] = threading.Timer(programDuration + 5, self.stopRecord, [threadData])
            threadData['stopRecordTimer'].start()
            threadData['recordHandle'] = subprocess.Popen(recordCommand, shell=False, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si, env=recordEnviron)
            output = threadData['recordHandle'].communicate()[0]
            returnCode = threadData['recordHandle'].returncode
            threadData['stopRecordTimer'].cancel()
            threadData['recordHandle'] = None
            deb('RecordService record finished, \noutput: %s, \nstatus: %d, Command: %s' % (output, returnCode, str(recordCommand)))
        except Exception, ex:
            deb('RecordService record exception: %s' % str(ex))
        return output

    def stopRecord(self, threadData, kill = False):
        if threadData['recordHandle'] is not None:
            try:
                threadData['recordHandle'].terminate()
                #if kill == True:
                    #threadData['recordHandle'].kill()
            except:
                pass

    def close(self):
        deb('RecordService close')
        self.terminating = True
        for element in self.timers[:]:
            element[1].cancel()
        self.timers = list()

        for thread in self.threadList[:]:
            if thread[0].is_alive():
                self.stopRecord(thread[1], kill = True) #stop all recordings
        for thread in self.threadList[:]:
            if thread[0].is_alive():
                thread[0].join(30) #wait for threads to clean up
        self.threadList = list()
        if self.cleanupTimer is not None:
            self.cleanupTimer.cancel()

    def getScheduledRecordingsForThisTime(self, startDate):
        for element in self.timers:
            if element[0] == startDate:
                debug('RecordService getScheduledRecordingsForThisTime found programs starting at %s' % startDate)
                return element
        debug('RecordService getScheduledRecordingsForThisTime no programs starting at %s' % startDate)
        return None

    def normalizeString(self, text):
        nkfd_form = unicodedata.normalize('NFKD', unicode(text))
        return (u"".join([c for c in nkfd_form if not unicodedata.combining(c)])).encode('ascii', 'ignore')

    def getOutputFilename(self, program, partNumber = 0):
        filename = self.normalizeString(program.title).replace(' ', '_').replace('?', '').replace(';', '').replace(':', '').replace('>', '').replace('<', '').replace('\\', '').replace('*', '').replace('"', ' ').replace('|', '').replace('/', '')  + "_" + str(program.startDate.strftime("%Y-%m-%d_%H-%M"))
        if partNumber > 1:
            filename = filename + "_part_%d" % partNumber
        return filename + ".flv"

    def getListOfFilenamesForProgram(self, program):
        debug('getListOfFilenamesForProgram')
        filenameList = list()
        filename = self.getOutputFilename(program)
        filePath = xbmc.translatePath(os.path.join(self.recordDestinationPath, filename))
        partNumber = 1
        while os.path.isfile(filePath):
            filenameList.append(filePath)
            partNumber = partNumber + 1
            filename = self.getOutputFilename(program, partNumber)
            filePath = os.path.join(self.recordDestinationPath, filename)
        return filenameList

    def isProgramRecorded(self, program):
        debug('RecordService isProgramRecorded program: %s' % program.title.encode('utf-8'))
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        filenameList = self.getListOfFilenamesForProgram(program)
        for filename in filenameList:
            playlist.add(url=filename)

        if playlist.size() > 0:
            return playlist
        return None

    def isProgramScheduled(self, program):
        if program is None:
            return False
        element = self.getScheduledRecordingsForThisTime(program.startDate)
        if element is not None: #Scheduled for future
            programList = element[2]
            for prog in programList:
                if program.channel == prog.channel:
                    return True
        for thread in self.threadList:
            if not thread[0].is_alive():
                continue
            threadData = thread[1]
            prog = threadData['program'] #program recorded by this thread
            if program.channel == prog.channel and program.startDate == prog.startDate:
                return True
        return False

    def cancelProgramRecord(self, program): #wylaczyc akturalnie nagrywany program?
        element = self.getScheduledRecordingsForThisTime(program.startDate)
        if element is not None:
            programList = element[2]
            try:
                for prog in programList:
                    if program.channel == prog.channel:
                        programList.remove(prog)
                        if len(programList) == 0:
                            element[1].cancel()
                            self.timers.remove(element)
                        debug('RecordService canceled scheduled recording of: %s' % program.title.encode('utf-8'))
                        return
            except:
                pass

        for thread in self.threadList:
            if not thread[0].is_alive():
                continue
            threadData = thread[1]
            prog = threadData['program']
            if program.channel == prog.channel and program.startDate == prog.startDate:
                threadData['terminateThread'] = True
                self.stopRecord(threadData)
                debug('RecordService canceled ongoing recording of: %s' % program.title.encode('utf-8'))
                return

    def cleanupFinishedThreads(self):
        for thread in self.threadList[:]:
            if not thread[0].is_alive():
                self.threadList.remove(thread)

    def isRecordOngoing(self):
        for thread in self.threadList:
            if thread[0].is_alive():
                return True
        return False

    def isRecordScheduled(self):
        if len(self.timers) > 0:
            return True
        return False

    def removeRecordedProgram(self, program):
        debug('removeRecordedProgram')
        if program is None:
            deb('removeRecordedProgram got faulty program!!!!')
        filenameList = self.getListOfFilenamesForProgram(program)
        for filename in filenameList:
            try:
                os.remove(filename)
                debug('removeRecordedProgram removing %s' % filename)
            except Exception, ex:
                deb('removeRecordedProgram exception: %s' % str(ex))
