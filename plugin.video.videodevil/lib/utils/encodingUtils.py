# -*- coding: latin-1 -*-

import sys, traceback
import re
import urllib, htmlentitydefs

from lib.common import smart_unicode

enable_debug = sys.modules["__main__"].enable_debug

def decode(s):
    if not s:
        return ''
    def sub(m):
        if htmlentitydefs.name2codepoint.has_key(m.group(1)):
            return unichr(htmlentitydefs.name2codepoint[m.group(1)])
        else:
            return ''
    return re.sub(r'&([^;]+);', sub, s)

def clean_safe(s):
    if not s:
        return ''
    try:
        o = smart_unicode(s)
        # remove &#XXX;
        o = re.sub(r'&#(\d+);', lambda m: unichr(int(m.group(1))), o)
        # remove &XXX;
        o = decode(o)
        # remove \uXXX
        o = re.sub(r'\\u(....)', lambda m: unichr(int(m.group(1), 16)), o)
    except:
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
        o = s
    return o

def unquote(s): # unquote
    if not s:
        return ''
    return urllib.unquote(s)

def quote(s): # quote
    if not s:
        return ''
    return urllib.quote(s)
