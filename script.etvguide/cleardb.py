#
#      Copyright (C) 2014 Sean Poyser and Richard Dean (write2dixie@gmail.com)
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
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import xbmcgui
import xbmcaddon
import notification
import xbmc
import source
from strings import *
import ConfigParser

def deleteDB():
    try:
        import glob
        xbmc.log('Deleting database...')
        profilePath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
        dbFile  = os.path.join(profilePath, 'source.db')
        os.remove(dbFile)

    
        passed = (not os.path.exists(dbFile))

        if passed: 
            xbmc.log('Deleting database...PASSED')
        else:
            xbmc.log('Deleting database...FAILED')

        return passed

    except Exception, e:
        xbmc.log('Deleting database...EXCEPTION %s' % str(e))
        return False



if __name__ == '__main__':
    
    d = xbmcgui.Dialog()
    if deleteDB():
        d.ok('EPG successfully reset.', 'It will be re-created next time you start the guide')    
    
    else:
        d.ok('Failed to reset EPG.', 'Database may be locked,', 'please restart Kodi and try again')
