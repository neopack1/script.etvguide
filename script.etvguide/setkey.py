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
import ConfigParser
from strings import *
import datetime
import threading
import time
import ConfigParser
import xbmc
from xbmcgui import Dialog, WindowXMLDialog
import source as src
from notification import Notification
import re, sys, os
import streaming

config = ConfigParser.RawConfigParser()
config.read(os.path.join(ADDON.getAddonInfo('path'), 'resources', 'skins', ADDON.getSetting('Skin'), 'settings.ini'))
try:
    skin_resolution = config.getboolean("Skin", "resolution")
except:
    skin_resolution = '720p'

class KeyListener(WindowXMLDialog):

  def __new__(cls):
    return super(KeyListener, cls).__new__(cls, 'DialogSetKey.xml', ADDON.getAddonInfo('path'), ADDON.getSetting('Skin'), skin_resolution)

  def onInit(self):
    self.key = 0
    self.a_info = 0
    self.a_home = 0
    self.a_stop = 0
    self.a_pp = 0
    self.a_pm = 0
    self.a_ctxt = 0
    self.a_rec = 0
    self.a_volUp = 0
    self.a_volDown = 0
    self.getControl(7001).setLabel(str(ADDON.getSetting('info_key')))
    self.getControl(7002).setLabel(str(ADDON.getSetting('stop_key')))
    self.getControl(7003).setLabel(str(ADDON.getSetting('pp_key')))
    self.getControl(7004).setLabel(str(ADDON.getSetting('pm_key')))
    self.getControl(7005).setLabel(str(ADDON.getSetting('home_key')))
    self.getControl(7006).setLabel(str(ADDON.getSetting('context_key')))
    self.getControl(7007).setLabel(str(ADDON.getSetting('record_key')))
    self.getControl(7009).setLabel(str(ADDON.getSetting('volume_up_key')))
    self.getControl(7010).setLabel(str(ADDON.getSetting('volume_down_key')))

  def onAction(self, action):

    if action.getId() == 107 or action.getId() == 100 or action.getId() == 7 or action.getButtonCode() == 61453 or action.getId() == 10:
        return
    else:
       self.key = action.getButtonCode()
       if self.key == 0:
            self.key = action.getId()

       if self.a_info == 1 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
          ADDON.setSetting(id="info_key", value=str(self.key))
          self.getControl(7001).setLabel(str(self.key))
          self.getControl(7001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_info = 0
       if self.a_info == 0 and self.a_stop == 1 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
          ADDON.setSetting(id="stop_key", value=str(self.key))
          self.getControl(7002).setLabel(str(self.key))
          self.getControl(7002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_stop = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 1 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
          ADDON.setSetting(id="pp_key", value=str(self.key))
          self.getControl(7003).setLabel(str(self.key))
          self.getControl(7003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_pp = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 1 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
          ADDON.setSetting(id="pm_key", value=str(self.key))
          self.getControl(7004).setLabel(str(self.key))
          self.getControl(7004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_pm = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 1 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
          ADDON.setSetting(id="home_key", value=str(self.key))
          self.getControl(7005).setLabel(str(self.key))
          self.getControl(7005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_home = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 1 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
          ADDON.setSetting(id="context_key", value=str(self.key))
          self.getControl(7006).setLabel(str(self.key))
          self.getControl(7006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_ctxt = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 1 and self.a_volUp == 0 and self.a_volDown == 0:
          ADDON.setSetting(id="record_key", value=str(self.key))
          self.getControl(7007).setLabel(str(self.key))
          self.getControl(7007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_rec = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 1 and self.a_volDown == 0:
          ADDON.setSetting(id="volume_up_key", value=str(self.key))
          self.getControl(7009).setLabel(str(self.key))
          self.getControl(7009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_volUp = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 1:
          ADDON.setSetting(id="volume_down_key", value=str(self.key))
          self.getControl(7010).setLabel(str(self.key))
          self.getControl(7010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_volDown = 0

  def onClick(self, controlId):
        if controlId == 9001 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_info = 1
            self.getControl(7001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9002 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_stop = 1
            self.getControl(7002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9003 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_pp = 1
            self.getControl(7003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9004 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_pm = 1
            self.getControl(7004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9005 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_home = 1
            self.getControl(7005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9006 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_ctxt = 1
            self.getControl(7006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9007 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_rec = 1
            self.getControl(7007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9008 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            deb('Key settings reset!')
            ADDON.setSetting(id="info_key", value=str(''))
            ADDON.setSetting(id="stop_key", value=str(''))
            ADDON.setSetting(id="pp_key", value=str(''))
            ADDON.setSetting(id="pm_key", value=str(''))
            ADDON.setSetting(id="home_key", value=str(''))
            ADDON.setSetting(id="context_key", value=str(''))
            ADDON.setSetting(id="record_key", value=str(''))
            ADDON.setSetting(id="volume_up_key", value=str(''))
            ADDON.setSetting(id="volume_down_key", value=str(''))
            self.close()
            xbmcgui.Dialog().ok(strings(31013).encode('utf-8'),"\n" + strings(310014).encode('utf-8'))

        if controlId == 9009 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_volUp = 1
            self.getControl(7009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9010 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.a_volDown = 1
            self.getControl(7010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9099 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_volUp == 0 and self.a_volDown == 0:
            self.close()


if __name__ == '__main__':
    dialog = KeyListener()
    dialog.doModal()
    del dialog
