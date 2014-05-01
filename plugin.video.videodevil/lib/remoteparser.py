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
            action = convAction[0:convAction.find(u'(')]
#            print('action = ' + action)
            param = convAction[len(action) + 1:-1]
#            print('param = ' + param)
            if param.find(u', ') != -1:
                params = param.split(u', ')
                if action == u'replace':
                    item[params[0]] = item[params[0]].replace(params[1], params[2])
                elif action == u'join':
                    j = []
                    for i in range(1, len(params)):
                        j.append(item[params[i]])
                    item[params[1]] = params[0].join(j)
                elif action == u'decrypt':
                    item[u'match'] = sesame.decrypt(item[params[0]], item[params[1]], 256)
            else:
                if action == u'unquote':
                    item[param] = urllib.unquote(item[param])
                elif action == u'quote':
                    item[param] = urllib.quote(item[param])
                elif action == u'decode':
                    item[param] = decode(item[param])
        else:
            action = convAction
            if action == u'append':
                item[u'url'] = url + item[u'url']
            elif action == u'appendparam':
                if url[-1] == u'?':
                    item[u'url'] = url + item[u'url']
                else:
                    item[u'url'] = url + u'&' + item[u'url']
            elif action == u'replaceparam':
                if url.rfind('?') == -1:
                    item[u'url'] = url + u'?' + item[u'url']
                else:
                    item[u'url'] = url[:url.rfind('?')] + u'?' + item[u'url']
            elif action == u'striptoslash':
                if url.rfind(u'/'):
                    idx = url.rfind(u'/')
                    if url[:idx + 1] == u'http://':
                        item[u'url'] = url + u'/' + item[u'url']
                    else:
                        item[u'url'] = url[:idx + 1] + item[u'url']
#            elif action == u'space':
#                try:
#                    item[u'title'] = u'  ' + item[u'title'].strip(u' ') + u'  '
#                except:
#                    pass
    return item

#
def getHTML(site, lItem):
    try:
        if len(site.txheaders) != 0:
            txheaders[site.txheaders[0]] = site.txheaders[1]
        req = Request(site.start, None, txheaders)
        try:
            handle = urlopen(req)
        except:
            print('Failed to open "%s," url is invalid' % site.start)
            if enable_debug:
                traceback.print_exc(file = sys.stdout)
            return
        data = handle.read()
    except IOError:
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
    print('site received')
    return site, lItem, data


def loadRemote(site, lItem, data):
    if enable_debug:
        f = open(os.path.join(cacheDir, site.cfg + u'.page.html'), 'w')
        f.write(u'<Title>'+ site.start + u'</Title>\n\n')
        f.write(data)
        f.close()
    print('parsing site')
    status = {}
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
    return None

# Helper functions for loadRemote

