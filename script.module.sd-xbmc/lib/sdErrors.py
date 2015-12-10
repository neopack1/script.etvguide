# -*- coding: utf-8 -*-
import os, string
import urllib, urllib2, re, sys, math
import xbmcgui, xbmc, xbmcaddon, xbmcplugin
import sdLog, sdNavigation

pmod = xbmcaddon.Addon(id='script.module.sd-xbmc')
t = lambda x: pmod.getLocalizedString(x).encode('utf-8')

log = sdLog.pLog()
dbg = sys.modules[ "__main__" ].dbg

ERRORS = [
	[ 'HTTP Error 403: Forbidden', t(55900), t(55901) ],
	[ 'HTTP Error 404: Not Found', t(55900), t(55910) ],
	[ 'urlopen error [Errno -2]', t(55900), t(55902) ],
	[ 'No JSON object could be decoded', t(55903), t(55904) ],
	[ '\'NoneType\' object has no attribute', t(55900), t(55905) ],
	[ 'global name', t(55900), t(55906) ],
	[ 'cannot concatenate', t(55900), t(55906) ],
	[ 'expected string or buffer', t(55900), t(55906) ],
	[ 'Expecting property name:', t(55900), t(55906) ],
	[ 'urlopen error timed out', t(55900), t(55907) ],
	[ '[Errno 2]', t(55900), t(55906) ],
	[ '[Errno 10035]', t(55900), t(55906) ],
	[ 'xml.parsers.expat.ExpatError', t(55900), t(55908)],
	[ 'must be string or read-only character buffer', t(55900), t(55909) ],
	[ 'not a valid non-string sequence or mapping object', t(55900), t(55909) ],
]

HTTP_CODES = {
	200: "OK",
	201: "Created",
	202: "Accepted",
	203: "Non-Authoritative Information",
	204: "No Content",
	205: "Reset Content",
	206: "Partial Content",
	300: "Multiple Choices",
	301: "Moved Permanently",
	302: "Found",
	303: "See Other",
	304: "Not Modified",
	305: "Use Proxy",
	306: "Unused",
	307: "Temporary Redirect",
	308: "Permanent Redirect",
	400: "Bad Request",
	401: "Unauthorized",
	402: "Payment Required",
	403: "Forbidden",
	404: "Not Found",
	405: "Method Not Allowed",
	406: "Not Acceptable",
	407: "Proxy Authentication Required",
	408: "Request Timeout",
	409: "Conflict",
	410: "Gone",
	411: "Length Required",
	412: "Precondition Required",
	413: "Request Entry Too Large",
	414: "Request-URI Too Long",
	415: "Unsupported Media Type",
	416: "Requested Range Not Satisfiable",
	417: "Expectation Failed",
	418: "I'm a teapot",
	428: "Precondition Required",
	429: "Too Many Requests",
	431: "Request Header Fields Too Large",
	500: "Internal Server Error",
	501: "Not Implemented",
	502: "Bad Gateway",
	503: "Service Unavailable",
	504: "Gateway Timeout",
	505: "HTTP Version Not Supported",
	511: "Network Authentication Required"
}

class Exception:
	def __init__(self):
		self.gui = sdNavigation.sdGUI()

	def getError(self, error):
		title = ''
		content = ''
		d = xbmcgui.Dialog()
		if dbg == 'true':
			log.info('Errors - getError()')
		for i in range(len(ERRORS)):
			log.info('Errors - getError()[for] ' + ERRORS[i][0] + ' = ' + error)
			if ERRORS[i][0] in error:
				log.info('Errors - getError()[for] ' + ERRORS[i][0] + ' = ' + error)
				title = ERRORS[i][1]
				content1 = ERRORS[i][2]
				content2 = error
				break
			elif (i + 1) == len(ERRORS):
				title = t(55900)
				content1 = t(55906)
				content2 = error
		d.ok(title, content1, content2)
		
	def getHttpError(self, error):
		errormsg = "Błąd "+str(error)+" - "+HTTP_CODES[int(error)]
		self.gui.notification("Błąd połączenia", errormsg)