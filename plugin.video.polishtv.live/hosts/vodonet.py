# -*- coding: utf-8 -*-
import os, time, urllib, re, sys, math, random
import xbmcgui, xbmc, xbmcaddon, xbmcplugin
import traceback

if sys.version_info >= (2,7): import json as _json
else: import simplejson as _json

scriptID = 'plugin.video.polishtv.live'
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

import sdLog, sdSettings, sdParser, sdCommon, sdErrors

log = sdLog.pLog()

SERVICE = 'vodonet'
THUMB_SERVICE = 'http://sd-xbmc.org/repository/xbmc-addons/'+ SERVICE + '.png'

MODULE_URL = {'content' : 'http://content.external.cms.onetapi.pl/l',
              'video'   : 'http://video.external.cms.onetapi.pl/l'}
              
HEADER = {'X-Onet-App': 'vod.android.mobile-apps.onetapi.pl', 'Content-Type': 'application/json-rpc', 'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.1.1; Core 10.1 3G Build/JRO03H)', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip'}

SERVICE_MENU_TABLE = { 1: "Polecamy",
                        2: "Filmy",
                        3: "Seriale",
                        4: "TV",
                        5: "Dokumenty",
                        6: "Bajki",}

vodonet_format = ptv.getSetting('vodonet_format')
vodonet_quality = ptv.getSetting('vodonet_quality')
#vodonet_proxy = ptv.getSetting('vodonet_proxy')

class vodonet:
  def __init__(self):
    log.info('Loading ' + SERVICE)
    self.settings = sdSettings.TVSettings()
    self.parser = sdParser.Parser()
    self.exception = sdErrors.Exception()
    self.common = sdCommon.common()
    self.proxy = sdCommon.proxy()
    self.api = API()

    
  def setTable(self):
    return SERVICE_MENU_TABLE
    
    
  def getMenuTable(self):
    nTab = []
    for num, val in SERVICE_MENU_TABLE.items():
      nTab.append(val)
    return nTab

    
  def listsAddDirMenu(self, table, name, category):
    for i in range(len(table)):
      #if len(table[i]) == 4:
        try:
          if table[i][3] != '':
            iconImage = self.api.getPoster(table[i][3])
          else: iconImage = THUMB_SERVICE
        except:
          iconImage = THUMB_SERVICE

        if name == 'None':
          self.add(SERVICE, 'main-menu', table[i], category, THUMB_SERVICE, '', True, False)
   
        if name == 'main-menu':
          if category == self.setTable()[3] or category == self.setTable()[4]:
            self.add(SERVICE, 'sub-menu', table[i][0].encode('UTF-8'),  str(table[i][1]), iconImage, str(table[i][2]), True, False)
          else:
            self.add(SERVICE, 'sub-menu', table[i][0].title().encode('UTF-8'), category, iconImage, '', True, False)
      
        if name == 'series':
          if category == 'None': self.add(SERVICE, 'series', table[i][0], str(table[i][1]), iconImage, str(table[i][2]), True, False)  
      
        if name == 'playSeries':
          self.add(SERVICE, 'playSelectedMovie', table[i][0].title().encode('UTF-8') + ', odcinek ' + str(table[i][2]), table[i][1], iconImage, '', True, False)      
        if name == 'movie':
          self.add(SERVICE, 'playSelectedMovie', table[i][0].title().encode('UTF-8'), table[i][1], iconImage, '', True, False)      
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    

  def add(self, service, name, title, category, iconimage, url, folder = True, isPlayable = True):
    u=sys.argv[0] + "?service=" + service + "&name=" + urllib.quote_plus(name) + "&title=" + urllib.quote_plus(title) + "&category=" + urllib.quote_plus(category) + "&url=" + urllib.quote_plus(url)
    if iconimage == '':
            iconimage = "DefaultVideo.png"
    liz=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if isPlayable:
        liz.setProperty("IsPlayable", "true")
    liz.setInfo('video', {'title' : title} )
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=folder)


  def listsSeasons(self, seriesId, seasons):
    strTab = []
    valTab = []
    for i in range(int(seasons)):
      strTab.append('Sezon ' + str(i+1))
      strTab.append(i+1)
      strTab.append(int(seriesId))
      strTab.append('')
      valTab.append(strTab)
      strTab = []
    return valTab

  def listsItems(self, node, childs, alt_childs = []):
    valTab = []
    for items in node:
      strTab = []
      if childs[0] in items:
        for i in childs:
          if i != '' and i in items: strTab.append(items[i])
          else:
            strTab.append('')
      elif 0 < len(alt_childs):
         for i in alt_childs:
           if i != '': strTab.append(items[i])
           else: strTab.append('')
      if 0 < len(strTab):
          if 'poster' in items: strTab.append(items['poster']['imageId'])
          else:
            try: strTab.append(items['leadMedia']['imageId'])
            except: strTab.append('')
          valTab.append(strTab)
    return valTab
  #def listsItems(self, node, childs, alt_childs = []):
  #  strTab = []
  #  valTab = []
  #  for items in node:
  #    if childs[0] in items:  
  #      for i in childs:
  #        if i != '' and i in items: strTab.append(items[i])
  #        else:
  #          strTab.append('')
  #    else:
  #       for i in alt_childs:
  #         if i != '': strTab.append(items[i])
  #         else: strTab.append('')            
  #    if 'poster' in items: strTab.append(items['poster']['imageId'])
  #    else:
  #      try: strTab.append(items['leadMedia']['imageId'])
  #      except: strTab.append('')
  #    valTab.append(strTab)
  #    strTab = []
  #  return valTab


  def getVideoUrl(self, tab, videoFormat, videoQuality):
    indexTab = []
    url =''
    for i in range(len(tab)):
        if tab[i][0] == videoFormat: indexTab.append(i)  
    if videoQuality == 'Niska': url = tab[indexTab[-1]][1]
    if videoQuality == 'Wysoka': url = tab[indexTab[0]][1]
    if videoQuality == 'Średnia':
        length = len(indexTab)
        i = int(math.ceil(float((indexTab[length/2] + indexTab[-(length+1)/2]))/2))
        url = tab[i][1]
    return url


  def getVideoProxyUrl(self, url):
    videoUrl = ''
    query_data = {'url': self.proxy.useProxy(url), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
    data = self.common.getURLRequestData(query_data)
    if self.proxy.isAuthorized(data) != False:
        match = re.compile('<a href="(.+?)">').findall(data)
        if len(match) > 0: videoUrl = self.common.html_entity_decode(match[0])
    return videoUrl


  def handleService(self):

    params = self.parser.getParams()
    name = str(self.parser.getParam(params, "name"))
    title = str(self.parser.getParam(params, "title"))
    category = str(self.parser.getParam(params, "category"))
    url = str(self.parser.getParam(params, "url"))

    #MAINMENU
    if name == 'None':
      self.listsAddDirMenu(self.getMenuTable(), 'None', 'None')
      
    #POLECAMY
    if name == 'main-menu' and title == self.setTable()[1]:
      data = self.api.getAPIData('content', self.api.makeListQuery({"context":"onet/vod", "method":"guideListsByType", "sort":"DEFAULT", "type":"mobile-sg-polecane", "guidelistView":"listitem"}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'][0]['contentLeads'], ['title','ckmId','videoId']), 'movie', 'None')
      except: pass      

    #BAJKI
    if name == 'main-menu' and title == self.setTable()[6]:    
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/bajki", "method":"search", "sort":"DATE_DESC", "noSeriesGroup":"True"}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','videoId']), 'movie', 'None')
          
    #SERIALE
    if name == 'main-menu' and title == self.setTable()[3]:  
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"DATE_DESC", "channel":"seriale"}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'], ['seriesTitle','season','seriesId']), name, self.setTable()[3])

    #SERIALE
    if name == 'main-menu' and title == self.setTable()[4]:  
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"DATE_DESC", "channel":"tv"}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'], ['seriesTitle','season','seriesId']), name, self.setTable()[4])

    
    #KATEGORIE FILMOWE
    if name == 'main-menu' and title == self.setTable()[2]:
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"aggregates", "sort":"TITLE_ASC", "channel":"filmy", "names":"genres"}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'][0]['items'], ['name','','']), name, self.setTable()[2])
             
    #DOKUMENTY (moze zwracac items jako film lub jako serial)
    if name == 'main-menu' and title == self.setTable()[5]:
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"POPULARITY_DESC", "channel":"dokumenty"}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'], ['seriesTitle','ckmId','seriesId'], ['title','ckmId','videoId']), 'movie', 'None')
      
    #sub-menu
    #filmy w kategoriach
    if name == 'sub-menu' and category == self.setTable()[2]:
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"POPULARITY_DESC", "channel":"filmy", "genre":title}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','videoId']), 'movie', 'None')
    
    #sezony w serialu
    if name == 'sub-menu' and self.common.isNumeric(category):
      self.listsAddDirMenu(self.listsSeasons(url, category), 'series','None')

    #serial bez sezonu
    if name == 'sub-menu' and category == 'None':
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"episodes", "sort":"DATE_DESC", "seriesId":int(url)}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','episode']), 'playSeries', 'None')     
    
    #odcinki w sezonie
    if name == 'series':
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"episodes", "sort":"DATE_DESC", "seriesId":int(url), "season":int(category)}))
      self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','episode']), 'playSeries', 'None')
    
    if name == 'playSelectedMovie':
        u = self.getVideoUrl(self.api.getVideoTab(category), vodonet_format, vodonet_quality)
        #if vodonet_proxy == 'true': u = self.getVideoProxyUrl(u)
        self.common.LOAD_AND_PLAY_VIDEO(u, title)


