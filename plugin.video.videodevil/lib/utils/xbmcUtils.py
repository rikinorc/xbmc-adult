# -*- coding: latin-1 -*-

import sys
import xbmc, xbmcgui, xbmcplugin

from lib.common import inheritInfos
from lib.utils.encodingUtils import clean_safe, smart_unicode

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
    if item['type'] != 'once':
        if 'inherited' in item:
            params = [item['inherited']]
        else:
            params = []
        for info_name, info_value in item.iteritems():
            if info_name.find('.once') == -1 and info_name != 'mode' and info_name != 'inherited':
                try:
                    if info_name == 'url':
                        info_value.replace('\xa0', ' ')
                    params.append(info_name + '=' + info_value.replace('&', '%26'))
                except UnicodeDecodeError:
                    xbmc.log('%s probably has unicode, trying to decode to unicode prior to encoding url' % info_value.encode('utf-8'))
                    params = []
                    for info_name, info_value in item.iteritems():
                        if info_name.find('.once') == -1 and info_name != 'mode' and info_name != 'inherited':
                            if info_name == 'url':
                                smart_unicode(info_value).replace(u'\xa0', u' ')
                            params.append(smart_unicode(info_name) + u'=' + smart_unicode(info_value).replace(u'&', u'%26'))
                    params.append(u'mode=%d' % smart_unicode(item['mode']))
                    params = u'&'.join(params).encode('utf-8')
                    break
        else:
            params.append('mode=%d' % item['mode'])
            params = '&'.join(params)
        url = sys.argv[0] + '?' + params
        liz = xbmcgui.ListItem(item['title'], item['title'], item['icon'], item['icon'])
        if item['type'] == 'video':
            action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], mode['DOWNLOAD'])
#            try:
            liz.addContextMenuItems([(__language__(30007), action)])
#            except:
#                pass
#            if self.site.skill.find('add') != -1:
#                action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], mode['ADD'])
#                try:
#                    liz.addContextMenuItems([(__language__(30010), action)])
#                except:
#                    pass
#            elif self.site.skill.find('remove') != -1:
#                action = 'XBMC.RunPlugin(%s%d)' % (url[:url.rindex('=') + 1], mode['ADD'])
#                try:
#                    liz.addContextMenuItems([(__language__(30011), action)])
#                except:
#                    pass
        for info_name, info_value in item.iteritems():
            if info_name.startswith('context.'):
                try:
                    cItem = {}
                    cItem['url'] = info_value
                    cItem['type'] = 'rss'
                    cItem = inheritInfos(cItem, item)
                    action = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?' + codeUrl(cItem))
                    liz.addContextMenuItems([(info_name[8:], action)])
                except:
                    pass
#            elif info_name != 'url' and info_name != 'title' and info_name != 'icon' and info_name != 'type' and info_name != 'extension':
            elif info_name not in ['url', 'title', 'icon', 'type', 'extension']:
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

def codeUrl(item):
    # in Frodo url parameters need to be encoded
    # ignore characters that can't be converted to ascii
    #this is added for handling the stupid &nbsp;
    params = []
    for info_name, info_value in item.iteritems():
        if info_name.find('.once') == -1 and info_name != 'mode':
            if info_name == 'url':
                info_value.replace('\xa0', ' ')
            try:
                params.append(info_name + '=' + info_value.replace('&', '%26'))
            except KeyError:
                xbmc.log('Skipping %s probably has unicode' % info_value.encode('utf-8'))
    params.append('mode=%d' % item['mode'])
    return '&'.join(params).encode('utf-8')

def infoFormatter(tmp):
    keep = {}
    for info_name, info_value in tmp.iteritems():
        if info_name == 'title':
            try:
                if info_value != '':
                    info_value = info_value.replace('\r\n', '').replace('\n', '').replace('\t', '')
                    info_value = info_value.lstrip('-!@#$%^&*_-+=.,)\'<>;:"[{]}\|/?`~')
                    info_value = info_value.rstrip('-@#$%^&*_-+=.,<>;(:\'"[{]}\|/?`~')
                    info_value = info_value.split(' ')
                    title = []
                    for word in info_value:
                        if word:
                            word = word.lower().capitalize()
                        title.append(word)
                    info_value = ' '.join(title)
                else:
                    info_value = ' ... '
            except UnicodeDecodeError:
                info_value = clean_safe(info_value)
                info_value = info_value.replace(u'\r\n', '').replace(u'\n', '').replace(u'\t', u'')
                info_value = info_value.lstrip(u'-!@#$%^&*_-+=.,)\'<>;:"[{]}\|/?`~')
                info_value = info_value.rstrip(u'-@#$%^&*_-+=.,<>;(:\'"[{]}\|/?`~')
                info_value = info_value.split(u' ')
                title = []
                for word in info_value:
                    if word:
                        word = word.lower().capitalize()
                    title.append(word)
                info_value = u' '.join(title)
        elif info_name == 'duration':
            info_value = info_value.strip('')
            if info_value.find('(') == -1:
                info_value = ' (%s)' % info_value
            if info_value[-3] == ':':
                try:
                    info_value = info_value[:-2] + '0' + info_value[-2:]
                except AttributeError:
                    print(info_value)
        elif info_name == 'icon':
            if info_value == '':
                info_value = os.path.join(imgDir, 'video.png')
        elif info_name.rfind('.tmp') != -1:
            continue
        keep[info_name] = info_value
    if 'duration' in keep:
        keep['title'] = ''.join((keep['title'], keep['duration']))
    return keep