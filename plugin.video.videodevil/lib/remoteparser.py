# -*- coding: latin-1 -*-
#from string import capitalize, lower
import sys, os.path
import os, traceback
import re
import urllib, urllib2
import cookielib
import time
import threading
import Queue

import xbmc

from lib.common import inheritInfos, smart_unicode

from lib.utils.encodingUtils import clean_safe
from lib.utils.xbmcUtils import addListItem, addListItems

import sesame

mode = sys.modules["__main__"].mode
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

def fetchHTML(site, lItem):
    req = Request(site.start, None, site.txheaders)
    start = time.clock()
    try:
        handle = urlopen(req)
    except:
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
        return 'Skipping due to failure'
    start = time.clock()
    data = handle.read()
    return site, lItem, data


def loadRemote(site, lItem, data):
    if enable_debug:
        f = open(os.path.join(cacheDir, site.cfg + '.page.html'), 'w')
        f.write('<Title>'+ site.start + '</Title>\n\n')
        f.write(data)
        f.close()
    return loadRemoteFor(site, lItem, data)
#    return loadRemoteWhile(site, lItem, data)

# Helper functions for loadRemote
def loadRemoteFor(site, lItem, data):
    lock, items = [], []
    for item_rule in site.rules:
        rule_items, tmp_rule_items = [], []
        if item_rule.type in lock:
            continue
        elif item_rule.skill.find('recursive') != -1:  #Need to fix this
            site.start = tmp['url']
            loadRemote(site, lItem, fetchHTML(site, lItem)[2])
            tmp = None
        else:
            item_rule.infosRE = re.compile(item_rule.infos, re.IGNORECASE + re.DOTALL + re.MULTILINE)
            reInfos = item_rule.infosRE.findall(data)
            if len(reInfos) >= 1:
                lock.append(item_rule.type)
                tmp_rule_items = [dict(zip(item_rule.order, infos_values)) for infos_values in reInfos]
                infos = list(item_rule.order)
                for info in item_rule.info_list:
                    info_value = ''
                    if info.name in infos:
                        if info.build.find('%s') != -1:
                            for tmp in tmp_rule_items:
                                tmp[info.name] = info.build % tmp[info.name]
                        continue
                    if info.rule != '':
                        info_rule = info.rule
                        if info.rule.find('%s') != -1:
                            src = tmp[info.src]
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
                            src = tmp[info.src]
                            info_value = info.build % src
                        else:
                            info_value = info.build
                    for tmp in tmp_rule_items:
                        tmp[info.name] = info_value
                if len(item_rule.actions) > 0:
                    for tmp in tmp_rule_items:
                        tmp = parseActions(tmp, item_rule.actions, site.start)
                for tmp in tmp_rule_items:
                    tmp['url'] = item_rule.url_build % tmp['url']
                    tmp['type'] = item_rule.type
                for i, tmp in enumerate(tmp_rule_items):
                    for item in tmp_rule_items[i + 1:]:
                        if tmp['url'] == item['url']:
                            break
                    else:
                        rule_items.append(tmp)
                infoFormatter(rule_items, item_rule.order + [info.name for info in item_rule.info_list])
                if item_rule.skill.find('space') != -1:
                    for item in rule_items:
                        item['title'] = '   ' + item['title'] + '   '
                elif item_rule.skill.find('bottom') == -1:
                    for item in rule_items:
                        item['title'] = ' ' + item['title'] + ' '
            if item_rule.curr:
                item_rule.currRE = re.compile(item_rule.curr, re.IGNORECASE + re.DOTALL + re.MULTILINE)
                reCurr = item_rule.currRE.findall(data)
                if len(reCurr) >= 1:
                    lock.append(item_rule.type)
                for infos_value in reCurr:
                    tmp = currBuilder(site, item_rule, lItem, site.start, infos_value = infos_value)
                    for item in rule_items:
                        if tmp['url'] == item['url']:
                            break
                    else:
                        rule_items.append(tmp)
            if item_rule.type == 'video':
                addListItems([inheritInfos(item, lItem) for item in rule_items])
            else:
                items.extend([inheritInfos(item, lItem) for item in rule_items])
    return items

def createInterestingLists(site):
    # Create variables for the while loop
    interests = []
    interests2 = []
    interesting_items = []
    # Append interests lists and modify rule RE patterns
    interestRE = re.compile(r'[-a-zA-Z0-9/,:;%!&$_#=~@<> ]+', re.IGNORECASE + re.DOTALL + re.MULTILINE)
    rules_tmp = []
    for item_rule in site.rules:
        match = interestRE.match(item_rule.infos)
        if match:
            interests.append(match.group(0))
        else:
            print(item_rule.infos)
            print('RE pattern in "%s" starts with a special character.\n RE pattern = "%s"' % (site.cfg, item_rule.infos))
        if item_rule.curr:
            match = interestRE.match(item_rule.curr)
            if match:
                interests2.append(match.group(0))
            else:
                print('RE pattern in "%s" starts with a special character.\n RE pattern = "%s"' % (site.cfg, item_rule.curr))
    # Combine interests list
    interests2.extend(interests)
    # Remove longer matches that may cause the while loop to shorter matches
    # i.e. remove '<img src' if '<img' is in the list
