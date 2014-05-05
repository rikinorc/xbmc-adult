# -*- coding: latin-1 -*-
from lib.utils.fileUtils import getFileExtension

class Mode:
    def __init__(self):
        self.current = 0
        self.modes = {
            'START': 0,
            'PLAY': 1,
            'DOWNLOAD': 2,
            'ADD': 5,
            'REMOVE': 6,
            'VIEW_RSS': 10,
            'VIEW_SEARCH': 11,
            'VIEW_RSS_DIRECTORY': 12,
            'VIEW_DIRECTORY': 13,
            'VIEWALL_RSS': 20,
            'VIEWALL_SEARCH': 21,
            'VIEWALL_DIRECTORY': 22
        }

    def __getitem__(self, m):
        return self.modes[m]

    def __eq__(self, m):
        return self.current == self.modes[m]

    def __str__(self):
        for key, value in self.modes.iteritems():
            if value == self.current:
                return 'Mode is %s' % key

    def setMode(self, m):
        try:
            self.current = self.modes[m]
        except KeyError:
            self.current = int(m)

    def getMode(self):
        return self.current

    def selectItemMode(self, item):
        if self.current == self.modes['VIEW_RSS'] or self.current == self.modes['VIEW_SEARCH'] or self.current == self.modes['VIEW_RSS_DIRECTORY']:
            if item['type'] == 'video':
                item['mode'] = self.modes['PLAY']
            elif item['type'] == 'search':
                item['mode'] = self.modes['VIEW_SEARCH']
            else:
                item['mode'] = self.modes['VIEW_RSS']

        elif self.current == self.modes['VIEWALL_RSS'] or self.current == self.modes['VIEWALL_SEARCH']:
            if item['type'] == 'video':
                item['mode'] = self.modes['PLAY']
            elif item['type'] == 'next':
                item['mode'] = self.modes['VIEWALL_RSS']
            else:
                item['mode'] = self.modes['VIEWALL_DIRECTORY']
        elif self.current == self.modes['VIEWALL_DIRECTORY']:
            if item['type'] == 'video':
                item['mode'] = self.modes['PLAY']
            else:
                item['mode'] = self.modes['VIEWALL_RSS']
        return item

    def selectLinkMode(self, link):
        if self.current == self.modes['START']:
            if link['url'] == 'sites.list':
                link['mode'] = self.modes['VIEWALL_RSS']
            else:
                link['mode'] = self.modes['VIEW_RSS']

        elif self.current == self.modes['VIEW_RSS'] or self.current == self.modes['VIEW_SEARCH'] or self.current == self.modes['VIEW_RSS_DIRECTORY']:
            if link['type'] == 'search':
                link['mode'] = self.modes['VIEW_SEARCH']
            elif getFileExtension(link['url']) == 'list':
                link['mode'] = self.modes['VIEW_DIRECTORY']
            else:
                link['mode'] = self.modes['VIEW_RSS_DIRECTORY']
        elif self.current == self.modes['VIEW_DIRECTORY']:
            link['mode'] = self.modes['VIEW_RSS']

        elif self.current == self.modes['VIEWALL_RSS'] or self.current == self.modes['VIEWALL_SEARCH']:
            if link['type'] == 'video':
                link['mode'] = self.modes['PLAY']
            elif link['type'] == 'next':
                link['mode'] = self.modes['VIEWALL_RSS']
            elif link['type'] == 'search':
                link['mode'] = self.modes['VIEWALL_SEARCH']
            else:
                link['mode'] = self.modes['VIEWALL_DIRECTORY']
        elif self.current == self.modes['VIEWALL_DIRECTORY']:
            if link['type'] == 'search':
                link['mode'] = self.modes['VIEWALL_SEARCH']
            else:
                link['mode'] = self.modes['VIEWALL_RSS']
        return link

    def selectMode(self, item, islink = False):
        if self.current == self.modes['START']:
            if item['url'] == 'sites.list':
                item['mode'] = self.modes['VIEWALL_RSS']
            else:
                item['mode'] = self.modes['VIEW_RSS']

        elif self.current == self.modes['VIEW_RSS'] or self.current == self.modes['VIEW_SEARCH'] or self.current == self.modes['VIEW_RSS_DIRECTORY']:
            if item['type'] == 'video':
                item['mode'] = self.modes['PLAY']
            elif item['type'] == 'search':
                item['mode'] = self.modes['VIEW_SEARCH']
            elif getFileExtension(item['url']) == 'list':
                item['mode'] = self.modes['VIEW_DIRECTORY']
            elif islink:
                item['mode'] = self.modes['VIEW_RSS_DIRECTORY']
            else:
                item['mode'] = self.modes['VIEW_RSS']
        elif self.current == self.modes['VIEW_DIRECTORY']: # and islink ?
            item['mode'] = self.modes['VIEW_RSS']

        elif self.current == self.modes['VIEWALL_RSS'] or self.current == self.modes['VIEWALL_SEARCH']:
            if item['type'] == 'video':
                item['mode'] = self.modes['PLAY']
            elif item['type'] == 'next':
                item['mode'] = self.modes['VIEWALL_RSS']
            elif item['type'] == 'search':
                item['mode'] = self.modes['VIEWALL_SEARCH']
            else:
                item['mode'] = self.modes['VIEWALL_DIRECTORY']
        elif self.current == self.modes['VIEWALL_DIRECTORY']:
            if item['type'] == 'video':
                item['mode'] = self.modes['PLAY']
            elif item['type'] == 'search':
                item['mode'] = self.modes['VIEWALL_SEARCH']
            else:
                item['mode'] = self.modes['VIEWALL_RSS']
        return item