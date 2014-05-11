# -*- coding: latin-1 -*-

import sys, traceback
import os.path
import re

from lib.common import smart_unicode, inheritInfos

from lib.entities.CItemTypes import CItemTypes

from lib.utils.fileUtils import smart_read_file, getFileExtension
from lib.utils.xbmcUtils import getSearchPhrase

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
enable_debug = sys.modules["__main__"].enable_debug
log = sys.modules["__main__"].log

class CItemInfo:
    def __init__(self):
        self.name = ''
        self.src = 'url'
        self.rule = ''
        self.default = ''
        self.build = ''

    def __str__(self):
        txt = ['item_info_name=%s' % self.name]
        if self.src != 'url':
            txt.append('item_info_from=%s' % self.src)
        if self.rule != '':
            txt.append('item_info=%s' % self.rule)
        if self.default != '':
            txt.append('item_info_default=%s' % self.default)
        txt.append('item_info_build=%s' % self.build)
        return '\n'.join(txt)


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

    def __str__(self):
        txt = ['item_infos=%s' % self.infos]
        txt.append('item_order=%s' %  '|'.join([k for k in self.order]))
        if self.skill != '':
            txt.append('item_skill=%s' % self.skill)
        if self.curr != '':
            txt.append('item_curr=%s' % self.curr)
        txt.append('item_type=%s' % self.type)
        if len(self.info_list) != 0:
            for info in self.info_list:
                txt.append(str(info))
        if len(self.actions) != 0:
            txt.append('item_infos_actions=%s' % '|'.join([k for k in self.actions]))
        txt.append('item_url_build=%s' % self.url_build)
        return '\n'.join(txt)


class CRuleSite:
    def __init__(self):
        self.start = ''
        self.txheaders = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.8.1.18) Gecko/20081029 Firefox/2.0.0.18',
            'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        }
        self.skill = ''
        self.sort = []
        self.startRE = ''
        self.cfg = None
        self.rules = []
        self.links = CItemTypes()
        self.items = CItemTypes()

    def __str__(self):
        txt = ['site_start=%s' % self.start]
        if len(self.txheaders) != 0: #needs to be fixed
            txt.append('site_header=%s' % '|'.join([k for k in self.txheaders]))
        if self.skill != '':
            txt.append('site_skill=%s' % self.skill)
        if len(self.sort) != 0:
            txt.append('site_sort=%s' % '|'.join([k for k in self.sort]))
        if self.startRE != '':
            txt.append('site_startRE=%s' % self.startRE)
        if self.cfg != None:
            txt.append('site_cfg=%s' % self.cfg)
        if len(self.rules) != 0:
            for rule in self.rules:
                txt.append(str(rule))
        if len(self.links) != 0:
            txt.append(str(self.links))
        if len(self.items) != 0:
            txt.append(str(self.items))
        return '\n'.join(txt)



