# -*- coding: latin-1 -*-

import sys, traceback
import os.path
import re

from lib.common import smart_unicode, inheritInfos

from lib.entities.CItemTypes import CItemTypes

from lib.utils.fileUtils import smart_read_file, getFileExtension

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
        self.name = u''
        self.src = u'url'
        self.rule = u''
        self.default = u''
        self.build = u''

    def __str__(self):
        txt = [u'item_info_name=%s' % self.name]
        if self.src != u'url':
            txt.append(u'item_info_from=%s' % self.src)
        if self.rule != u'':
            txt.append(u'item_info=%s' % self.rule)
        if self.default != u'':
            txt.append(u'item_info_default=%s' % self.default)
        txt.append(u'item_info_build=%s' % self.build)
        return u'\n'.join(txt)


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
        txt = [u'item_infos=%s' % self.infos]
        txt.append(u'item_order=%s' %  u'|'.join([k for k in self.order]))
        if self.skill != '':
            txt.append(u'item_skill=%s' % self.skill)
        if self.curr != '':
            txt.append(u'item_curr=%s' % self.curr)
        txt.append(u'item_type=%s' % self.type)
        if len(self.info_list) != 0:
            for info in self.info_list:
                txt.append(str(info))
        if len(self.actions) != 0:
            txt.append(u'item_infos_actions=%s' % u'|'.join([k for k in self.actions]))
        txt.append(u'item_url_build=%s' % self.url_build)
        return u'\n'.join(txt)


class CRuleSite:
    def __init__(self):
        self.start = ''
        self.txheaders = []
        self.skill = ''
        self.sort = []
        self.startRE = ''
        self.cfg = None
        self.rules = []
        self.links = CItemTypes()
        self.items = CItemTypes()

    def __str__(self):
        txt = [u'site_start=%s' % self.start]
        if len(self.txheaders) != 0:
            txt.append(u'site_header=%s' % u'|'.join([k for k in self.txheaders]))
        if self.skill != '':
            txt.append(u'site_skill=%s' % self.skill)
        if len(self.sort) != 0:
            txt.append(u'site_sort=%s' % u'|'.join([k for k in self.sort]))
        if self.startRE != '':
            txt.append(u'site_startRE=%s' % self.startRE)
        if self.cfg != None:
            txt.append(u'site_cfg=%s' % self.cfg)
        if len(self.rules) != 0:
            for rule in self.rules:
                txt.append(str(rule))
        if len(self.links) != 0:
            txt.append(str(self.links))
        if len(self.items) != 0:
            txt.append(str(self.items))
        return u'\n'.join(txt)

