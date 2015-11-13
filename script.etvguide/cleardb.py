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


if __name__ == '__main__':
    database = src.Database()

    def onDBCleared():
        d = xbmcgui.Dialog()
        d.ok('e-TVGuide', 'Baza danych zostala usunieta.', 'Zostanie utworzona po uruchomieniu eTVGuide.')
        #xbmcgui.Dialog().ok(strings(CLEAR_DB), strings(DONE_DB))

    def onInitialized(success):
        if success:
            database.clearDB()
            database.close(onDBCleared)
        else:
            database.close()

    database.initialize(onInitialized)