def loadLocal(lItem, search_phrase = None):
    def loadKey(txt):
        return keys[-1] == txt and keys.pop()
    site = None
    links = []
    keys, values = loadFile(lItem)
    ext = getFileExtension(lItem['url'])
    if ext == 'cfg' or ext == 'list':
        filename = lItem['url']
        if ext == 'cfg' and 'cfg' not in lItem:
            lItem['cfg'] = filename
    else:
        filename = lItem['cfg']
    if 'type' in lItem and lItem['type'] == 'search' and search_phrase == None:
        search_phrase = getSearchPhrase()
    while keys:
        old_line = len(keys)
        while keys and keys[-1].startswith('site_'):
            old_line = len(keys)
            if loadKey('site_start'):
                site = CRuleSite()
                if ext == 'cfg':
                    site.start = values.pop()
                else:
                    if lItem['type'] == 'search':
                        lItem['url'] = lItem['url'] % search_phrase
                    site.start = lItem['url']
                    del values[-1]
                if site.cfg == None and ext == 'cfg':
                    site.cfg = filename
                elif 'cfg' in lItem:
                    site.cfg = lItem['cfg']
            if loadKey('site_header'):
                headers = values.pop().split('|')
                site.txheaders[headers[0]] = headers[1]
            if loadKey('site_skill'):
                site.skill = values.pop()
                skill_file = filename[:filename.find('.')] + '.lnk'
                if site.skill.find('redirect') != -1:
                    try:
                        f = open(str(os.path.join(resDir, skill_file)), 'r')
                    except IOError:
                        pass
                    else:
                        forward_cfg = f.read()
                        f.close()
                        if forward_cfg != filename:
                            lItem['url'] = forward_cfg
                            lItem['cfg'] = forward_cfg
                            return loadLocal(lItem)
                elif site.skill.find('store') != -1:
                    f = open(str(os.path.join(resDir, skill_file)), 'w')
                    f.write(filename)
                    f.close()
            if loadKey('site_sort'):
                if values[-1].find('|') != -1:
                    site.sort.extend(values.pop().split('|'))
                else:
                    site.sort.append(values.pop())
            if loadKey('site_startRE'):
                site.startRE = values.pop()
            if loadKey('site_cfg'):
                site.cfg = values.pop()
            if len(keys) == old_line:
                log('Syntax Error: "%s" is invalid.' % filename)
                del keys[-1]
        while keys and keys[-1].startswith('item_'):
            old_line = len(keys)
            if loadKey('item_infos'):
                rule_tmp = CRuleItem()
                rule_tmp.infos = values.pop()
            if loadKey('item_order'):
                if values[-1].find('|') != -1:
                    rule_tmp.order.extend(values.pop().split('|'))
                else:
                    rule_tmp.order.append(values.pop())
            if loadKey('item_skill'):
                rule_tmp.skill = values.pop()
            if loadKey('item_curr'):
                rule_tmp.curr = values.pop()
            if loadKey('item_type'):
                rule_tmp.type = values.pop()
            while keys and keys[-1].startswith('item_info_'):
                old_line = len(keys)
                if loadKey('item_info_name'):
                    info_tmp = CItemInfo()
                    if values[-1].startswith('video.devil.context'):
                        values[-1] = 'context.' + __language__(int(values[-1][20:]))
                    info_tmp.name = values.pop()
                if loadKey('item_info_from'):
                    info_tmp.src = values.pop()
                if loadKey('item_info'):
                    info_tmp.rule = values.pop()
                if loadKey('item_info_default'):
                    info_tmp.default = values.pop()
                if loadKey('item_info_build'):
                    if values[-1].startswith('video.devil.'):
                        if values[-1].startswith('video.devil.locale'):
                            values[-1] = '  ' + __language__(int(values[-1][19:])) + '  '
                        elif values[-1].startswith('video.devil.image'):
                            values[-1] = os.path.join(imgDir, values[-1][18:])
                    info_tmp.build = values.pop()
                    rule_tmp.info_list.append(info_tmp)
                    info_tmp = None
                if len(keys) == old_line:
                    log('Syntax Error: "%s" is invalid.' % filename)
                    del keys[-1]
            if loadKey('item_infos_actions'):
                if values[-1].find('|') != -1:
                    rule_tmp.actions.extend(values.pop().split('|'))
                else:
                    rule_tmp.actions.append(values.pop())
            if loadKey('item_url_build'):
                rule_tmp.url_build = values.pop()
                site.rules.append(rule_tmp)
                rule_tmp = None
            if len(keys) == old_line:
                log('Syntax Error: "%s" is invalid.' % filename)
                del keys[-1]
        while keys and keys[-1].startswith('link_'):
            old_line = len(keys)
            if loadKey('link_title'):
                tmp = {}
                if values[-1].startswith('video.devil.locale'):
                    values[-1] = '  ' + __language__(int(values[-1][19:])) + '  '
                tmp['title'] = values.pop()
            while tmp != None and keys[-1] != 'link_url':
                if values[-1].startswith('video.devil.image'):
                    values[-1] = os.path.join(imgDir, values[-1][18:])
                tmp[keys[-1][5:]] = values.pop()
                del keys[-1]
            if loadKey('link_url'):
                tmp['url'] = values.pop()
                if filename == 'sites.list':
                    if addon.getSetting(tmp['title']) == 'true':
                        tmp['cfg'] = tmp['url']
                        links.append(tmp)
                else:
                    tmp = inheritInfos(tmp, lItem)
                    if site != None:
                        if ext == 'cfg' and tmp['type'] == 'once':
                            tmp['type'] = 'links'
                        site.links[tmp['type']] = (tmp, [tmp])
                    else:
                        links.append(tmp)
                tmp = None
                break
            if len(keys) == old_line:
                log('Syntax Error: "%s" is invalid.' % filename)
                del keys[-1]
        if len(keys) == old_line:
            log('Syntax Error: "%s" is invalid.' % filename)
            del keys[-1]
    if site != None:
        return site
    return links

