# -*- coding: utf-8 -*-
import xbmcaddon
import sys, os
import sdLog
from xml.dom import minidom

scriptID = sys.modules[ "__main__" ].scriptID
log = sdLog.pLog()

addon = xbmcaddon.Addon(scriptID)

class TVSettings:
	def __init__(self):
		pass
		
	def showSettings(self):
		addon.openSettings(sys.argv[0])
	
	def getSettings(self, service):
		valDict = {}
		settingsTab = self.getSettingsTab()
		for i in range(len(settingsTab)):
			if settingsTab[i][0] == service:
				valDict[settingsTab[i][1]] = addon.getSetting(settingsTab[i][1])
		return valDict

	def getSettingsTab(self):
		valTab = []
		strTab = []
		xmlfile = addon.getAddonInfo('path') + os.path.sep + 'resources' + os.path.sep + 'settings.xml'
		xmldoc = minidom.parse(xmlfile)
		setlist = xmldoc.getElementsByTagName('setting')  
		for i in range(len(setlist)):
			try: s = setlist[i].attributes["id"]
			except: pass
			else:
				s = s.value
				tab = s.split('_')
				strTab.append(tab[0])
				strTab.append(s)
				valTab.append(strTab)
				strTab = []
		return valTab
