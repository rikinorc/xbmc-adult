# -*- coding: latin-1 -*-
from string import capitalize, lower
import sys, os.path
import tempfile
import urllib, urllib2
import re
import os, traceback
import cookielib, htmlentitydefs
import threading
import Queue

import xbmcplugin, xbmcaddon
import xbmc, xbmcgui

import sesame

addon = xbmcaddon.Addon(id='plugin.video.videodevil')
__language__ = addon.getLocalizedString
rootDir = addon.getAddonInfo('path')
if rootDir[-1] == u';':
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

if addon.getSetting('enable_debug') == u'true':
    enable_debug = True
    xbmc.log('VideoDevil debug logging enabled')
else:
    enable_debug = False

entitydefs = {
    'AElig':    u'\u00C6', # latin capital letter AE = latin capital ligature AE, U+00C6 ISOlat1'
    'Aacute':   u'\u00C1', # latin capital letter A with acute, U+00C1 ISOlat1'
    'Acirc':    u'\u00C2', # latin capital letter A with circumflex, U+00C2 ISOlat1'
    'Agrave':   u'\u00C0', # latin capital letter A with grave = latin capital letter A grave, U+00C0 ISOlat1'
    'Alpha':    u'\u0391', # greek capital letter alpha, U+0391'
    'Aring':    u'\u00C5', # latin capital letter A with ring above = latin capital letter A ring, U+00C5 ISOlat1'
    'Atilde':   u'\u00C3', # latin capital letter A with tilde, U+00C3 ISOlat1'
    'Auml':     u'\u00C4', # latin capital letter A with diaeresis, U+00C4 ISOlat1'
    'Beta':     u'\u0392', # greek capital letter beta, U+0392'
    'Ccedil':   u'\u00C7', # latin capital letter C with cedilla, U+00C7 ISOlat1'
    'Chi':      u'\u03A7', # greek capital letter chi, U+03A7'
    'Dagger':   u'\u2021', # double dagger, U+2021 ISOpub'
    'Delta':    u'\u0394', # greek capital letter delta, U+0394 ISOgrk3'
    'ETH':      u'\u00D0', # latin capital letter ETH, U+00D0 ISOlat1'
    'Eacute':   u'\u00C9', # latin capital letter E with acute, U+00C9 ISOlat1'
    'Ecirc':    u'\u00CA', # latin capital letter E with circumflex, U+00CA ISOlat1'
    'Egrave':   u'\u00C8', # latin capital letter E with grave, U+00C8 ISOlat1'
    'Epsilon':  u'\u0395', # grek capital letter epsilon, U+0395'
    'Eta':      u'\u0397', # greek capital letter eta, U+0397'
    'Euml':     u'\u00CB', # latin capital letter E with diaeresis, U+00CB ISOlat1'
    'Gamma':    u'\u0393', # greek capital letter gamma, U+0393 ISOgrk3'
    'Iacute':   u'\u00CD', # latin capital letter I with acute, U+00CD ISOlat1'
    'Icirc':    u'\u00CE', # latin capital letter I with circumflex, U+00CE ISOlat1'
    'Igrave':   u'\u00CC', # latin capital letter I with grave, U+00CC ISOlat1'
    'Iota':     u'\u0399', # greek capital letter iota, U+0399'
    'Iuml':     u'\u00CF', # latin capital letter I with diaeresis, U+00CF ISOlat1'
    'Kappa':    u'\u039A', # greek capital letter kappa, U+039A'
    'Lambda':   u'\u039B', # greek capital letter lambda, U+039B ISOgrk3'
    'Mu':       u'\u039C', # greek capital letter mu, U+039C'
    'Ntilde':   u'\u00D1', # latin capital letter N with tilde, U+00D1 ISOlat1'
    'Nu':       u'\u039D', # greek capital letter nu, U+039D'
    'OElig':    u'\u0152', # latin capital ligature OE, U+0152 ISOlat2'
    'Oacute':   u'\u00D3', # latin capital letter O with acute, U+00D3 ISOlat1'
    'Ocirc':    u'\u00D4', # latin capital letter O with circumflex, U+00D4 ISOlat1'
    'Ograve':   u'\u00D2', # latin capital letter O with grave, U+00D2 ISOlat1'
    'Omega':    u'\u03A9', # greek capital letter omega, U+03A9 ISOgrk3'
    'Omicron':  u'\u039F', # greek capital letter omicron, U+039F'
    'Oslash':   u'\u00D8', # latin capital letter O with stroke = latin capital letter O slash, U+00D8 ISOlat1'
    'Otilde':   u'\u00D5', # latin capital letter O with tilde, U+00D5 ISOlat1'
    'Ouml':     u'\u00D6', # latin capital letter O with diaeresis, U+00D6 ISOlat1'
    'Phi':      u'\u03A6', # greek capital letter phi, U+03A6 ISOgrk3'
    'Pi':       u'\u03A0', # greek capital letter pi, U+03A0 ISOgrk3'
    'Prime':    u'\u2033', # double prime = seconds = inches, U+2033 ISOtech'
    'Psi':      u'\u03A8', # greek capital letter psi, U+03A8 ISOgrk3'
    'Rho':      u'\u03A1', # greek capital letter rho, U+03A1'
    'Scaron':   u'\u0160', # latin capital letter S with caron, U+0160 ISOlat2'
    'Sigma':    u'\u03A3', # greek capital letter sigma, U+03A3 ISOgrk3'
    'THORN':    u'\u00DE', # latin capital letter THORN, U+00DE ISOlat1'
    'Tau':      u'\u03A4', # greek capital letter tau, U+03A4'
    'Theta':    u'\u0398', # greek capital letter theta, U+0398 ISOgrk3'
    'Uacute':   u'\u00DA', # latin capital letter U with acute, U+00DA ISOlat1'
    'Ucirc':    u'\u00DB', # latin capital letter U with circumflex, U+00DB ISOlat1'
    'Ugrave':   u'\u00D9', # latin capital letter U with grave, U+00D9 ISOlat1'
    'Upsilon':  u'\u03A5', # greek capital letter upsilon, U+03A5 ISOgrk3'
    'Uuml':     u'\u00DC', # latin capital letter U with diaeresis, U+00DC ISOlat1'
    'Xi':       u'\u039E', # greek capital letter xi, U+039E ISOgrk3'
    'Yacute':   u'\u00DD', # latin capital letter Y with acute, U+00DD ISOlat1'
    'Yuml':     u'\u0178', # latin capital letter Y with diaeresis, U+0178 ISOlat2'
    'Zeta':     u'\u0396', # greek capital letter zeta, U+0396'
    'aacute':   u'\u00E1', # latin small letter a with acute, U+00E1 ISOlat1'
    'acirc':    u'\u00E2', # latin small letter a with circumflex, U+00E2 ISOlat1'
    'acute':    u'\u00B4', # acute accent = spacing acute, U+00B4 ISOdia'
    'aelig':    u'\u00E6', # latin small letter ae = latin small ligature ae, U+00E6 ISOlat1'
    'agrave':   u'\u00E0', # latin small letter a with grave = latin small letter a grave, U+00E0 ISOlat1'
    'alefsym':  u'\u2135', # alef symbol = first transfinite cardinal, U+2135 NEW'
    'alpha':    u'\u03B1', # greek small letter alpha, U+03B1 ISOgrk3'
    'amp':      u'\u0026', # ampersand, U+0026 ISOnum'
    'and':      u'\u2227', # logical and = wedge, U+2227 ISOtech'
    'ang':      u'\u2220', # angle, U+2220 ISOamso'
    'aring':    u'\u00E5', # latin small letter a with ring above = latin small letter a ring, U+00E5 ISOlat1'
    'asymp':    u'\u2248', # almost equal to = asymptotic to, U+2248 ISOamsr'
    'atilde':   u'\u00E3', # latin small letter a with tilde, U+00E3 ISOlat1'
    'auml':     u'\u00E4', # latin small letter a with diaeresis, U+00E4 ISOlat1'
    'bdquo':    u'\u201E', # double low-9 quotation mark, U+201E NEW'
    'beta':     u'\u03B2', # greek small letter beta, U+03B2 ISOgrk3'
    'brvbar':   u'\u00A6', # broken bar = broken vertical bar, U+00A6 ISOnum'
    'bull':     u'\u2022', # bullet = black small circle, U+2022 ISOpub'
    'cap':      u'\u2229', # intersection = cap, U+2229 ISOtech'
    'ccedil':   u'\u00E7', # latin small letter c with cedilla, U+00E7 ISOlat1'
    'cedil':    u'\u00B8', # cedilla = spacing cedilla, U+00B8 ISOdia'
    'cent':     u'\u00A2', # cent sign, U+00A2 ISOnum'
    'chi':      u'\u03C7', # greek small letter chi, U+03C7 ISOgrk3'
    'circ':     u'\u02C6', # modifier letter circumflex accent, U+02C6 ISOpub'
    'clubs':    u'\u2663', # black club suit = shamrock, U+2663 ISOpub'
    'cong':     u'\u2245', # approximately equal to, U+2245 ISOtech'
    'copy':     u'\u00A9', # copyright sign, U+00A9 ISOnum'
    'crarr':    u'\u21B5', # downwards arrow with corner leftwards = carriage return, U+21B5 NEW'
    'cup':      u'\u222A', # union = cup, U+222A ISOtech'
    'curren':   u'\u00A4', # currency sign, U+00A4 ISOnum'
    'dArr':     u'\u21D3', # downwards double arrow, U+21D3 ISOamsa'
    'dagger':   u'\u2020', # dagger, U+2020 ISOpub'
    'darr':     u'\u2193', # downwards arrow, U+2193 ISOnum'
    'deg':      u'\u00B0', # degree sign, U+00B0 ISOnum'
    'delta':    u'\u03B4', # greek small letter delta, U+03B4 ISOgrk3'
    'diams':    u'\u2666', # black diamond suit, U+2666 ISOpub'
    'divide':   u'\u00F7', # division sign, U+00F7 ISOnum'
    'eacute':   u'\u00E9', # latin small letter e with acute, U+00E9 ISOlat1'
    'ecirc':    u'\u00EA', # latin small letter e with circumflex, U+00EA ISOlat1'
    'egrave':   u'\u00E8', # latin small letter e with grave, U+00E8 ISOlat1'
    'empty':    u'\u2205', # empty set = null set = diameter, U+2205 ISOamso'
    'emsp':     u'\u2003', # em space, U+2003 ISOpub'
    'ensp':     u'\u2002', # en space, U+2002 ISOpub'
    'epsilon':  u'\u03B5', # greek small letter epsilon, U+03B5 ISOgrk3'
    'equiv':    u'\u2261', # identical to, U+2261 ISOtech'
    'eta':      u'\u03B7', # greek small letter eta, U+03B7 ISOgrk3'
    'eth':      u'\u00F0', # latin small letter eth, U+00F0 ISOlat1'
    'euml':     u'\u00EB', # latin small letter e with diaeresis, U+00EB ISOlat1'
    'euro':     u'\u20AC', # euro sign, U+20AC NEW'
    'exist':    u'\u2203', # there exists, U+2203 ISOtech'
    'fnof':     u'\u0192', # latin small f with hook = function = florin, U+0192 ISOtech'
    'forall':   u'\u2200', # for all, U+2200 ISOtech'
    'frac12':   u'\u00BD', # vulgar fraction one half = fraction one half, U+00BD ISOnum'
    'frac14':   u'\u00BC', # vulgar fraction one quarter = fraction one quarter, U+00BC ISOnum'
    'frac34':   u'\u00BE', # vulgar fraction three quarters = fraction three quarters, U+00BE ISOnum'
    'frasl':    u'\u2044', # fraction slash, U+2044 NEW'
    'gamma':    u'\u03B3', # greek small letter gamma, U+03B3 ISOgrk3'
    'ge':       u'\u2265', # greater-than or equal to, U+2265 ISOtech'
    'gt':       u'\u003E', # greater-than sign, U+003E ISOnum'
    'hArr':     u'\u21D4', # left right double arrow, U+21D4 ISOamsa'
    'harr':     u'\u2194', # left right arrow, U+2194 ISOamsa'
    'hearts':   u'\u2665', # black heart suit = valentine, U+2665 ISOpub'
    'hellip':   u'\u2026', # horizontal ellipsis = three dot leader, U+2026 ISOpub'
    'iacute':   u'\u00ED', # latin small letter i with acute, U+00ED ISOlat1'
    'icirc':    u'\u00EE', # latin small letter i with circumflex, U+00EE ISOlat1'
    'iexcl':    u'\u00A1', # inverted exclamation mark, U+00A1 ISOnum'
    'igrave':   u'\u00EC', # latin small letter i with grave, U+00EC ISOlat1'
    'image':    u'\u2111', # blackletter capital I = imaginary part, U+2111 ISOamso'
    'infin':    u'\u221E', # infinity, U+221E ISOtech'
    'int':      u'\u222B', # integral, U+222B ISOtech'
    'iota':     u'\u03B9', # greek small letter iota, U+03B9 ISOgrk3'
    'iquest':   u'\u00BF', # inverted question mark = turned question mark, U+00BF ISOnum'
    'isin':     u'\u2208', # element of, U+2208 ISOtech'
    'iuml':     u'\u00EF', # latin small letter i with diaeresis, U+00EF ISOlat1'
    'kappa':    u'\u03BA', # greek small letter kappa, U+03BA ISOgrk3'
    'lArr':     u'\u21D0', # leftwards double arrow, U+21D0 ISOtech'
    'lambda':   u'\u03BB', # greek small letter lambda, U+03BB ISOgrk3'
    'lang':     u'\u2329', # left-pointing angle bracket = bra, U+2329 ISOtech'
    'laquo':    u'\u00AB', # left-pointing double angle quotation mark = left pointing guillemet, U+00AB ISOnum'
    'larr':     u'\u2190', # leftwards arrow, U+2190 ISOnum'
    'lceil':    u'\u2308', # left ceiling = apl upstile, U+2308 ISOamsc'
    'ldquo':    u'\u201C', # left double quotation mark, U+201C ISOnum'
    'le':       u'\u2264', # less-than or equal to, U+2264 ISOtech'
    'lfloor':   u'\u230A', # left floor = apl downstile, U+230A ISOamsc'
    'lowast':   u'\u2217', # asterisk operator, U+2217 ISOtech'
    'loz':      u'\u25CA', # lozenge, U+25CA ISOpub'
    'lrm':      u'\u200E', # left-to-right mark, U+200E NEW RFC 2070'
    'lsaquo':   u'\u2039', # single left-pointing angle quotation mark, U+2039 ISO proposed'
    'lsquo':    u'\u2018', # left single quotation mark, U+2018 ISOnum'
    'lt':       u'\u003C', # less-than sign, U+003C ISOnum'
    'macr':     u'\u00AF', # macron = spacing macron = overline = APL overbar, U+00AF ISOdia'
    'mdash':    u'\u2014', # em dash, U+2014 ISOpub'
    'micro':    u'\u00B5', # micro sign, U+00B5 ISOnum'
    'middot':   u'\u00B7', # middle dot = Georgian comma = Greek middle dot, U+00B7 ISOnum'
    'minus':    u'\u2212', # minus sign, U+2212 ISOtech'
    'mu':       u'\u03BC', # greek small letter mu, U+03BC ISOgrk3'
    'nabla':    u'\u2207', # nabla = backward difference, U+2207 ISOtech'
    'nbsp':     u'\u00A0', # no-break space = non-breaking space, U+00A0 ISOnum'
    'ndash':    u'\u2013', # en dash, U+2013 ISOpub'
    'ne':       u'\u2260', # not equal to, U+2260 ISOtech'
    'ni':       u'\u220B', # contains as member, U+220B ISOtech'
    'not':      u'\u00AC', # not sign, U+00AC ISOnum'
    'notin':    u'\u2209', # not an element of, U+2209 ISOtech'
    'nsub':     u'\u2284', # not a subset of, U+2284 ISOamsn'
    'ntilde':   u'\u00F1', # latin small letter n with tilde, U+00F1 ISOlat1'
    'nu':       u'\u03BD', # greek small letter nu, U+03BD ISOgrk3'
    'oacute':   u'\u00F3', # latin small letter o with acute, U+00F3 ISOlat1'
    'ocirc':    u'\u00F4', # latin small letter o with circumflex, U+00F4 ISOlat1'
    'oelig':    u'\u0153', # latin small ligature oe, U+0153 ISOlat2'
    'ograve':   u'\u00F2', # latin small letter o with grave, U+00F2 ISOlat1'
    'oline':    u'\u203E', # overline = spacing overscore, U+203E NEW'
    'omega':    u'\u03C9', # greek small letter omega, U+03C9 ISOgrk3'
    'omicron':  u'\u03BF', # greek small letter omicron, U+03BF NEW'
    'oplus':    u'\u2295', # circled plus = direct sum, U+2295 ISOamsb'
    'or':       u'\u2228', # logical or = vee, U+2228 ISOtech'
    'ordf':     u'\u00AA', # feminine ordinal indicator, U+00AA ISOnum'
    'ordm':     u'\u00BA', # masculine ordinal indicator, U+00BA ISOnum'
    'oslash':   u'\u00F8', # latin small letter o with stroke, = latin small letter o slash, U+00F8 ISOlat1'
    'otilde':   u'\u00F5', # latin small letter o with tilde, U+00F5 ISOlat1'
    'otimes':   u'\u2297', # circled times = vector product, U+2297 ISOamsb'
    'ouml':     u'\u00F6', # latin small letter o with diaeresis, U+00F6 ISOlat1'
    'para':     u'\u00B6', # pilcrow sign = paragraph sign, U+00B6 ISOnum'
    'part':     u'\u2202', # partial differential, U+2202 ISOtech'
    'permil':   u'\u2030', # per mille sign, U+2030 ISOtech'
    'perp':     u'\u22A5', # up tack = orthogonal to = perpendicular, U+22A5 ISOtech'
    'phi':      u'\u03C6', # greek small letter phi, U+03C6 ISOgrk3'
    'pi':       u'\u03C0', # greek small letter pi, U+03C0 ISOgrk3'
    'piv':      u'\u03D6', # greek pi symbol, U+03D6 ISOgrk3'
    'plusmn':   u'\u00B1', # plus-minus sign = plus-or-minus sign, U+00B1 ISOnum'
    'pound':    u'\u00A3', # pound sign, U+00A3 ISOnum'
    'prime':    u'\u2032', # prime = minutes = feet, U+2032 ISOtech'
    'prod':     u'\u220F', # n-ary product = product sign, U+220F ISOamsb'
    'prop':     u'\u221D', # proportional to, U+221D ISOtech'
    'psi':      u'\u03C8', # greek small letter psi, U+03C8 ISOgrk3'
    'quot':     u'\u0022', # quotation mark = APL quote, U+0022 ISOnum'
    'rArr':     u'\u21D2', # rightwards double arrow, U+21D2 ISOtech'
    'radic':    u'\u221A', # square root = radical sign, U+221A ISOtech'
    'rang':     u'\u232A', # right-pointing angle bracket = ket, U+232A ISOtech'
    'raquo':    u'\u00BB', # right-pointing double angle quotation mark = right pointing guillemet, U+00BB ISOnum'
    'rarr':     u'\u2192', # rightwards arrow, U+2192 ISOnum'
    'rceil':    u'\u2309', # right ceiling, U+2309 ISOamsc'
    'rdquo':    u'\u201D', # right double quotation mark, U+201D ISOnum'
    'real':     u'\u211C', # blackletter capital R = real part symbol, U+211C ISOamso'
    'reg':      u'\u00AE', # registered sign = registered trade mark sign, U+00AE ISOnum'
    'rfloor':   u'\u230B', # right floor, U+230B ISOamsc'
    'rho':      u'\u03C1', # greek small letter rho, U+03C1 ISOgrk3'
    'rlm':      u'\u200F', # right-to-left mark, U+200F NEW RFC 2070'
    'rsaquo':   u'\u203A', # single right-pointing angle quotation mark, U+203A ISO proposed'
    'rsquo':    u'\u2019', # right single quotation mark, U+2019 ISOnum'
    'sbquo':    u'\u201A', # single low-9 quotation mark, U+201A NEW'
    'scaron':   u'\u0161', # latin small letter s with caron, U+0161 ISOlat2'
    'sdot':     u'\u22C5', # dot operator, U+22C5 ISOamsb'
    'sect':     u'\u00A7', # section sign, U+00A7 ISOnum'
    'shy':      u'\u00AD', # soft hyphen = discretionary hyphen, U+00AD ISOnum'
    'sigma':    u'\u03C3', # greek small letter sigma, U+03C3 ISOgrk3'
    'sigmaf':   u'\u03C2', # greek small letter final sigma, U+03C2 ISOgrk3'
    'sim':      u'\u223C', # tilde operator = varies with = similar to, U+223C ISOtech'
    'spades':   u'\u2660', # black spade suit, U+2660 ISOpub'
    'sub':      u'\u2282', # subset of, U+2282 ISOtech'
    'sube':     u'\u2286', # subset of or equal to, U+2286 ISOtech'
    'sum':      u'\u2211', # n-ary sumation, U+2211 ISOamsb'
    'sup':      u'\u2283', # superset of, U+2283 ISOtech'
    'sup1':     u'\u00B9', # superscript one = superscript digit one, U+00B9 ISOnum'
    'sup2':     u'\u00B2', # superscript two = superscript digit two = squared, U+00B2 ISOnum'
    'sup3':     u'\u00B3', # superscript three = superscript digit three = cubed, U+00B3 ISOnum'
    'supe':     u'\u2287', # superset of or equal to, U+2287 ISOtech'
    'szlig':    u'\u00DF', # latin small letter sharp s = ess-zed, U+00DF ISOlat1'
    'tau':      u'\u03C4', # greek small letter tau, U+03C4 ISOgrk3'
    'there4':   u'\u2234', # therefore, U+2234 ISOtech'
    'theta':    u'\u03B8', # greek small letter theta, U+03B8 ISOgrk3'
    'thetasym': u'\u03D1', # greek small letter theta symbol, U+03D1 NEW'
    'thinsp':   u'\u2009', # thin space, U+2009 ISOpub'
    'thorn':    u'\u00FE', # latin small letter thorn with, U+00FE ISOlat1'
    'tilde':    u'\u02DC', # small tilde, U+02DC ISOdia'
    'times':    u'\u00D7', # multiplication sign, U+00D7 ISOnum'
    'trade':    u'\u2122', # trade mark sign, U+2122 ISOnum'
    'uArr':     u'\u21D1', # upwards double arrow, U+21D1 ISOamsa'
    'uacute':   u'\u00FA', # latin small letter u with acute, U+00FA ISOlat1'
    'uarr':     u'\u2191', # upwards arrow, U+2191 ISOnum'
    'ucirc':    u'\u00FB', # latin small letter u with circumflex, U+00FB ISOlat1'
    'ugrave':   u'\u00F9', # latin small letter u with grave, U+00F9 ISOlat1'
    'uml':      u'\u00A8', # diaeresis = spacing diaeresis, U+00A8 ISOdia'
    'upsih':    u'\u03D2', # greek upsilon with hook symbol, U+03D2 NEW'
    'upsilon':  u'\u03C5', # greek small letter upsilon, U+03C5 ISOgrk3'
    'uuml':     u'\u00FC', # latin small letter u with diaeresis, U+00FC ISOlat1'
    'weierp':   u'\u2118', # script capital P = power set = Weierstrass p, U+2118 ISOamso'
    'xi':       u'\u03BE', # greek small letter xi, U+03BE ISOgrk3'
    'yacute':   u'\u00FD', # latin small letter y with acute, U+00FD ISOlat1'
    'yen':      u'\u00A5', # yen sign = yuan sign, U+00A5 ISOnum'
    'yuml':     u'\u00FF', # latin small letter y with diaeresis, U+00FF ISOlat1'
    'zeta':     u'\u03B6', # greek small letter zeta, U+03B6 ISOgrk3'
    'zwj':      u'\u200D', # zero width joiner, U+200D NEW RFC 2070'
    'zwnj':     u'\u200C'  # zero width non-joiner, U+200C NEW RFC 2070'
}

