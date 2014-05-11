# -*- coding: latin-1 -*-

import sys, traceback
import os
import re
import urllib, urllib2
import cookielib

import xbmc, xbmcgui

from lib.common import inheritInfos, smart_unicode

from lib.utils.encodingUtils import clean_safe
from lib.utils.fileUtils import smart_read_file
import sesame

addon = sys.modules["__main__"].addon
__language__ = sys.modules["__main__"].__language__
rootDir = sys.modules["__main__"].rootDir
settingsDir = sys.modules["__main__"].settingsDir
cacheDir = sys.modules["__main__"].cacheDir
resDir = sys.modules["__main__"].resDir
imgDir = sys.modules["__main__"].imgDir
catDir = sys.modules["__main__"].catDir
enable_debug = sys.modules["__main__"].enable_debug
log = sys.modules["__main__"].log
USERAGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.8.1.18) Gecko/20081029 Firefox/2.0.0.18'

urlopen = urllib2.urlopen
cj = cookielib.LWPCookieJar()
Request = urllib2.Request

if cj != None:
    if os.path.isfile(xbmc.translatePath(os.path.join(settingsDir, 'cookies.lwp'))):
        cj.load(xbmc.translatePath(os.path.join(settingsDir, 'cookies.lwp')))
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
else:
    opener = urllib2.build_opener()
    urllib2.install_opener(opener)

def parseActions(item, convActions, url = None):
    for convAction in convActions:
        if convAction.find(u"(") != -1:
            action = convAction[0:convAction.find('(')]
            param = convAction[len(action) + 1:-1]
            if param.find(', ') != -1:
                params = param.split(', ')
                if action == 'replace':
                    item[params[0]] = item[params[0]].replace(params[1], params[2])
                elif action == 'join':
                    j = []
                    for i in range(1, len(params)):
                        j.append(item[params[i]])
                    item[params[1]] = params[0].join(j)
                elif action == 'decrypt':
                    item['match'] = sesame.decrypt(item[params[0]], item[params[1]], 256)
            else:
                if action == 'unquote':
                    item[param] = urllib.unquote(item[param])
                elif action == 'quote':
                    item[param] = urllib.quote(item[param])
                elif action == 'decode':
                    item[param] = decode(item[param])
        else:
            action = convAction
            if action == 'append':
                item['url'] = url + item['url']
            elif action == 'appendparam':
                if url[-1] == '?':
                    item['url'] = url + item['url']
                else:
                    item['url'] = url + '&' + item['url']
            elif action == 'replaceparam':
                if url.rfind('?') == -1:
                    item['url'] = url + '?' + item['url']
                else:
                    item['url'] = url[:url.rfind('?')] + '?' + item['url']
            elif action == 'striptoslash':
                if url.rfind('/'):
                    idx = url.rfind('/')
                    if url[:idx + 1] == 'http://':
                        item['url'] = url + '/' + item['url']
                    else:
                        item['url'] = url[:idx + 1] + item['url']
#            elif action == 'space':
#                try:
#                    item['title'] = '  ' + item['title'].strip(' ') + '  '
#                except:
#                    pass
    return item

class CCatcherRuleItem:
    def __init__(self):
        self.target = None
        self.actions = []
        self.dkey = None
        self.dkey_actions = []
        self.info = None
        self.player = None
        self.extension = 'flv'
        self.quality = 'standard'
        self.build = None
        self.type = 'video'
        self.priority = 0


class CCatcherRuleSite:
    def __init__(self):
        self.url = ''
        self.startRE = None
        self.stopRE = None
        self.txheaders = {'User-Agent':USERAGENT}
        self.limit = 0
        self.data = ''
        self.rules = []


