# -*- coding: latin-1 -*-
from string import capitalize, lower
import sys, os.path
import os, traceback
import urllib, urllib2
import threading
import Queue

import xbmcplugin, xbmcaddon
import xbmc, xbmcgui

from lib.common import log, inheritInfos, smart_unicode

from lib.entities.CItemTypes import CItemTypes
from lib.entities.Mode import Mode

from lib.utils.fileUtils import clean_filename, getFileExtension, saveList
from lib.utils.xbmcUtils import getKeyboard, getSearchPhrase

addon = xbmcaddon.Addon(id='plugin.video.videodevil')
__language__ = addon.getLocalizedString
rootDir = addon.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = xbmc.translatePath(rootDir)
settingsDir = addon.getAddonInfo('profile')
settingsDir = xbmc.translatePath(settingsDir)
cacheDir = os.path.join(settingsDir, 'cache')
resDir = os.path.join(rootDir, 'resources')
imgDir = os.path.join(resDir, 'images')
catDir = os.path.join(resDir, 'catchers')

if addon.getSetting('enable_debug') == 'true':
    enable_debug = True
    xbmc.log('VideoDevil debug logging enabled')
else:
    enable_debug = False

sort_dict = {
    'label' : xbmcplugin.SORT_METHOD_LABEL, 
    'size' : xbmcplugin.SORT_METHOD_SIZE, 
    'duration' : xbmcplugin.SORT_METHOD_DURATION, 
    'genre' : xbmcplugin.SORT_METHOD_GENRE, 
    'rating' : xbmcplugin.SORT_METHOD_VIDEO_RATING, 
    'date' : xbmcplugin.SORT_METHOD_DATE
}

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

