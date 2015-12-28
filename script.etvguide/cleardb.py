#
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
import datetime
import os
import xbmc
import xbmcgui
import source as src

from strings import *

class clearDB:
    
    def __init__(self):
        self.database = src.Database()
        self.command = sys.argv[1]
        deb('ClearDB onInitialized param %s' % self.command)
        if self.command == 'deleteDbFile':
            self.database.deleteDbFile()
            self.database.close()
            xbmcgui.Dialog().ok(strings(DB_DELETED), 'OK')
        else:
            self.database.initialize(self.onInitialized)

    def onDBCleared(self):
        xbmcgui.Dialog().ok(strings(CLEAR_DB), strings(DONE_DB))

    def onInitialized(self, success):
        if success:
            if self.command == 'clearAll':
                self.database.clearDB()
            if self.command == 'clearCustom':
                self.database.deleteAllStreams()
                
            self.database.close(self.onDBCleared)
        else:
            self.database.close()

    
cleardb = clearDB()

