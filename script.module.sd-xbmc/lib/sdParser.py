# -*- coding: utf-8 -*-
import sys
import urllib, urlparse
import sdLog, ast

log = sdLog.pLog()

class Parser:
    def __init__(self):
        pass

    def getParam(self, params, name):
        try:
            return params[name]
        except:
            return None

    def getIntParam (self, params, name):
        try:
            param = self.getParam(params, name)
            return int(param)
        except:
            return None
    
    def getBoolParam (self, params, name):
        try:
            param = self.getParam(params,name)
            return 'True' == param
        except:
            return None

    def getTypeParam(self, params, name):
        try:
            return ast.literal_eval(params[name])
        except:
            return None

    def getParams(self, paramstring = sys.argv[2]):
        param = {}
        if len(paramstring) >= 2:
            params = paramstring.replace('?', '')
            param = dict(urlparse.parse_qsl(params))
        return param

    def debugParams(self, params, mode=False):
        if mode == True:
            for name, val in params.items():
                log.info(str(name) + ': ' + str(val))
                
    def setParam(self, params, add=False):
        param = urllib.urlencode(params)
        if add == False:
            return "?"+param
        else:
            return param
