# -*- coding: utf-8 -*-
'''
method getURLRequestData(params):
	params['use_host'] - True or False. If false the method can use global HOST
	params['host'] -  Use when params['outside_host'] is setting on True. Enter a own host
	params['use_cookie'] - True, or False. Enable using cookie
	params['cookiefile'] - Set cookie file
	params['save_cookie'] - True, or False. Save cookie to file
	params['load_cookie'] - True, or False. Load cookie
	params['url'] - Url address
	params['use_post'] - True, or False. Use post method.
	post_data - Post data
	params['return_data'] - True, or False. Return response read data.
	params['read_data'] - True, or False. Use when params['return_data'] is False.

	If you want to get data from url use this method (for default host):
	data = { 'url': <your url>, 'use_host': False, use_cookie': False, 'use_post': False, 'return_data': True }
	response = self.getURLRequestData(data)

	If you want to get XML, or JSON data then:
	data = { 'url': <your url>, 'use_host': False, use_cookie': False, 'use_post': False, 'return_data': False }
	response = self.getURLRequestData(data)

	If you want to get data with different user-agent then:
	data = { 'url': <your url>, 'use_host': True, 'host': <your own user-agent define>, use_cookie': False, 'use_post': False, 'return_data': True }
	response = self.getURLRequestData(data)

	If you want to save cookie file:
	data = { 'url': <your url>, 'use_host': True, 'host': <your own user-agent define>, 'use_cookie': True, 'load_cookie': False, 'save_cookie': True, 'cookiefile': <path to cookie file>, 'use_post': True, 'return_data': True }
	response = self.getURLRequestData(data, post_data)

	If you want to load cookie file:
	data = { 'url': <your url>, 'use_host': True, 'host': <your own user-agent define>, 'use_cookie': True, 'load_cookie': True, 'save_cookie': False, 'cookiefile': <path to cookie file>, 'use_post': True, 'return_data': True }
	response = self.getURLRequestData(data, post_data)

	If you want to load cookie file without post:
	data = { 'url': <your url>, 'use_host': True, 'host': <your own user-agent define>, 'use_cookie': True, 'load_cookie': True, 'save_cookie': False, 'cookiefile': <path to cookie file>, 'use_post': False, 'return_data': True }
	response = self.getURLRequestData(data)

	and etc...
'''

import re, os, sys, cookielib, random
try:
	from StringIO import StringIO
	import gzip
except:
	pass
import urllib, urllib2, re, sys, math, htmlentitydefs
import xbmcaddon, xbmc, xbmcgui
import hashlib, StorageServer
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

import sdLog, sdErrors

log = sdLog.pLog()

scriptID = sys.modules[ "__main__" ].scriptID
ptv = xbmcaddon.Addon(scriptID)

dbg = sys.modules[ "__main__" ].dbg

HOST_TABLE = {
	100: 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0',
	101: 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11',
	102: 'Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.11',
	103: 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
	104: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0',
	105: 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:17.0) Gecko/20100101 Firefox/17.0',
	106: 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11',
	107: 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
	108: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17',
	109: 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
	110: 'Opera/9.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.01',
	111: 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
	112: 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
	113: 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)',
}

HOST = 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'
	
cj = cookielib.LWPCookieJar()

CHARS = [
	[ ' ', '_' ],
	[ ',', '-' ],
	[ '!', '_' ],
	[ '?', '_' ],
	[ ':', '_' ],
	[ '/', '-' ],
	[ 'ą', 'a' ],
	[ 'Ą', 'A' ],
	[ 'ę', 'e' ],
	[ 'Ę', 'E' ],
	[ 'ć', 'c' ],
	[ 'Ć', 'C' ],
	[ 'ł', 'l' ],
	[ 'Ł', 'L' ],
	[ 'ń', 'n' ],
	[ 'Ń', 'N' ],
	[ 'ó', 'o' ],
	[ 'Ó', 'O' ],
	[ 'ś', 's' ],
	[ 'Ś', 'S' ],
	[ 'ż', 'z' ],
	[ 'Ż', 'Z' ],
	[ 'ź', 'z' ],
	[ 'Ź', 'Z' ],
]