#        print('interests2 = ' + str(interests2))
    list1 = set(interests2)
    list2 = set(interests2)
    while len(list1) > 0:
        x = list1.pop()
        for y in list1:
            if x.startswith(y):
                if y not in interesting_items:
                    interesting_items.append(y)
            elif y.startswith(x):
                interesting_items.append(x)
                break
    for x in list2:
        if x not in interesting_items:
            for z in interesting_items:
                if x.startswith(z):
                    break
            else:
                interesting_items.append(x)
    # Create interestingRE from interesting_items list
    interesting_pattern = '(' + '|'.join(interesting_items) + ')'
    interestingRE = re.compile(interesting_pattern, re.IGNORECASE + re.DOTALL + re.MULTILINE)
    # Create REs for while loop
    for item_rule in rules_tmp:
        match = interestingRE.match(item_rule.infos)
        if match:
            item_rule.infos = item_rule.infos[match.end():]
        item_rule.infosRE = re.compile(item_rule.infos, re.IGNORECASE + re.DOTALL + re.MULTILINE)
        if item_rule.curr:
            item_rule.currRE = re.compile(item_rule.curr, re.IGNORECASE + re.DOTALL + re.MULTILINE)
    print "Init loop took: %s" % (time.clock() - init_loop_time)
    return interests, interestingRE

def loadRemoteWhile(site, lItem, data):
    interests, interestingRE = createInterestingLists(site)
    point = 0
    length = len(data)
    # Find links
    while point < length:
        interest = interestingRE.search(data, point)
        if interest:
            point = interest.start()
            intersting_point = interest.start()
            jump = len(interest.group(0))
            for index, rule_name in enumerate(interests):
                item_rule = rules_tmp[index]
                if rule_name.startswith(interest.group(0)):
                    match = item_rule.infosRE.match(data, point + jump)
                    if match:
                        while match:
                            if not match.group(0):
                                break
                            point += jump + len(match.group(0))
                            itemBuilder(site, item_rule, lItem, site.start, match)
                            match = item_rule.infosRE.match(data, point + jump)
                        break
                if point == intersting_point and item_rule.curr and item_rule.curr.startswith(interest.group(0)):
                    match = item_rule.currRE.match(data, point)
                    if match:
                        while match:
                            if not match.group(0):
                                break
                            point += len(match.group(0))
                            currBuilder(site, item_rule, lItem, site.start, match)
                            match = item_rule.currRE.match(data, point)
                        break
            if point == intersting_point:
                point += 1
        else:
            break
    return None

def itemBuilder(site, rule, lItem, url, match = None, infos_values = None):
    infos_names = rule.order
    if infos_values == None:
        infos_values = match.groups()
    tmp = dict(zip(infos_names, infos_values))
    for info in rule.info_list:
        info_value = ''
        if info.name in tmp:
            if info.build.find('%s') != -1:
                tmp[info.name] = info.build % tmp[info.name]
            continue
        if info.rule != '':
            info_rule = info.rule
            if info.rule.find('%s') != -1:
                src = tmp[info.src]
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
                src = tmp[info.src]
                info_value = info.build % src
            else:
                info_value = info.build
        tmp[info.name] = info_value
    if len(rule.actions) > 0:
        tmp = parseActions(tmp, rule.actions, url)
    tmp['url'] = rule.url_build % tmp['url']
    tmp['type'] = rule.type
    if rule.skill.find('recursive') != -1:  #Need to fix this
        site.start = tmp['url']
        loadRemote(site, lItem, fetchHTML(site, lItem)[2])
        tmp = None
    return tmp

def currBuilder(site, rule, lItem, url, match = None, infos_value = None):
    if infos_value == None:
        title = match.group(1).strip()
    else:
        title = infos_value.strip()
    tmp = {}
    if rule.skill.find('space') != -1:
        tmp['title'] = '   ' + title + ' (' + __language__(30106) + ')   '
    else:
        tmp['title'] = '  ' + title + ' (' + __language__(30106) + ')  '
    tmp['url'] = url
    tmp['type'] = rule.type
    for info in rule.info_list:
        if info.name == 'icon':
            tmp['icon'] = info.build
    return tmp


def infoFormatter(items, infos):
    if 'title' in infos:
        for item in items:
            try:
                if item['title'] != '':
                    item['title'] = item['title'].replace('\r\n', '').replace('\n', '').replace('\t', '')
                    item['title'] = item['title'].lstrip(' -@#$%^&*_-+=.,\';:"\|/?`~>)]}!')
                    item['title'] = item['title'].rstrip(' -@#$%^&*_-+=.,;:\'"\|/?`~<([{')
                    item['title'] = item['title'].title()
                else:
                    item['title'] = ' ... '
            except UnicodeDecodeError:
                item['title'] = smart_unicode(item['title'])
                item['title'] = item['title'].replace(u'\r\n', u'').replace(u'\n', u'').replace(u'\t', u'')
                item['title'] = item['title'].lstrip(u' -@#$%^&*_-+=.,\';:"\|/?`~>)]}!')
                item['title'] = item['title'].rstrip(u' -@#$%^&*_-+=.,;:\'"\|/?`~<([{')
                item['title'] = item['title'].title()
    if 'duration' in infos:
        for item in items:
            item['duration'] = item['duration'].strip(' ()')
            if item['duration'][-2] == ':':
    #            try:
                item['duration'] = item['duration'][:-2] + '0' + item['duration'][-2:]
    #            except AttributeError:
    #                print(item['duration'])
            item['title'] = item['title'] + ' (' +  item['duration'] + ')'
    if 'icon' in infos:
        for item in items:
            if item['icon'] == '':
                item['icon'] = os.path.join(imgDir, 'video.png')
    for info in infos:
        if info.endswith('.tmp'):
            for item in items:
                del item[info]
    return items

