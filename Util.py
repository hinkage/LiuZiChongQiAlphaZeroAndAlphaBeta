# -*- coding: utf-8 -*-
"""
    @author 何江
    @date 2019/2/9 21:17
"""

def init():
    global globalVars
    globalVars = {}

def setGlobalVar(key, value):
    globalVars[key] = value

def getGobalVar(key):
    try:
        return globalVars[key]
    except:
        return None