entitydefs2 = {
    '$':    '%24',
    '&':    '%26',
    '+':    '%2B',
    ',':    '%2C',
    '/':    '%2F',
    ':':    '%3A',
    ';':    '%3B',
    '=':    '%3D',
    '?':    '%3F',
    '@':    '%40',
    ' ':    '%20',
    '"':    '%22',
    '<':    '%3C',
    '>':    '%3E',
    '#':    '%23',
    '%':    '%25',
    '{':    '%7B',
    '}':    '%7D',
    '|':    '%7C',
    '\\':   '%5C',
    '^':    '%5E',
    '~':    '%7E',
    '[':    '%5B',
    ']':    '%5D',
    '`':    '%60'
}

entitydefs3 = {
    u'ÂÁÀÄÃÅ':  u'A',
    u'âáàäãå':  u'a',
    u'ÔÓÒÖÕ':   u'O',
    u'ôóòöõðø': u'o',
    u'ÛÚÙÜ':    u'U',
    u'ûúùüµ':   u'u',
    u'ÊÉÈË':    u'E',
    u'êéèë':    u'e',
    u'ÎÍÌÏ':    u'I',
    u'îìíï':    u'i',
    u'ñ':       u'n',
    u'ß':       u'B',
    u'÷':       u'%',
    u'ç':       u'c',
    u'æ':       u'ae'
}