class Main:
    def __init__(self):
        xbmc.log('Initializing VideoDevil')
        self.pDialog = None
        self.curr_file = ''
        self.handle = 0
        self.currentlist = None
        self.catcher = None
        xbmc.log('VideoDevil initialized')
        self.items = []
        self.links = CItemTypes()
        self.run()

    def parseViewAll(self, lItem):
        result = 0
        #loadLocal
        print('Loading Local Files')
        if lItem['mode'] == Mode.VIEWALL_SEARCH:
            search_phrase = getSearchPhrase()
            List = self.currentlist.loadLocal(lItem['url'], lItem)
            for type, infos, items in List.links.files():
                for item in items:
                    item['type'] = 'rss'
                    site = self.currentlist.loadLocal(item['cfg'], item)
                    site.start = item['url'] % search_phrase
                    self.currentlist.sites.append((site, item))
        elif lItem['mode'] == Mode.VIEWALL_RSS or lItem['mode'] == Mode.VIEWALL_DIRECTORY:
            List = self.currentlist.loadLocal(lItem['url'], lItem)
            if lItem['mode'] == Mode.VIEWALL_RSS:
                if lItem['url'] == 'sites.list':
                    for type, infos, items in List.links.files():
                        for item in items:
                            site = self.currentlist.loadLocal(item['url'], item)
                            self.currentlist.sites.append((site, item))
                else:
                    for type, infos, items in List.links.files():
                        for item in items:
                            site = self.currentlist.loadLocal(item['cfg'], item)
                            site.start = item['url']
                            self.currentlist.sites.append((site, item))
            else:
                for type, infos, items in List.links.files():
                    for item in items:
                        if item['mode'] == Mode.VIEWALL_DIRECTORY:
                            print(item['mode'])
                            item['mode'] = Mode.VIEWALL_RSS
                            self.currentlist.items[type] = (infos, [item])
                        else:
                            site = self.currentlist.loadLocal(item['cfg'], item)
                            site.start = item['url']
                            self.currentlist.sites.append((site, item))
        #loadRemote
        print('Parsing Websites')
        if self.currentlist.sites == []:
            print('No further sites to parse')
        elif len(self.currentlist.sites) == 1:
            self.currentlist.loadRemote(self.currentlist.sites[0][0], self.currentlist.sites[0][1])
        else:
            run_parallel_in_threads(self.currentlist.loadRemote, self.currentlist.sites)
        #Combine item lists
        print('Gathering Items')
        if lItem['mode'] == Mode.VIEWALL_RSS or lItem['mode'] == Mode.VIEWALL_SEARCH:
            for (site, item) in self.currentlist.sites:
                for type, infos, items in site.items.files():
                    self.currentlist.items[type] = (infos, items)
                for type, infos, items in site.links.files():
                    self.currentlist.links[type] = (infos, items)
        elif lItem['mode'] == Mode.VIEWALL_DIRECTORY:
            for (site, item) in self.currentlist.sites:
                for type, infos, items in site.items.files():
                    self.currentlist.items[type] = (infos, items)
        for sort_method in self.currentlist.sort:
            xbmcplugin.addSortMethod(handle = self.handle, sortMethod = sort_dict[sort_method])
        if lItem['mode'] == Mode.VIEWALL_RSS or lItem['mode'] == Mode.VIEWALL_SEARCH:
            print(self.currentlist.items.types)
            print(self.currentlist.links.types)
            try:
                totalItems = len(self.currentlist.items['video']) + len(self.currentlist.items) + len(self.currentlist.links) - 1
            except:
                try:
                    totalItems = len(self.currentlist.items[lItem['type']]) + len(self.currentlist.items) + len(self.currentlist.links) - 1
                    if lItem['type'] in self.currentlist.items:
                        totalItems -= 1
                except:
                    totalItems = len(self.currentlist.items) + len(self.currentlist.links)
            print(totalItems)
            for type, infos, items in self.currentlist.items.files():
                if type == 'video':
                    self.addListItems(items, totalItems)
                else:
                    filename = clean_filename(infos['title'].strip(' ') + '.list')
                    saveList(cacheDir, filename, infos['title'].strip(' '), items)
                    tmp = {
                        'title': infos['title'],
                        'url': filename,
                        'type': infos['type'],
                        'icon': infos['icon']
                    }
                    if tmp['type'] == 'search':
                        tmp['mode'] = Mode.VIEWALL_SEARCH
                    elif tmp['type'] == 'next':
                        tmp['mode'] = Mode.VIEWALL_RSS
                    else:
                        tmp['mode'] = Mode.VIEWALL_DIRECTORY
                    tmp = inheritInfos(tmp, lItem)
                    self.addListItem(tmp, totalItems)
            for type, infos, items in self.currentlist.links.files():
                filename = clean_filename(infos['title'].strip(' ') + '.list')
                saveList(cacheDir, filename, infos['title'].strip(' '), items, mode = 'a')
                if type not in self.currentlist.items:
                    tmp = {
                        'title': infos['title'],
                        'url': filename,
                        'type': infos['type'],
                        'icon': infos['icon'],
                        'mode': Mode.VIEWALL_DIRECTORY
                    }
                    tmp = inheritInfos(tmp, lItem)
                    self.addListItem(tmp, totalItems)
        elif lItem['mode'] == Mode.VIEWALL_DIRECTORY:
            self.createDirs(self.currentlist.items[lItem['type']])
            totalItems = len(self.links)
            for item_title, infos, item_value in self.links.files():
                filename = clean_filename(lItem['title'].strip() + '.' + item_title.strip() + '.list')
                saveList(cacheDir, filename, item_title.strip(), item_value)
                tmp = {
                    'title': capitalize(item_title),
                    'url': filename,
                    'type': 'rss',
                    'icon': infos['icon'],
                    'mode': str(Mode.VIEWALL_RSS)
                }
                tmp = inheritInfos(tmp, lItem)
                self.addListItem(tmp, totalItems)
        return result

    def addListItems(self, items, totalItems):
        for item in items:
            self.addListItem(item, totalItems)
        return None

    def addListItem(self, item, totalItems):
        if item['type'] != 'once':
            url = sys.argv[0] + '?' + self.codeUrl(item)
            liz = xbmcgui.ListItem(item['title'], item['title'], item['icon'], item['icon'])
            if item['type'] == 'video' and self.currentlist.skill.find('nodownload') == -1:
                action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], Mode.DOWNLOAD)
                try:
                    liz.addContextMenuItems([(__language__(30007), action)])
                except:
                    pass
            if self.currentlist.skill.find('add') != -1:
                action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], Mode.ADD)
                try:
                    liz.addContextMenuItems([(__language__(30010), action)])
                except:
                    pass
            elif self.currentlist.skill.find('remove') != -1:
                action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], Mode.ADD)
                try:
                    liz.addContextMenuItems([(__language__(30011), action)])
                except:
                    pass
            for info_name, info_value in item.iteritems():
                if info_name.startswith('context.'):
                    try:
                        cItem = {}
                        cItem['url'] = info_value
                        cItem['type'] = 'rss'
                        cItem = inheritInfos(cItem, item)
                        action = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?' + self.codeUrl(cItem))
                        liz.addContextMenuItems([(info_name[8:], action)])
                    except:
                        pass
                elif info_name != 'url' and info_name != 'title' and info_name != 'icon' and info_name != 'type' and info_name != 'extension':
                    try:
                        if info_name.rfind('.int') != -1:
                            liz.setInfo('Video', infoLabels = {capitalize(info_name[:-4]): int(info_value)})
                        elif info_name.rfind('.once') != -1:
                            liz.setInfo('Video', infoLabels = {capitalize(info_name[:-5]): info_value})
                        else:
                            liz.setInfo('Video', infoLabels = {capitalize(info_name): info_value})
                    except:
                        pass
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, liz, True, totalItems)
        return None

    def codeUrl(self, item):
        # in Frodo url parameters need to be encoded
        # ignore characters that can't be converted to ascii
        #this is added for handling the stupid &nbsp;
        params = []
        for info_name, info_value in item.iteritems():
            if info_name.find('.once') == -1 and info_name != 'mode':
                if info_name == 'url':
                    info_value.replace('\xa0', ' ')
                info_name = info_name.encode('utf-8')
                info_value = info_value.encode('utf-8')
                try:
                    params.append(info_name + '=' + info_value.replace('&', '%26'))
                except KeyError:
                    xbmc.log('Skipping %s probably has unicode' % info_value.encode('utf-8'))
        params.append('mode=' + str(item['mode']))
        return '&'.join(params)

    def decodeUrl(self, url):
        item = {}
        if url.find('&') == -1:
            item['url'] = urllib.unquote(url)
            item['type'] = 'start'
            item['mode'] = Mode.START
        else:
            for info_name_value in url.split('&'):
                info_name, info_value = info_name_value.split('=', 1)
                item[info_name] = urllib.unquote(info_value)
            item['mode'] = int(item['mode'])
        return item

    def createDirs(self, List):
        keys = []
        Dict = {}
        for item in List:
            keys.append(item['title'])
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

    def purgeCache(self):
        for root, dirs, files in os.walk(cacheDir , topdown = False):
            for name in files:
                os.remove(os.path.join(root, name))

    def run(self):
        xbmc.log('VideoDevil running')
        try:
            self.handle = int(sys.argv[1])
            paramstring = sys.argv[2]
            if len(paramstring) <= 2:
                if addon.getSetting('hide_warning') == 'false':
                    dialog = xbmcgui.Dialog()
                    if not dialog.yesno(__language__(30061), __language__(30062), __language__(30063), __language__(30064), __language__(30065), __language__(30066)):
                        return
                log(
                    'Settings directory: ' + str(settingsDir) + '\n' +
                    'Cache directory: ' + str(cacheDir) + '\n' +
                    'Resource directory: ' + str(resDir) + '\n' +
                    'Image directory: ' + str(imgDir) + '\n' +
                    'Catchers directory: ' + str(catDir)
                )
                if not os.path.exists(settingsDir):
                    log('Creating settings directory ' + str(settingsDir))
                    os.mkdir(settingsDir)
                    log('Settings directory created')
                if not os.path.exists(cacheDir):
                    log('Creating cache directory ' + str(cacheDir))
                    os.mkdir(cacheDir)
                    log('Cache directory created')
                log('Purging cache directory')
                self.purgeCache()
                log('Cache directory purged')
