# -*- coding: latin-1 -*-

import sys, os, traceback
import xbmc, xbmcgui, xbmcplugin

from lib.common import inheritInfos
from lib.utils.encodingUtils import clean_safe, smart_unicode

mode = sys.modules["__main__"].mode
addon = sys.modules["__main__"].addon
__language__ = sys.modules["__main__"].__language__
imgDir = sys.modules["__main__"].imgDir

def getKeyboard(default = '', heading = '', hidden = False):
    kboard = xbmc.Keyboard(default, heading, hidden)
    kboard.doModal()
    if kboard.isConfirmed():
        return kboard.getText()
    return ''

def getSearchPhrase():
    try:
        curr_phrase = addon.getSetting('curr_search')
    except:
        addon.setSetting('curr_search', '')
        curr_phrase = ''
    search_phrase = getKeyboard(default = curr_phrase, heading = __language__(30102))
    addon.setSetting('curr_search', search_phrase)
    return search_phrase.replace(' ', '+')

def addListItems(items):
#    map(addListItem, map(mode.selectItemMode, items))
    for item in items:
        addListItem(mode.selectItemMode(item))
    return None

def addListLinks(items):
    map(addListItem, map(mode.selectLinkMode, items))
    return None

exclusions = ['url', 'title', 'icon', 'type', 'extension', 'duration']
def addListItem(item, totalItems = 0):
    if item['type'] != 'once':
        url = sys.argv[0] + '?' + codeUrl(item)
        liz = xbmcgui.ListItem(item['title'], item['title'], item['icon'], item['icon'])
        context_menu_items = []
        if item['type'] == 'video':
            action = 'XBMC.RunPlugin(%s&mode=%d)' % (url, mode['DOWNLOAD'])
            context_menu_items.append((__language__(30007), action))
        for info_name, info_value in item.iteritems():
            if info_name.startswith('context.'):
                print 'adding "%s" to the context menu' % info_name[8:]
                cItem = {}
                cItem['url'] = info_value
                cItem['type'] = 'rss'
                cItem = inheritInfos(cItem, item)
                action = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?' + codeUrl(cItem))
                context_menu_items.append((info_name[8:], action))
            elif info_name not in exclusions:
#                try:
                if info_name.rfind('.int') != -1:
                    liz.setInfo('Video', infoLabels = {info_name[:-4].capitalize(): int(info_value)})
                elif info_name.rfind('.once') != -1:
                    liz.setInfo('Video', infoLabels = {info_name[:-5].capitalize(): info_value})
                else:
                    liz.setInfo('Video', infoLabels = {info_name.capitalize(): info_value})
#                except:
#                    pass
        liz.addContextMenuItems(context_menu_items)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, liz, True, totalItems)
    return None

def codeUrl(item):
    # in Frodo url parameters need to be encoded
    # ignore characters that can't be converted to ascii
    #this is added for handling the stupid &nbsp;
    try:
        params = [info_name + '=' + info_value.replace('&', '%26') for info_name, info_value in item.iteritems() if info_name.find('.once') == -1]
        params = '&'.join(params)
    except UnicodeDecodeError:
        xbmc.log('%s probably has unicode, trying to decode to unicode prior to encoding url' % clean_safe(info_value))
        params = [smart_unicode(info_name) + u'=' + smart_unicode(info_value).replace(u'&', u'%26') for info_name, info_value in item.iteritems() if info_name.find('.once') == -1]
        params = u'&'.join(params).encode('utf-8')
    return params