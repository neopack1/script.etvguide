# -*- coding: utf-8 -*-
import urllib, urllib2, sys, re, os
import xbmcgui, xbmc, xbmcplugin, xbmcaddon
import xml.etree.ElementTree as ET 
#import rtmp
#import multitask
#import RTMPListener as RT
from threading import Thread
import traceback
import subprocess

import sdLog, sdSettings, sdParser, sdNavigation, sdCommon, sdErrors, Subtitles

log = sdLog.pLog()
HANDLE = int(sys.argv[1])

scriptID = 'plugin.video.polishtv.live'
scriptname = "Polish Live TV"
ptv = xbmcaddon.Addon(scriptID)
language = ptv.getLocalizedString
t = sys.modules[ "__main__" ].language

BASE_RESOURCE_PATH = os.path.join( ptv.getAddonInfo('path'), "../resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )

SERVICE = 'cinematixtv'

dstpath = ptv.getSetting('default_dstpath')
dbg = ptv.getSetting('default_debug')
enable_sub = 'true'
rtmpID = 'script.module.rtmpserver'
fontcolor = "00A5FF"

mainUrl = 'http://cinematix.tv'
pid_rtmp = xbmc.translatePath(ptv.getAddonInfo('profile') + "rtmp.pid")
tmp_ffmpeg = xbmc.translatePath(ptv.getAddonInfo('profile') + "ffmpeg.tmp")
sub_ass = xbmc.translatePath(ptv.getAddonInfo('profile') + "subtitles.ass")
#pid_ffmpeg = xbmc.translatePath(ptv.getAddonInfo('profile') + "ffmpeg.pid")
#tmp_ffmpeg = pid_ffmpeg[:-4] + '.conf'
pythonapp = 'python'
start_rtmp = pythonapp + ' ' + ptv.getAddonInfo('path').split(scriptID)[0] + os.sep + rtmpID + os.sep + 'lib' + os.sep + 'RTMPListener.py start ' + pid_rtmp
stop_rtmp = pythonapp + ' ' + ptv.getAddonInfo('path').split(scriptID)[0] + os.sep + rtmpID + os.sep + 'lib' + os.sep + 'RTMPListener.py stop ' + pid_rtmp
#start_ffmpeg = pythonapp + ' ' + ptv.getAddonInfo('path').split(scriptID)[0] + os.sep + rtmpID + os.sep + 'lib' + os.sep + 'FFMPEGencoder.py start ' + pid_ffmpeg
#stop_ffmpeg = pythonapp + ' ' + ptv.getAddonInfo('path').split(scriptID)[0] + os.sep + rtmpID + os.sep + 'lib' + os.sep + 'FFMPEGencoder.py stop ' + pid_ffmpeg


class Movies:
    def __init__(self):
        self.common = sdCommon.common()
        self.chars = sdCommon.Chars()
        self.navigation = sdNavigation.VideoNav()
        self.exception = sdErrors.Exception()
    
    def addDir(self, service, type, title, link, img):
        liz = xbmcgui.ListItem(title, iconImage = "DefaultFolder.png", thumbnailImage = img)
        liz.setProperty("IsPlayable", "false")
        liz.setInfo(type = "Video", infoLabels={ "Title": title } )
        u = '%s?service=%s&type=%s&title=%s&icon=%s&url=%s' % (sys.argv[0], SERVICE, type, str(title), urllib.quote_plus(img), urllib.quote_plus(link))
        xbmcplugin.addDirectoryItem(HANDLE, url = u, listitem = liz, isFolder = True)

    def addLink(self, service, type, title, img, desc, link):
        u = '%s?service=%s&type=%s&title=%s&icon=%s&url=%s' % (sys.argv[0], SERVICE, type, str(title), urllib.quote_plus(img), urllib.quote_plus(link))
        liz = xbmcgui.ListItem(title, iconImage = "DefaultFolder.png", thumbnailImage = img)
        liz.setProperty("IsPlayable", "false")
        liz.setInfo(type = "Video", infoLabels={ "Title": title,
                                                "Plot": desc })
                                                #"Studio": "WEEB.TV",
                                                #"Tagline": tags,
                                                #"Aired": user } )
        if dstpath != "None" or not dstpath:
            if dbg == 'true':
                log.info('CinematixTV - addLink() -> title: ' + title)
                log.info('CinematixTV - addLink() -> url: ' + link)
                log.info('CinematixTV - addLink() -> dstpath: ' + os.path.join(dstpath, SERVICE))
            cm = self.navigation.addVideoContextMenuItems({ 'service': SERVICE, 'title': urllib.quote_plus(self.chars.replaceChars(title)), 'url': urllib.quote_plus(link), 'path': os.path.join(dstpath, SERVICE) })
            liz.addContextMenuItems(cm, replaceItems=False)
        xbmcplugin.addDirectoryItem(HANDLE, url = u, listitem = liz, isFolder = False)
             
    def MainCategories(self):
        query_data = { 'url': mainUrl, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()        
        match = re.compile('<h2 class="forumtitle"><a href="(.+?)">(.+?)</a></h2>').findall(response)
        if len(match) > 0:
            for i in range(len(match)):
                link = mainUrl + '/' + match[i][0]
                img = ''
                self.addDir(SERVICE, 'categories', match[i][1], link, img)
            xbmcplugin.endOfDirectory(HANDLE)

    def ContentCategories1(self, url):
        query_data = { 'url': url, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()        
        match = re.compile('<a class="title" href="(.+?)" id=".+?">(.+?)</a>').findall(response)
        if len(match) > 0:
            for i in range(len(match)):
                link = mainUrl + '/' + match[i][0]
                img = ''
                self.addDir(SERVICE, 'content', match[i][1], link, img)
            xbmcplugin.endOfDirectory(HANDLE)
            return True
        else:
            return False

    def ContentCategories2(self, url):
        query_data = { 'url': url, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()        
        match = re.compile('<h2 class="forumtitle"><a href="(.+?)">(.+?)</a></h2>').findall(response)
        if len(match) > 0:
            for i in range(len(match)):
                link = mainUrl + '/' + match[i][0]
                img = ''
                self.addDir(SERVICE, 'content', match[i][1], link, img)
            xbmcplugin.endOfDirectory(HANDLE)
            return True
        else:
            return False

    def ContentMovies(self, url):
        query_data = { 'url': url, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
            #response = response.replace(r'\r\n', '')
            #log.info('response: ' + str(response))
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        #match = re.compile('<div align="center"><font size="4"><b><font color="Purple">(.+?)</font></b></font></div><br />.+?<td style="border-width:0px"><a href="fcpp://(.+?)" title="Film online"><img src="(.+?)" border="0" alt="Watch online" /></a>').findall(response)
        #match = re.compile('<div align="center"><font size="4"><b><font color="Purple">(.+?)</font></b></font></div><br />\r\n.+?<td style="border-width:0px"><a href="fcpp://(.+?)" title="Film online"><img src="(.+?)" border="0" alt="Watch online" /></a>').findall(response)     
        match = re.compile('<a href="fcpp://(.+?)" title="Film online"><img src="(.+?)" border="0" alt="Watch online" /></a>').findall(response)
        #if len(match) == 0:
        #    match = re.compile('<div align="center"><font size="4"><b><font color="Purple">(.+?)</font></b></font></div><br />\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?\r\n.+?<td style="border-width:0px"><a href="fcpp://(.+?)" title="Film online"><img src="(.+?)" border="0" alt="Watch online" /></a>').findall(response)
        if len(match) > 0:
            a = 1
            for i in range(len(match)):
                #addDir(self, service, type, title, link, img)
                #addLink(self, service, type, title, img, desc, link)
                #self.addDir(SERVICE, 'movies', match[i][0], 'http://' + match[i][1], match[i][2])
                #self.addDir(SERVICE, 'movies', 'Movie ' + str(a), 'http://' + match[i][0], match[i][1])
                self.addLink(SERVICE, 'movies', 'Movie ' + str(a), match[i][0], '', 'http://' + match[i][0])
                a = a + 1
            xbmcplugin.endOfDirectory(HANDLE)

    def InitPlay(self, url):
        #sub = "None"
        menu = Menu()
        values = XML().loadValues(url)
        if dbg == 'true':
            log.info('CinematixTV - LOAD_AND_PLAY()[0] -> v_array:' + str(values['video']))
            log.info('CinematixTV - LOAD_AND_PLAY()[0] -> a_array:' + str(values['audio']))
            #log.info('CinematixTV - handleService() -> array:')
        d = xbmcgui.Dialog()
        video_menu = d.select("Wybór jakości video", menu.createValuesTab(values['video']))
        video_value = menu.getValueFromTab(video_menu, values['video'])
        audio_menu = d.select("Wybór ścieżki audio", menu.createValuesTab(values['audio']))
        audio_value = menu.getValueFromTab(audio_menu, values['audio'])
        subtitle_value = { 'url': 'None', 'title': 'None' }
        if (len(values['subtitle']) > 0):
            subtitle_menu = d.select("Wybór napisów", menu.createValuesTab(values['subtitle'], 'Bez napisów'))
            sub_id = int(subtitle_menu) - 1
            if sub_id >= 0:
                subtitle_value = menu.getValueFromTab(sub_id, values['subtitle'])
                #sub = self.getSubtitle(subtitle_value['url'], video_value['fps'])
            #log.info('subtitle_menu_id: ' + str(subtitle_menu))
            #log.info('value tab subtitle: ' + str(values['subtitle']))
            #log.info('subtitle val: ' + str(subtitle_value))
        if video_value != '' and audio_value != '':
            if dbg == 'true':
                log.info(start_rtmp)
            if len(values['subtitle']) > 0:
                s_args = { 'url': subtitle_value['url'], 'fps': video_value['fps'], 'width': video_value['dimension'].split("x")[0], 'height': video_value['dimension'].split("x")[1], 'fontcolor': fontcolor, 'title': video_value['title'] }
                self.getSubtitle(s_args)
            os.system(start_rtmp)
            args = { 'v_url': video_value['url'], 'a_url': audio_value['url'], 'a_sampling_rate': audio_value['sampling_rate'], 'v_bitrate': video_value['bitrate'], 'a_bitrate': audio_value['bitrate'], 'v_dimension': video_value['dimension'], 'v_fps': video_value['fps'], 'subtitles': subtitle_value['url'] }
            ffmpeg = FFMPEG(args)
            ffmpeg.start()
            pDialog = xbmcgui.DialogProgress()
            DialogMsg = "Loading rtmp stream "
            pDialog.create('XBMC', DialogMsg)
            msg = 'waiting'
            dot = ""
            percent = 0
            i = 0
            while True:
                try:
                    if os.path.isfile(pid_rtmp):
                        pass
                except:
                    pDialog.close()
                if pDialog.iscanceled():
                    #os.system(pythonapp + ' ' + ptv.getAddonInfo('path').split(scriptID)[0] + os.sep + rtmpID + os.sep + 'lib' + os.sep + 'FFMPEGencoder.py stop ' + pid_ffmpeg)
                    pDialog.close()
                    os.system(stop_rtmp)
                    exit()
                if msg == 'waiting':
                    fl = open(tmp_ffmpeg, "r")
                    while True:
                        line = fl.readline()
                        if line == '':
                            break
                        if line == 'encoding':
                            msg = line.strip()
                            break
                    if i < 7:
                        dot += "."
                        i = i + 1
                    else:
                        dot = ""
                        i = 0
                    pDialog.update(0, "", DialogMsg + dot, "")
                elif msg == 'encoding':
                    break
                xbmc.sleep(1000)
            pDialog.close()
            if msg == 'encoding':
                liz=xbmcgui.ListItem("bunny", iconImage="DefaultVideo.png", thumbnailImage="")
                liz.setInfo( type="Video", infoLabels={ "Title": "bunny" } )
                rtmp = "rtmp://127.0.0.1/stream/live playpath=live live=true"
                #xbmcPlayer = xbmc.Player()
                #xbmcPlayer.play(rtmp, liz)
                try:
                    player = Player()
                    player.play(rtmp, liz)
                    #if sub != 'None':
                        #log.info('sub: ' + str(subtitle_value))
                    #    player.setSubtitles(sub.encode("utf-8"))
                    while player.is_active:
                        player.sleep(100)
                except:
                    traceback.print_exc()
                    os.system(stop_rtmp)

    def saveConfFile(self, args):
        confFile = pid_ffmpeg[:-4] + '.conf'
        f = open(confFile, "w")
        f.write('ffmpeg ' + pythonapp + '\r\n')
        f.write('v_url ' + args['v_url'] + '\r\n')
        f.write('a_url ' + args['a_url'] + '\r\n')
        f.write('v_bitrate ' + args['v_bitrate'] + '\r\n')
        f.write('a_bitrate ' + args['a_bitrate'] + '\r\n')
        f.write('v_dimension ' + args['v_dimension'] + '\r\n')
        f.write('a_sampling_rate ' + args['a_sampling_rate'] + '\r\n')
        f.write('pid_file ' + pid_ffmpeg + '\r\n')
        f.close()
        
    def getSubtitle(self, args = {}):
        url = args['url']
        fps = args['fps']
        fsub = xbmc.translatePath(ptv.getAddonInfo('profile') + "subtitles.ass")
        #if url.endswith(".srt"):
        #    fsub = xbmc.translatePath(ptv.getAddonInfo('profile') + "subtitle.srt")
        query_data = { 'url': url, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        tabSub = Subtitles.MicroDVD(fps).getSubtitleTab(response.decode("cp1250"))
        fw = open(fsub, "w")
        fw.write(Subtitles.ASS(tabSub, { 'width': args['width'], 'height': args['height'], 'fontcolor': args['fontcolor'], 'title': args['title'] }).content())
        fw.close()
        return fsub       
        

class XML:
    def __init__(self):
        self.common = sdCommon.common()
        #self.chars = sdCommon.Chars()
        #self.navigation = sdNavigation.VideoNav()
        self.exception = sdErrors.Exception()

    def loadValues(self, url):
        values = {}
        query_data = { 'url': url, 'use_host': True, 'host': self.common.getRandomHost(), 'use_cookie': False, 'use_post': False, 'return_data': False }
        try:
            response = self.common.getURLRequestData(query_data)
        except Exception, exception:
            traceback.print_exc()
            self.exception.getError(str(exception))
            exit()
        elems = ET.parse(response).getroot()
        
        infos = elems.find("MOVIE_INFO")
        info_genre = infos.find("Genre").text
        info_desc = infos.find("Description").text
        info_avdir = infos.find("AVDir").text
        info = { 'genre': info_genre, 'description': info_desc, 'avdir': info_avdir }
        
        videos = elems.find("VIDEO_STREAMS")
        v_streams = []
        for vi in range(100):
            try:
                va = vi + 1
                v_stream = videos.find("VIDEO_STREAM_" + str(va))
                video_link = '%s/%s' % (info_avdir, v_stream.find("FileName").text)
                video_bitrate = v_stream.find("Bitrate").text
                video_dimension = '%sx%s' % (v_stream.find("Width").text, v_stream.find("Height").text)
                video_title = '%s - %sx%s, %s kbps, %s fps' % (v_stream.find("Quality").text, v_stream.find("Width").text, v_stream.find("Height").text, v_stream.find("Bitrate").text, v_stream.find("FPS").text)
                video_fps = v_stream.find("FPS").text
                v_streams.append({ 'url': video_link, 'title': video_title, 'bitrate': video_bitrate, 'dimension': video_dimension, 'fps': video_fps })
            except:
                break
              
        audios = elems.find("AUDIO_STREAMS")
        a_streams = []
        for ai in range(100):
            try:
                aa = ai + 1
                a_stream = audios.find("AUDIO_STREAM_" + str(aa))
                audio_link = '%s/%s' % (info_avdir, a_stream.find("FileName").text)
                audio_bitrate = a_stream.find("Bitrate").text
                audio_sampling_rate = a_stream.find("SamplingRate").text
                audio_title = '%s - %s, %s, %s kbps, %s Hz, %s ch' % (a_stream.find("Language").text, a_stream.find("Quality").text, a_stream.find("FormatName").text, a_stream.find("Bitrate").text, a_stream.find("SamplingRate").text, a_stream.find("Channels").text)
                a_streams.append({ 'url': audio_link, 'title': audio_title, 'bitrate': audio_bitrate, 'sampling_rate': audio_sampling_rate })
            except:
                break            

        subtitles = elems.find("SUBTITLES")
        s_streams = []
        for si in range(100):
            try:
                sa = si + 1
                s_stream = subtitles.find("SUBTITLE_" + str(sa))
                subtitle_link = '%s/%s' % (info_avdir, s_stream.find("FileName").text)
                subtitle_title = '%s, format: %s' % (s_stream.find("Language").text, s_stream.find("Format").text)
                s_streams.append({ 'url': subtitle_link, 'title': subtitle_title })
            except:
                break
        
        return { 'info': info, 'video': v_streams, 'audio': a_streams, 'subtitle': s_streams }


class Menu:
    def __init__(self):
        pass
    
    def getValueFromTab(self, key, tab):
        value = {}
        for i in range(len(tab)):
            if key == i:
                value = tab[i]
                break
        return value
    
    def createValuesTab(self, tab, first_value = ''):
        out = []
        if first_value != '':
            out.append(first_value)
        for i in range(len(tab)):
            out.append(tab[i]['title'])
        return out


class FFMPEG(Thread):
    def __init__(self, args = {}):
        Thread.__init__(self)
        self.v_url = args['v_url']
        self.a_url = args['a_url']
        self.a_sampling_rate = args['a_sampling_rate']
        self.a_bitrate = args['a_bitrate']
        self.v_bitrate = args['v_bitrate']
        self.v_dimension = args['v_dimension']
        self.v_fps = args['v_fps']
        self.sub = args['subtitles']
        self.temp_ffmpeg = open(tmp_ffmpeg, "w")
        self.temp_ffmpeg.write("running")
        self.temp_ffmpeg.close()
        
    def run(self):
        send = self.sender()
        if send:
            while 1:
                if not os.path.isfile(tmp_ffmpeg):
                    if dbg == 'true':
                        log.info('CinematixTV - FFMPEG() -> shutting down...')
                    exit()
                xbmc.sleep(100)
    
    def sender(self):
        try:
            v_opts = "-b %s -s %s -r %s" % (str(int(self.v_bitrate)*4000), self.v_dimension, self.v_fps) 
            a_opts = "-ab %s -ac 1 -ar 44100" % (str(int(self.a_bitrate)*1000))
            s_opts = ""
            if self.sub != 'None' and enable_sub == 'true':
                s_opts = "-vf ass=\"%s\"" % (sub_ass)
            rtmp_link = "rtmp://127.0.0.1/stream/live"
            #args = "ffmpeg -re -i %s %s -i %s %s -f flv %s &" % (self.video, v_opts, self.audio, a_opts, rtmp_link)
            args = "%s -re -i %s -i %s %s %s -f flv \"%s\"" % ('/usr/local/ffmpeg/bin/ffmpeg', self.v_url, self.a_url, v_opts, a_opts, rtmp_link)
            if self.sub != 'None' and enable_sub == 'true':
                args = "%s -re -i %s -i %s %s %s %s -f flv \"%s\"" % ('/usr/local/ffmpeg/bin/ffmpeg', self.v_url, self.a_url, v_opts, a_opts, s_opts, rtmp_link)
            if dbg == "true":
                log.info('CinematixTV - FFMPEG sender() -> ffmpeg: ' + str(args))
            p = subprocess.Popen(args, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if dbg == "true":
                log.info('CinematixTV - FFMPEG sender() -> ffmpeg run subprocess')
            while True:
                line = p.stderr.readline()
                if line == '':
                    os.system(stop_rtmp)
                    break
                if dbg == 'true':
                    log.info('CinematixTV - FFMPEG sender() -> ffmpeg line: ' + str(line))
                if 'Press [q] to stop, [?] for help' in line:
                    f = open(tmp_ffmpeg, "w")
                    f.write('encoding')
                    f.close()
                    break
                elif ('No such filter:' in line) or ('Unrecognized option' in line) or ('Error' in line) or ('Cannot open connection' in line):
                    #match = re.compile('').findall(line)
                    os.system(stop_rtmp)
                    d = xbmcgui.Dialog()
                    d.ok("Przygotowanie strumienia ffmpeg...", "Wystąpił błąd:", str(line.strip()))
                    break                  
                #sys.stdout.flush()
                xbmc.sleep(100)
            return True
        except:
            traceback.print_exc()
            return False        


class Player(xbmc.Player):
    def __init__(self, *args, **kwargs):
        self.is_active = True
        print "#Starting control WeebPlayer events#"
  
    def onPlayBackPaused(self):
        print "#Im paused#"
        ThreadPlayerControl("Stop").start()
        self.is_active = False
        os.system(stop_rtmp)
        
    def onPlayBackResumed(self):
        print "#Im Resumed #"
        
    def onPlayBackStarted(self):
        print "#Playback Started#"
        try:
            print "#Im playing :: " + self.getPlayingFile()
        except:
            print "#I failed get what Im playing#"
            
    def onPlayBackEnded(self):
        print "#Playback Ended#"
        self.is_active = False
        os.system(stop_rtmp)
        
    def onPlayBackStopped(self):
        print "## Playback Stopped ##"
        self.is_active = False
        os.system(stop_rtmp)
    
    def sleep(self, s):
        xbmc.sleep(s)


class ThreadPlayerControl(Thread):
    def __init__(self, command):
        self.command = command
        threading.Thread.__init__ (self)
    
    def run(self):
        xbmc.executebuiltin('PlayerControl(' + self.command + ')')
                    
    
class CinematixTV:
    def __init__(self):
        self.common = sdCommon.common()
        self.chars = sdCommon.Chars()
        self.movie = Movies()
        self.parser = sdParser.Parser()
        self.xml = XML()
        
    def handleService(self):
        params = self.parser.getParams()
        title = str(self.parser.getParam(params, "title"))
        type = str(self.parser.getParam(params, "type"))
        service = str(self.parser.getParam(params, "service"))
        image = self.parser.getParam(params, "image")
        url = self.parser.getParam(params, "url")
        
        if dbg == 'true':
            log.info('CinematixTV - handleService()[0] -> title: ' + str(title))
            log.info('CinematixTV - handleService()[0] -> type: ' + str(type))
            log.info('CinematixTV - handleService()[0] -> service: ' + str(service))
            #log.info('CinematixTV - handleService()[0] -> image: ' + str(image))
            log.info('CinematixTV - handleService()[0] -> url: ' + str(url))
            
        if title == 'None' and type == 'None':
            self.movie.MainCategories()
        elif title != 'None' and type == 'categories':
            c1 = self.movie.ContentCategories1(urllib.unquote_plus(url))
            if not c1:
                c2 = self.movie.ContentCategories2(urllib.unquote_plus(url))
                if not c2:
                    exit()
        elif title != 'None' and type == 'content':
            self.movie.ContentMovies(urllib.unquote_plus(url))
        elif title != 'None' and type == 'movies':
            self.movie.InitPlay(url)
