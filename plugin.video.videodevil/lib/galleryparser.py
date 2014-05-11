# -*- coding: latin-1 -*-
from string import capitalize, lower
import sys, os.path
import os, traceback
import re
import urllib, urllib2
import cookielib

import xbmcplugin, xbmcaddon
import xbmc, xbmcgui

from lib.common import log, inheritInfos, smart_unicode

from lib.entities.CItemTypes import CItemTypes
from lib.entities.Mode import Mode

from lib.utils.encodingUtils import clean_safe
from lib.utils.fileUtils import smart_read_file, getFileExtension, saveList

import sesame

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

urlopen = urllib2.urlopen
cj = cookielib.LWPCookieJar()
Request = urllib2.Request
USERAGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.8.1.18) Gecko/20081029 Firefox/2.0.0.18'

if cj != None:
    if os.path.isfile(xbmc.translatePath(os.path.join(settingsDir, 'cookies.lwp'))):
        cj.load(xbmc.translatePath(os.path.join(settingsDir, 'cookies.lwp')))
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
else:
    opener = urllib2.build_opener()
    urllib2.install_opener(opener)

if addon.getSetting('enable_debug') == 'true':
    enable_debug = True
    xbmc.log('VideoDevil debug logging enabled')
else:
    enable_debug = False

def parseActions(item, convActions, url = None):
#    print('item = ' + str(item))
    for convAction in convActions:
        if convAction.find(u"(") != -1:
            action = convAction[0:convAction.find('(')]
#            print('action = ' + action)
            param = convAction[len(action) + 1:-1]
#            print('param = ' + param)
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

class CItemInfo:
    def __init__(self):
        self.name = ''
        self.src = 'url'
        self.rule = ''
        self.default = ''
        self.build = ''


class CRuleItem:
    def __init__(self):
        self.infos = ''
        self.infosRE = ''
        self.order = []
        self.skill = ''
        self.curr = ''
        self.currRE = ''
        self.type = ''
        self.info_list = []
        self.actions = []
        self.url_build = ''