class API:
  def __init__(self):
    self.common = sdCommon.common()
    self.exception = sdErrors.Exception()

    
  def getVideoTab(self, ckmId):
    #MD5('gastlich') = d2dd64302895d26784c706717a1996b0
    #contentUrl = 'http://vod.pl/' + ckmId + ',d2dd64302895d26784c706717a1996b0.html?dv=aplikacja_androidVOD%2Ffilmy&back=onetvod%3A%2F%2Fback'     
    tm = str(int(time.time() * 1000))
    jQ = str(random.randrange(562674473039806,962674473039806))
    authKey = '22D4B3BC014A3C200BCA14CDFF3AC018'
    contentUrl = 'http://qi.ckm.onetapi.pl/?callback=jQuery183040'+ jQ + '_' + tm + '&body%5Bid%5D=' + authKey + '&body%5Bjsonrpc%5D=2.0&body%5Bmethod%5D=get_asset_detail&body%5Bparams%5D%5BID_Publikacji%5D=' + ckmId + '&body%5Bparams%5D%5BService%5D=vod.onet.pl&content-type=application%2Fjsonp&x-onet-app=player.front.onetapi.pl&_=' + tm
    query_data = {'url': contentUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
    data = self.common.getURLRequestData(query_data)
    
    #extract json
    result = _json.loads(data[data.find("(")+1:-2])
    strTab = []
    valTab = []
    for items in result['result']['0']['formats']['wideo']:
        for i in range(len(result['result']['0']['formats']['wideo'][items])):
            strTab.append(items)
            strTab.append(result['result']['0']['formats']['wideo'][items][i]['url'].encode('UTF-8'))
            if result['result']['0']['formats']['wideo'][items][i]['video_bitrate']:
                strTab.append(int(float(result['result']['0']['formats']['wideo'][items][i]['video_bitrate'])))
            else:
                strTab.append(0)
            valTab.append(strTab)
            strTab = []
    return valTab
    
  
  def getPoster(self, h):
    posterUrl = 'http://m.ocdn.eu/_m/' + h + ',10,1.jpg'
    return posterUrl


  def getAPIData(self, module, post_data):
    query_data = {'url': MODULE_URL[module], 'use_host': False, 'use_header': True, 'header': HEADER, 'use_cookie': False, 'use_post': True, 'raw_post_data': True, 'return_data': True}
    try:
        data = self.common.getURLRequestData(query_data, post_data)
        result = _json.loads(data)
    except Exception, exception:
        traceback.print_exc()
        self.exception.getError(str(exception))
    return result


  def makeListQuery(self, p):
    args =   {"device":"mobile", "withoutDRM":"True", "payment":["-svod","-ppv"]}
    params = {"context":"", "method":"", "sort":"", "range":[0,10000], "args":args}
    dict =   {"id":"query_cmsQuery", "jsonrpc":"2.0", "method":"cmsQuery", "params":params}
    for key in p.keys():
        if any(key in s for s in ['context','method','sort']): 
            dict['params'][key] = p[key]
        else:
            dict['params']['args'][key] = p[key]
    return _json.dumps(dict)


  def makeVideoDetailsQuery(self, p):
    args =   {"device":"mobile", "withoutDRM":"True", "payment":["-svod","-ppv"]}
    params = {"id":0, "context":"", "object":"Video", "WithoutDRM":"True", "args":args}
    dict =   {"id":"query_cmsGet", "jsonrpc":"2.0", "method":"cmsGet", "params":params}
    for key in p.keys():
        dict['params'][key] = p[key]
    return _json.dumps(dict)
