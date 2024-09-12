#!/usr/bin/env python3

import re, copy, os
import unicodedata as ud
from math import log10
from itertools import groupby, zip_longest
from difflib import SequenceMatcher

def escape(s, allchars=False):
    '''Turn normal Unicode into escaped tailoring syntax'''
    res = ""
    escs = '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~'
    lastbase = False
    for k in s:
        if k in escs:
            res += "\\" + k
            continue
        elif k == "'":
            res += k + k
            continue
        i = ord(k)
        if 32 < i < 127:
            res += k
        elif lastbase or not ud.category(k).startswith("M"):
            lastbase = True
            res += k
        elif allchars and i > 0xFFFF:
            res += '\\U' + ("00000000" + (hex(i)[2:]))[-8:]
        elif allchars:
            res += '\\u' + ("0000" + (hex(i)[2:]))[-4:]
        else:
            res += k
    return res

def unescape(s):
    '''Parse tailoring escaped characters into normal Unicode'''
    s = re.sub(r'(?:\\U([0-9A-F]{8})|\\u([0-9A-F]{4}))', lambda m: chr(int(m.group(m.lastindex), 16)), s, re.I)
    s = re.sub(r'\\(.)', r'\1', s)
    s = s.replace("''", "'")
    return s

def ducetSortKey(d, k, extra=None):
    '''Turn a sequence of sort keys for the given string into a single
        sort key.'''
    res = [[], [], []]
    i = len(k)
    singlechar = False
    if len(k) == 1:
        singlechar = True  
    while i > 0:
        try:
            if extra and k[:i] in extra:
                key = extra[k[:i]].key
            else:
                key = list(zip(*d[k[:i]]))
        except KeyError:
            i -= 1
            continue
        res = [res[j] + list(key[j]) for j in range(3)]
        k = k[i:]
        i = len(k)
    if singlechar:
        return SortKey([[v for v in r] for r in res])  # don't strip 0s if the only item in the string features a zero
    return SortKey([[v for v in r if v != 0] for r in res])  # strip 0s

def _stripzero(l):
    res = l[:]
    while len(l):
        if res[-1] == 0:
            res.pop()
        else:
            break
    return res

def cmpKey(a, b, level):
    for i in range(level):
        if _stripzero(a[i]) != _stripzero(b[i]):
            return False
    return True 

def lenKey(a, b, level):
    for i in range(level):
        if len(_stripzero(a[i])) != len(_stripzero(b[i])):
            return False
    return True

__moduleDucet__ = None  # cache the default ducet
def readDucet(path="") :
    if not path:
        global __moduleDucet__
        if __moduleDucet__ is not None:
            return __moduleDucet__
        ducetpath = os.path.join(os.path.abspath(os.path.dirname(__file__)), "allkeys.txt")
    else:
        ducetpath = path

    result = {}
    keyre = re.compile(r'([0-9A-F]{4})', re.I)
    valre = re.compile(r'\[[.*]([0-9A-F]{4})\.([0-9A-F]{4})\.([0-9A-F]{4})\]', re.I)

    try :
        with open(ducetpath, 'r') as f :
            for contentLine in f.readlines():
                parts = contentLine.split(';')
                if len(parts) != 2 or parts[0].strip().startswith("@"):
                    continue
                key = "".join(chr(int(x, 16)) for x in keyre.findall(parts[0]))
                vals = valre.findall(parts[1])
                result[key] = tuple(tuple(int(x, 16) for x in v) for v in vals)
    except :
        print("ERROR: unable to read DUCET data in allkeys.txt")
        return {}
    if not path:
        __moduleDucet__ = result
    return result


class SortKey(list):
    """ List of subkeys for each level. Each subkey is a list of values """
    def append(self, other):
        self[:] = self + other

    def __add__(self, other):
        return [sum(z, []) for z in zip_longest(self, other, fillvalue=[])]

    def cmp(self, other):
        ''' Returns the level of the difference and negative if self < other '''
        for i, z in enumerate(zip_longest(self, other)):
            if z[0] < z[1]:
                return -(i+1)
            elif z[0] > z[1]:
                return i+1
        return 0

    def __lt__(self, other):
        return self.cmp(other) < 0

    def __gt__ (self, other):
        return self.cmp(other) > 0

    def __eq__(self, other):
        return self.cmp(other) == 0

    def __ge__(self, other):
        return self.cmp(other) >= 0

    def __le__(self, other):
        return self.cmp(other) <= 0

    def __iadd__(self, other):
        return self.append(other)

    def __ne__(self, other):
        return self.cmp(other) != 0

    def copy(self):
        return self.__class__([v.copy() for v in self])

    def __hash__(self):
        return hash(tuple(tuple(x) for x in self))