class ThreadUrl(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, fetch_queue, parse_queue, continuous = False):
        threading.Thread.__init__(self)
        self.fetch_queue = fetch_queue
        self.parse_queue = parse_queue
        self.continuous = continuous

    def run(self):
        args = self.fetch_queue.get()
        site, lItem = args
        start = time.clock()
        results = fetchHTML(site, lItem)
        print '%s took: %s to fetch' % (site.cfg, (time.clock() - start))
        self.parse_queue.put(results)
        self.fetch_queue.task_done()
        while self.continuous:
            args = self.fetch_queue.get()
            if isinstance(args, str) and args == 'quit':
                self.continuous = False
            else:
                site, lItem = args
                start = time.clock()
                results = fetchHTML(site, lItem)
                print '%s took: %s to fetch' % (site.cfg, (time.clock() - start))
                if isinstance(results, str) and results == 'Skipping due to failure':
                    print('Skipping due to failure')
                else:
                    self.parse_queue.put(results)
            self.fetch_queue.task_done()

class DatamineThread(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, parse_queue, items, continuous = True):
        threading.Thread.__init__(self)
        self.parse_queue = parse_queue
        self.continuous = continuous
        self.items = items

    def run(self):
        args = self.parse_queue.get()
        site, lItem, data = args
        self.items.extend(loadRemote(site, lItem, data))
        self.parse_queue.task_done()
        while self.continuous:
            args = self.parse_queue.get()
            if isinstance(args, str) and args == 'quit':
                self.continuous = False
            else:
                site, lItem, data = args
                self.items.extend(loadRemote(site, lItem, data))
            self.parse_queue.task_done()

class remoteParser:
    def __init__(self):
        self.fetch_queue = None
        self.parse_queue = None
        self.fetch_threads = []
        self.parse_threads = []
        self.task_count = 0
        self.items = []

    def start_fetch_threads(self):
        for fetch_thread in self.fetch_threads:
            fetch_thread.start()

    def start_parse_threads(self):
        for parse_thread in self.parse_threads:
            parse_thread.start()

    def kill_fetch_threads(self):
        for fetch_thread in self.fetch_threads:
            self.fetch_queue.put('quit')

    def kill_parse_threads(self):
        for parse_thread in self.parse_threads:
            self.parse_queue.put('quit')

    def populate_fetch_queue(self, tasks):
        for task in tasks:
            self.fetch_queue.put(task)

    def populate_parse_queue(self, tasks):
        for task in tasks:
            self.parse_queue.put(task)

    def wait_for_fetch_queue(self):
        self.fetch_queue.join()

    def wait_for_parse_queue(self):
        self.parse_queue.join()

    def spawn_fetch_threads(self, count): #by default thread does not loop continuously set 3rd arg to True loop continuously
        for i in range(count):
            fetch_thread = ThreadUrl(self.fetch_queue, self.parse_queue)
            fetch_thread.setDaemon(True)
            self.fetch_threads.append(fetch_thread)

    def spawn_parse_threads(self, count): #by default thread loops continuously set 3rd arg to False to only process one queue item
        for i in range(count):
            parse_thread = DatamineThread(self.parse_queue, self.items)
            parse_thread.setDaemon(True)
            self.parse_threads.append(parse_thread)

    def remoteDataMiner(self):
        for i in range(self.task_count):
            args = self.parse_queue.get()
            site, lItem, data = args
            self.items.extend(loadRemote(site, lItem, data))
            self.parse_queue.task_done()

    def main(self, tasks):
        self.task_count += len(tasks)
        start = time.clock()
        if len(tasks) > 1:
            self.fetch_queue = Queue.Queue()
            self.parse_queue = Queue.Queue()
            self.spawn_fetch_threads(len(tasks))
            self.start_fetch_threads()
            self.populate_fetch_queue(tasks)
#            self.kill_fetch_threads()
#            self.spawn_parse_threads(1)
#            self.start_parse_threads()
            self.remoteDataMiner()
            self.wait_for_fetch_queue()
#            self.kill_parse_threads()
#            self.wait_for_parse_queue()
        elif len(tasks) == 1:
            self.items = loadRemote(*fetchHTML(*tasks[0]))
        print "Elapsed Time: %s" % (time.clock() - start)
        cj.save(os.path.join(settingsDir, 'cookies.lwp'))
        return self.items