class localParser:
    def __init__(self):
        self.lItem = None
        self.all_cfg_items = None
        self.cfg_items_in_list = []
        self.cfg_items_not_in_list = []
        self.ext = None
        self.filename = None
        self.search_phrase = None
        self.keys = []
        self.values = []
        self.site = None
        self.rule_tmp = None
        self.info_tmp = None
        self.tmp = None
        self.sites = []
        self.links = []

    def resetLinks(self):
        self.links = []
        return None

    def resetSites(self):
        self.Sites = []
        return None

    def resetFiles(self):
        self.files = []
        self.keys = []
        self.values = []
        return None

    def reset(self):
        self.resetLinks()
        self.resetSites()
        self.resetFiles()
        return None

    def load_all_cfg_list(self, lItem = {'url': u'sites.list'}):
        self.all_cfg_items = self.loadLocal(lItem)

    def load_list(self, lItem):
        self.load_all_cfg_list()
        if lItem[u'url'] != u'sites.list':
            self.resetLinks()
            self.loadLocal(lItem)
        return self.links

    def load_sites_in_list(self, lItem = None):
        cfgs_in_list = set([link[u'cfg'] for link in self.links])
        self.cfg_items_not_in_list = [item for item in self.all_cfg_items if item[u'url'] not in cfgs_in_list]
        return [(self.loadLocal(item), item) for item in self.links]

    def load_sites_not_in_list(self, lItem = None):
        sites = []
        cfgs_in_list = set([link[u'cfg'] for link in self.links])
        self.cfg_items_in_list = [item for item in self.all_cfg_items if item[u'url'] in cfgs_in_list]
        self.cfg_items_not_in_list = [item for item in self.all_cfg_items if item[u'url'] not in cfgs_in_list]
        for item in self.cfg_items_not_in_list:
            site = self.loadLocal(item)
            for type, infos, items in site.links.files():
                if type == self.links[0][u'type']:
                    site.start = items[0][u'url']
                    sites.append((site, items[0]))
                    break
        return sites

    def loadLocal(self, lItem):
        self.loadFile(lItem)
        ext = getFileExtension(lItem[u'url'])
        if ext == u'cfg' or ext == u'list':
            filename = lItem[u'url']
            if ext == u'cfg' and u'cfg' not in lItem:
                lItem[u'cfg'] = filename
        else:
            filename = lItem[u'cfg']
        if u'type' in lItem and lItem[u'type'] == u'search' and not self.search_phrase:
            self.search_phrase = getSearchPhrase()
        while self.keys:
            old_line = len(self.keys)
            while self.keys and self.keys[-1].startswith(u'site_'):
                old_line = len(self.keys)
                if self.loadKey(u'site_start'):
                    if self.site != None:
                        self.sites.append(self.site)
                    self.site = CRuleSite()
                    if ext == u'cfg': #fix when allsites.list is removed
                        self.site.start = self.values.pop()
                    else:
                        if lItem[u'type'] == u'search':
                            lItem[u'url'] = lItem[u'url'] % self.search_phrase
                        self.site.start = lItem[u'url']
                        del self.values[-1]
                    if self.site.cfg == None and ext == u'cfg':
                        self.site.cfg = filename
                    elif u'cfg' in lItem:
                        self.site.cfg = lItem[u'cfg']
                if self.loadKey(u'site_header'):
                    self.site.txheaders.extend(self.values.pop().split(u'|'))
                if self.loadKey(u'site_skill'):
                    self.site.skill = self.values.pop()
                    skill_file = filename[:filename.find(u'.')] + u'.lnk'
                    if self.site.skill.find(u'redirect') != -1:
                        try:
                            f = open(str(os.path.join(resDir, skill_file)), 'r')
                            forward_cfg = f.read()
                            f.close()
                            if forward_cfg != filename:
                                return self.loadLocal(forward_cfg, lItem)
