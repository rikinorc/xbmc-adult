# -*- coding: latin-1 -*-
from string import capitalize
import sys, os.path
import os, traceback

import xbmc, xbmcplugin

from lib.common import inheritInfos
from lib.localparser import localParser
localParser = localParser()

from lib.utils.fileUtils import clean_filename, saveList
from lib.utils.xbmcUtils import getSearchPhrase, addListItem

mode = sys.modules["__main__"].mode
addon = sys.modules["__main__"].addon
__language__ = sys.modules["__main__"].__language__
rootDir = sys.modules["__main__"].rootDir
settingsDir = sys.modules["__main__"].settingsDir
cacheDir = sys.modules["__main__"].cacheDir
resDir = sys.modules["__main__"].resDir
imgDir = sys.modules["__main__"].imgDir
catDir = sys.modules["__main__"].catDir

sort_dict = {
    u'label' : xbmcplugin.SORT_METHOD_LABEL, 
    u'size' : xbmcplugin.SORT_METHOD_SIZE, 
    u'duration' : xbmcplugin.SORT_METHOD_DURATION, 
    u'genre' : xbmcplugin.SORT_METHOD_GENRE, 
    u'rating' : xbmcplugin.SORT_METHOD_VIDEO_RATING, 
    u'date' : xbmcplugin.SORT_METHOD_DATE
}
sort = [u'label', u'genre']
class viewManager:
    def __init__(self, handle, lItem):
        self.handle = handle
        if mode == u'VIEW_DIRECTORY' or mode == u'START':
            self.links = None
        else:
            self.site = None
            from lib.remoteparser import loadRemote
            self.loadRemote = loadRemote
        self.result = self.parseView(lItem)

    def parseView(self, lItem):
        #loadLocal
        if mode == u'VIEW_RSS' or mode == u'VIEW_SEARCH' or mode == u'VIEW_RSS_DIRECTORY':
            if lItem[u'url'] != lItem[u'cfg']:
                self.site = localParser.loadLocal(lItem)
                if lItem[u'type'] == u'search':
                    lItem[u'url'] = lItem[u'url'] % getSearchPhrase()
                self.site.start = lItem[u'url']
            else:
                self.site = localParser.loadLocal(lItem)
            sort.extend(self.site.sort)
            self.loadRemote(self.site, lItem)
        elif mode == u'VIEW_DIRECTORY' or mode == u'START':
            self.links = localParser.loadLocal(lItem)
        for sort_method in sort:
            xbmcplugin.addSortMethod(handle = self.handle, sortMethod = sort_dict[sort_method])
        if mode == u'VIEW_RSS' or mode == u'VIEW_SEARCH' or mode == u'VIEW_RSS_DIRECTORY':
            try:
                totalItems = len(self.site.items[u'video']) + len(self.site.items) + len(self.site.links) - 1
            except:
                try:
                    totalItems = len(self.site.items[lItem[u'type']]) + len(self.site.items) + len(self.site.links) - 1
                    if lItem[u'type'] in self.site.items:
                        totalItems -= 1
                except:
                    totalItems = len(self.site.items) + len(self.site.links)
            for type, infos, items in self.site.items.files():
                if type == u'video' or type == u'next' or (mode == u'VIEW_RSS_DIRECTORY' and type == lItem[u'type']):
                    for item in items:
                        addListItem(mode.selectItemMode(item), totalItems)
                else:
                    filename = clean_filename(infos[u'title'].strip(u' ') + u'.list')
                    saveList(cacheDir, filename, infos[u'title'].strip(u' '), items)
                    tmp = {
                        u'title': infos[u'title'],
                        u'url': filename,
                        u'type': infos[u'type'],
                        u'icon': infos[u'icon']
                    }
                    addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
            for type, infos, items in self.site.links.files():
                if type not in self.site.items:
                    for item in items:
                        addListItem(mode.selectLinkMode(item), totalItems)
        elif mode == u'VIEW_DIRECTORY':
                totalItems = len(self.links)
                for link in self.links:
                    addListItem(mode.selectLinkMode(link), totalItems)
        elif mode == u'START':
            totalItems = len(self.links)
            tmp = {
                u'title': u' All Sites',
                u'type': u'rss',
                u'director': u'VideoDevil',
                u'icon': os.path.join(imgDir, 'face_devil_grin.png'),
                u'url': u'sites.list'
            }
            addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
            for link in self.links:
                addListItem(mode.selectLinkMode(link), totalItems)
        return 0