class CRuleSite:
    def __init__(self):
        self.status = {}
        self.start = ''
        self.txheaders = {
            'User-Agent': USERAGENT,
            'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        }
        self.startRE = ''
        self.cfg = ''
        self.data = ''
        self.rules = []
        self.items = CItemTypes()
        self.links = CItemTypes()


class CCurrentList:
    def __init__(self):
        self.sort = ['label', 'genre']
        self.skill = ''
        self.sites = []
        self.items = CItemTypes()
        self.links = CItemTypes()

    def videoCount(self):
        count = 0
        for item in self.items:
            if item['type'] == 'video':
                count = count +1
        return count

    def getVideo(self):
        for item in self.items:
            if item['type'] == 'video':
                return item
 
    def loadLocal(self, filename, lItem):
        site = CRuleSite()
        key, value, site.status['file'] = smart_read_file(filename)
        if key == None and value == None:
            return None
        site.cfg = filename
        if 'cfg' not in lItem:
            if getFileExtension(filename) == 'cfg':
                lItem['cfg'] = filename
        tmp = None
        line = 0
        length = len(key) - 1
        breaker = -10
        if key[line] == 'start':
            site.start = value[line]
            line += 1
        if key[line] == 'header':
            index = value[line].find('|')
            site.txheaders[value[line][:index]] = value[line][index+1:]
            line += 1
        if key[line] == 'sort':
            self.sort.append(value[line])
            line += 1
        if key[line] == 'skill':
            skill_file = filename[:filename.find('.')] + '.lnk'
            if value[line].find('redirect') != -1:
                try:
                    f = open(str(os.path.join(resDir, skill_file)), 'r')
                    forward_cfg = f.read()
                    f.close()
                    if forward_cfg != filename:
                        return self.loadLocal(forward_cfg, lItem)
                    return site
                except:
                    pass
            elif value[line].find('store') != -1:
                f = open(str(os.path.join(resDir, skill_file)), 'w')
                f.write(filename)
                f.close()
            line += 1
        if key[line] == 'startRE':
            site.startRE = value[line]
            line += 1
        while line < length:
            breaker += 1
            while line < length and key[line].startswith('item'):
                breaker += 1
                if key[line] == 'item_infos':
                    rule_tmp = CRuleItem()
                    rule_tmp.infos = value[line]
                    line += 1
                if key[line] == 'item_order':
                    if value[line].find('|'):
                        rule_tmp.order = value[line].split('|')
                    else:
                        rule_tmp.order.append(value[line])
                    line += 1
                if key[line] == 'item_skill':
                    rule_tmp.skill = value[line]
                    line += 1
                if key[line] == 'item_curr':
                    rule_tmp.curr = value[line]
                    line += 1
                if key[line] == 'item_type':
                    rule_tmp.type = value[line]
                    line += 1
                while key[line].startswith('item_info_'):
                    breaker += 1
                    if key[line] == 'item_info_name':
                        info_tmp = CItemInfo()
                        info_tmp.name = value[line]
                        line += 1
                    if key[line] == 'item_info_from':
                        info_tmp.src = value[line]
                        line += 1
                    if key[line] == 'item_info':
                        info_tmp.rule = value[line]
                        line += 1
                    if key[line] == 'item_info_default':
                        info_tmp.default = value[line]
                        line += 1
                    if key[line] == 'item_info_build':
                        info_tmp.build = value[line]
                        rule_tmp.info_list.append(info_tmp)
                        line += 1
                    if breaker == length:
                        break
                if key[line] == 'item_infos_actions':
                    rule_tmp.actions = value[line].split('|') or [value[line]]
                    line += 1
                if key[line] == 'item_url_build':
                    rule_tmp.url_build = value[line]
                    site.rules.append(rule_tmp)
                    line += 1
            if breaker == length:
                break
            while line < length:
                breaker += 1
                if key[line] == 'title':
                    tmp = {}
                    tmp['title'] = value[line]
                    line += 1
                while line < length and key[line] != 'url':
                    if tmp:
                        if key[line] == 'mode':
                            tmp[key[line]] = int(value[line])
                        else:
                            tmp[key[line]] = value[line]
                        line += 1
                    else:
                        break
                if key[line] == 'url':
                    tmp['url'] = value[line]
                    if lItem != None:
                        tmp = inheritInfos(tmp, lItem)
                    if lItem['mode'] == Mode.START:
                        tmp['mode'] = Mode.VIEW_RSS
                    elif lItem['mode'] == Mode.VIEW_RSS:
                        if tmp['type'] == 'search':
                            tmp['mode'] = Mode.VIEW_SEARCH
                    elif lItem['mode'] == Mode.VIEW_SEARCH:
                        tmp['mode'] = Mode.VIEW_RSS
                    elif lItem['mode'] == Mode.VIEW_DIRECTORY:
                        tmp['mode'] = Mode.VIEW_RSS
                        tmp['type'] = 'rss'
                    elif lItem['mode'] == Mode.VIEWALL_RSS:
                        if tmp['type'] == 'search':
                            tmp['mode'] = Mode.VIEWALL_SEARCH
                    elif lItem['mode'] == Mode.VIEWALL_SEARCH:
                        tmp['mode'] = Mode.VIEWALL_RSS
                    site.links[tmp['type']] = (tmp, [tmp])
                    tmp = None
                    line += 1
                if line >= length or breaker == length:
                    break
        if breaker == length:
            site.status['syntax'] = 'Cfg syntax is invalid.\nKey error in line %s' % str(line)
        else:
            site.status['syntax'] = 'Cfg syntax is valid'
        return site

    def loadRemote(self, site, lItem):
        # Get HTML site
        try:
            if enable_debug:
                f = open(os.path.join(cacheDir, site.cfg + '.page.html'), 'w')
                f.write('<Title>'+ site.start + '</Title>\n\n')
            req = Request(site.start, None, site.txheaders)
            try:
                handle = urlopen(req)
                site.status['web_request'] = 'Successfully opened %s' % site.start
            except:
                site.status['web_request'] = 'Failed to open "%s"\r\nUrl is invalid' % site.start
                print('Failed to open "%s"\r\nUrl is invalid' % site.start)
                if enable_debug:
                    traceback.print_exc(file = sys.stdout)
                return
            data = handle.read()
            cj.save(os.path.join(settingsDir, 'cookies.lwp'))
            site.status['web_response'] = 'Successfully fetched'
            if enable_debug:
                f.write(data)
                f.close()
        except IOError:
            site.status['web_response'] = 'Failed to receive a response from ' % site.start
            print('Failed to receive a response from ' % site.start)
            if enable_debug:
                traceback.print_exc(file = sys.stdout)
            return
        # Create variables while loop
        interests = []
        interests2 = []
        if site.startRE:
            point = data.find(site.startRE.encode('utf-8'))
            if point == -1:
                print('startRe not found for %s' % site.cfg)
                point = 0
        else:
            point = 0
        length = len(data)
        # Append interests lists and modify rule RE patterns
        interestRE = re.compile(r'[-a-zA-Z0-9/,:;%!&$_#=~@<> ]+', re.IGNORECASE + re.DOTALL + re.MULTILINE)
        for item_rule in site.rules:
            item_rule.infos = item_rule.infos.encode('utf-8')
            if item_rule.curr:
                item_rule.curr = item_rule.curr.encode('utf-8')
            match = interestRE.match(item_rule.infos)
            if match:
                interests.append(match.group(0))
            else:
                print('RE pattern in ' +
                    site.cfg + 
                    'starts with a special character.\n RE pattern = \' ' +
                    item_rule.infos +
                    '\''
                    )
            if item_rule.curr:
                match = interestRE.match(item_rule.curr)
                if match:
                    interests2.append(match.group(0))
                else:
                    print('RE pattern in ' +
                        site.cfg + 
                        ' starts with a special character.\n RE pattern = \' ' +
                        item_rule.curr +
                        '\''
                    )
        # Combine interests list
        interests2.extend(interests)
        # Remove longer matches that may cause the while loop to shorter matches
        # i.e. remove '<img src' if '<img' is in the list
#        print('interests2 = ' + str(interests2))
        interesting_items = self.listFormatter(interests2)
#        print('interesting_items = ' + str(interesting_items))
        # Create interestingRE from interesting_items list
        interesting_pattern = '(' + '|'.join(interesting_items) + ')'
        interestingRE = re.compile(interesting_pattern, re.IGNORECASE + re.DOTALL + re.MULTILINE)
        # Create REs for while loop
        for item_rule in site.rules:
            match = interestingRE.match(item_rule.infos)
            if match:
                item_rule.infos = item_rule.infos[match.end():]
            item_rule.infosRE = re.compile(item_rule.infos, re.IGNORECASE + re.DOTALL + re.MULTILINE)
            if item_rule.curr:
                item_rule.currRE = re.compile(item_rule.curr, re.IGNORECASE + re.DOTALL + re.MULTILINE)
        # Find links
#        print('start point = ' + str(point))
#        print('start point datachunk = ' + data[point:point + 100])
        while point < length:
            interest = interestingRE.search(data, point)
            if interest:
                point = interest.start()
                intersting_point = interest.start()
                jump = len(interest.group(0))
#                print('point of interest = ' + str(point))
#                print('interesting point found = ' + interest.group(0))
                for index, rule_name in enumerate(interests):
                    item_rule = site.rules[index]
                    if rule_name.startswith(interest.group(0)):
#                        print('rule_name = ' + rule_name)
#                        print('datachunk = ' + data[point:point + 25])
#                        print('trying to match at datachunk = ' + data[point + jump:point + jump + 25])
#                        print('With rule pattern = ' + item_rule.infos)
                        match = item_rule.infosRE.match(data, point + jump)
                        if match:
#                            print('match found')
                            while match:
#                                print('match found = ' + match.group(0))
                                if not match.group(0):
                                    break
                                point += jump + len(match.group(0))
                                self.itemBuilder(site, item_rule, lItem, site.start, match)
                                match = item_rule.infosRE.match(data, point + jump)
                            break
                    if point == intersting_point and item_rule.curr and item_rule.curr.startswith(interest.group(0)):
                        match = item_rule.currRE.match(data, point)
                        if match:
                            while match:
                                if not match.group(0):
                                    break
                                point += len(match.group(0))
                                self.currBuilder(site, item_rule, lItem, site.start, match)
                                match = item_rule.currRE.match(data, point)
                            break
                if point == intersting_point:
                    point += 1
            else:
                log('Parsing complete')
                break
        return

    # Helper functions for loadRemote

    def itemBuilder(self, site, rule, lItem, url, match):
        tmp = {}
        tmp = self.loadDict(tmp, rule, url, match)
        tmp['type'] = rule.type
        if rule.type in site.items:
            for item in site.items[rule.type]:
                if tmp['url'] == item['url']:
                    tmp = None
                    return
        tmp = self.infoFormatter(tmp)
        try:
            if rule.skill.find('space') != -1:
                tmp['title'] = '  ' + tmp['title'] + '  '
            elif rule.skill.find('bottom') != -1:
                tmp['title'] = tmp['title'].strip()
        except:
            pass
        tmp = inheritInfos(tmp, lItem)
        if rule.skill.find('recursive') != -1:
            site.start = tmp['url']
            self.loadRemote(site, tmp)
            tmp = None
        else:
            if lItem['mode'] == Mode.VIEW_RSS:
                if tmp['type'] == 'video':
                    tmp['mode'] = Mode.PLAY
            elif lItem['mode'] == Mode.VIEW_SEARCH:
                if tmp['type'] == 'video':
                    tmp['mode'] = Mode.PLAY
                elif tmp['type'] == 'next':
                    tmp['mode'] = Mode.VIEW_RSS
                else:
                    tmp['mode'] = Mode.VIEW_DIRECTORY
            elif lItem['mode'] == Mode.VIEWALL_RSS:
                if tmp['type'] == 'video':
                    tmp['mode'] = Mode.PLAY
                elif tmp['type'] != 'next':
                    tmp['mode'] = Mode.VIEWALL_DIRECTORY
            elif lItem['mode'] == Mode.VIEWALL_SEARCH:
                if tmp['type'] == 'video':
                    tmp['mode'] = Mode.PLAY
                elif tmp['type'] == 'next':
                    tmp['mode'] = Mode.VIEWALL_RSS
                else:
                    tmp['mode'] = Mode.VIEWALL_DIRECTORY
            elif lItem['mode'] == Mode.VIEWALL_DIRECTORY:
                if tmp['type'] == 'video':
                    tmp['mode'] = Mode.PLAY
                else:
                    tmp['mode'] = Mode.VIEWALL_RSS
            if rule.type in site.items:
                site.items[rule.type] = (tmp, [tmp])
            else:
                tmp_infos = {'type': rule.type}
                for info in rule.info_list:
                    if info.name == 'title':
                        tmp_infos['title'] = info.build
                    elif info.name == 'icon':
                        tmp_infos['icon'] = info.build
            tmp_infos = inheritInfos(tmp_infos, lItem)
                site.items[rule.type] = (tmp_infos, [tmp])
        return

    def loadDict(self, item, rule, url, match):
        infos_names = rule.order
        infos_values = match.groups()
        for idx, infos_name in enumerate(infos_names):
            item[infos_name] = clean_safe(infos_values[idx])
        for info in rule.info_list:
            info_value = ''
            if info.name in item:
                if info.build.find('%s') != -1:
                    item[info.name] = info.build % item[info.name]
                continue
            if info.rule != '':
                info_rule = info.rule
                if info.rule.find('%s') != -1:
                    src = item[info.src]
                    info_rule = info.rule % src
                infosearch = re.search(info_rule, data)
                if infosearch:
                    info_value = infosearch.group(1).strip()
                    if info.build.find('%s') != -1:
                        info_value = info.build % info_value
                elif info.default != '':
                    info_value = info.default
            else:
                if info.build.find('%s') != -1:
                    src = item[info.src]
                    info_value = info.build % src
                else:
                    info_value = info.build
            item[info.name] = info_value
        if len(rule.actions) > 0:
            item = parseActions(item, rule.actions, url)
        item['url'] = rule.url_build % item['url']
        return item

    def infoFormatter(self, item):
        keep = {}
        for info_name, info_value in item.iteritems():
            if info_name == 'title':
                if info_value != '':
                    try:
                        info_value = info_value.replace('\r\n', '').replace('\n', '').replace('\t', '')
                        info_value = info_value.lstrip(' -!@#$%^&*_-+=.,)\'<>;:"[{]}\|/?`~')
                        info_value = info_value.rstrip(' -@#$%^&*_-+=.,<>;(:\'"[{]}\|/?`~')
                        info_value = info_value.split(' ')
                        title = []
                        for word in info_value:
                            if word:
                                word = word.lower().capitalize()
                            title.append(word)
                        info_value = ' '.join(title).replace('  ', ' ')
                        info_value = ' ' + info_value + ' '
                    except:
                        info_value = ' ... '
                else:
                    info_value = ' ... '
            elif info_name == 'duration':
                if info_value[-2] == ';':
                    info_value = info_value.insert(-1, 0)
            elif info_name == 'icon':
                if info_value == '':
                    info_value = os.path.join(imgDir, 'video.png')
            elif info_name.rfind('.tmp') != -1:
                continue
            keep[info_name] = info_value
        
        return keep

    def currBuilder(self, site, rule, lItem, url, match):
        title = clean_safe(match.group(1).strip())
        tmp = {}
        if rule.skill.find('space') != -1:
            tmp['title'] = '   ' + title + ' (' + __language__(30106) + ')   '
        else:
            tmp['title'] = '  ' + title + ' (' + __language__(30106) + ')  '
        tmp['url'] = url
        tmp['type'] = rule.type
    tmp = inheritInfos(tmp, lItem)
        if lItem['mode'] == Mode.VIEW_RSS:
            if tmp['type'] == 'video':
                tmp['mode'] = Mode.PLAY
            elif tmp['type'] != 'next':
                tmp['mode'] = Mode.VIEW_DIRECTORY
        elif lItem['mode'] == Mode.VIEW_SEARCH:
            if tmp['type'] == 'video':
                tmp['mode'] = Mode.PLAY
            elif tmp['type'] == 'next':
                tmp['mode'] = Mode.VIEW_RSS
            else:
                tmp['mode'] = Mode.VIEW_DIRECTORY
        elif lItem['mode'] == Mode.VIEWALL_RSS:
            if tmp['type'] == 'video':
                tmp['mode'] = Mode.PLAY
            elif tmp['type'] != 'next':
                tmp['mode'] = Mode.VIEWALL_DIRECTORY
        elif lItem['mode'] == Mode.VIEWALL_SEARCH:
            if tmp['type'] == 'video':
                tmp['mode'] = Mode.PLAY
            elif tmp['type'] == 'next':
                tmp['mode'] = Mode.VIEWALL_RSS
            else:
                tmp['mode'] = Mode.VIEWALL_DIRECTORY
        elif lItem['mode'] == Mode.VIEWALL_DIRECTORY:
            tmp['mode'] = Mode.VIEWALL_RSS
        if rule.type in site.items:
            site.items[rule.type] = (tmp, [tmp])
        else:
            tmp_infos = {'type': rule.type}
            for info in rule.info_list:
                if info.name == 'title':
                    tmp_infos['title'] = info.build
                elif info.name == 'icon':
                    tmp_infos['icon'] = info.build
        tmp_infos = inheritInfos(tmp_infos, lItem)
            site.items[rule.type] = (tmp_infos, [tmp])
        return

    def listFormatter(self, List):
        list1 = set(List)
        list2 = []
        list3 = set(List)
        while len(list1) > 0:
            x = list1.pop()
            for y in list1:
                if x.startswith(y):
                    if y not in list2:
                        list2.append(y)
                elif y.startswith(x):
                    list2.append(x)
                    break
        for x in list3:
            if x not in list2:
                for z in list2:
                    if x.startswith(z):
                        break
                else:
                    list2.append(x)
        return list2

    # Helper functions for the class

    def addItem(self, name):
        item = self.getItem(name)
        del self.items[:]
        try:
            self.loadLocal('entry.list')
        except:
            del self.items[:]
        if item and not self.itemInLocalList(name):
            self.items.append(item)
            saveList(resDir, 'entry.list', 'Added sites and live streams', self.items, {skill : remove})
        return

    def getItem(self, name):
        item = None
        for root, dirs, files in os.walk(resDir):
            for listname in files:
                if getFileExtension(listname) == 'list' and listname != 'catcher.list':
                    item = self.getItemFromList(listname, name)
                if item != None:
                    return item
        return None

    def itemInLocalList(self, name):
        for item in self.items:
            if item['url'] == name:
                return True
        return False

    def getItemFromList(self, listname, name):
        self.loadLocal(listname)
        for item in self.items:
            if item['url'] == name:
                return item
        return None

    def removeItem(self, name):
        item = self.getItemFromList('entry.list', name)
        if item != None:
            self.items.remove(item)
            saveList(resDir, 'entry.list', 'Added sites and live streams', self.items, {skill : remove})
        return

