#
#      Copyright (C) 2014 Krzysztof Cebulski
#      Copyright (C) 2013 Szakalit
#
#      Copyright (C) 2012 Tommy Winther
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
import xbmcaddon, xbmc

ADDON_ID            = 'script.etvguide'
ADDON               = xbmcaddon.Addon(id = ADDON_ID)
ADDON_PATH          = ADDON.getAddonInfo('path')
ADDON_CIDUPDATED    = False    #zabezpieczenie przed ponownym updatem cidow
ADDON_AUTOSTART     = False    #zabezpieczenie przed ponownym uruchomieniem wtyczki
FORCE_ADD_LOG_DEBUG = False     #True - Logowanie nawet jezeli wylaczone debugowanie w XBMC

NO_DESCRIPTION = 30000
CALCULATING_REMAINING_TIME = 30002
TIME_LEFT = 30003
BACKGROUND_UPDATE_IN_PROGRESS = 30004

NO_STREAM_AVAILABLE_TITLE = 30100
NO_STREAM_AVAILABLE_LINE1 = 30101
NO_STREAM_AVAILABLE_LINE2 = 30102

CLEAR_CACHE = 30104
CLEAR_NOTIFICATIONS = 30108
CLEAR_DB = 30950
DONE = 30105
DONE_DB = 30951

LOAD_ERROR_TITLE = 30150
LOAD_ERROR_LINE1 = 30151
LOAD_ERROR_LINE2 = 30152
CONFIGURATION_ERROR_LINE2 = 30153

SKIN_ERROR_LINE1 = 30154
SKIN_ERROR_LINE2 = 30155
SKIN_ERROR_LINE3 = 30156

NOTIFICATION_5_MINS = 30200
NOTIFICATION_NOW = 30201

WATCH_CHANNEL = 30300
REMIND_PROGRAM = 30301
DONT_REMIND_PROGRAM = 30302
CHOOSE_STRM_FILE = 30304
REMOVE_STRM_FILE = 30306

PREVIEW_STREAM = 30604
STOP_PREVIEW = 30607

WEEBTV_WEBTV_MISSING_1 = 30802
WEEBTV_WEBTV_MISSING_2 = 30803
WEEBTV_WEBTV_MISSING_3 = 30804

DATABASE_SCHEMA_ERROR_1 = 30157
DATABASE_SCHEMA_ERROR_2 = 30158
DATABASE_SCHEMA_ERROR_3 = 30159

#Controls ID
C_MAIN_TITLE = 4920         #nazwa programu telewizyjnego
C_MAIN_TIME = 4921          #godziny trwania progrmay
C_MAIN_DESCRIPTION = 4922   #opis programu tv
C_MAIN_IMAGE = 4923
C_MAIN_LOGO = 4924          #logo programu
C_MAIN_LIVE = 4944
C_PROGRAM_PROGRESS = 4999

C_MAIN_EPG = 5000

def strings(id, replacements = None):
    string = ADDON.getLocalizedString(id)
    if replacements is not None:
        return string % replacements
    else:
        return string

def getStateLabel(control, label_idx, default=0):
    """Pobiera z <label2>1234|5678</label2> na podstawie label_idx odpowiednia wartosc
       Jezeli chcesz uzyc tylko jednej wartosci wpisz tak:  1234|
       Jezeli nie wpiszesz znaku | to label2 zostanie uznane za puste - nie moga byc same cyfry
    """
    try:
        values = control.getLabel2().split("|")
        return int(values[label_idx])
    except Exception:
        pass
    return default

def deb(s):
    if FORCE_ADD_LOG_DEBUG:
        xbmc.log("MTVGUIDE @ " + str(s))
    else:
        xbmc.log("MTVGUIDE @ " + str(s), xbmc.LOGDEBUG)
