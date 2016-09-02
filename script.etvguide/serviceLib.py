#      Copyright (C) 2016 Andrzej Mleczko

import urllib, urllib2, httplib, sys, StringIO, cookielib, re, socket, copy
from xml.etree import ElementTree
import simplejson as json
import xbmc
import time
import os, xbmcaddon
from strings import *
import strings as strings2
import threading
import datetime
import zlib

HOST        = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20121213 Firefox/19.0'
pathAddons  = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'addons.ini')
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')

try:
    MAX_CONNECTION_TIME = int(ADDON.getSetting('max_connection_time'))
except:
    MAX_CONNECTION_TIME = 30

HTTP_ConnectionTimeout = 5

class ShowList:
    def __init__(self, logCall=deb):
        self.logCall = logCall

    def decode(self, string):
        json_ustr = json.dumps(string, ensure_ascii=False)
        return json_ustr.encode('utf-8')

    def JsonToSortedTab(self, json):
        strTab = []
        outTab = []
        for v,k in json.iteritems():
            strTab.append(int(v))
            strTab.append(k)
            outTab.append(strTab)
            strTab = []
        outTab.sort(key=lambda x: x[0])
        return outTab

    def getJsonFromAPI(self, url, post={}):
        result_json = None
        raw_json = None
        try:
            data     = urllib.urlencode(post)
            reqUrl   = urllib2.Request(url, data)
            reqUrl.add_header('User-Agent', 'Python-urllib/2.1')
            reqUrl.add_header('Keep-Alive', 'timeout=60')
            reqUrl.add_header('Connection', 'Keep-Alive')
            reqUrl.add_header('ContentType', 'application/x-www-form-urlencoded')
            reqUrl.add_header('Accept-Encoding', 'gzip')

            startTime = datetime.datetime.now()
            while (datetime.datetime.now() - startTime).seconds < MAX_CONNECTION_TIME and strings2.M_TVGUIDE_CLOSING == False:
                try:
                    raw_json = urllib2.urlopen(reqUrl, timeout = HTTP_ConnectionTimeout)
                    content_json = raw_json.read()
                    if raw_json.headers.get("Content-Encoding", "") == "gzip":
                        content_json = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(content_json)

                    result_json = json.loads(content_json)
                    raw_json.close()
                    break
                except (httplib.IncompleteRead, socket.timeout) as ex:
                    self.logCall('ShowList getJsonFromAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))

                except urllib2.HTTPError as ex:
                    if ex.code in [500, 408]:
                        self.logCall('ShowList getJsonFromAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                except urllib2.URLError as ex:
                    if 'timed out' in str(ex) or 'Timeout' in str(ex):
                        self.logCall('ShowList getJsonFromAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                try:
                    if raw_json:
                        raw_json.close()
                        raw_json = None
                except:
                    pass
                if strings2.M_TVGUIDE_CLOSING:
                    self.logCall('ShowList getJsonFromAPI M_TVGUIDE_CLOSING - aborting!')
                    break
                xbmc.sleep(150)

        except (urllib2.URLError, NameError, ValueError, httplib.BadStatusLine) as ex:
            self.logCall('ShowList getJsonFromAPI exception: %s - aborting!' % str(ex))
            return None
        return result_json

    def getJsonFromExtendedAPI(self, url, post_data = None, save_cookie = False, load_cookie = False, cookieFile = None, jsonLoadsResult = False, jsonLoadResult = False, customHeaders = None, max_conn_time = MAX_CONNECTION_TIME):
        result_json = None
        raw_json = None
        customOpeners = []
        cj = cookielib.LWPCookieJar()

        def urlOpen(req, customOpeners):
            if len(customOpeners) > 0:
                opener = urllib2.build_opener( *customOpeners )
                response = opener.open(req, timeout = HTTP_ConnectionTimeout)
            else:
                response = urllib2.urlopen(req, timeout = HTTP_ConnectionTimeout)
            return response

        try:
            if cookieFile is not None:
                customOpeners.append( urllib2.HTTPCookieProcessor(cj) )
                if load_cookie == True:
                    cj.load(cookieFile, ignore_discard = True)

            if customHeaders is not None:
                headers = customHeaders
            else:
                headers = { 'User-Agent' : HOST }
            headers['Accept-Encoding'] = 'gzip'

            if post_data:
                data = urllib.urlencode(post_data)
            else:
                data = None
            reqUrl = urllib2.Request(url=url, data=data, headers=headers)

            startTime = datetime.datetime.now()
            while (datetime.datetime.now() - startTime).seconds < max_conn_time and strings2.M_TVGUIDE_CLOSING == False:
                try:
                    raw_json = urlOpen(reqUrl, customOpeners)
                    result_json = raw_json.read()
                    if raw_json.headers.get("Content-Encoding", "") == "gzip":
                        result_json = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(result_json)

                    if jsonLoadsResult == True:
                        result_json = json.loads(result_json)
                    raw_json.close()
                    break
                except (httplib.IncompleteRead, socket.timeout) as ex:
                    self.logCall('ShowList getJsonFromExtendedAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))

                except urllib2.HTTPError as ex:
                    if ex.code in [500, 408]:
                        self.logCall('ShowList getJsonFromExtendedAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                except urllib2.URLError as ex:
                    if 'timed out' in str(ex) or 'Timeout' in str(ex):
                        self.logCall('ShowList getJsonFromExtendedAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                try:
                    if raw_json:
                        raw_json.close()
                        raw_json = None
                except:
                    pass
                if strings2.M_TVGUIDE_CLOSING:
                    self.logCall('ShowList getJsonFromExtendedAPI M_TVGUIDE_CLOSING - aborting!')
                    break
                xbmc.sleep(150)
                #time.sleep(.15)

            if cookieFile is not None and save_cookie == True:
                cj.save(cookieFile, ignore_discard = True)

        except (urllib2.URLError, NameError, ValueError, httplib.BadStatusLine) as ex:
            self.logCall('ShowList getJsonFromExtendedAPI exception: %s - aborting!' % str(ex))
            return None

        return result_json

    def getCookieItem(self, cookiefile, item):
        ret = ''
        if os.path.isfile(cookiefile):
            cj = cookielib.LWPCookieJar()
            cj.load(cookiefile, ignore_discard = True)
            for cookie in cj:
                if cookie.name == item:
                    ret = cookie.value
        return ret

    def downloadUrl(self, url):
        fileContent = None
        try:
            urlFile = urllib2.urlopen(url, timeout=HTTP_ConnectionTimeout)
            fileContent = urlFile.read()
            urlFile.close()
        except Exception, ex:
            self.logCall('File download error, exception: %s' % str(ex))
            fileContent = None

        return fileContent

    def parseDOM(self, html, name=u"", attrs={}, ret=False):
        # Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

        if isinstance(html, str):
            try:
                html = [html.decode("utf-8")] # Replace with chardet thingy
            except:
                html = [html]
        elif isinstance(html, unicode):
            html = [html]
        elif not isinstance(html, list):
            return u""

        if not name.strip():
            return u""

        ret_lst = []
        for item in html:
            temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
            for match in temp_item:
                item = item.replace(match, match.replace("\n", " "))

            lst = []
            for key in attrs:
                lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
                if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
                    lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

                if len(lst) == 0:
                    lst = lst2
                    lst2 = []
                else:
                    test = range(len(lst))
                    test.reverse()
                    for i in test:  # Delete anything missing from the next list.
                        if not lst[i] in lst2:
                            del(lst[i])

            if len(lst) == 0 and attrs == {}:
                lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
                if len(lst) == 0:
                    lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

            if isinstance(ret, str):
                lst2 = []
                for match in lst:
                    attr_lst = re.compile('<' + name + '.*?' + ret + '=([\'"].[^>]*?[\'"])>', re.M | re.S).findall(match)
                    if len(attr_lst) == 0:
                        attr_lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
                    for tmp in attr_lst:
                        cont_char = tmp[0]
                        if cont_char in "'\"":
                            # Limit down to next variable.
                            if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
                                tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

                            # Limit to the last quotation mark
                            if tmp.rfind(cont_char, 1) > -1:
                                tmp = tmp[1:tmp.rfind(cont_char)]
                        else:
                            if tmp.find(" ") > 0:
                                tmp = tmp[:tmp.find(" ")]
                            elif tmp.find("/") > 0:
                                tmp = tmp[:tmp.find("/")]
                            elif tmp.find(">") > 0:
                                tmp = tmp[:tmp.find(">")]

                        lst2.append(tmp.strip())
                lst = lst2
            else:
                lst2 = []
                for match in lst:
                    endstr = u"</" + name

                    start = item.find(match)
                    end = item.find(endstr, start)
                    pos = item.find("<" + name, start + 1 )

                    while pos < end and pos != -1:
                        tend = item.find(endstr, end + len(endstr))
                        if tend != -1:
                            end = tend
                        pos = item.find("<" + name, pos + 1)

                    if start == -1 and end == -1:
                        temp = u""
                    elif start > -1 and end > -1:
                        temp = item[start + len(match):end]
                    elif end > -1:
                        temp = item[:end]
                    elif start > -1:
                        temp = item[start + len(match):]

                    if ret:
                        endstr = item[end:item.find(">", item.find(endstr)) + 1]
                        temp = match + temp + endstr

                    item = item[item.find(temp, item.find(match)) + len(temp):]
                    lst2.append(temp)
                lst = lst2
            ret_lst += lst

        return ret_lst


class TvCid:
    def __init__(self, cid, name, title, strm = "", img = ""):
        self.cid = cid
        self.name = name
        self.title = title
        self.strm = strm
        self.src = ""
        self.img = img
        self.rtmpdumpLink = None
        self.ffmpegdumpLink = None

class MapString:
    def __init__(self, channelid, titleRegex, strm, src):
        self.channelid = channelid
        self.titleRegex = titleRegex
        self.strm = strm
        self.src = src

    @staticmethod
    def Parse(xmlstr, logCall=deb):
        rstrm = ''
        logCall('\n')
        logCall('[UPD] Parsowanie pliku mapy')
        io = StringIO.StringIO(xmlstr)
        context = ElementTree.iterparse(io, events=("start", "end"))
        event, root = context.next()
        elements_parsed = 0
        if ADDON.getSetting('debug_log') == 'true':
            logCall('[UPD] %-35s %-35s %s' % ('ID' , 'TITLE_REGEX', 'STRM'))
        result = list()
        for event, elem in context:
            if event == "end":
                if elem.tag == "channel":
                    aid    = elem.get("id")
                    atitle = elem.get("title")
                    astrm  = elem.get("strm")
                    if ADDON.getSetting('debug_log') == 'true':
                        logCall('[UPD] %-35s %-35s %s' % (aid, atitle, astrm))
                    result.append(MapString(aid, atitle, astrm, ''))
                if elem.tag == "map":
                    rstrm = elem.get("strm")
        logCall('\n')
        logCall('[UPD] Stream rule = %s' % rstrm)
        return [result, rstrm]

    @staticmethod
    def loadFile(path, logCall=deb):
        logCall('\n')
        logCall('[UPD] Wczytywanie mapy => mtvguide: %s' % path)
        with open(path, 'r') as content_file:
            content = content_file.read()
        return content

class SleepSupervisor(object):
    def __init__(self, stopCallback):
        self.stopPlaybackCall = stopCallback
        self.sleepEnabled = ADDON.getSetting('sleep__enabled')
        self.sleepAction = ADDON.getSetting('sleep__action')
        self.sleepTimer = int(ADDON.getSetting('sleep_timer')) * 60 #time in secs
        self.timer = None
        self.actions = {
                        '0': 'PlayerControl(Stop)',
                        '1': 'Quit',
                        '2': 'Powerdown',
                        '3': 'Suspend'
        }
        try:
            self.action = self.actions[self.sleepAction]
        except KeyError:
            self.action = 'PlayerControl(Stop)'
        deb('SleepSupervisor timer init: sleepEnabled %s, sleepAction: %s, sleepTimer: %s' % (self.sleepEnabled, self.action, self.sleepTimer))

    def Start(self):
        if self.sleepEnabled == 'true' and self.sleepTimer > 0:
            self.Stop()
            debug('SleepSupervisor timer Start, action = %s' % self.action)
            self.timer = threading.Timer(self.sleepTimer, self.sleepTimeout)
            self.timer.start()

    def Stop(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
            debug('SleepSupervisor timer Stop')

    def sleepTimeout(self):
        deb('SleepSupervisor sleepTimeout, executing action: %s' % self.action)
        self.timer = None
        self.stopPlaybackCall()
        xbmc.executebuiltin('%s' % self.action)

class baseServiceUpdater:
    def __init__(self):
        self.sl = ShowList(self.log)
        self.login = ''
        self.password = ''
        self.highQuality = 'true'
        self.url = ''
        self.thread = None
        self.serviceName = 'baseService'
        self.serviceRegex = ''
        self.servicePriority = int(0)
        self.useCid = True
        self.traceList = list()
        self.traceList.append('\n')
        self.traceList.append('##############################################################################################################')
        self.traceList.append('\n')
        self.rstrm = ''
        self.forcePrintintingLog = False
        self.printLogTimer = None
        self.onlineMapFile = ''
        self.localMapFile = ''
        self.maxAllowedStreams = 1
        self.breakAfterFirstMatchFromMap = True
        self.addDuplicatesToList = False
        self.addDuplicatesAtBeginningOfList = False
        self.serviceEnabled = 'false'

    def waitUntilDone(self):
        if self.thread is not None:
            return self.thread.join()

    def log(self, message):
        if self.thread is not None and self.thread.is_alive() and self.forcePrintintingLog == False:
            self.traceList.append(self.__class__.__name__ + ' ' + message)
        else:
            deb(self.__class__.__name__ + ' ' + message)

    def printLog(self):
        for trace in self.traceList:
            deb(trace)
        del self.traceList[:]
        self.traceList = list()

    def startLoadingChannelList(self):
        self.thread = threading.Thread(name='loadChannelList thread', target = self.loadChannelList)
        self.thread.start()
        self.printLogTimer = threading.Timer(6, self.printLogTimeout)
        self.printLogTimer.start()

    def printLogTimeout(self):
        self.printLogTimer = None
        self.forcePrintintingLog = True
        self.printLog()

    def close(self):
        if self.printLogTimer is not None:
            self.printLogTimer.cancel()
        self.printLog()
        self.forcePrintintingLog = True

    def unlockService(self):
        pass

    def loadChannelList(self):
        try:
            self.channels = self.getChannelList()
            if len(self.channels) <= 0:
                self.log('loadChannelList error lodaing channel list for service %s - aborting!' % self.serviceName)
                self.automap = list()
                self.close()
                return

            self.log('\n')
            mapfile = self.sl.downloadUrl(self.onlineMapFile)
            if mapfile is None:
                self.log('loadChannelList map file download Error, using local instead!')
                pathMap = os.path.join(pathMapBase, self.localMapFile)
                mapfile = MapString.loadFile(pathMap, self.log)
            else:
                self.log('loadChannelList success downloading online map file: %s' % self.onlineMapFile)

            self.automap, rstrm = MapString.Parse(mapfile, self.log)
            if not self.rstrm or self.rstrm == '':
                self.rstrm = rstrm

            self.log('\n')
            self.log('[UPD] Wyszykiwanie STRM')
            self.log('-------------------------------------------------------------------------------------')
            self.log('[UPD]     %-30s %-30s %-20s %-35s' % ('-ID mTvGuide-', '-    Orig Name    -', '-    SRC   -', '-    STRM   -'))

            for x in self.automap[:]:
                if x.strm != '':
                    x.src = 'CONST'
                    self.log('[UPD]     %-30s %-15s %-35s' % (x.channelid, x.src, x.strm))
                    continue
                try:
                    p = re.compile(x.titleRegex, re.IGNORECASE)
                    for y in self.channels:
                        b=p.match(y.title)
                        if (b):
                            if x.strm != '' and self.addDuplicatesToList == True:
                                newMapElement = copy.deepcopy(x)
                                if self.useCid == True:
                                    newMapElement.strm = self.rstrm % y.cid
                                else:
                                    newMapElement.strm = y.strm
                                y.src = newMapElement.src
                                y.strm = newMapElement.strm
                                self.log('[UPD] [B] %-30s %-30s %-20s %-35s ' % (newMapElement.channelid, y.name, newMapElement.src, newMapElement.strm))
                                if self.addDuplicatesAtBeginningOfList == False:
                                    self.automap.append(newMapElement)
                                else:
                                    self.automap.insert(0, newMapElement)
                            else:
                                if self.useCid == True:
                                    x.strm = self.rstrm % y.cid
                                else:
                                    x.strm = y.strm
                                y.strm = x.strm
                                x.src  = self.serviceName
                                y.src = x.src
                                self.log('[UPD]     %-30s %-30s %-20s %-35s ' % (x.channelid, y.name, x.src, x.strm))
                                if self.breakAfterFirstMatchFromMap:
                                    break

                except Exception, ex:
                    self.log('%s Error %s %s' % (x.channelid, x.titleRegex, str(ex)))

            self.log('\n')
            self.log('[UPD] Nie wykorzystano STRM nadawanych przez %s programow:' % self.serviceName)
            self.log('-------------------------------------------------------------------------------------')
            for y in self.channels:
                if y.src == '' or y.src != self.serviceName:
                    self.log('[UPD] CID=%-10s NAME=%-40s STRM=%-45s' % (y.cid, y.name, str(y.strm)))

            self.log("[UPD] Zakonczono analize...")
            self.log('\n')

        except Exception, ex:
            self.log('loadChannelList Error %s' % str(ex))
        self.close()