#                            return self.site
                        except:
                            pass
                    elif self.site.skill.find(u'store') != -1:
                        f = open(str(os.path.join(resDir, skill_file)), 'w')
                        f.write(filename)
                        f.close()
                if self.loadKey(u'site_sort'):
                    if self.values[-1].find(u'|') != -1:
                        self.site.sort.extend(self.values.pop().split(u'|'))
                    else:
                        self.site.sort.append(self.values.pop())
                if self.loadKey(u'site_startRE'):
                    self.site.startRE = self.values.pop()
                if self.loadKey(u'site_cfg'):
                    self.site.cfg = self.values.pop()
                if len(self.keys) == old_line:
                    log('Syntax Error: "%s" is invalid.' % filename)
                    del self.keys[-1]
            while self.keys and self.keys[-1].startswith(u'item_'):
                old_line = len(self.keys)
                if self.loadKey(u'item_infos'):
                    self.rule_tmp = CRuleItem()
                    self.rule_tmp.infos = self.values.pop()
                if self.loadKey(u'item_order'):
                    if self.values[-1].find(u'|') != -1:
                        self.rule_tmp.order.extend(self.values.pop().split(u'|'))
                    else:
                        self.rule_tmp.order.append(self.values.pop())
                if self.loadKey(u'item_skill'):
                    self.rule_tmp.skill = self.values.pop()
                if self.loadKey(u'item_curr'):
                    self.rule_tmp.curr = self.values.pop()
                if self.loadKey(u'item_type'):
                    self.rule_tmp.type = self.values.pop()
                while self.keys and self.keys[-1].startswith(u'item_info_'):
                    old_line = len(self.keys)
                    if self.loadKey(u'item_info_name'):
                        self.info_tmp = CItemInfo()
                        self.info_tmp.name = self.values.pop()
                    if self.loadKey(u'item_info_from'):
                        self.info_tmp.src = self.values.pop()
                    if self.loadKey(u'item_info'):
                        self.info_tmp.rule = self.values.pop()
                    if self.loadKey(u'item_info_default'):
                        self.info_tmp.default = self.values.pop()
                    if self.loadKey(u'item_info_build'):
                        self.info_tmp.build = self.values.pop()
                        self.rule_tmp.info_list.append(self.info_tmp)
                        self.info_tmp = None
                    if len(self.keys) == old_line:
                        log('Syntax Error: "%s" is invalid.' % filename)
                        del self.keys[-1]
                if self.loadKey(u'item_infos_actions'):
                    if self.values[-1].find(u'|') != -1:
                        self.rule_tmp.actions.extend(self.values.pop().split(u'|'))
                    else:
                        self.rule_tmp.actions.append(self.values.pop())
                if self.loadKey(u'item_url_build'):
                    self.rule_tmp.url_build = self.values.pop()
                    self.site.rules.append(self.rule_tmp)
                    self.rule_tmp = None
                if len(self.keys) == old_line:
                    log('Syntax Error: "%s" is invalid.' % filename)
                    del self.keys[-1]
            while self.keys and self.keys[-1].startswith(u'link_'):
                old_line = len(self.keys)
                if self.loadKey(u'link_title'):
                    self.tmp = {}
                    self.tmp[u'title'] = self.values.pop()
                if self.keys[-1].startswith(u'link_') and self.keys != u'link_url':
                    self.tmp[self.keys[-1][5:]] = self.values.pop()
                    del self.keys[-1]
                if self.loadKey(u'link_url'):
                    self.tmp[u'url'] = self.values.pop()
                    if lItem != None:
                        self.tmp = inheritInfos(self.tmp, lItem)
                    if (u'cfg' not in self.tmp) and getFileExtension(self.tmp[u'url']) == u'cfg':
                        self.tmp[u'cfg'] = self.tmp[u'url']
                    if filename == u'sites.list':
                        if addon.getSetting(self.tmp[u'title']) == 'true':
                            self.links.append(self.tmp)
                    else:
                        if self.site != None:
                            self.site.links[self.tmp[u'type']] = (self.tmp, [self.tmp])
                        else:
                            self.links.append(self.tmp)
                    self.tmp = None
                    break
                if len(self.keys) == old_line:
                    log('Syntax Error: "%s" is invalid.' % filename)
                    del self.keys[-1]
            if len(self.keys) == old_line:
                log('Syntax Error: "%s" is invalid.' % filename)
                del self.keys[-1]
        if self.site != None:
            self.sites.append(self.site)
            self.site = None
            print('returning site')
            return self.sites[-1]
        print('returning links')
        return self.links

    def loadFile(self, lItem, shortcuts = True):
        ext = getFileExtension(lItem[u'url'])
        if ext == u'cfg' or ext == u'list':
            filename = lItem[u'url']
        else:
            filename = lItem[u'cfg']
        for directory in [catDir, resDir, cacheDir, allsitesDir, '']:
            try:
                filepath = os.path.join(directory, filename)
                f = open(filepath, 'r')
                break
            except:
                if directory == '':
                    traceback.print_exc(file = sys.stdout)
                    log('File Not Found: "%s"' % filename)
                    return None
        keys = []
        values = []
        for line in f:
            line =  smart_unicode(line)
            if line and line.startswith(u'#'):
                continue
            try:
                line = line.replace(u'\r\n', u'').replace(u'\n', u'')
            except:
                continue
            try:
                k, v = line.split(u'=', 1)
            except:
                continue
            if shortcuts and v.startswith(u'video.devil.'):
                idx = v.find(u'|')
                if v[:idx] == u'video.devil.locale':
                    v = u'  ' + __language__(int(v[idx+1:])) + u'  '
                elif v[:idx] == u'video.devil.image':
                    v = os.path.join(imgDir, v[idx+1:])
                elif v[:idx] == u'video.devil.context':
                    v = u'context.' + __language__(int(v[idx+1:]))
            keys.append(k)
            values.append(v)
        f.close()
        keys.reverse()
        values.reverse()
        self.keys += keys
        self.values += values
        self.site = None
        self.rule_tmp = None
        self.info_tmp = None
        self.tmp = None
        return None

    def loadKey(self, txt):
        if self.keys[-1] == txt:
            del self.keys[-1]
            return True
        return False