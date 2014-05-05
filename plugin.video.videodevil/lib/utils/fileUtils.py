# -*- coding: latin-1 -*-

import sys, traceback
import os.path

from lib.common import smart_unicode

addon = sys.modules["__main__"].addon
__language__ = sys.modules["__main__"].__language__
rootDir = sys.modules["__main__"].rootDir
settingsDir = sys.modules["__main__"].settingsDir
cacheDir = sys.modules["__main__"].cacheDir
allsitesDir = sys.modules["__main__"].allsitesDir
resDir = sys.modules["__main__"].resDir
imgDir = sys.modules["__main__"].imgDir
catDir = sys.modules["__main__"].catDir
log = sys.modules["__main__"].log

def clean_filename(s):
    if not s:
        return ''
    badchars = '\\/:*?\"<>|'
    for c in badchars:
        s = s.replace(c, '_')
    return s;

def getFileExtension(filename):
    ext_pos = filename.rfind('.')
    if ext_pos != -1:
        return filename[ext_pos+1:]
    return None

def saveList(directory, filename, Listname, items = None, List_dict = None, file_mode = 'w'):
    f = open(str(os.path.join(directory, filename)), file_mode)
    Listname = '#' + Listname.center(54) + '#\n'
    pound_signs = '########################################################\n'
    f.write(pound_signs)
    f.write(Listname)
    f.write(pound_signs)
    if List_dict != None:
        for info_name, info_value in List_dict.iteritems():
            f.write('site_' + info_name + '=' + info_value + '\n')
        f.write(pound_signs)
    if items != None:
        for item in items:
            try:
                f.write('link_title=' + item['title'] + '\n')
            except:
                f.write('link_title=...\n')
            for info_name, info_value in item.iteritems():
                if info_name != 'url' and info_name != 'title':
                    if info_name == 'mode':
                        f.write('link_mode=' + str(info_value) + '\n')
                    else:
                        f.write('link_' + info_name + '=' + info_value + '\n')
            f.write('link_url=' + item['url'] + '\n')
            f.write(pound_signs)
    f.close()
    return

def smart_read_file(filename, shortcuts = True):
    for directory in [catDir, resDir, cacheDir, allsitesDir, '']:
        try:
            filepath = os.path.join(directory, filename)
            print(os.path.join('', filename))
            f = open(filepath, 'r')
            break
        except:
            if directory == '':
                traceback.print_exc(file = sys.stdout)
                log('File Not Found: "%s"' % filename)
                return None, None
    log('File Opened: "%s"' % filepath)
    key = []
    value = []
    for line in f:
        if line and line.startswith('#'):
            continue
        try:
            line = line.replace('\r\n', '').replace('\n', '')
        except:
            continue
        try:
            k, v = line.split('=', 1)
        except:
            continue
        if shortcuts and v.startswith('video.devil.'):
            idx = v.find('|')
            if v[:idx] == 'video.devil.locale':
                v = '  ' + __language__(int(v[idx+1:])) + '  '
            elif v[:idx] == 'video.devil.image':
                v = os.path.join(imgDir, v[idx+1:])
            elif v[:idx] == 'video.devil.context':
                v = 'context.' + __language__(int(v[idx+1:]))
        key.append(k)
        value.append(v)
    key.reverse()
    value.reverse()
    f.close()
    log('File Closed: "%s"' % filepath)
    return key, value