def clean1(s): # remove &XXX;
    if not s:
        return ''
    for name, value in entitydefs.iteritems():
        if u'&' in s:
            s = s.replace(u'&' + name + u';', value)
    return s;

def clean2(s): # remove \\uXXX
    pat = re.compile(r'\\u(....)')
    def sub(mo):
        return unichr(int(mo.group(1), 16))
    return pat.sub(sub, smart_unicode(s))

def clean3(s): # remove &#XXX;
    pat = re.compile(r'&#(\d+);')
    def sub(mo):
        return unichr(int(mo.group(1)))
    return decode(pat.sub(sub, smart_unicode(s)))

def decode(s):
    if not s:
        return ''
    try:
        dic = htmlentitydefs.name2codepoint
        for key in dic.keys():
            entity = '&' + key + ';'
            s = s.replace(entity, unichr(dic[key]))
    except:
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
    return s

def unquote_safe(s): # unquote
    if not s:
        return ''
    try:
        for key, value in entitydefs2.iteritems():
            s = s.replace(value, key)
    except:
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
    return s;

def quote_safe(s): # quote
    if not s:
        return ''
    try:
        for key, value in entitydefs2.iteritems():
            s = s.replace(key, value)
    except:
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
    return s;

def smart_unicode(s):
    if not s:
        return ''
    try:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'UTF-8')
        elif not isinstance(s, unicode):
            s = unicode(s, 'UTF-8')
    except:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'ISO-8859-1')
        elif not isinstance(s, unicode):
            s = unicode(s, 'ISO-8859-1')
    return s

