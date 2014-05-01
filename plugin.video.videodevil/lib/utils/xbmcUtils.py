# -*- coding: latin-1 -*-

import sys
import xbmc, xbmcgui, xbmcplugin

from lib.common import inheritInfos

mode = sys.modules["__main__"].mode
addon = sys.modules["__main__"].addon
__language__ = sys.modules["__main__"].__language__

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

def addListItem(item, totalItems):
    if item[u'type'] != u'once':
        params = []
        for info_name, info_value in item.iteritems():
            if info_name.find(u'.once') == -1 and info_name != u'mode':
                if info_name == u'url':
                    info_value.replace(u'\xa0', u' ')
                try:
                    params.append(info_name + u'=' + info_value.replace(u'&', u'%26'))
                except KeyError:
                    xbmc.log('Skipping %s probably has unicode' % info_value.encode('utf-8'))
        params.append(u'mode=%d' % item[u'mode'])
        url = sys.argv[0] + '?' + u'&'.join(params).encode('utf-8')
        liz = xbmcgui.ListItem(item[u'title'], item[u'title'], item[u'icon'], item[u'icon'])
        if item[u'type'] == u'video':
            action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], mode[u'DOWNLOAD'])
            try:
                liz.addContextMenuItems([(__language__(30007), action)])
            except:
                pass
#            if self.site.skill.find(u'add') != -1:
#                action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], mode[u'ADD'])
#                try:
#                    liz.addContextMenuItems([(__language__(30010), action)])
#                except:
#                    pass
#            elif self.site.skill.find(u'remove') != -1:
#                action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], mode[u'ADD'])
#                try:
#                    liz.addContextMenuItems([(__language__(30011), action)])
#                except:
#                    pass
        for info_name, info_value in item.iteritems():
            if info_name.startswith(u'context.'):
                try:
                    cItem = {}
                    cItem[u'url'] = info_value
                    cItem[u'type'] = u'rss'
                    cItem = inheritInfos(cItem, item)
                    action = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?' + codeUrl(cItem))
                    liz.addContextMenuItems([(info_name[8:], action)])
                except:
                    pass
            elif info_name != u'url' and info_name != u'title' and info_name != u'icon' and info_name != u'type' and info_name != u'extension':
                try:
                    if info_name.rfind(u'.int') != -1:
                        liz.setInfo('Video', infoLabels = {capitalize(info_name[:-4]): int(info_value)})
                    elif info_name.rfind(u'.once') != -1:
                        liz.setInfo('Video', infoLabels = {capitalize(info_name[:-5]): info_value})
                    else:
                        liz.setInfo('Video', infoLabels = {capitalize(info_name): info_value})
                except:
                    pass
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, liz, True, totalItems)
    return None

def codeUrl(item):
    # in Frodo url parameters need to be encoded
    # ignore characters that can't be converted to ascii
    #this is added for handling the stupid &nbsp;
    params = []
    for info_name, info_value in item.iteritems():
        if info_name.find(u'.once') == -1 and info_name != u'mode':
            if info_name == u'url':
                info_value.replace(u'\xa0', u' ')
            try:
                params.append(info_name + u'=' + info_value.replace(u'&', u'%26'))
            except KeyError:
                xbmc.log('Skipping %s probably has unicode' % info_value.encode('utf-8'))
    params.append(u'mode=%d' % item[u'mode'])
    return u'&'.join(params).encode('utf-8')