def loadFile(lItem):
    ext = getFileExtension(lItem['url'])
    if ext == 'cfg' or ext == 'list':
        filename = lItem['url']
    else:
        filename = lItem['cfg']
    for directory in [resDir, cacheDir, allsitesDir, catDir, '']:
        try:
            f = open(os.path.join(directory, filename), 'r')
        except IOError:
            pass
        else:
            data = f.read()
            f.close()
            data = data.splitlines()
            keys = []
            values = []
            for line in reversed(data):
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    keys.append(key)
                    values.append(value)
            return keys, values
    else:
        traceback.print_exc(file = sys.stdout)
        log('File Not Found: "%s"' % filename)
        raise


class localParser:
    def __init__(self):
        self.all_cfg_items = None
        self.cfg_items_in_list = []
        self.cfg_items_not_in_list = []
        self.search_phrase = None
        self.site = None
        self.sites = []
        self.links = []

    def resetLinks(self):
        tmp = []
        tmp, self.links = self.links, tmp
        return tmp

    def resetSites(self):
        tmp = []
        tmp, self.sites = self.sites, tmp
        return tmp

    def reset(self):
        self.resetLinks()
        self.resetSites()
        return None

    def load_site(self, lItem = {'url': 'sites.list'}):
        self.site = loadLocal(lItem)
        return self.site

    def load_links(self, lItem = {'url': 'sites.list'}):
        self.links = loadLocal(lItem)
        return self.links

    def load_all_sites_links(self, lItem = {'url': 'sites.list'}):
        self.all_sites_links = loadLocal(lItem)
        return None

    def load_links_and_all_sites_links(self, lItem):
        self.load_all_sites_links()
        self.load_links(lItem)
        return None

    def load_links_and_sites_in_list(self, lItem):
        self.load_links(lItem)
        if 'type' in lItem and lItem['type'] == 'category':
            sites_in_list = set([link['cfg'] for link in self.links])
            search_links = loadLocal({'url': 'search.list'})
            search_as_category_links = [link for link in search_links if link['cfg'] not in sites_in_list]
            search_phrase = lItem['title'].strip().lower()
            search_as_category_sites = [loadLocal(link, search_phrase) for link in search_as_category_links]
            sites = map(loadLocal, self.links) + search_as_category_sites
            self.links += search_as_category_links
            self.sites = zip(sites, self.links)
        else:
            self.sites = zip(map(loadLocal, self.links), self.links)
        return None

    def load_links_and_sites_not_in_list(self, lItem):
        self.load_links_and_all_sites_links(lItem)
        sites_in_list = set([link['cfg'] for link in self.links])
        self.cfg_links_not_in_list = [link for link in self.all_sites_links if link['cfg'] not in sites_in_list]
        for link in self.cfg_links_not_in_list:
            site = loadLocal(link)
            for type, infos, links in site.links.files():
                if type == self.links[0]['type']:
                    site.start = links[0]['url']
                    self.sites.append((site, links[0]))
                    break
        return None