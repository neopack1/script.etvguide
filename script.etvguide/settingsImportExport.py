#
#      Copyright (C) 2016 Andrzej Mleczko
#
import os
import xbmc
import xbmcgui
import io, zipfile
from strings import *
import datetime
import shutil

compressionType = zipfile.ZIP_STORED
try:
    import zlib
    compressionType = zipfile.ZIP_DEFLATED
except:
    pass


dbFileName = 'source.db'
settingsFileName = 'settings.xml'

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
            self.importRecordApp()

    def exportSettings(self):
        success = False
        dirname = xbmcgui.Dialog().browseSingle(type=3, heading=strings(58001).encode('utf-8'), shares='pictures')
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
        filename = xbmcgui.Dialog().browseSingle(type=1, heading=strings(58007).encode('utf-8'), shares='pictures', mask='.zip')
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

    def importRecordApp(self):
        try:
            binaryFinalPath = None
            xbmcRootDir = xbmc.translatePath('special://xbmc')
            filename = xbmcgui.Dialog().browseSingle(type=1, heading=strings(69012).encode('utf-8'), shares='pictures')
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

                if 'ffmpeg' in binaryFilename or 'rtmpdump' in binaryFilename:
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
                if 'ffmpeg' in binaryFilename or 'rtmpdump' in binaryFilename:
                    binaryFinalPath = filename

            if binaryFinalPath is not None:
                if os.path.isfile(binaryFinalPath):
                    if 'ffmpeg' in binaryFilename:
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

settingI = SettingsImp()