def itemBuilder(site, rule, lItem, url, match):
    infos_names = rule.order
    infos_values = match.groups()
    tmp = {}
    for idx, infos_name in enumerate(infos_names):
        tmp[infos_name] = clean_safe(infos_values[idx])
    for info in rule.info_list:
        info_value = u''
        if info.name in tmp:
            if info.build.find(u'%s') != -1:
                tmp[info.name] = info.build % tmp[info.name]
            continue
        if info.rule != u'':
            info_rule = info.rule
            if info.rule.find(u'%s') != -1:
                src = tmp[info.src]
                info_rule = info.rule % src
            infosearch = re.search(info_rule, data)
            if infosearch:
                info_value = infosearch.group(1).strip()
                if info.build.find(u'%s') != -1:
                    info_value = info.build % info_value
            elif info.default != '':
                info_value = info.default
        else:
            if info.build.find(u'%s') != -1:
                src = tmp[info.src]
                info_value = info.build % src
            else:
                info_value = info.build
        tmp[info.name] = info_value
    if len(rule.actions) > 0:
        tmp = parseActions(tmp, rule.actions, url)
    tmp[u'url'] = rule.url_build % tmp[u'url']
    tmp[u'type'] = rule.type
    if rule.skill.find(u'recursive') != -1:
        site.start = tmp[u'url']
        loadRemote(site, tmp)
        tmp = None
    else:
        if rule.type in site.items:
            for item in site.items[rule.type]:
                if tmp[u'url'] == item['url']:
                    tmp = None
                    return None
        keep = {}
        for info_name, info_value in tmp.iteritems():
            if info_name == u'title':
                if info_value != u'':
                    try:
                        info_value = info_value.replace(u'\r\n', u'').replace(u'\n', u'').replace(u'\t', u'')
                        info_value = info_value.lstrip(u' -!@#$%^&*_-+=.,)\'<>;:"[{]}\|/?`~')
                        info_value = info_value.rstrip(u' -@#$%^&*_-+=.,<>;(:\'"[{]}\|/?`~')
                        info_value = info_value.split(u' ')
                        title = []
                        for word in info_value:
                            if word:
                                word = word.lower().capitalize()
                            title.append(word)
                        info_value = u' '.join(title).replace(u'  ', u' ')
                        info_value = u' ' + info_value + u' '
                    except:
                        info_value = u' ... '
                else:
                    info_value = u' ... '
            elif info_name == u'duration':
                info_value = info_value.strip(u'')
                if info_value.find(u'(') == -1:
                    info_value = u' (%s)' % info_value
                if info_value[-3] == u':':
                    try:
                        info_value = info_value[:-2] + u'0' + info_value[-2:]
                    except AttributeError:
                        print(info_value)
            elif info_name == u'icon':
                if info_value == u'':
                    info_value = os.path.join(imgDir, u'video.png')
            elif info_name.rfind(u'.tmp') != -1:
                continue
            keep[info_name] = info_value
        if u'duration' in keep:
            keep[u'title'] = u''.join((keep[u'title'], keep[u'duration']))
        tmp = inheritInfos(keep, lItem)
        try:
            if rule.skill.find(u'space') != -1:
                tmp[u'title'] = u'  ' + tmp[u'title'] + u'  '
            elif rule.skill.find(u'bottom') != -1:
                tmp[u'title'] = tmp[u'title'].strip()
        except:
            pass
        if rule.type in site.items:
                site.items[rule.type] = (tmp, [tmp])
        else:
            tmp_infos = {u'type': rule.type}
            for info in rule.info_list:
                if info.name == 'title':
                    tmp_infos['title'] = info.build
                elif info.name == 'icon':
                    tmp_infos['icon'] = info.build
            tmp_infos = inheritInfos(tmp_infos, lItem)
            site.items[rule.type] = (tmp_infos, [tmp])
    return None

def currBuilder(site, rule, lItem, url, match):
    title = clean_safe(match.group(1).strip())
    tmp = {}
    if rule.skill.find(u'space') != -1:
        tmp[u'title'] = u'   ' + title + u' (' + __language__(30106) + u')   '
    else:
        tmp[u'title'] = u'  ' + title + u' (' + __language__(30106) + u')  '
    tmp[u'url'] = url
    tmp[u'type'] = rule.type
    for info in rule.info_list:
        if info.name == 'icon':
            tmp['icon'] = info.build
    tmp = inheritInfos(tmp, lItem)
    if rule.type in site.items:
        site.items[rule.type] = (tmp, [tmp])
    else:
        tmp_infos = {u'type': rule.type}
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
            site, lItem = self.queue.get()
            if isinstance(site, str) and site == 'quit':
                self.not_finished = False
                print('killing thread')
            else:
                self.out_queue.put(getHTML(site, lItem))
            self.queue.task_done()

class DatamineThread(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.not_finished = True

    def run(self):
        while self.not_finished:
            loadRemote(*self.out_queue.get())
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
        queue.put(('quit', 'quit'))

    for i in range(9):
        dt = DatamineThread(out_queue)
        dt.setDaemon(True)
        dt.start()


    #wait on the queue until everything has been processed
    queue.join()
    out_queue.join()
    print "Elapsed Time: %s" % (time.time() - start)
    cj.save(os.path.join(settingsDir, 'cookies.lwp'))
    return