class CCatcherList:
    def __init__(self, lItem):
        self.status = {}
        self.key = []
        self.value = []
        self.skill = ''
        self.player = None
        self.sites = []
        self.urlList = []
        self.extensionList = []
        self.selectionList = []
        self.decryptList = []
        self.playerList = []
        self.videoExtension = '.flv'
        self.dkey = None
        self.link = None
        self.videoItem = self.getDirectLink(lItem)

    def getDirectLink(self, lItem):
        filename = lItem.get('catcher', lItem['cfg'].rsplit('.', 1)[0] + '.catcher')
        if not os.path.isfile(os.path.join(catDir, filename)):
            filename = 'simple-match.catcher'
        self.loadCatcher(filename)
        redirected = self.parseVideoPage(lItem['url'])
        if redirected != None:
            return redirected.videoItem
        if self.link != None:
            tmp = {
                'url': self.link,
                'extension': self.videoExtension
                }
            if self.player != None:
                tmp['player'] = self.player
            tmp = inheritInfos(tmp, lItem)
            return tmp
        elif len(self.urlList) > 0:
            self.selectLink()
        if self.link != None:
            tmp = {
                'url': self.link,
                'extension': self.videoExtension
                }
            if self.player != None:
                tmp['player'] = self.player
            tmp = inheritInfos(tmp, lItem)
            return tmp
        return None

    def loadCatcher(self, filename):
        del self.key[:]
        del self.value[:]
        self.key, self.value = smart_read_file(filename)
        if self.key == None and self.value == None:
            return None
        site = None
        rule = None
        while self.key:
            old_line = len(self.key)
            if self.loadKey('url'):
                if site:
                    self.sites.append(site)
                site = CCatcherRuleSite()
                site.url = self.value.pop()
            if self.loadKey('data'):
                site.data = self.value.pop()
            if self.loadKey('header'):
                index = self.value[-1].find('|')
                site.txheaders[value[-1][:index]] = value[-1][index+1:]
                del self.value[-1]
            if self.loadKey('limit'):
                site.limit = int(self.value.pop())
            if self.loadKey('startRE'):
                site.startRE = self.value.pop()
            if self.loadKey('stopRE'):
                site.stopRE = self.value.pop()
            while self.key:
                old_line = len(self.key)
                if self.loadKey('target'):
                    if rule:
                        site.rules.append(rule)
                    rule = CCatcherRuleItem()
                    rule.target = smart_unicode(self.value.pop())
                if self.loadKey('quality'):
                    rule.quality = self.value.pop()
                    continue
                if self.loadKey('priority'):
                    rule.priority = int(self.value.pop())
                    continue
                if self.loadKey('type'):
                    rule.type = self.value.pop()
                    if rule.type == 'forward' or rule.type.startswith('redirect'):
                        site.rules.append(rule)
                        rule = None
                        break
                else:
                    if self.loadKey('actions'):
                        if self.value[-1].find('|') != -1:
                            rule.actions.extend(self.value.pop().split('|'))
                        else:
                            rule.actions.append(self.value.pop())
                    if self.loadKey('build'):
                        rule.build = self.value.pop()
                    if self.loadKey('dkey'):
                        rule.dkey = smart_unicode(self.value.pop())
                        if self.loadKey('dkey_actions'):
                            if self.value[-1].find('|') != -1:
                                rule.dkey_actions.extend(self.value.pop().split('|'))
                            else:
                                rule.dkey_actions.append(self.value.pop())
                    if self.loadKey('extension'):
                        rule.extension = self.value.pop()
                    if self.loadKey('info'):
                        rule.info = self.value.pop()
                    if self.loadKey('player'):
                        rule.player = self.value.pop()
                if len(self.key) == old_line:
                    log('Syntax Error:\n"%s" is invalid.' % self.filename)
            if len(self.key) == old_line:
                log('Syntax Error:\n"%s" is invalid.' % self.filename)
        if rule != None:
            site.rules.append(rule)
        self.sites.append(site)
        return None

    def loadKey(self, txt):
        if self.key[-1] == txt:
            del self.key[-1]
            return True
        return False

    def parseVideoPage(self, url):
        video_found = False
        for index, site in enumerate(self.sites):
            if video_found:
                break
            # Download website
            if site.data == '':
                if site.url.find('%') != -1:
                    url = site.url % url
                req = Request(url, None, site.txheaders)
                urlfile = opener.open(req)
                if site.limit == 0:
                    data = urlfile.read()
                else:
                    data = urlfile.read(site.limit)
            else:
                data_url = site.data % url
                req = Request(site.url, data_url, site.txheaders)
                response = urlopen(req)
                if site.limit == 0:
                    data = response.read()
                else:
                    data = response.read(site.limit)
            if enable_debug:
                f = open(os.path.join(cacheDir, 'site.html'), 'w')
                f.write('<Titel>'+ url + '</Title>\n\n')
                f.write(data)
                f.close()

            if site.startRE:
                start = data.find(site.startRE.encode('utf-8'))
                if start == -1:
                    print('startRe not found for %s' % url)
                else:
                    data = data[start:]
                    if site.stopRE:
                        stop = data.find(site.stopRE.encode('utf-8'))
                        if stop == -1:
                            print('stopRe not found for %s' % url)
                        else:
                            data = data[:stop]

            # If user setting is not set to "Ask me"
            # Sort rules to parse in the order specified in the settings
            # Parsing will continue until a match is found with rule.priority anything other than 0
            if len(site.rules) > 1:
                decorated1 = [(rule.priority, i, rule) for i, rule in enumerate(site.rules) if rule.priority < 0]
                decorated1 = sorted(decorated1, reverse = True)
                if int(addon.getSetting('video_type')) == 3:
                    decorated = [(rule.priority, i, rule) for i, rule in enumerate(site.rules) if rule.priority >= 0]
                    decorated = sorted(decorated)
                    site.rules = [rule for priority, i, rule in decorated]
                elif int(addon.getSetting('video_type')) == 2:
                    decorated = [(rule.priority, i, rule) for i, rule in enumerate(site.rules) if rule.priority > 0]
                    decorated = sorted(decorated)
                    if len(decorated) % 2 == 0:
                        decorated = decorated[len(decorated) // 2 - 1:] + list(reversed(decorated[:len(decorated) // 2 - 1]))
                    else:
                        decorated = decorated[len(decorated) // 2:] + list(reversed(decorated[:len(decorated) // 2]))
                    site.rules = [rule for rule in site.rules if rule.priority == 0] + [rule for priority, i, rule in decorated]
                elif int(addon.getSetting('video_type')) == 1:
                    decorated = [(rule.priority, i, rule) for i, rule in enumerate(site.rules) if rule.priority > 0]
                    decorated = sorted(decorated, reverse = True)
                    site.rules = [rule for rule in site.rules if rule.priority == 0] + [rule for priority, i, rule in decorated]
                site.rules += [rule for priority, i, rule in decorated1]
                if site.startRE:
                    start = data.find(site.startRE.encode('utf-8'))
                    if start == -1:
                        print('startRe not found for %s' % url)
                    else:
                        data = data[start:]
                        if site.stopRE:
                            stop = data.find(site.stopRE.encode('utf-8'))
                            if stop == -1:
                                print('stopRe not found for %s' % url)
                            else:
                                data = data[:stop]
            # Parse Website
            for rule in site.rules:
                match = re.search(rule.target, data, re.IGNORECASE + re.DOTALL + re.MULTILINE)
                if match:
                    link = match.group(1)
                    if len(rule.actions) > 0:
                        for group in range(1, len(match.groups()) + 1):
                            if group == 1:
                                link = {'match' : link}
                            else:
                                link['group' + str(group)] = match.group(group)
                        link = parseActions(link, rule.actions)['match']
                    if rule.build != None:
                        link = rule.build % link
                    if rule.type == 'video':
                        video_found = True
                        self.urlList.append(link)
                        self.extensionList.append(rule.extension)
                        self.playerList.append(rule.player)
                        if rule.dkey != None:
                            match = re.search(rule.dkey, data, re.IGNORECASE + re.DOTALL + re.MULTILINE)
                            if match:
                                dkey = match.group(1)
                                if len(rule.dkey_actions) > 0:
                                    dkey = {'match' : dkey}
                                    dkey = parseActions(dkey, rule.dkey_actions)['match']
                                self.decryptList.append(dkey)
                        else:
                            self.decryptList.append(None)
                        if int(addon.getSetting('video_type')) == 0:
                            selList_type = {
                                'low' : __language__(30056), 
                                'standard' : __language__(30057), 
                                'high' : __language__(30058)
                            }
                            append = rule.info or rule.extension
                            self.selectionList.append(selList_type[rule.quality] + ' (' + append + ')')
                    elif rule.type == 'dkey':
                        self.dkey = link
                    elif rule.type == 'forward':
                        url = clean_safe(urllib.unquote(link))
                        break
                    elif rule.type.startswith('redirect'):
                        tmp_lItem = {'url': clean_safe(urllib.unquote(link))}
                        if rule.type.find(u"(") != -1:
                            tmp_lItem['catcher'] = rule.type[rule.type.find(u"(") + 1:-1]
                        ### need to make the else statement below an elif statement 
                        ### and make the else default to simple-match catcher 
                        else:
                            for root, dirs, files in os.walk(catDir):
                                for filename in files:
                                    if url.find(filename) != -1:
                                        tmp_lItem['catcher'] = filename
                        ret_videoItem = CCatcherList(tmp_lItem)
                        if ret_videoItem.videoItem != None:
                            return ret_videoItem
                        break
                    if int(addon.getSetting('video_type')) != 0 and rule.priority != 0:
                        break
        return None

    def selectLink(self):
        if int(addon.getSetting('video_type')) != 0:
            selection = 0
        else:
            dia = xbmcgui.Dialog()
            selection = dia.select(__language__(30055), self.selectionList)
        self.urlList[selection] = clean_safe(urllib.unquote(self.urlList[selection]))
        if self.dkey != None:
            self.dkey = clean_safe(urllib.unquote(self.dkey))
            self.urlList[selection] = sesame.decrypt(self.urlList[selection], self.dkey, 256)
        elif self.decryptList[selection] != None:
            self.decryptList[selection] = clean_safe(urllib.unquote(self.decryptList[selection]))
            self.urlList[selection] = sesame.decrypt(self.urlList[selection], self.decryptList[selection], 256)
        self.link = self.urlList[selection]
        self.videoExtension = '.' + self.extensionList[selection]
        self.player = self.playerList[selection]
        return None