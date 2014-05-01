# -*- coding: latin-1 -*-
from string import capitalize, lower
import sys, traceback
import re
import os, os.path
import threading
import Queue
import time

import xbmc, xbmcplugin

from lib.common import inheritInfos
from lib.localparser import localParser
localParser = localParser()
import lib.remoteparser as remoteparser

from lib.entities.CItemTypes import CItemTypes

from lib.utils.fileUtils import clean_filename, saveList
from lib.utils.xbmcUtils import getSearchPhrase, addListItem

mode = sys.modules["__main__"].mode
addon = sys.modules["__main__"].addon
__language__ = sys.modules["__main__"].__language__
rootDir = sys.modules["__main__"].rootDir
settingsDir = sys.modules["__main__"].settingsDir
cacheDir = sys.modules["__main__"].cacheDir
allsitesDir = sys.modules["__main__"].allsitesDir
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
def run_parallel_in_threads(target, args_list):
    result = Queue.Queue()
    # wrapper to collect return value in a Queue
    def task_wrapper(*args):
        result.put(target(*args))
    threads = [threading.Thread(target=task_wrapper, args=args) for args in args_list]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result

class viewallManager:
    def __init__(self, handle, lItem):
        self.handle = handle
        self.sort = [u'label', u'genre']
        self.sites = []
        self.items = CItemTypes()
        self.links = CItemTypes()
        self.result = self.parseViewAll(lItem)

    def parseViewAll(self, lItem):
        #loadLocal
        start = time.time()
        localParser.load_list(lItem)
        if mode == u'VIEWALL_RSS' or mode == u'VIEWALL_SEARCH':
            self.sites = localParser.load_sites_in_list()
        elif mode == u'VIEWALL_DIRECTORY':
            self.sites = localParser.load_sites_not_in_list()
            create_lists = False
            fileDir = os.path.join(allsitesDir, lItem[u'type'].strip(u' '))
            if not os.path.exists(fileDir):
                os.mkdir(fileDir)
                create_lists = True
                for link in localParser.links:
                    link[u'mode'] = mode[u'VIEWALL_RSS']
                    self.items[link['type']] = (link, [link])
        print "Elapsed Time: %s" % (time.time() - start)
        remoteparser.main(self.sites)
        xbmc.log('Parsing complete')
        start = time.time()
        if mode == u'VIEWALL_RSS' or mode == u'VIEWALL_SEARCH':
            for (site, item) in self.sites:
                for type, infos, items in site.items.files():
                    self.items[type] = (infos, items)
        elif mode == u'VIEWALL_DIRECTORY' and create_lists:
            for (site, item) in self.sites:
                for type, infos, items in site.items.files():
                    self.items[type] = (infos, items)
        sort.extend(self.sort)
        for sort_method in sort:
            xbmcplugin.addSortMethod(handle = self.handle, sortMethod = sort_dict[sort_method])
        if mode == u'VIEWALL_RSS' or mode == u'VIEWALL_SEARCH':
            try:
                totalItems = len(self.items[u'video']) + len(self.items) - 1
            except:
                try:
                    totalItems = len(self.items[lItem[u'type']]) + len(self.items) - 1
                    if lItem[u'type'] in self.items:
                        totalItems -= 1
                except:
                    totalItems = len(self.items)
            for type, infos, items in self.items.files():
                if type == u'video':
                    for item in items:
                        addListItem(mode.selectItemMode(item), totalItems)
                else:
                    filename = clean_filename(infos[u'type'].strip(u' ') + u'.list')
                    if type == u'next':
                        saveList(cacheDir, filename, infos[u'title'].strip(u' '), items)
                    elif not os.path.exists(os.path.join(allsitesDir, filename)):
                        saveList(allsitesDir, filename, infos[u'title'].strip(u' '), items)
                    tmp = {
                        u'title': infos[u'title'],
                        u'type': infos[u'type'],
                        u'icon': infos[u'icon'],
                        u'url': filename
                    }
                    addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
        elif mode == u'VIEWALL_DIRECTORY':
            if create_lists:
                self.createDirs(self.items[lItem[u'type']])
                totalItems = len(self.links)
                tmp_items = []
                for item_title, infos, item_value in self.links.files():
                    filename = clean_filename(lItem[u'type'].strip(u' ') + u'.' + item_title.strip(u' ') + u'.list')
                    saveList(fileDir, filename, item_title.strip(), item_value)
                    tmp = {
                        u'title': capitalize(item_title),
                        u'type': u'rss',
                        u'icon': infos[u'icon'],
                        u'url': os.path.join(fileDir, filename)
                    }
                    tmp_items.append(tmp)
                    addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
                if tmp_items:
                    saveList(allsitesDir, lItem[u'type'].strip(u' ') + u'.list', lItem[u'title'].strip(u' '), tmp_items)
            else:
                totalItems = len(items)
                for item in items:
                    addListItem(mode.selectLinkMode(inheritInfos(item, lItem)), totalItems)
        tmp = {
            u'title': u'  ' + __language__(30102) + u'  ',
            u'type': u'search',
            u'icon': os.path.join(imgDir, 'search.png'),
            u'url': u'search.list'
        }
        addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
        print "Elapsed Time: %s" % (time.time() - start)
        return 0

    def createDirs(self, List):
        keys = []
        Dict = {}
        for item in List:
            keys.append(item[u'title'])
        for i in range(len(keys)):
            key = keys.pop().lower().strip()
            value = List.pop()
            if key in Dict:
                Dict[key].append(value)
            else:
                Dict[key] = [value]
        keys1 = sorted(Dict.keys())
        keys1.reverse()
        keys2 = sorted(Dict.keys())
        keys2.reverse()
        while len(keys1)> 0:
            key1 = keys1.pop()
            for key2 in keys2:
                if key1 != key2:
                    if key2.startswith(key1):
                        if key1 not in self.links:
                            self.links[key1] = (Dict[key1][0], Dict[key1])
                        self.links[key1] = (Dict[key2][0], Dict[key2])
                        keys1.remove(key2)
        return None