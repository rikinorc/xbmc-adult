# -*- coding: latin-1 -*-
import sys, os
import time

import xbmc, xbmcplugin

from lib.common import inheritInfos
from lib.localparser import localParser
localParser = localParser()
from lib.remoteparser import remoteParser
remoteParser = remoteParser()

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
    'label' : xbmcplugin.SORT_METHOD_LABEL, 
    'size' : xbmcplugin.SORT_METHOD_SIZE, 
    'duration' : xbmcplugin.SORT_METHOD_DURATION, 
    'genre' : xbmcplugin.SORT_METHOD_GENRE, 
    'rating' : xbmcplugin.SORT_METHOD_VIDEO_RATING, 
    'date' : xbmcplugin.SORT_METHOD_DATE
}

def createListItems(directory, items_list, lItem, totalItems = 50):
    tmp_items = []
    for title, items in items_list.iteritems():
        tmp_items.append(createListItem(directory, title, items, lItem, totalItems))
    return tmp_items

def createListItem(directory, Listname, items, lItem, totalItems = 50):
    filename = Listname + '.list'
    saveList(directory, filename, Listname, items)
    tmp = {}
    tmp['title'] = '   ' + Listname.capitalize() + '   '
    tmp['url'] = os.path.join(directory, filename)
    for item in items:
        if not item['icon'].startswith(imgDir):
            tmp['icon'] = item['icon']
            break
    else:
        tmp['icon'] = os.path.join(imgDir, 'video.png')
    addListItem(mode.selectLinkMode(inheritInfos(tmp, lItem)), totalItems)
    return tmp

class parseView:
    def __init__(self, handle, lItem):
        self.handle = handle
        self.sort = ['label', 'genre']
        self.site = None
        self.sites = []
        self.items = []
        self.links = []
        self.result = self.run(lItem)

    def createDirs(self, List):
        keys = [item['title'] for item in List]
        Dict = {}
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
                            self.links[key1] = Dict[key1]
                        self.links[key1].extend(Dict[key2])
                        keys1.remove(key2)
        return None

    def run(self, lItem):
        #loadLocal
        start = time.time()
        if mode == 'START':
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
        elif mode == 'VIEW_RSS' or mode == 'VIEW_SEARCH' or mode == 'VIEW_RSS_DIRECTORY':
            self.site = localParser.load_site(lItem)
            self.sort.extend(self.site.sort)
            remoteParser.main(((localParser.site, lItem),))
            type_dict = {}
            for item in remoteParser.items:
                if item['type'] in type_dict:
                    type_dict[item['type']].append(item)
                else:
                    type_dict[item['type']] = [item]
            for type, items in type_dict.iteritems():
                if type == 'next' or (mode == 'VIEW_RSS_DIRECTORY' and type == lItem['type']):
                    for item in items:
                        addListItem(mode.selectItemMode(item), 0)
                else:
                    createListItem(cacheDir, type, items, lItem)
            for type, infos, items in self.site.links.files():
                if type not in self.site.items:
                    for item in items:
                        addListItem(mode.selectLinkMode(item), 0)
        elif mode == 'VIEW_DIRECTORY':
            localParser.load_links(lItem)
            totalItems = len(localParser.links)
            for link in localParser.links:
                addListItem(mode.selectLinkMode(link), totalItems)
        elif mode == 'VIEWALL_RSS' or mode == 'VIEWALL_SEARCH':
            localParser.load_links_and_sites_in_list(lItem)
            print "Elapsed Time: %s" % (time.time() - start)
            remoteParser.main(localParser.sites)
            xbmc.log('Parsing complete')
            start = time.time()
            type_dict = {}
            for item in remoteParser.items:
                if item['type'] in type_dict:
                    type_dict[item['type']].append(item)
                else:
                    type_dict[item['type']] = [item]
            for type, items in type_dict.iteritems():
                print(type)
                if type == 'next':
                    createListItem(cacheDir, type, items, lItem)
                elif not os.path.isfile(os.path.join(allsitesDir, type + '.list')):
                    createListItem(allsitesDir, type, items, lItem)
        elif mode == 'VIEWALL_DIRECTORY':
            print "Elapsed Time: %s" % (time.time() - start)
            fileDir = os.path.join(allsitesDir, lItem['type'])
            if not os.path.exists(fileDir):
                os.mkdir(fileDir)
                localParser.load_links_and_sites_not_in_list(lItem)
                remoteParser.main(localParser.sites)
                xbmc.log('Parsing complete')
                start = time.time()
                tmp_items = [item for item in remoteParser.items if item['type'] == lItem['type']]
                items = self.createDirs(tmp_items + localParser.links)
                items = createListItems(fileDir, items, lItem)
                if items:
                    saveList(allsitesDir, lItem['type'] + '.list', lItem['title'], items)
            else:
                localParser.load_links(lItem)
                totalItems = len(localParser.links)
                for link in localParser.links:
                    addListItem(mode.selectLinkMode(link), totalItems)
        print "Elapsed Time: %s" % (time.time() - start)
        for sort_method in self.sort:
            xbmcplugin.addSortMethod(handle = self.handle, sortMethod = sort_dict[sort_method])
        return 0