class common:	
	def __init__(self, proxyURL= '', useProxy = False):
		self.proxyURL = proxyURL
		self.useProxy = useProxy

	def getCookieItem(self, cookiefile, item):
		ret = ''
		if os.path.isfile(cookiefile):
		    cj = cookielib.LWPCookieJar()
		    cj.load(cookiefile, ignore_discard = True)
		    for cookie in cj:
			if cookie.name == item: ret = cookie.value
		return ret

	#item = {'name': 'xxx', 'value': 'yyy', 'domain': 'zzz'}
	def addCookieItem(self, cookiefile, item, load_cookie=True):
		if load_cookie==True and os.path.isfile(cookiefile):
			cj.load(cookiefile, ignore_discard = True)
		c = cookielib.Cookie(0, item['name'], item['value'], None, False, item['domain'], False, False, '/', True, False, None, True, None, None, {})
		cj.set_cookie(c)
		cj.save(cookiefile, ignore_discard = True)
	
	def getPage(self, url, addParams = {}, post_data = None):
		''' wraps getURLRequestData '''
		try:
			addParams['url'] = url
			if 'return_data' not in addParams:
				addParams['return_data'] = True
			response = self.getURLRequestData(addParams, post_data)
			status = True
		except:
			if dbg == True:
				log.info('pCommon - getPage() -> exception: ' + traceback.format_exc())
			response = None
			status = False
		return (status, response)

	def getURLRequestData(self, params = {}, post_data = None):
		
		def urlOpen(req, customOpeners):
			if len(customOpeners) > 0:
				opener = urllib2.build_opener( *customOpeners )
				response = opener.open(req)
			else:
				response = urllib2.urlopen(req)
			return response
		
		cj = cookielib.LWPCookieJar()

		response = None
		req	  = None
		out_data = None
		opener   = None
		
		if 'host' in params:
			host = params['host']
		else:
			host = HOST

		if 'header' in params:
			headers = params['header']
		else:
			headers = { 'User-Agent' : host }

		if dbg == True:
			log.info('pCommon - getURLRequestData() -> params: ' + str(params))
			log.info('pCommon - getURLRequestData() -> params: ' + str(headers))

		customOpeners = []
		#cookie support
		if 'use_cookie' not in params and 'cookiefile' in params and ('load_cookie' in params or 'save_cookie' in params):
			params['use_cookie'] = True 
		
		if params.get('use_cookie', False):
			customOpeners.append( urllib2.HTTPCookieProcessor(cj) )
			if params.get('load_cookie', False):
				cj.load(params['cookiefile'], ignore_discard = True)
		#proxy support
		if self.useProxy == True:
			if dbg == True: log.info('getURLRequestData USE PROXY')
			customOpeners.append( urllib2.ProxyHandler({"http":self.proxyURL}) )

		if None != post_data:
			if dbg == True: log.info('pCommon - getURLRequestData() -> post data: ' + str(post_data))
			if params.get('raw_post_data', False):
				dataPost = post_data
			else:
				dataPost = urllib.urlencode(post_data)
			req = urllib2.Request(params['url'], dataPost, headers)
		else:
			req = urllib2.Request(params['url'], None, headers)

		if not params.get('return_data', False):
			out_data = urlOpen(req, customOpeners)
		else:
			gzip_encoding = False
			try:
				response = urlOpen(req, customOpeners)
				if response.info().get('Content-Encoding') == 'gzip':
					gzip_encoding = True
				data = response.read()
				response.close()
			except urllib2.HTTPError, e:
				sdErrors.Exception().getHttpError(e.code)
				raise
	
			if gzip_encoding:
				log.info('pCommon - getURLRequestData() -> Content-Encoding == gzip')
				buf = StringIO(data)
				f = gzip.GzipFile(fileobj=buf)
				out_data = f.read()
			else:
				out_data = data
 
		if params.get('use_cookie', False) and params.get('save_cookie', False):
			cj.save(params['cookiefile'], ignore_discard = True)

		return out_data 

	def makeABCList(self):
		strTab = []
		strTab.append('0 - 9');
		for i in range(65,91):
			strTab.append(str(unichr(i)))
		return strTab

	def getItemByChar(self, char, tab):
		strTab = []
		char = char[0]
		for i in range(len(tab)):
			if ord(char) >= 65:
				if tab[i][0].upper() == char:
					strTab.append(tab[i])
			else:
				if ord(tab[i][0]) >= 48 and ord(tab[i][0]) <= 57:
					strTab.append(tab[i])
		return strTab

	def isNumeric(self,s):
		try:
			float(s)
			return True
		except ValueError:
			return False

	def isEmptyDict(self, dictionry, key):
		if key in dictionry:
			if dictionry[key]:
				return False
		return True

	def checkDir(self, path):
		if not os.path.isdir(path):
			os.mkdir(path)

	def getRandomHost(self):
		host_id = random.choice(HOST_TABLE.keys())
		log.info("host ID: " + str(host_id))
		host = HOST_TABLE[host_id]
		return host

	def LOAD_AND_PLAY_VIDEO(self, url, title, player = True):
		if url == '':
			d = xbmcgui.Dialog()
			d.ok('Nie znaleziono streamingu', 'Może to chwilowa awaria.', 'Spróbuj ponownie za jakiś czas')
			return False
		thumbnail = xbmc.getInfoImage("ListItem.Thumb")
		liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
		liz.setInfo( type="Video", infoLabels={ "Title": title } )
		try:
			if player != True:
				print "custom player pCommon"
				xbmcPlayer = player
			else:
				print "default player pCommon"
				xbmcPlayer = xbmc.Player()
				xbmcPlayer.play(url, liz)
		except:
			d = xbmcgui.Dialog()
			d.ok('Błąd przy przetwarzaniu, lub wyczerpany limit czasowy oglądania.', 'Zarejestruj się i opłać abonament.', 'Aby oglądać za darmo spróbuj ponownie za jakiś czas')
			return False
		return True

	def formatDialogMsg(self, msg):
		valTab = []
		LENGTH = 56
		item = msg.split(' ');
		valTab.append('')
		valTab.append('')
		valTab.append('')

		if len(msg) <= LENGTH or len(item)==1:
			valTab[0] = msg
		else:
			isFull = [False, False]
			for i in item:
				if isFull[0] == False and isFull[1] == False:
					if len(valTab[0] + ' ' + i) <= LENGTH:
						s = valTab[0] + ' ' + i
						valTab[0] = s.strip()
					else:
						isFull[0] = True
				if isFull[0]:
					if len(valTab[1] + ' ' + i) <= LENGTH:
						s = valTab[1] + ' ' + i
						valTab[1] = s.strip()
					else:
						isFull[1] = True
				if isFull[1]:
					if len(valTab[2] + ' ' + i) <= LENGTH:
						s = valTab[2] + ' ' + i
						valTab[2] = s.strip()
					else:
						break
		return valTab

	def html_entity_decode_char(self, m):
		ent = m.group(1)
		if ent.startswith('x'):
			return unichr(int(ent[1:],16))
		try:
			return unichr(int(ent))
		except Exception, exception:
			if ent in htmlentitydefs.name2codepoint:
				return unichr(htmlentitydefs.name2codepoint[ent])
			else:
				return ent

	def html_entity_decode(self, string):
		string = string.decode('UTF-8')
		s = re.compile("&#?(\w+?);").sub(self.html_entity_decode_char, string)
		return s.encode('UTF-8')
	
	def __notification(self, title=" ", msg=" ", time=5000):
		''' cannot use sdNotification lib '''
		xbmc.executebuiltin("XBMC.Notification("+title+","+msg+","+str(time)+")")

	def requestLoginData(self, loginUrl, loginOKData, COOKIEFILE, loginData = {}, header = {}):
		if loginData == {}:
			self.__notification("Niezalogowany", "uzywam Player z limitami")
			return False
		else:
			self.checkDir(ptv.getAddonInfo('path') + os.path.sep + "cookies")
			query_data = { 'url': loginUrl, 'use_host': False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE, 'use_post': True, 'return_data': True }
			if header != {}: query_data.update({'use_header': True, 'header': header});
			data = self.getURLRequestData(query_data, loginData)
			if loginOKData in data:
				self.__notification("Sukces", "Zostałeś poprawnie zalogowany")
				return True
			else:
				self.__notification("Błąd logowania", "używam Player z limitami")
				return False

	def setLinkTable(self, url, host):
		strTab = []
		strTab.append(url)
		strTab.append(host)
		return strTab

	def getItemTitles(self, table):
		out = []
		for i in range(len(table)):
			value = table[i]
			out.append(value[1])
		return out

	def makeSTRMFile(self, service, title, params = {}):
		p =''
		if ptv.getSetting('default_strm') != 'None':
			strmdir = ptv.getSetting('default_strm') + service
			if not os.path.isdir(strmdir):
			   os.mkdir(strmdir)
			for k, v in params.iteritems():
			    p = p + k + "=" + urllib.quote_plus(v) + "&"
			    FILE = open(os.path.join(strmdir, "%s.strm" % ''.join(c for c in title if c in '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')),"w+")
			    FILE.write("plugin://plugin.video.polishtv.live/?service=%s&title=%s&%s" % (service, urllib.quote_plus(title), p))