def clean_safe(s):
    if not s:
        return ''
    try:
        s = clean1(clean2(clean3(smart_unicode(s))))
    except:
        if enable_debug:
            traceback.print_exc(file = sys.stdout)
    return s

def clean_filename(s):
    if not s:
        return ''
    badchars = '\\/:*?\"<>|'
    for c in badchars:
        s = s.replace(c, '_')
    return s;

def smart_read_file(filename):
    for directory in [catDir, resDir, cacheDir, '']:
        try:
            f = open(os.path.join(directory, filename), 'r')
            log(
                'File: ' +
                os.path.join(directory, filename) +
                ' opened'
            )
            break
        except:
            log(
                'File: ' +
                os.path.join(directory, filename) +
                ' not found'
            )
            if directory == u'':
                traceback.print_exc(file = sys.stdout)
            if directory == u'':
                return False, False

    key = []
    value = []

    for line in f:
        line =  smart_unicode(line)
        if line and line.startswith(u'#'):
            continue
        line = line.replace(u'\r\n', u'').replace(u'\n', u'')
        try:
            k, v = line.split(u'=', 1)
        except:
            log('Line does not start with a \'#\' or contain an \'=\'')
            log('Line = ' + line)
            continue
        if v.startswith(u'video.devil.'):
            idx = v.find(u'|')
            if v[:idx] == u'video.devil.locale':
                v = '  ' + __language__(int(v[idx+1:])) + '  '
            elif v[:idx] ==u'video.devil.image':
                v = os.path.join(imgDir, v[idx+1:])
            elif v[:idx] == u'video.devil.context':
                v = 'context.' + __language__(int(v[idx+1:]))
            v = smart_unicode(v)
        key.append(k)
        value.append(v)
    f.close()
    return key, value

def parseActions(item, convActions, url = None):
    for convAction in convActions:
        if convAction.find("(") != -1:
            action = convAction[0:convAction.find("(")]
            param = convAction[len(action) + 1:-1]
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

            if action == u'urlappend':
                item[u'url'] = url + item[u'url']
            elif action == u'striptoslash':
                if url.rfind(u'/'):
                    idx = url.rfind(u'/')
                    if url[:idx + 1] == u'http://':
                        item[u'url'] = url + u'/' + item[u'url']
                    else:
                        item[u'url'] = url[:idx + 1] + item[u'url']
            elif action == u'space':
                try:
                    item[u'title'] = ' ' + item[u'title'].strip() + ' '
                except:
                    pass
    return item

def log(s):
    if enable_debug:
        xbmc.log(s)
    return

def run_parallel_in_threads(target, args_list):
    result = Queue.Queue()
    # wrapper to collect return value in a Queue
    def task_wrapper(*args):
        result.put(target(*args))
    threads = [threading.Thread(target=task_wrapper, args=args) for args in args_list]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result

class CListItem:
    def __init__(self):
        self.infos_dict = {}

    def merge(self, item):
        for key in item.infos_dict.keys():
            if key not in self.infos_dict:
                self.infos_dict[key] = item.infos_dict[key]

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
        self.pattern1 = ''
        self.pattern1RE = ''
        self.order = []
        self.skill = ''
        self.curr = ''
        self.pattern2 = ''
        self.pattern2RE = ''
        self.dtitle = ''
        self.dicon = ''
        self.info_list = []
        self.actions = []
        self.url_build = ''

class CCatcherRuleItem:
    def __init__(self):
        self.target = ''
        self.pattern1 = ''
        self.pattern1RE = ''
        self.actions = []
        self.dkey = ''
        self.pattern2 = ''
        self.pattern2RE = ''
        self.dkey_action = []
        self.info = ''
        self.extension = 'flv'
        self.quality = 'standard'
        self.build = ''
        self.forward = False
        self.link = ''

class CCatcherItem:
    def __init__(self):
        self.url = ''
        self.txheaders = {'User-Agent':USERAGENT}
        self.limit = 0
        self.data = ''
        self.rules = []

