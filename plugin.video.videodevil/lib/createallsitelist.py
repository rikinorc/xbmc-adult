# -*- coding: latin-1 -*-
from string import capitalize
import sys, os.path
import os, traceback

import xbmcplugin
import xbmc, xbmcgui

from lib.localparser import localParser
localParser = localParser()
from lib.entities.CItemTypes import CItemTypes
from lib.entities.Mode import Mode

from lib.utils.fileUtils import smart_read_file

addon = sys.modules["__main__"].addon
allsitesDir = sys.modules["__main__"].allsitesDir
imgDir = sys.modules["__main__"].imgDir

sort_dict = {
    u'label' : xbmcplugin.SORT_METHOD_LABEL, 
    u'size' : xbmcplugin.SORT_METHOD_SIZE, 
    u'duration' : xbmcplugin.SORT_METHOD_DURATION, 
    u'genre' : xbmcplugin.SORT_METHOD_GENRE, 
    u'rating' : xbmcplugin.SORT_METHOD_VIDEO_RATING, 
    u'date' : xbmcplugin.SORT_METHOD_DATE
}

class createAllSitesList:
    def __init__(self):
        self.searchlist_items = CItemTypes()
        self.sites = []
        self.loadLocal = localParser.loadLocal
        self.createList()

    def createList(self):
        tmp = {
            u'title': u' All Sites',
            u'icon': os.path.join(imgDir, u'face_devil_grin.png'),
            u'director': u'VideoDevil',
            u'url': u'sites.list',
            u'type': u'rss'
        }
        items = self.loadLocal(tmp)
        for item in items:
            if item[u'url'] != u'allsites.list':
                site = self.loadLocal(item)[0]
                idxs = []
                for idx, rule in enumerate(site.rules):
                    if rule.type != u'video' and rule.type != u'next' and rule.type != u'category':
                        idxs.append(idx)
                if len(idxs) > 0:
                    for i in range(len(idxs)):
                        idx = idxs.pop()
                        del site.rules[idx]
                idxs = []
                if u'search' in site.links:
                    self.searchlist_items[u'search'] = (site.links[u'search'][0], site.links[u'search'])
                for idx, type in enumerate(site.links.types):
                    if type != u'category':
                        idxs.append(idx)
                if len(idxs) > 0:
                    for i in range(len(idxs)):
                        idx = idxs.pop()
                        del site.links[idx]
                self.sites.append(site)
        txt = []
        for site in self.sites:
            txt.append(str(site))
        f = open(os.path.join(allsitesDir, u'allsites.list'), 'w')
        f.write('\n'.join(txt))
        f.close()
        f = open(os.path.join(allsitesDir, u'search.list'), 'w')
        f.write(str(self.searchlist_items))
        f.close()
        return None