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
    'label' : xbmcplugin.SORT_METHOD_LABEL, 
    'size' : xbmcplugin.SORT_METHOD_SIZE, 
    'duration' : xbmcplugin.SORT_METHOD_DURATION, 
    'genre' : xbmcplugin.SORT_METHOD_GENRE, 
    'rating' : xbmcplugin.SORT_METHOD_VIDEO_RATING, 
    'date' : xbmcplugin.SORT_METHOD_DATE
}

class createAllSitesList:
    def __init__(self):
        self.searchlist_items = CItemTypes()
        self.sites = []
        self.loadLocal = localParser.loadLocal
        self.createList()

    def createList(self):
        tmp = {
            'title': ' All Sites',
            'icon': os.path.join(imgDir, 'face_devil_grin.png'),
            'director': 'VideoDevil',
            'url': 'sites.list',
            'type': 'rss'
        }
        items = self.loadLocal(tmp)
        for item in items:
            if item['url'] != 'allsites.list':
                site = self.loadLocal(item)[0]
                idxs = []
                for idx, rule in enumerate(site.rules):
                    if rule.type != 'video' and rule.type != 'next' and rule.type != 'category':
                        idxs.append(idx)
                if len(idxs) > 0:
                    for i in range(len(idxs)):
                        idx = idxs.pop()
                        del site.rules[idx]
                idxs = []
                if 'search' in site.links:
                    self.searchlist_items['search'] = (site.links['search'][0], site.links['search'])
                for idx, type in enumerate(site.links.types):
                    if type != 'category':
                        idxs.append(idx)
                if len(idxs) > 0:
                    for i in range(len(idxs)):
                        idx = idxs.pop()
                        del site.links[idx]
                self.sites.append(site)
        txt = []
        for site in self.sites:
            txt.append(str(site))
        f = open(os.path.join(allsitesDir, 'allsites.list'), 'w')
        f.write('\n'.join(txt))
        f.close()
        f = open(os.path.join(allsitesDir, 'search.list'), 'w')
        f.write(str(self.searchlist_items))
        f.close()
        return None