class CRuleSite:
    def __init__(self):
        self.start = ''
        self.startRE = ''
        self.player = ''
        self.cfg = ''
        self.txheaders = {
            'User-Agent':USERAGENT,
            'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        }
        self.data = ''
        self.rules = []

class CCurrentList:
    def __init__(self):
        self.sort = [u'label']
        self.skill = ''
        self.catcher = []
        self.sites = []
        self.items = []
        self.dirs = {}
        self.urlList = []
        self.extensionList = []
        self.selectionList = []
        self.decryptList = []
        self.dkey = ''

    def parser(self, url):
        lItem = self.decodeUrl(url)
        url = lItem.infos_dict[u'url']
        ext = self.getFileExtension(url)
        if ext == u'videodevil' or ext == u'dwnlddevil':
            url = url[:len(url) - 11]
            lItem.infos_dict[u'url'] = url
            catcher = lItem.infos_dict[u'catcher']
            if lItem.infos_dict[u'type'] == u'video':
                self.loadCatcher(catcher)
                lItem.infos_dict[u'url'] = self.getDirectLink(lItem.infos_dict[u'url'], lItem)
            if 'extension' in lItem.infos_dict:
                self.videoExtension = u'.' + lItem.infos_dict[u'extension']
            resultCode = -2
        elif ext == u'add':
            self.addItem(url[:len(url) - 4], lItem)
            result = -2
        elif ext == u'remove':
            dia = xbmcgui.Dialog()
            if dia.yesno('', __language__(30054)):
                self.removeItem(url[:len(url) - 7])
                xbmc.executebuiltin(u'Container.Refresh')
            result = -2
        elif ext == u'dir':
            resultCode = self.loadLocal(url, lItem)
        elif ext == u'list':
            resultCode = self.loadLocal(url, lItem)
            tmpItems = list(self.items)
            self.items = []
            self.sites = []
            for item in tmpItems:
                if u'cfg' in item.infos_dict:
                    resultCode = self.loadLocal(item.infos_dict[u'cfg'], item)
                    if u'url' in item.infos_dict:
                        self.sites[-1].start = item.infos_dict[u'url']
                else:
                    resultCode = self.loadLocal(item.infos_dict[u'url'], item)
            xbmc.log('Fetching websites')
            args_list = []
            for site in self.sites:
                args = (site, site.start)
                args_list.append(args)
            run_parallel_in_threads(self.fetchHTML, args_list)
            xbmc.log('Websites fetched')
            xbmc.log('Parsing websites')
            
            for item, site in enumerate(self.sites):
                resultCode = self.loadRemote(site, tmpItems[item])
            xbmc.log('Websites parsed')

            # Create directory items
            xbmc.log('Creating directory items')
            tmpItems = []
            for dir_name, dir_value in self.dirs.iteritems():
                tmp = CListItem()
                catfilename = clean_filename(dir_name[0].strip() + u'.dir')
                tmp.infos_dict[u'title'] = dir_name[0]
                tmp.infos_dict[u'icon'] = dir_name[1]
                tmp.infos_dict[u'url'] = catfilename
                tmp.merge(lItem)
                self.items.append(tmp)
                for item_title, item_value in dir_value.iteritems():
                    itemfilename = clean_filename(dir_name[0].strip() + u'.' + item_title.strip() + u'.list')
                    self.saveList(cacheDir, itemfilename, item_value, Listname = 'Temporary file')
                    tmp = CListItem()
                    tmp.infos_dict[u'title'] = item_title
                    tmp.infos_dict[u'icon'] = dir_name[1]
                    tmp.infos_dict[u'url'] = itemfilename
                    tmp.merge(lItem)
                    tmpItems.append(tmp.infos_dict)
                self.saveList(cacheDir, catfilename, tmpItems, Listname = 'Temporary file')
            self.dirs = {}
            xbmc.log('Directory items created')

        return resultCode, lItem, ext

    def loadLocal(self, filename, lItem = None, firstPage = True):
        key, value = smart_read_file(filename)
        if not key and value:
            return -1
        site_tmp = CRuleSite()
        site_tmp.cfg = filename
        if self.getFileExtension(site_tmp.cfg) == u'cfg' and lItem != None:
            if u'cfg' not in lItem.infos_dict:
                lItem.infos_dict[u'cfg'] = site_tmp.cfg
        tmp = None
        line = 0
        length = len(key) - 1
        breaker = -10
        if key[line] == u'start':
            site_tmp.start = value[line]
            line += 1
        if key[line] == u'header':
            index = value[line].find(u'|')
            site_tmp.txheaders[value[line][:index]] = value[line][index+1:]
            line += 1
        if key[line] == u'sort':
            self.sort.append(value[line])
            line += 1
        if key[line] == u'skill':
            self.skill = value[line]
            skill_file = filename[:filename.find(u'.')] + u'.lnk'
            if self.skill.find(u'redirect') != -1:
                try:
                    f = open(str(os.path.join(resDir, skill_file)), 'r')
                    forward_cfg = f.read()
                    f.close()
                    if forward_cfg != site_tmp.cfg:
                        return self.loadLocal(forward_cfg, lItem)
                    return 0
                except:
                    pass
            elif self.skill.find(u'store') != -1:
                f = open(str(os.path.join(resDir, skill_file)), 'w')
                f.write(site_tmp.cfg)
                f.close()
            line += 1
        if key[line] == u'startRE':
            site_tmp.startRE = value[line]
            line += 1
        while line < length:
            breaker += 1
            while line < length and key[line].startswith(u'item'):
                breaker += 1
                if key[line] == u'item_infos':
                    rule_tmp = CRuleItem()
                    rule_tmp.infos = value[line]
                    line += 1
                if key[line] == u'item_order':
                    if value[line].find(u'|'):
                        rule_tmp.order = value[line].split(u'|')
                    else:
                        rule_tmp.order.append(value[line])
                    line += 1
                if key[line] == u'item_skill':
                    rule_tmp.skill = value[line]
                    line += 1
                if key[line] == u'item_curr':
                    rule_tmp.curr = value[line]
                    line += 1
                while key[line].startswith(u'item_info_'):
                    breaker += 1
                    if key[line] == u'item_info_name':
                        info_tmp = CItemInfo()
                        info_tmp.name = value[line]
                        line += 1
                    if key[line] == u'item_info_from':
                        info_tmp.src = value[line]
                        line += 1
                    if key[line] == u'item_info':
                        info_tmp.rule = value[line]
                        line += 1
                    if key[line] == u'item_info_default':
                        info_tmp.default = value[line]
                        line += 1
                    if key[line] == u'item_info_build':
                        info_tmp.build = value[line]
                        if rule_tmp.skill.find(u'directory') != -1:
                            if info_tmp.name == u'title':
                                rule_tmp.dtitle = value[line]
                            elif info_tmp.name == u'icon':
                                rule_tmp.dicon = value[line]
                        rule_tmp.info_list.append(info_tmp)
                        line += 1
                    if line == length or breaker == length:
                        break
                if key[line] == u'item_infos_actions':
                    rule_tmp.actions = value[line].split(u'|') or [value[line]]
                    line += 1
                if key[line] == u'item_url_build':
                    rule_tmp.url_build = value[line]
                    site_tmp.rules.append(rule_tmp)
                    line += 1
            if line >= length or breaker == length:
                break
            if key[line] == u'title':
                tmp = CListItem()
                tmp.infos_dict[u'title'] = value[line]
                line += 1
            if key[line] == u'type':
                if firstPage and value[line] == u'once':
                    value[line] = u'rss'
                tmp.infos_dict[u'type'] = value[line]
                line += 1
            while line < length and key[line] != u'url':
                breaker += 1
                if tmp:
                    tmp.infos_dict[key[line]] = value[line]
                    line += 1
                if breaker == length:
                    break
            if key[line] == u'url':
                tmp.infos_dict[u'url'] = value[line]
                if lItem != None:
                    tmp.merge(lItem)
                self.items.append(tmp)
                tmp = None
                line += 1
            if line >= length or breaker == length:
                break
        self.sites.append(site_tmp)
        return 0

    def loadRemote(self, site, lItem):
        data = site.data
        url = site.start

        # Parser HTML site
        self.remoteLoops(site, url, site.rules, data, lItem)

        # Remove Duplicate items
        tmpUrl = []
        tmpItems = []
        for item in self.items:
            if not item.infos_dict[u'url'] in tmpUrl:
                tmpUrl.append(item.infos_dict[u'url'])
                tmpItems.append(item)
        self.items = tmpItems

        return 0

    def loadCatcher(self, title):
        key, value = smart_read_file(title)
        for catcher in self.catcher:
            del self.catcher[:]
        catcher_tmp = ''
        line = 0
        length = len(key)
        if key[line] == u'player':
            self.player = value[line]
            line += 1
        while line < length and key[line]:
            if key[line] == u'url':
                catcher_tmp = CCatcherItem()
                catcher_tmp.url = value[line]
                line += 1
            if key[line] == u'data':
                catcher_tmp.data = value[line]
                line += 1
            if key[line] == u'header':
                index = value[line].find(u'|')
                catcher_tmp.txheaders[value[line][:index]] = value[line][index+1:]
                line += 1
            if key[line] == u'limit':
                catcher_tmp.limit = int(value[line])
                line += 1
            while line < length:
                if key[line] == u'target':
                    rule_tmp = CCatcherRuleItem()
                    rule_tmp.target = value[line]
                    line += 1
                if key[line] == u'quality':
                    rule_tmp.quality = value[line]
                    catcher_tmp.rules.append(rule_tmp)
                    line += 1
                    continue
                if key[line] == u'build':
                    rule_tmp.build = value[line]
                    self.catcher.append(catcher_tmp)
                    line += 1
                    break
                if key[line] == u'forward':
                    rule_tmp.forward = value[line]
                    catcher_tmp.rules.append(rule_tmp)
                    self.catcher.append(catcher_tmp)
                    line += 1
                    break
                while key[line] != u'quality':
                    if key[line] == u'actions':
                        if value[line].find(u'|'):
                            rule_tmp.actions = value[line].split(u'|')
                        else:
                            rule_tmp.actions.append(value[line])
                        line += 1
                    if key[line] == u'dkey':
                        rule_tmp.dkey = value[line]
                        line += 1
                        if key[line] == u'dkey_actions':
                            if value[line].find(u'|'):
                                rule_tmp.dkey_actions = value[line].split(u'|')
                            else:
                                rule_tmp.dkey_actions.append(value[line])
                            line += 1
                    if key[line] == u'extension':
                        rule_tmp.extension = value[line]
                        line += 1
                    if key[line] == u'info':
                        rule_tmp.info = value[line]
                        line += 1
                    if line == length:
                        break
        return -1

    def getDirectLink(self, url, lItem):
        for catcher in self.catcher:

            # Download website
            if catcher.data == u'':
                if catcher.url.find(u'%') != -1:
                    url = catcher.url % url
                req = Request(url, None, catcher.txheaders)
                urlfile = opener.open(req)
                if catcher.limit == 0:
                    data = urlfile.read()
                else:
                    data = urlfile.read(catcher.limit)
            else:
                data_url = catcher.data % url
                req = Request(catcher.url, data_url, catcher.txheaders)
                response = urlopen(req)
                if catcher.limit == 0:
                    data = response.read()
                else:
                    data = response.read(catcher.limit)
            if enable_debug:
                f = open(os.path.join(cacheDir, 'catcher.html'), 'w')
                f.write(u'<Titel>'+ url + '</Title>\n\n')
                f.write(data)
                f.close()

            url = self.remoteLoops(url, catcher.rules, data, lItem)

        link = self.selectLink()
        return link

    # Parsing loops for loadRemote and getDirectlink

    def remoteLoops(self, site, url, rules, data, lItem):

        # Create interests lists and modify rule RE patterns
        interests = []
        interests2 = []
        interestRE = re.compile(r'[-a-zA-Z0-9/,:;%!&$_#=~@<> ]+', re.IGNORECASE + re.DOTALL + re.MULTILINE)

        for item_rule in rules:
            if lItem.infos_dict[u'type'] == u'video':
                item_rule.pattern1 = item_rule.target
                if item_rule.dkey:
                    item_rule.pattern2 = item_rule.dkey
            else:
                item_rule.pattern1 = item_rule.infos
                if item_rule.curr:
                    item_rule.pattern2 = item_rule.curr
            match = interestRE.match(item_rule.pattern1)
            item_rule.pattern1 = item_rule.pattern1[match.end():]
            interests.append(match.group(0))
            if item_rule.pattern2:
                match = interestRE.match(item_rule.pattern2)
                interests2.append(match.group(0))

        # Combine interests list
        interests2.extend(interests)

        # Remove longer matches that may cause the while loop to shorter matches
        # i.e. remove '<img src' if '<img' is in the list
        interesting_items = self.listFormatter(interests2)

        # Create interestingRE from interesting_items list
        interesting_pattern = u'(' + u'|'.join(interesting_items) + u')'
        interestingRE = re.compile(interesting_pattern, re.IGNORECASE + re.DOTALL + re.MULTILINE)

        # Create REs for while loop
        for item_rule in rules:
            item_rule.pattern1RE = re.compile(item_rule.pattern1, re.IGNORECASE + re.DOTALL + re.MULTILINE)
            if item_rule.pattern2:
                item_rule.pattern2RE = re.compile(item_rule.pattern2, re.IGNORECASE + re.DOTALL + re.MULTILINE)

        # Find video links
        if site.startRE:
            point = data.find(site.startRE.encode('utf-8'))
            if point == -1:
                point = 0
        else:
            point = 0

        length = len(data)

        while point < length:
            interest = interestingRE.search(data, point)
            if interest:
                point = interest.start()
                intersting_point = interest.start()
                jump = len(interest.group(0))
                for index, rule_name in enumerate(interests):
                    item_rule = rules[index]
                    if rule_name.startswith(interest.group(0)):
                        match = item_rule.pattern1RE.match(data, point + jump)
                        if match:
                            while match:
                                if not match.group(0):
                                    break
                                point += jump + len(match.group(0))
                                if lItem.infos_dict[u'type'] == u'video':
                                    url, point = self.saveLink(item_rule, url, match, point, length)
                                else:
                                    self.itemBuilder(item_rule, lItem, url, match)
                                match = item_rule.pattern1RE.match(data, point + jump)
                            break
                    elif item_rule.pattern2 and item_rule.pattern2.startswith(interest.group(0)):
                        match = item_rule.pattern2RE.match(data, point)
                        if match:
                            while match:
                                point += len(match.group(0))
                                if lItem.infos_dict[u'type'] == u'video':
                                    self.dkeyBuilder(item_rule, url, match)
                                else:
                                    self.currBuilder(item_rule, lItem, url, match)
                                match = item_rule.pattern2RE.match(data, point)
                            break
                if point == intersting_point:
                    point += 1
            else:
                break
        return url

    # HTML site downloader for loadRemote

    def fetchHTML(self, site, url):
        try:
            if enable_debug:
                f = open(os.path.join(cacheDir, site.cfg + u'.page.html'), 'w')
                f.write(u'<Title>'+ url + u'</Title>\n\n')
            req = Request(url, None, site.txheaders)
            try:
                handle = urlopen(req)
            except:
                if enable_debug:
                    xbmc.log('site cfg = ' + site.cfg)
                    xbmc.log('url = ' + url)
                    traceback.print_exc(file = sys.stdout)
                return
            site.data = handle.read()
            cj.save(os.path.join(settingsDir, 'cookies.lwp'))
            if enable_debug:
                f.write(site.data)
                f.close()
        except IOError:
            if enable_debug:
                traceback.print_exc(file = sys.stdout)
            return -1

    # Helper Functions for Function loadRemote

    def itemBuilder(self, rule, lItem, url, match):
        tmp = CListItem()
        tmp.infos_dict = self.loadDict(tmp.infos_dict, rule, url, match)
        tmp.infos_dict = self.infoFormatter(tmp.infos_dict, lItem)
        try:
            if rule.skill.find(u'space') != -1:
                tmp.infos_dict[u'title'] = ' ' + tmp.infos_dict[u'title'] + ' '
            elif rule.skill.find(u'bottom') != -1:
                tmp.infos_dict[u'title'] = tmp.infos_dict[u'title'].strip()
        except:
            pass
        tmp.merge(lItem)
        if rule.skill.find(u'recursive') != -1:
            self.loadRemote(tmp.infos_dict[u'url'], False, tmp)
            tmp = None
        else:
            if rule.skill.find(u'directory') != -1:
                rule = self.dirsBuilder(tmp.infos_dict, rule, lItem)
            else:
                self.items.append(tmp)
        return

    def loadDict(self, item, rule, url, match):
        infos_names = rule.order
        infos_values = match.groups()
        for (infos_name, infos_value) in zip(infos_names, infos_values):
            if infos_name.startswith(u'url') or infos_name.startswith(u'icon'):
                item[infos_name] = smart_unicode(infos_value)
            else:
                item[infos_name] = clean_safe(infos_value)
        for info in rule.info_list:
            info_value = u''
            if info.name in item:
                if info.build.find(u'%s') != -1:
                    item[info.name] = info.build % item[info.name]
                continue
            if info.rule != u'':
                info_rule = info.rule
                if info.rule.find(u'%s') != -1:
                    src = item[info.src]
                    info_rule = info.rule % src
                infosearch = re.search(info_rule, data)
                if infosearch:
                    info_value = infosearch.group(1).strip()
                    if info.build.find(u'%s') != -1:
                        info_value = info.build % (info_value)
                elif info.default != u'':
                    info_value = info.default
            else:
                if info.build.find(u'%s') != -1:
                    src = item[info.src]
                    info_value = info.build % src
                else:
                    info_value = info.build
            item[info.name] = info_value
        if len(rule.actions) > 0:
            item = parseActions(item, rule.actions, url)
        item[u'url'] = rule.url_build % item[u'url']
        
        return item

    def infoFormatter(self, item, lItem):
        keep = {}
        for info_name, info_value in item.iteritems():
            if info_name == u'title':
                try:
                    info_value = info_value.replace(u'\r\n', u'').replace(u'\n', u'').replace(u'\t', u'')
                    info_value = u' ' + info_value.strip() + u' '
                except:
                    info_value = u'...'
                keep[info_name] = info_value
            elif info_name == u'icon':
                if info_value == u'':
                    info_value = os.path.join(imgDir, u'video.png')
                keep[info_name] = info_value
            elif len(info_value) == 0:
                info_value = u'...'
                keep[info_name] = info_value
            elif info_name.rfind(u'.tmp') != -1:
                continue
            else:
                keep[info_name] = info_value
        return keep

    def currBuilder(self, rule, lItem, url, match):
        title = match.group(1)
        tmp = CListItem()
        if rule.skill.find(u'space') != -1:
            tmp.infos_dict[u'title'] = u'   ' + title.strip() + u' (' + __language__(30106) + u')   '
        else:
            tmp.infos_dict[u'title'] = u'  ' + title.strip() + u' (' + __language__(30106) + u')  '
        tmp.infos_dict[u'url'] = url
        tmp.merge(lItem)
        if rule.skill.find(u'directory') != -1:
            rule = self.dirsBuilder(tmp.infos_dict, rule, lItem)
        else:
            self.items.append(tmp)
        return

    def dirsBuilder(self, item, rule, lItem):
        dir = (rule.dtitle, rule.dicon)
        if dir in self.dirs:
            for dir_name, dir_value in self.dirs.iteritems():
                if dir == dir_name:
                    if item[u'title'] not in dir_value:
                        dir_value[item[u'title']] = [item]
        else:
            self.dirs[dir] = {item[u'title']: [item]}
        return rule

    # Helper functions for Function getDirectLink

    def saveLink(self, rule, url, match, point, length):
        link = match.group(1)
        if len(rule.actions) > 0:
            for group in range(1, len(match.groups()) + 1):
                if group == 1:
                    link = {'match' : link}
                else:
                    link[u'group' + str(group)] = match.group(group)
            link = parseActions(link, rule.actions)
            link = link[u'match']
        if rule.build.find(u'%s') != -1:
            link = rule.build % link
        if rule.forward:
            url = link
            point = length
            return url, point
        if rule.quality == u'fallback':
            self.videoExtension = '.' + rule.extension
            point = length
        rule.link = link
        self.selectLinkLists(link, rule)
        return url, point

    def selectLink(self):
        video_type = {
            1:[u'low', 'standard', 'high'], 
            2:[u'standard', 'low', 'high'], 
            3:[u'high', 'standard', 'low']
        }
        if len(self.urlList) > 0:
            if len(self.urlList) == 1:
                self.videoExtension = '.' + self.extensionList[0]
                if self.decryptList[0]:
                    link = sesame.decrypt(self.urlList[0], self.dkey, 256)
                else:
                    link = self.urlList[0]
                link = self.urlList[0]
            elif int(addon.getSetting('video_type')) == 0:
                dia = xbmcgui.Dialog()
                selection = dia.select(__language__(30055), self.selectionList)
                self.videoExtension = '.' + self.extensionList[selection]
                if self.decryptList[selection]:
                    link = sesame.decrypt(self.urlList[selection], self.dkey, 256)
                else:
                    link = self.urlList[selection]
            else:
                video_type = video_type[int(addon.getSetting('video_type'))]
                for video_qual in video_type:
                    for rule_name, rule_value in self.catcher.rules.iteritems():
                        item_rule = rule_value
                        if item_rule.quality == video_qual and item_rule.link != u'':
                            self.videoExtension = '.' + item_rule.extension
                            if self.decryptList[index]:
                                try:
                                    link = sesame.decrypt(item_rule.link, self.dkey, 256)
                                    log(link)
                                except:
                                    log('Incorrect decryption key may have been supplied')
                            else:
                                link = item_rule.link
        else:
            link = ''
        return link

    def selectLinkLists(self, link, rule):
        selList_type = {
            'low' : __language__(30056), 
            'standard' : __language__(30057), 
            'high' : __language__(30058)
        }
        self.urlList.append(link)
        self.extensionList.append(rule.extension)
        append = rule.info or rule.extension
        self.selectionList.append(selList_type[rule.quality] + u' (' + append + u')')
        self.decryptList.append(rule.dkey)

    def dkeyBuilder(self, rule, url, match):
        link = match.group(1)
        link = {'match' : link}
        self.dkey = parseActions(link, rule.dkey_actions)[u'match']
        return

    # Helper functions for the class

    def getKeyboard(self, default = '', heading = '', hidden = False):
        kboard = xbmc.Keyboard(default, heading, hidden)
        kboard.doModal()
        if kboard.isConfirmed():
            return kboard.getText()
        return ''

    def getSearchPhrase(self, ):
        try:
            curr_phrase = urllib.unquote_plus(addon.getSetting('curr_search'))
        except:
            addon.setSetting('curr_search', '')
        search_phrase = self.getKeyboard(default = curr_phrase, heading = __language__(30102))
        return search_phrase

    def getFileExtension(self, filename):
        ext_pos = filename.rfind(u'.')
        if ext_pos != -1:
            return smart_unicode(filename[ext_pos+1:])
        else:
            return ''

    def videoCount(self):
        count = 0
        for item in self.items:
            if item.infos_dict[u'type'] == u'video':
                count = count +1
        return count

    def getVideo(self):
        for item in self.items:
            if item.infos_dict[u'type'] == u'video':
                return item

    def getItemFromList(self, listname, name):
        self.loadLocal(listname, False)
        for item in self.items:
            if item.infos_dict[u'url'] == name:
                return item
        return None

    def itemInLocalList(self, name):
        for item in self.items:
            if item.infos_dict[u'url'] == name:
                return True
        return False

    def getItem(self, name):
        item = None
        for root, dirs, files in os.walk(resDir):
            for listname in files:
                if self.getFileExtension(listname) == u'list' and listname != u'catcher.list':
                    item = self.getItemFromList(listname, name)
                if item != None:
                    return item
        return None

    def addItem(self, name):
        item = self.getItem(name)
        del self.items[:]
        try:
            self.loadLocal(u'entry.list', False)
        except:
            del self.items[:]
        if item and not self.itemInLocalList(name):
            self.items.append(item)
            self.saveList(resDir, 'entry.list', self.items, 'Added sites and live streams', {skill : remove})
        return

    def removeItem(self, name):
        item = self.getItemFromList(u'entry.list', name)
        if item != None:
            self.items.remove(item)
            self.saveList(resDir, 'entry.list', self.items, 'Added sites and live streams', {skill : remove})
        return

    def saveList(self, directory, filename, items, Listname, List_dict = None):
        f = open(str(os.path.join(directory, filename)), 'w')
        Listname = u'#' + Listname.center(54) + u'#\n'
        f.write(u'########################################################\n')
        f.write(Listname)
        f.write(u'########################################################\n')
        if List_dict != None:
            for info_name, info_value in List_dict.iteritems():
                f.write(info_name + '=' + info_value + '\n')
            f.write(u'########################################################\n')
        for item in items:
            try:
                f.write(u'title=' + item[u'title'] + u'\n')
            except:
                f.write(u'title=...\n')
            for info_name, info_value in item.iteritems():
                if info_name != u'url' and info_name != u'title':
                    f.write(info_name + u'=' + info_value + u'\n')
            f.write(u'url=' + item[u'url'] + u'\n')
            f.write(u'########################################################\n')
        f.close()
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

    def codeUrl(self, item, suffix = None):
        # in Frodo url parameters need to be encoded
        # ignore characters that can't be converted to ascii
        def doubleQuote(s):
            s = urllib.quote(s).replace('%', '%25')
            return s
        url = item.infos_dict[u'url'].replace(u'\xa0', u' ')
        url = u'url%3A'.encode('utf-8') + doubleQuote(url.encode('utf-8'))
        del item.infos_dict[u'url']
        #this is added for handling the stupid &nbsp;
        if suffix:
            url = url + u'.'.encode('utf-8') + suffix.encode('utf-8')
        for info_name, info_value in item.infos_dict.iteritems():
            try:
                if info_name.find(u'.once') == -1:
                    url += u'%26'.encode('utf-8') + info_name.encode('utf-8') + u'%3A'.encode('utf-8') + doubleQuote(info_value.encode('utf-8'))
            except KeyError:
                xbmc.log('Skipping %s probably has unicode' % info_value.encode('utf-8'))
        return url

    def decodeUrl(self, url, url_type = u'rss'):
        item = CListItem()
        if url.find(u'%26') == -1:
            item.infos_dict[u'url'] = urllib.unquote(url)
        else:
            infos_names_values = url.split(u'%26')
            for info_name_value in infos_names_values:
                info_name, info_value = info_name_value.split(u'%3a')
                info_value = info_value.replace(u'%25', u'%')
                item.infos_dict[info_name] = urllib.unquote(info_value)
        if 'type' not in item.infos_dict:
            item.infos_dict[u'type'] = url_type
        return item

class Main:
    def __init__(self):
        xbmc.log('Initializing VideoDevil')
        self.pDialog = None
        self.curr_file = ''
        self.videoExtension = '.flv'
        self.handle = 0
        self.currentlist = CCurrentList()
        xbmc.log('VideoDevil initialized')
        self.run()

    def playVideo(self, videoItem):
        if videoItem == None:
            return
        if videoItem.infos_dict[u'url'] == u'':
            return
        url = videoItem.infos_dict[u'url']
        try:
            icon = videoItem.infos_dict[u'icon']
        except:
            icon = os.path.join(imgDir, 'video.png')
        try:
            title = videoItem.infos_dict[u'title']
        except:
            title = '...'
        try:
            urllib.urlretrieve(icon, os.path.join(cacheDir, 'thumb.tbn'))
            icon = os.path.join(cacheDir, 'thumb.tbn')
        except:
            if enable_debug:
                traceback.print_exc(file = sys.stdout)
            icon = os.path.join(imgDir, 'video.png')
        flv_file = url
        listitem = xbmcgui.ListItem(title, title, icon, icon)
        listitem.setInfo('video', {'Title':title})
        for info_name, info_value in videoItem.infos_dict.iteritems():
            try:
                listitem.setInfo(type = 'Video', infoLabels = {info_name: info_value})
            except:
                pass
        if self.currentlist.skill.find(u'nodownload') == -1:
            if addon.getSetting('download') == 'true':
                flv_file = self.downloadMovie(url, title)
            elif addon.getSetting('download') == 'false' and addon.getSetting('download_ask') == 'true':
                dia = xbmcgui.Dialog()
                if dia.yesno('', __language__(30052)):
                    flv_file = self.downloadMovie(url, title)

        player_type = {
            0:xbmc.PLAYER_CORE_AUTO, 
            1:xbmc.PLAYER_CORE_MPLAYER, 
            2:xbmc.PLAYER_CORE_DVDPLAYER
        }
        player_type = player_type[int(addon.getSetting('player_type'))]
        if self.currentlist.player == u'auto':
            player_type = xbmc.PLAYER_CORE_AUTO
        elif self.currentlist.player == u'mplayer':
            player_type = xbmc.PLAYER_CORE_MPLAYER
        elif self.currentlist.player == u'dvdplayer':
            player_type = xbmc.PLAYER_CORE_DVDPLAYER

        xbmc.Player(player_type).play(str(flv_file), listitem)
        xbmc.sleep(200)

    def downloadMovie(self, url, title):
        download_path = addon.getSetting('download_path')
        if download_path == u'':
            try:
                download_path = xbmcgui.Dialog().browse(0, __language__(30017), 'files', '', False, False)
                addon.setSetting(id='download_path', value=download_path)
                if not os.path.exists(download_path):
                    os.mkdir(download_path)
            except:
                pass
        tmp_file = tempfile.NamedTemporaryFile(suffix = self.currentlist.videoExtension, dir=download_path)
        tmp_file = xbmc.makeLegalFilename(tmp_file.name)
        vidfile = xbmc.makeLegalFilename(download_path + clean_filename(title) + self.currentlist.videoExtension)
        self.pDialog = xbmcgui.DialogProgress()
        self.pDialog.create('VideoDevil', __language__(30050), __language__(30051))
        urllib.urlretrieve(url, tmp_file, self.video_report_hook)
        self.pDialog.close()
        if not os.path.exists(tmp_file):
            dialog = xbmcgui.Dialog()
            dialog.ok('VideoDevil Info', __language__(30053))
        try:
            os.rename(tmp_file, vidfile)
            return vidfile
        except:
            return tmp_file

    def video_report_hook(self, count, blocksize, totalsize):
        percent = int(float(count * blocksize * 100) / totalsize)
        self.pDialog.update(percent, __language__(30050), __language__(30051))
        if self.pDialog.iscanceled():
            raise KeyboardInterrupt

    def parseView(self, url):
        result, lItem, ext = self.currentlist.parser(url)
        if ext == u'videodevil' or ext == u'dwnlddevil':
            if ext == u'videodevil':
                result = self.playVideo(lItem)
            else:
                self.downloadMovie(lItem.infos_dict[u'url'], lItem.infos_dict[u'title'])
                result = -2
        else:
            sort_dict = {
                'label' : xbmcplugin.SORT_METHOD_LABEL, 
                'size' : xbmcplugin.SORT_METHOD_SIZE, 
                'duration' : xbmcplugin.SORT_METHOD_DURATION, 
                'genre' : xbmcplugin.SORT_METHOD_GENRE, 
                'rating' : xbmcplugin.SORT_METHOD_VIDEO_RATING, 
                'date' : xbmcplugin.SORT_METHOD_DATE
            }
            for sort_method in self.currentlist.sort:
                xbmcplugin.addSortMethod(handle = self.handle, sortMethod = sort_dict[sort_method])

            if self.currentlist.skill.find(u'play') != -1 and self.currentlist.videoCount() == 1:
                url = self.currentlist.codeUrl(self.currentlist.getVideo(), 'videodevil')
                result = self.parseView(url)
            else:
                for m in self.currentlist.items:
                    m_url = m.infos_dict[u'url']
                    try:
                        m_type = m.infos_dict[u'type']
                    except:
                        m_type = u'rss'
                    m_icon = m.infos_dict[u'icon']
                    m_title = clean_safe(m.infos_dict[u'title'])
                    if m_type == u'rss' or m_type == u'search':
                        self.addListItem(m_title, self.currentlist.codeUrl(m), m_icon, len(self.currentlist.items), m)
                    elif m_type.find(u'video') != -1:
                        self.addListItem(m_title, self.currentlist.codeUrl(m, 'videodevil'), m_icon, len(self.currentlist.items), m)
        return result

    def addListItem(self, title, url, icon, totalItems, lItem):
        u = sys.argv[0] + '?url=' + url
        liz = xbmcgui.ListItem(title, title, icon, icon)
        if self.currentlist.getFileExtension(url) == u'videodevil' and self.currentlist.skill.find(u'nodownload') == -1:
            action = 'XBMC.RunPlugin(%s.dwnlddevil)' % u[:len(u)-11]
            try:
                liz.addContextMenuItems([(__language__(30007), action)])
            except:
                pass
        if self.currentlist.skill.find(u'add') != -1:
            action = 'XBMC.RunPlugin(%s.add)' % u
            try:
                liz.addContextMenuItems([(__language__(30010), action)])
            except:
                pass
        if self.currentlist.skill.find(u'remove') != -1:
            action = 'XBMC.RunPlugin(%s.remove)' % u
            try:
                liz.addContextMenuItems([(__language__(30011), action)])
            except:
                pass
        for info_name, info_value in lItem.infos_dict.iteritems():
            if info_name.find(u'context.') != -1:
                try:
                    cItem = lItem
                    cItem.infos_dict[u'url'] = info_value
                    cItem.infos_dict[u'type'] = u'rss'
                    action = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?url=' + self.currentlist.codeUrl(cItem))
                    liz.addContextMenuItems([(info_name[info_name.find(u'.') + 1:], action)])
                except:
                    pass
            if info_name != u'url' and info_name != u'title' and info_name != u'icon' and info_name != u'type' and info_name != u'extension' and info_name.find(u'context.') == -1:
                try:
                    if info_name.find(u'.int') != -1:
                        liz.setInfo('Video', infoLabels = {capitalize(info_name[:info_name.find(u'.int')]): int(info_value)})
                    elif info_name.find(u'.once') != -1:
                        liz.setInfo('Video', infoLabels = {capitalize(info_name[:info_name.find(u'.once')]): info_value})
                    else:
                        liz.setInfo('Video', infoLabels = {capitalize(info_name): info_value})
                except:
                    pass
        xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = True, totalItems = totalItems)

    def purgeCache(self):
        for root, dirs, files in os.walk(cacheDir , topdown = False):
            for name in files:
                os.remove(os.path.join(root, name))

    def run(self):
        xbmc.log('VideoDevil running')
        try:
            self.handle = int(sys.argv[1])
            paramstring = sys.argv[2]
            if len(paramstring) <= 2:
                if addon.getSetting('hide_warning') == 'false':
                    dialog = xbmcgui.Dialog()
                    if not dialog.yesno(__language__(30061), __language__(30062), __language__(30063), __language__(30064), __language__(30065), __language__(30066)):
                        return
                log(
                    'Settings directory: ' + str(settingsDir) + '\n' +
                    'Cache directory: ' + str(cacheDir) + '\n' +
                    'Resource directory: ' + str(resDir) + '\n' +
                    'Image directory: ' + str(imgDir) + '\n' +
                    'Catchers directory: ' + str(catDir)
                )
                if not os.path.exists(settingsDir):
                    log('Creating settings directory ' + str(settingsDir))
                    os.mkdir(settingsDir)
                    log('Settings directory created')
                if not os.path.exists(cacheDir):
                    log('Creating cache directory ' + str(cacheDir))
                    os.mkdir(cacheDir)
                    log('Cache directory created')
                log('Purging cache directory')
                self.purgeCache()
                log('Cache directory purged')
                self.parseView(u'sites.list')
                del self.currentlist.items[:]
                xbmc.log('End of directory')
                xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))
            else:
                params = sys.argv[2]
                currentView = params[5:]
                log(
                    'currentView: ' +
                     urllib2.unquote(repr(currentView)).replace(u'&', u'\n'))
                if self.parseView(currentView) == 0:
                    xbmcplugin.endOfDirectory(int(sys.argv[1]))
                    log('End of directory')
        except Exception, e:
            if enable_debug:
                traceback.print_exc(file = sys.stdout)
            dialog = xbmcgui.Dialog()
            dialog.ok('VideoDevil Error', 'Error running VideoDevil.\n\nReason:\n' + str(e))