class proxy:
	def __init__(self):
		self.common = common()
		#pass

	def useProxy(self, url):
		m = hashlib.md5()
		m.update(ptv.getSetting('donation_email') + ptv.getSetting('donation_password'))
		proxyUrl = 'http://sd-xbmc.info/support/proxy_auth.php?h=' + m.hexdigest() + '&u=' +  urllib.quote_plus(url)
		return proxyUrl

	def isAuthorized(self, data):
		if data == 'NOTOK (permission denied)':
			d = xbmcgui.Dialog()
			d.ok('sd-xbmc proxy', 'Nie jestes upowazniony do uzywania proxy.', 'Sprawdz email i haslo w ustawieniach wtyczki', 'lub odwiedz sd-xbmc.org w celu uzyskania dostepu.')
			return False
		return True
	
	def geoCheck(self):
		data = self.common.getPage('http://www.geoplugin.net/json.gp')
		if data[0]:
			try:
				result = _json.loads(data[1])
			except ValueError, e:
				exit()
			if result['geoplugin_countryCode'] == 'PL':
				return True
			else:
				return False
		return False

class history:
	def __init__(self):
		self.cache = StorageServer.StorageServer("SDXBMC")

	def addHistoryItem(self, service, item):
		item = item.decode('UTF-8')
		if item == "":
			return True
		historyLits = self.cache.get("history_"+service).split(";")
		if historyLits == ['']:
			historyLits = []
		historyLits.insert(0, item)
		from pprint import pprint
		pprint(historyLits)
		historyLits =  ';'.join(historyLits[:5])
		self.cache.set("history_"+service, historyLits)

	def clearHistoryItems(self, service):
		self.cache.delete("history_%")

	def loadHistoryFile(self, service):
		valTab = []
		historyLits = self.cache.get("history_"+service).split(";")
		for item in historyLits:
			valTab.append(item.encode('UTF-8'))
		return valTab

class Chars:
	def __init__(self):
		pass

	def setCHARS(self):
		return CHARS

	def replaceString(self, array, string):
		out = string
		for i in range(len(array)):
			out = string.replace(array[i][0], array[i][1])
			string = out
		return out

	def replaceChars(self, string):
		out = string
		for i in range(len(CHARS)):
			out = string.replace(CHARS[i][0], CHARS[i][1])
			string = out
		return out