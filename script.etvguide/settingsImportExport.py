#
#      Copyright (C) 2016 Andrzej Mleczko
#
import os
import xbmc
import xbmcgui
import io, zipfile
from strings import *
import datetime

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

settingI = SettingsImp()