class Collation(dict):
    """ Dict keyed by sort element string with value a CollElement of the base 
        and corresponding level """

    def __init__(self, ducetDict=None):
        if ducetDict is None:
            ducetDict = readDucet()
        self.ducet = ducetDict

    def parse(self, string):
        """Parse LDML/ICU sort tailoring"""
        prefix = ""
        string = re.sub(r'^#.*$', '', string, flags=re.M)
        for n, run in enumerate(string.split('&')):
            bits = [x.strip() for x in re.split(r'([<=]+)', run)]
            m = re.match(r"^\s*&?\s*(?:\[before\s+(\d)\s*\]\s*)?(.*?)\s*$", unescape(bits[0]))
            if m:
                base = m.group(2)
                before = 0
                if m.group(1):
                    before = int(m.group(1))
            else:
                continue
            for i in range(1, len(bits), 2):
                s = re.sub(r'\s#.*$', '', bits[i], flags=re.M)
                if s == '=': l = 4
                else:
                    l = s.count('<')
                k = re.sub(r'\s#.*$', '', bits[i+1], flags=re.M)
                key = unescape(k)
                exp = key.find("/")
                expstr = ""
                if exp > 0:
                    expstr = key[exp+1:].strip()
                    key = key[:exp].strip()
                else:
                    exp = None
                while key in self:
                    key += " "
                self[key] = CollElement(base, l, before)
                self[key].order = (n,i)
                if prefix:
                    self[key].prefix = prefix
                    prefix = ""
                if expstr:
                    self[key].exp = expstr
                base = key
                before = 0

    def __setitem__(self, key, val):
        if key in self:
            raise KeyError("key {} already exists in collation with value {}".format(key, self[key]))
        dict.__setitem__(self, key, val)

    def _setSortKeys(self, force=False):
        '''Calculates tailored sort keys for everything in this collation'''
        if len(self) > 0 :
            numbefores = sum((1 for c in self.values() if c.before > 0))
            inc = 1. / pow(10, int(log10((numbefores + 1) * len(self)))+1)
            for v in sorted(self.values(), key=lambda x:x.order):
                # v.expand(self, self.ducet)
                v.sortkey(self, self.ducet, inc, (1./(numbefores+1)), force=force)

    def asICU(self, wrap=0, withkeys=False, ordering=lambda x:x[1].shortkey): 
        # needs fix to factor in characters coming before 'a' syntax, see llu.xml in sldr for an example of what that's supposed to look like. this needs to apply to all strengths of sorting
        """Returns ICU tailoring syntax of this Collation"""
        self._setSortKeys()
        lastk = None
        res = ""
        loc = 0
        eqchain = None
        lastbefore = 0
        skip = []
        for k, v in sorted(self.items(), key=ordering):
            k = k.rstrip()
            if v.prefix:
                res += v.prefix
            if k in skip:
                continue
            if v.base != lastk and v.base != eqchain or v.before != lastbefore:
                loc = len(res) + 1
                res += "\n&" + (f"[before {v.before}]" if v.before else "") + escape(v.base)
                eqchain = None
            if wrap and len(res) - loc > wrap:
                res += "\n"
                loc = len(res)
            else:
                res += " "
            if v.level == 4:
                res += "= "
                if eqchain is None:
                    eqchain = v.base
            else:
                res += ("<<<"[:v.level]) + " "
                eqchain = None
            res += escape(k)
            if v.exp:
                res += "/" + escape(v.exp)
            if withkeys:
                res += str(v.key) + "|" + str(v.shortkey) + "(" + str(v.order) + ")"
            lastk = k
        return res[1:] if len(res) else ""

    def minimise(self):
        self._setSortKeys()
        allkeys = set(self.keys()) | set([v.base for v in self.values() if v.base is not None])
        kducet = {k: ducetSortKey(self.ducet, k) for k in allkeys}
        korder = sorted(kducet.keys(), key=lambda k:kducet[k])
        for v in self.values():
            v.inDucet = None

        def parents(key, level):
            # return all the keys that immediately precede key in the ducet at the given level
            currd = kducet[key]
            curr = korder.index(key)
            curr -= 1
            if curr < 0:
                return []
            based = kducet[korder[curr]]
            if cmpKey(based, currd, level) or not lenKey(based, currd, level):
                return []
            res = [korder[curr]]
            while curr > 0:
                curr -= 1
                if cmpKey(korder[curr], based, level):
                    break
                res.append(korder[curr])
            return res

        def isInDucet(ce, key):
            if ce.inDucet is not None:
                return ce.inDucet
            if ce.base is None:
                res = True
            # a possible reset point
            elif ce.level == 1 or ce.base not in self or isInDucet(self[ce.base], ce.base):
                res = ce.base in parents(key, ce.level) and not ce.before
            else:
                res = False
            ce.inDucet = res
            return res

        # calculate all the ducet states first
        for k, v in list(self.items()):
            isInDucet(v, k)
        # then delete them
        for k, v in list(self.items()):
            if isInDucet(v, k):
                del self[k]

    def getSortKey(self, s):
        return ducetSortKey(self.ducet, s)

    def itemise(self, s):
        curr = ""
        for c in s:
            if curr+c not in self and curr+c not in self.ducet:
                yield curr
                curr = ""
            curr += c
        yield curr

    def convertSimple(self, valueList, strict=False):
        sortResult = []
        simplelist = list("abcdefghijklmnopqrstuvwxyz'")
        if len(valueList) > 0 :
            currBase = None
            for value in valueList :
                spaceItems = value.split(' ')
                if len(spaceItems) == 2 and spaceItems[0].lower() == spaceItems[1].lower():
                    # Kludge: deal with a limitation of Paratext. Since these items are case equivalent, the user probably
                    # intended x/X rather than x X and was not permitted by Paratext.
                    spaceItems = ["{}/{}".format(*spaceItems)]
                currLevel = 1
                for spaceItem in spaceItems :
                    slashItems = [s.strip() for s in spaceItem.split('/')]
                    # Kludge to handle something like x which should really be x/X and ngy/NGY -> ngy/Ngy/NGy/NGY
                    if not strict and slashItems[0].lower() == slashItems[0] and (
                            (len(slashItems[0]) > 1 and all((s.lower() == slashItems[0] for s in slashItems[1:]))) \
                            or len(slashItems) == 1):
                        s = slashItems[0]
                        for i in range(1, len(s)+1):
                            n = s[:i].upper() + s[i:].lower()
                            if n not in slashItems:
                                slashItems.append(n)
                        slashItems = [s] + sorted(slashItems[1:], reverse=True) # get capitals first
                    for s in slashItems:
                        if len(s) == 0:
                            continue
                        if currBase is not None:
                            try:
                                self[s] = CollElement(currBase, currLevel, 0)
                            except KeyError:
                                continue
                        currLevel = 3
                        currBase = s
                    currLevel = 2
        self._insertBefore()

    def _insertBefore(self):
        self._setSortKeys()
        outlist = sorted(self.keys(), key=lambda k:self[k].key)
        inlist = sorted(set(self.keys()), key=lambda k:ducetSortKey(self.ducet, k))
        for m in SequenceMatcher(a=inlist, b=outlist).get_opcodes():
            if m[0] in ("replace", "insert") and m[4] < len(outlist):
                newbase = outlist[m[4]]
                bcoll = self[outlist[m[3]]]
                if bcoll.base in self:
                    ocoll = self[bcoll.base]
                    ocoll.before = 1
                    ocoll.base = newbase
                else:
                    ocoll = CollElement(newbase, 1, 1)
                    self[bcoll.base] = ocoll
                del self[newbase]
            break
        self._setSortKeys(force=True)


