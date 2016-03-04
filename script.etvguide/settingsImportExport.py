#
#      Copyright (C) 2016 Andrzej Mleczko
#
import os
import stat
import xbmc
import xbmcgui
import io, zipfile
from strings import *
import datetime
import shutil
import platform
import subprocess
import urllib, urllib2, httplib

compressionType = zipfile.ZIP_STORED
try:
    import zlib
    compressionType = zipfile.ZIP_DEFLATED
except:
    pass

dbFileName = 'source.db'
settingsFileName = 'settings.xml'
WINDOWS_OS_NAME = 'Windows'
ANDROID_OS_NAME = 'Android'
OPENELEC_OS_NAME = 'OpenELEC'
LINUX_OS_NAME = 'Linux'
OSMC_OS_NAME = 'OSMC'
OTHER_OS_NAME = 'Other'

recordAppWindows = 'http://mods-kodi.pl/m-tvguide/record_apps/recording_windows.zip'
recordAppAndroid = 'http://mods-kodi.pl/m-tvguide/record_apps/recording_android.zip'

class SettingsImp:
    def __init__(self):
        self.profilePath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
        self.command = sys.argv[1]
        if self.command is None or self.command == '':
            return
        deb('SettingsImp __init__ command %s' % self.command)
        if self.command == 'Import':
            self.importSettings()
        elif self.command == 'Export':
            self.exportSettings()
        elif self.command == 'ImportRecordApp':
            try:
                recordApp = sys.argv[2]
            except:
                recordApp = None
            self.importRecordApp(recordApp)
        elif self.command == 'DownloadRecordAppFromModsKodi':
            self.downloadRecordApp()

    def exportSettings(self):
        success = False
        dirname = xbmcgui.Dialog().browseSingle(type=3, heading=strings(58001).encode('utf-8'), shares='files')
        filename = 'm-TVGuide_backup_' + str(datetime.datetime.now().strftime("%Y-%m-%d")) + '.zip'
        if dirname is not None and dirname != '':
            if os.path.isdir(self.profilePath) == False:
                xbmcgui.Dialog().ok(strings(58002).encode('utf-8'),"\n" + strings(58004).encode('utf-8'))
                return success

            deb('SettingsImp exportSettings to file %s' % os.path.join(dirname, filename))

            zf = zipfile.ZipFile(os.path.join(dirname, filename), mode='w', compression=compressionType)
            try:
                if os.path.isfile(os.path.join(self.profilePath, dbFileName)):
                    zf.write(os.path.join(self.profilePath, dbFileName), dbFileName)
                    success = True
                if os.path.isfile(os.path.join(self.profilePath, settingsFileName)):
                    zf.write(os.path.join(self.profilePath, settingsFileName), settingsFileName)
                    success = True
            finally:
                zf.close()
            if success == True:
                xbmcgui.Dialog().ok(strings(58002).encode('utf-8'),"\n" + strings(58005).encode('utf-8'))
            else:
                xbmcgui.Dialog().ok(strings(58002).encode('utf-8'),"\n" + strings(58006).encode('utf-8'))
        return success

    def importSettings(self):
        success = False
        filename = xbmcgui.Dialog().browseSingle(type=1, heading=strings(58007).encode('utf-8'), shares='files', mask='.zip')
        if filename is not None and filename != '':
            deb('SettingsImp importSettings file %s' % filename)
            if os.path.isdir(self.profilePath) == False:
                os.makedirs(self.profilePath)

            zf = zipfile.ZipFile(filename)
            for fileN in [ dbFileName, settingsFileName ]:
                try:
                    zf.extract(fileN, self.profilePath)
                    success = True
                except Exception, ex:
                    deb('SettingsImp importSettings: Error got exception %s while reading archive %s' % (str(ex), filename))
            if success == True:
                xbmcgui.Dialog().ok(strings(58003).encode('utf-8'),"\n" + strings(58008).encode('utf-8'))
                xbmc.executebuiltin('Addon.OpenSettings(%s)' % ADDON_ID)
            else:
                xbmcgui.Dialog().ok(strings(58003).encode('utf-8'),"\n" + strings(58009).encode('utf-8') + "\n" + strings(58010).encode('utf-8'))
        return success

    def importRecordApp(self, filename):
        try:
            binaryFinalPath = None
            xbmcRootDir = xbmc.translatePath('special://xbmc')
            if filename is None:
                filename = xbmcgui.Dialog().browseSingle(type=1, heading=strings(69012).encode('utf-8'), shares='files')
            if filename == '':
                deb('importRecordApp no file selected for import!')
                return
            binaryFilename = os.path.basename(filename)
            deb('RecordAppImporter filepath: %s, filename: %s' % (filename, binaryFilename))

            if '/data/data' in xbmcRootDir:
                #android
                recordDirName = 'recapp-' +  os.name
                recordAppDir = os.path.join(xbmcRootDir.replace('cache/apk/assets/', ''), recordDirName)
                recordAppLibDir = os.path.join(recordAppDir, 'lib')
                deb('RecordAppImporter recordAppDir: %s, recordAppLibDir: %s' % (recordAppDir, recordAppLibDir))

                if 'ffmpeg' in binaryFilename or 'rtmpdump' in binaryFilename or 'avconv' in binaryFilename:
                    try:
                        os.makedirs(recordAppDir)
                    except:
                        pass
                    try:
                        os.makedirs(recordAppLibDir)
                    except:
                        pass
                    deb('RecordAppImporter copying files')
                    try:
                        shutil.copy2(filename, recordAppDir)
                    except:
                        pass
                    fileLib = os.path.join(os.path.dirname(filename), 'lib')
                    if os.path.isdir(fileLib):
                        for filen in os.listdir(fileLib):
                            deb('importRecordApp copy file from lib: %s' % filen)
                            try:
                                shutil.copy2(os.path.join(fileLib, filen), recordAppLibDir)
                            except:
                                pass

                    binaryFinalPath = os.path.join(recordAppDir, binaryFilename)
            else:
                #other than android
                if 'ffmpeg' in binaryFilename or 'rtmpdump' in binaryFilename or 'avconv' in binaryFilename:
                    binaryFinalPath = filename

            if binaryFinalPath is not None:
                if os.path.isfile(binaryFinalPath):
                    try:
                        st = os.stat(binaryFinalPath)
                        os.chmod(binaryFinalPath, st.st_mode | stat.S_IEXEC)
                    except:
                        deb('Unable to set exec permissions to file %s' % binaryFinalPath)
                    if 'ffmpeg' in binaryFilename or 'avconv' in binaryFilename:
                        deb('importRecordApp setting ffmpeg app to: %s' % binaryFinalPath)
                        ADDON.setSetting(id="ffmpegExe", value=str(binaryFinalPath))
                        xbmcgui.Dialog().ok(strings(69012).encode('utf-8'),"\n" + 'ffmpeg ' + strings(69013).encode('utf-8'))

                    if 'rtmpdump' in binaryFilename:
                        deb('importRecordApp setting rtmpdump app to: %s' % binaryFinalPath)
                        ADDON.setSetting(id="rtmpdumpExe", value=str(binaryFinalPath))
                        xbmcgui.Dialog().ok(strings(69012).encode('utf-8'),"\n" + 'rtmpdump ' + strings(69013).encode('utf-8'))
                else:
                    deb('importRecordApp error destination file: %s does not exist' % binaryFinalPath)

        except Exception, ex:
            deb('RecordAppImporter Error: %s' % str(ex))
            raise

    def downloadRecordApp(self):
        recordApp = None
        rtmpdumpExe = None
        ffmpegExe = None
        failedToDownload = False
        failedToFindBinary = False

        if platform.system() == WINDOWS_OS_NAME: # WINDOWS_OS_NAME:
            deb('downloadRecordApp detected os = %s, downloading recordApp from %s' % (platform.system(), recordAppWindows))
            recordApp = recordAppWindows
        else:
            deb('downloadRecordApp detected os family = %s, please select your operating system' % platform.system())
            systems = list()
            systems.append(strings(30204).encode('utf-8', 'replace'))
            systems.append(WINDOWS_OS_NAME)
            systems.append(ANDROID_OS_NAME)
            systems.append(OPENELEC_OS_NAME)
            systems.append(LINUX_OS_NAME)
            systems.append(OSMC_OS_NAME)
            systems.append(OTHER_OS_NAME)
            ret = xbmcgui.Dialog().select(strings(69023).encode('utf-8', 'replace'), systems)
            if ret > 0:
                system = systems[ret]
                deb('downloadRecordApp %s was choosen' % system)
                if system == WINDOWS_OS_NAME:
                    recordApp = recordAppWindows
                elif system == ANDROID_OS_NAME:
                    recordApp = recordAppAndroid
                elif system == OPENELEC_OS_NAME or system == LINUX_OS_NAME or system == OTHER_OS_NAME or system == OSMC_OS_NAME:
                    possibleAppDirs = ['/bin', '/usr/local/bin', '/usr/bin']
                    defaultRtmpdumpExe = 'rtmpdump'
                    defaultFFmpegExe1 = 'ffmpeg'
                    defaultFFmpegExe2 = 'avconv'
                    for path in possibleAppDirs:
                        if os.path.isfile(os.path.join(path, defaultRtmpdumpExe)):
                            rtmpdumpExe = os.path.join(path, defaultRtmpdumpExe)
                        if os.path.isfile(os.path.join(path, defaultFFmpegExe1)):
                            ffmpegExe = os.path.join(path, defaultFFmpegExe1)
                        elif os.path.isfile(os.path.join(path, defaultFFmpegExe2)):
                            ffmpegExe = os.path.join(path, defaultFFmpegExe2)
                        #dopisac do importa obsluge nazwy avconv !!!!!!!!!!!!!
                    if rtmpdumpExe is None and ffmpegExe is None:
                        failedToFindBinary = True
                        #install libav-tools
            else:
                deb('downloadRecordApp Abort was choosen')
                return

        if recordApp is not None:
            xbmcgui.Dialog().ok(strings(69012).encode('utf-8', 'replace'),"\n" + strings(69018).encode('utf-8'))
            try:
                deb('downloadRecordApp downloading app from %s' % recordApp)
                recordAppDir = os.path.join(self.profilePath, 'record_app')
                if os.path.isdir(recordAppDir):
                    shutil.rmtree(recordAppDir)
                if os.path.isdir(recordAppDir) == False:
                    os.makedirs(recordAppDir)

                failCounter = 0
                content = None
                while failCounter < 10:
                    try:
                        u = urllib2.urlopen(recordApp, timeout=5)
                        content = u.read()
                        break
                    except httplib.IncompleteRead as ex:
                        failCounter = failCounter + 1
                        deb('downloadRecordApp download exception: %s, failCounter: %d - retrying' % (str(ex), failCounter))
                    except Exception, ex:
                        deb('downloadRecordApp download exception: %s, failCounter: %d - aborting' % (str(ex), failCounter))
                        break

                if content == None:
                    deb('downloadRecordApp failed to download record app from %s' % recordApp)
                    failedToDownload = True
                else:
                    memfile = io.BytesIO(content)
                    unziped = zipfile.ZipFile(memfile)
                    unziped.extractall(recordAppDir)
                    for filename in unziped.namelist():
                        if 'ffmpeg' in filename:
                            ffmpegExe = os.path.join(recordAppDir, filename)
                        elif 'rtmpdump' in filename:
                            rtmpdumpExe = os.path.join(recordAppDir, filename)

            except Exception, ex:
                deb('downloadRecordApp exception: %s!' % str(ex) )
                raise

        settingsImportScript = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'settingsImportExport.py')
        if ffmpegExe is not None:
            sys.argv = [settingsImportScript, 'ImportRecordApp', ffmpegExe]
            execfile(settingsImportScript)
        if rtmpdumpExe is not None:
            sys.argv = [settingsImportScript, 'ImportRecordApp', rtmpdumpExe]
            execfile(settingsImportScript)

        if ffmpegExe is not None and rtmpdumpExe is None:
            deb('downloadRecordApp found only FFmpeg but no rtmpdump - setting ffmpeg as only app')
            ADDON.setSetting(id="use_only_ffmpeg", value=str('true'))

        if failedToDownload == True:
            xbmcgui.Dialog().ok(strings(69012).encode('utf-8', 'replace'),"\n" + strings(69019).encode('utf-8'))
        elif failedToFindBinary == True:
            xbmcgui.Dialog().ok(strings(69012).encode('utf-8', 'replace'),"\n" + strings(69021).encode('utf-8'))
        elif ffmpegExe is None and rtmpdumpExe is None:
            xbmcgui.Dialog().ok(strings(69012).encode('utf-8', 'replace'),"\n" + strings(69022).encode('utf-8'))

settingI = SettingsImp()
