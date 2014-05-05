# -*- coding: latin-1 -*-
from string import capitalize
import sys, os.path
import os, traceback

import xbmc, xbmcplugin

from lib.common import inheritInfos
from lib.localparser import localParser
localParser = localParser()

from lib.utils.fileUtils import clean_filename, saveList
from lib.utils.xbmcUtils import getSearchPhrase, addListItem, infoFormatter

mode = sys.modules["__main__"].mode
addon = sys.modules["__main__"].addon
__language__ = sys.modules["__main__"].__language__
rootDir = sys.modules["__main__"].rootDir
settingsDir = sys.modules["__main__"].settingsDir
cacheDir = sys.modules["__main__"].cacheDir
resDir = sys.modules["__main__"].resDir
imgDir = sys.modules["__main__"].imgDir
catDir = sys.modules["__main__"].catDir

if mode == 'VIEW_RSS' or mode == 'VIEW_SEARCH' or mode == 'VIEW_RSS_DIRECTORY':
    from lib.remoteparser import getHTML, loadRemote

sort_dict = {
    'label' : xbmcplugin.SORT_METHOD_LABEL, 
    'size' : xbmcplugin.SORT_METHOD_SIZE, 
    'duration' : xbmcplugin.SORT_METHOD_DURATION, 
    'genre' : xbmcplugin.SORT_METHOD_GENRE, 
    'rating' : xbmcplugin.SORT_METHOD_VIDEO_RATING, 
    'date' : xbmcplugin.SORT_METHOD_DATE
}
sort = ['label', 'genre']
class viewManager:
    def __init__(self, handle, lItem):
        self.handle = handle
        self.links = None
        self.site = None
        self.result = self.parseView(lItem)

    def parseView(self, lItem):
        #loadLocal
        if mode == 'VIEW_RSS' or mode == 'VIEW_SEARCH' or mode == 'VIEW_RSS_DIRECTORY':
            self.site = localParser.load_site(lItem)
            sort.extend(self.site.sort)
            loadRemote(*getHTML(localParser.site, lItem))
            try:
                totalItems = len(self.site.items['video']) + len(self.site.items) + len(self.site.links) - 1
            except:
                try:
                    totalItems = len(self.site.items[lItem['type']]) + len(self.site.items) + len(self.site.links) - 1
                    if lItem['type'] in self.site.items:
                        totalItems -= 1
                except:
                    totalItems = len(self.site.items) + len(self.site.links)
            for type, infos, items in self.site.items.files():
                if type == 'video' or type == 'next' or (mode == 'VIEW_RSS_DIRECTORY' and type == lItem['type']):
                    for item in items:
                        addListItem(mode.selectItemMode(infoFormatter(item)), totalItems)
                else:
                    filename = clean_filename(infos['title'].strip(' ') + '.list')
                    saveList(cacheDir, filename, infos['title'].strip(' '), map(infoFormatter, items))
                    tmp = {
                        'title': infos['title'],
                        'type': infos['type'],
                        'genre': ' Directory',
                        'director': 'VideoDevil',
                        'icon': infos['icon'],
                        'url': filename
                    }
                    addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
            for type, infos, items in self.site.links.files():
                if type not in self.site.items:
                    for item in items:
                        addListItem(mode.selectLinkMode(item), totalItems)
        elif mode == 'VIEW_DIRECTORY':
            localParser.load_links(lItem)
            totalItems = len(localParser.links)
            for link in localParser.links:
                addListItem(mode.selectLinkMode(link), totalItems)
        elif mode == 'START':
            localParser.load_links(lItem)
            totalItems = len(localParser.links)
            tmp = {
                'title': ' All Sites',
                'type': 'rss',
                'genre': ' Directory',
                'director': 'VideoDevil',
                'icon': os.path.join(imgDir, 'face_devil_grin.png'),
                'url': 'sites.list'
            }
            addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
            for link in localParser.links:
                addListItem(mode.selectLinkMode(link), totalItems)
        for sort_method in sort:
            xbmcplugin.addSortMethod(handle = self.handle, sortMethod = sort_dict[sort_method])
        return 0