class CollElement(object):

    def __init__(self, base, level, before):
        self.base = base
        self.level = level
        self.before = before
        self.exp = ""
        self.prefix = ""
        self.shortkey = ""
        self.order = (0,)
        self.inDucet = None

    def __repr__(self):
        res = ">>>>"[:self.level] + self.base
        res += f"[before {self.before}]" if self.before else ""
        if self.exp:
            return repr(res + "/" + self.exp)
        else:
            return repr(res)

    def expand(self, collations, ducetDict):
        if self.exp:
            return
        for i in range(len(self.base), 0, -1):
            if self.base[:i] in collations or self.base[:i] in ducetDict:
                l = i
                break
        else:
            return
        self.exp = self.base[l:]
        self.base = self.base[:l]
        
    def sortkey(self, collations, ducetDict, inc, beforeshift, force=False):
        if hasattr(self, 'key') and not force:
            return self.key
        self.key = ducetSortKey(ducetDict, self.base)   # stop lookup loops
        b = collations.get(self.base, None)
        if b is not None and b.order <= self.order:
            b.sortkey(collations, ducetDict, inc, beforeshift, force=force)
            basekey = b.shortkey.copy()
        else:
            basekey = self.key.copy()
        # Update the copied base SortKey to immediately follow the base
        if self.level < 4 :
            basekey[self.level-1][-1] += inc if not self.before or self.before != self.level else -beforeshift 
        if not self.exp and b is not None and b.exp:
            self.exp = b.exp
        if self.exp:
            expkey = ducetSortKey(ducetDict, self.exp, extra=collations)
            if expkey > basekey:
                self.shortkey = expkey.copy() + SortKey([[1]])
            else:
                self.shortkey = basekey.copy()
            basekey.append(expkey)
        else:
            self.shortkey = basekey
        self.key = basekey
        return basekey


def main():
    import sys
    coll = Collation()
    if len(sys.argv) > 1:
        if "<" not in sys.argv[1]:
            rules = [r.strip() for r in sys.argv[1].split(";")]
            coll.convertSimple(rules)
        else:
            coll.parse(sys.argv[1])
        coll.minimise()
        print(coll.asICU())

if __name__ == '__main__':
    main()
