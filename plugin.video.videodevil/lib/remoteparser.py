# -*- coding: latin-1 -*-
from string import capitalize, lower
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
txheaders = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.8.1.18) Gecko/20081029 Firefox/2.0.0.18',
    'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
}

if cj != None:
    if os.path.isfile(xbmc.translatePath(os.path.join(settingsDir, 'cookies.lwp'))):
        cj.load(xbmc.translatePath(os.path.join(settingsDir, 'cookies.lwp')))
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
else:
    opener = urllib2.build_opener()
    urllib2.install_opener(opener)

queue = Queue.Queue()
out_queue = Queue.Queue()

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

#
def getHTML(site, lItem):
    if len(site.txheaders) != 0:
        txheaders[site.txheaders[0]] = site.txheaders[1]
    req = Request(site.start, None, txheaders)
    try:
        handle = urlopen(req)
    except:
        print('Failed to open "%s", url is invalid' % site.start)
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
        return 'Skipping due to failure'
    data = handle.read()
#    print('site received')
    return site, lItem, data


def loadRemote(site, lItem, data):
    if enable_debug:
        f = open(os.path.join(cacheDir, site.cfg + '.page.html'), 'w')
        f.write('<Title>'+ site.start + '</Title>\n\n')
        f.write(data)
        f.close()
#    print('parsing site')
#    loadRemoteFor(site, lItem, data)
    loadRemoteWhile(site, lItem, data)
    return None

# Helper functions for loadRemote
def loadRemoteFor(site, lItem, data):
    for item_rule in site.rules:
        item_rule.infosRE = re.compile(item_rule.infos, re.IGNORECASE + re.DOTALL + re.MULTILINE)
        for infos_values in item_rule.infosRE.findall(data):
            itemBuilder(site, item_rule, lItem, site.start, infos_values = infos_values)
        if item_rule.curr:
            item_rule.currRE = re.compile(item_rule.curr, re.IGNORECASE + re.DOTALL + re.MULTILINE)
            for infos_value in item_rule.currRE.findall(data):
                currBuilder(site, item_rule, lItem, site.start, infos_value = infos_value)
    return None

def loadRemoteWhile(site, lItem, data):
#    init_loop_time = time.time()
    # Create variables for the while loop
    interests = []
    interests2 = []
    interesting_items = []
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
    for item_rule in site.rules:
        match = interestingRE.match(item_rule.infos)
        if match:
            item_rule.infos = item_rule.infos[match.end():]
        item_rule.infosRE = re.compile(item_rule.infos, re.IGNORECASE + re.DOTALL + re.MULTILINE)
        if item_rule.curr:
            item_rule.currRE = re.compile(item_rule.curr, re.IGNORECASE + re.DOTALL + re.MULTILINE)
#    print "Init loop took: %s" % (time.time() - init_loop_time)
    loop_time = time.time()
    # Find links
    while point < length:
        interest = interestingRE.search(data, point)
        if interest:
            point = interest.start()
            intersting_point = interest.start()
            jump = len(interest.group(0))
            for index, rule_name in enumerate(interests):
                item_rule = site.rules[index]
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
#    print "loop took: %s" % (time.time() - loop_time)
    elapsed_loop_time = time.time() - loop_time
    if float(elapsed_loop_time) > 0.1:
        print('loop took too long: %s' % site.cfg)
    return None

def itemBuilder(site, rule, lItem, url, match = None, infos_values = None):
    infos_names = rule.order
    if infos_values == None:
        infos_values = match.groups()
    tmp = {}
    for idx, infos_name in enumerate(infos_names):
        tmp[infos_name] = infos_values[idx]
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
    if rule.skill.find('recursive') != -1:
        site.start = tmp['url']
        loadRemote(site, tmp)
        tmp = None
    else:
#        try:
        tmp['title'] = tmp['title'].strip()
        if rule.skill.find('space') != -1:
            tmp['title'] = '   ' + tmp['title'] + '   '
        elif rule.skill.find('bottom') == -1:
            tmp['title'] = ' ' + tmp['title'] + ' '
#        except:
#            pass
        if rule.type in site.items:
            for item in site.items[rule.type]:
                if tmp['url'] == item['url']:
                    tmp = None
                    return None
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
    return None

def currBuilder(site, rule, lItem, url, match = None, infos_value = None):
    if infos_value == None:
        title = match.group(1).strip()
    else:
        title = infos_value
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
    tmp = inheritInfos(tmp, lItem)
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
    return None

class ThreadUrl(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, queue, out_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue
        self.not_finished = True

    def run(self):
        while self.not_finished:
            args = self.queue.get()
            if isinstance(args, str) and args == 'quit':
                self.not_finished = False
#                print('killing thread')
            else:
                results = getHTML(*args)
                if isinstance(results, str) and results == 'Skipping due to failure':
                    print('Skipping due to failure')
                else:
                    self.out_queue.put(results)
            self.queue.task_done()

class DatamineThread(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.not_finished = True

    def run(self):
        while self.not_finished:
            args = self.out_queue.get()
            if isinstance(args, str) and args == 'quit':
                self.not_finished = False
#                print('killing thread')
            else:
                loadRemote(*args)
            self.out_queue.task_done()


def main(tasks):
    start = time.time()
    #spawn a pool of threads, and pass them queue instance
    for i in range(len(tasks)):
        t = ThreadUrl(queue, out_queue)
        t.setDaemon(True)
        t.start()

    #populate queue with data
    for task in tasks:
        queue.put(task)

    #ThreadUrl killer
    for task in tasks:
        queue.put('quit')
    dt_count = 1
    for i in range(dt_count):
        dt = DatamineThread(out_queue)
        dt.setDaemon(True)
        dt.start()


    #wait on the queue until everything has been processed
    queue.join()

    #DatamineThread killer
    for i in range(dt_count):
        out_queue.put('quit')

    out_queue.join()
    print "Elapsed Time: %s" % (time.time() - start)
    cj.save(os.path.join(settingsDir, 'cookies.lwp'))
    return