#                from lib.galleryparser import CCurrentList
#                self.currentlist = CCurrentList()
#                self.parseView(self.decodeUrl('sites.list'))
                from lib.viewmanager import viewManager
                self.currentlist = viewManager(self.handle, self.decodeUrl('sites.list'))
#                self.currentlist.parseView(self.decodeUrl('sites.list'))
#                if xbmcplugin.getSetting('custom_entry') == 'false':
#                    self.parseView('sites.list')
#                    del self.currentlist.items[:]
#                self.parseView('entry')
                xbmc.log('End of directory')
                if int(addon.getSetting('list_view')) == 0:
                    xbmc.executebuiltin("Container.SetViewMode(500)")
                xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))
            else:
                params = sys.argv[2][1:]
                log(
                    'currentView: ' +
                    urllib2.unquote(repr(params).replace('&', '\n')))
                lItem = self.decodeUrl(params)
                if lItem['mode'] == Mode.PLAY or lItem['mode'] == Mode.DOWNLOAD:
                    from lib.videoparser import CCatcherList
                    self.catcher = CCatcherList()
                    videoItem = self.catcher.getDirectLink(lItem)
                    if lItem['mode'] == Mode.PLAY:
                        from lib.utils.videoUtils import playVideo
                        result = playVideo(videoItem)
                    elif lItem['mode'] == Mode.DOWNLOAD:
                        from lib.utils.videoUtils import downloadMovie
                        result = downloadMovie(videoItem)
                elif lItem['mode'] == Mode.ADD:
                    self.addItem(lItem['url'][:-4], lItem)
                    result = -1
                elif lItem['mode'] == Mode.REMOVE:
                    dia = xbmcgui.Dialog()
                    if dia.yesno('', __language__(30054)):
                        self.removeItem(lItem['url'][:-7])
                    result = -2
                else:
                    if lItem['mode'] == Mode.VIEW_RSS or lItem['mode'] == Mode.VIEW_SEARCH or lItem['mode'] == Mode.VIEW_DIRECTORY:
                        from lib.viewmanager import viewManager
                        result = viewManager(self.handle, lItem).result
                    elif lItem['mode'] == Mode.VIEWALL_RSS or lItem['mode'] == Mode.VIEWALL_SEARCH or lItem['mode'] == Mode.VIEWALL_DIRECTORY:
                        from lib.viewallmanager import viewallManager
                        result = viewallManager(self.handle, lItem).result
                if result == 0:
                    if int(addon.getSetting('list_view')) == 0:
                        xbmc.executebuiltin("Container.SetViewMode(500)")
                    xbmcplugin.endOfDirectory(int(sys.argv[1]))
                    xbmc.log('End of directory')
                elif result == -2:
                    xbmc.executebuiltin('Container.Refresh')
        except Exception, e:
            if enable_debug:
                traceback.print_exc(file = sys.stdout)
            dialog = xbmcgui.Dialog()
            dialog.ok('VideoDevil Error', 'Error running VideoDevil.\n\nReason:\n' + str(e))