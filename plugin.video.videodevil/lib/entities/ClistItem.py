# -*- coding: latin-1 -*-

class ClistItems:
    def __init__(self):
        self.keys = []
        self.values = []

    def __getitem__(self, key):
        return self.values[self.keys.index(key)]

    def __setitem__(self, key, value):
        if key in self.keys:
            self.values[self.keys.index(key)] = value
        else:
            self.keys.append(key)
            self.values.append(value)

    def __contains__(self, key):
        if key in self.keys:
            return True
        else:
            return False

    def __str__(self):
        if 'title' in self.keys:
            txt = 'link_title=%s\n' % self.values[self.keys.index('title')]
        txt += '\n'.join(['='.join(['link_%s' % k,v]) for k,v in self.zipped() if k != 'title' if k != 'url'])
        txt += '\nlink_url=%s' % self.values[self.keys.index('url')]
        return txt

    def zipped(self):
        return zip(self.keys, self.values)