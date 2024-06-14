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
    return SortKey([[v for v in r if v != 0] for r in res])  # strip 0s

def _filtersame(dat, level):
    '''A kind of groupby, return first of every sequence with the sortkey
        up to the given level'''
    # anyopne want to refactor this to use groupby()?
    res = []
    acc = (0,)
    level -= 1
    for d in dat:
        if d[1][level] != acc:
            acc = d[1][level]
            res.append(d)
    return res

def _makegroupdict(dat, keyfunc):
    '''Create a dictionary for each sublist of dat keyed by first
        in sublist. Used to collect subgroups with the same primary
        key keyed by the first in the sublist.'''
    res = {}
    for k, t in groupby(dat, keyfunc):
        d = list(t)
        res[d[0][0]] = d
    return res

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
            base = unescape(bits[0])
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
                self[key] = CollElement(base, l)
                self[key].order = (n,i)
                if prefix:
                    self[key].prefix = prefix
                    prefix = ""
                if expstr:
                    self[key].exp = expstr
                base = key

    def __setitem__(self, key, val):
        if key in self:
            raise KeyError("key {} already exists in collation with value {}".format(key, self[key]))
        dict.__setitem__(self, key, val)

    def _setSortKeys(self):
        '''Calculates tailored sort keys for everything in this collation'''
        if len(self) > 0 :
            inc = 1. / pow(10, int(log10(len(self)))+1)
            for v in sorted(self.values(), key=lambda x:x.order):
                v.expand(self, self.ducet)
                v.sortkey(self, self.ducet, inc)

    def asICU(self, alphabet, wrap=0, withkeys=False, ordering=lambda x:x[1].shortkey): 
        # needs fix to factor in characters coming before 'a' syntax, see llu.xml in sldr for an example of what that's supposed to look like. this needs to apply to all strengths of sorting
        """Returns ICU tailoring syntax of this Collation"""
        self._setSortKeys()
        lastk = None
        res = ""
        loc = 0
        eqchain = None
        beforea = True
        skip = []
        for k, v in sorted(self.items(), key=ordering):
            k = k.rstrip()
            if v.prefix:
                res += v.prefix
            if 'a' in alphabet and alphabet.index('a') != 0 and 'a' in self.keys() and beforea:
                loc = len(res) + 1
                for y, z in sorted(self.items(), key=ordering):
                    skip.append(y)
                    if y == 'a':
                        beforelvl = z.level
                    if y == 'A':
                        break
                res += "\n&[before " + str(beforelvl) + "]a "
                res += ("<<<"[:beforelvl]) + " "
                for i in range(alphabet.index('a')):
                    res += alphabet[i] + " "
                    if i == (alphabet.index('a') - 1):
                        continue
                    elif alphabet[i] in skip or i == 0: 
                        newlvl = None
                        for y, z in sorted(self.items(), key=ordering):
                            if z.base == alphabet[i]:
                                newlvl = z.level
                                res += ("<<<"[:newlvl]) + " "
                                break
                        if newlvl == None: 
                            res += "< "
                    elif alphabet[i].islower() and alphabet[i].upper() == alphabet[i+1]:
                        res += "<<< "
                    else:
                        res += "< "
                beforea = False
            if k in skip:
                continue
            if v.base != lastk and v.base != eqchain:
                loc = len(res) + 1
                res += "\n&" + escape(v.base)
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

    def _stripoverlaps(self, a_arg, b_arg):
        '''Given two sorted lists of (k, sortkey(k)) delete from this
            collation any k that is not inserted into the first list.
            I.e. only keep things inserted into the ducet sequence'''
        a = [k[0] for k in a_arg]
        b = [k[0] for k in b_arg]
        if len(a) > 0 and len(b) > 0:
            s = SequenceMatcher(a=a, b=b)
            for g in s.get_opcodes():
                if g[0] == 'insert' or g[0] == 'replace': continue
                for i in range(g[3], g[4]):
                    # delete if we have the element
                    #   and the primary sortkey lengths are different
                    if b[i] in self:
                        # old 'and' kept just in case it's needed, but currently breaks some files : and len(a_arg[g[1]+i-g[3]][1][0]) == len(b_arg[i][1][0]):
                        if b[i] == 'a' and b_arg[i][1][0][0] > a_arg[g[1]+i-g[3]][1][0][0]:
                            continue
                        del self[b[i]]

    def minimise(self, alphabet): 
        '''Minimise a sort tailoring such that the minimised tailoring
            functions the same as the unminimised tailoring for the
            strings in alphabet (e.g. main+aux exemplars)'''
        self._setSortKeys()
        # create (k, sortkey(k)) for the alphabet from the ducet and from the tailored
        base = sorted([(x, ducetSortKey(self.ducet, x)) for x in alphabet if x in self.ducet], key=lambda x: x[1])
        this = sorted([(x, ducetSortKey(self.ducet, x, extra=self)) for x in alphabet], key=lambda x: x[1])
        # strip down to only primary orders
        basep = _filtersame(base, 1)
        thisp = _filtersame(this, 1)
        # Remove any non-inserted elements
        self._stripoverlaps(basep, thisp)

        # dict[primary] = list of (k, sortkey(k)) with same primary as primary
        bases = _makegroupdict(base, lambda x:x[1][0])
        thiss = _makegroupdict(this, lambda x:x[1][0])
        for k, v in thiss.items():
            # no subsorting then ignore, if primary is tailored then all subsorts are tailored too
            if len(v) == 1 or k in self:
                continue
            # remove any non-inserted subsorts in the subsequences
            try:
                self._stripoverlaps(bases[k][1:], v[1:])
            except:
                for i in range(len(v)):
                    try:
                        altk = v[i][0]
                        self._stripoverlaps(bases[altk][1:], v[0:i, i+1:])
                    except:
                        continue

    def getSortKey(self, s):
        keys = SortKey()
        inc = 1. / pow(10, int(log10(len(self)+1)))
        for c in self.itemise(s):
            keys.append(ducetSortKey(self.ducet, c, extra=self))
        for i in range(3):
            if not len(keys[i]):
                keys[i] = [100000]
        return keys

    def itemise(self, s):
        curr = ""
        for c in s:
            if curr+c not in self and curr+c not in self.ducet:
                yield curr
                curr = ""
            curr += c
        yield curr

    def convertSimple(self, valueList):
        sortResult = []
        alphabet = []
        simple = True
        simplelist = list("abcdefghijklmnopqrstuvwxyz'")
        if len(valueList) > 0 :
            currBase = None
            for value in valueList :
                spaceItems = value.split(' ')
                if len(spaceItems) == 2 and spaceItems[0].lower() == spaceItems[1].lower():
                    # Kludge: deal with a limitation of Paratext. Since these items are case equivalent, the user probably
                    # intended x/X rather than x X and was not permitted by Paratext.
                    spaceItems = ["{}/{}".format(*spaceItems)]
                sortSpecItems = []
                spaceSep = "&"
                prevSlashItems = None
                currLevel = 1
                for spaceItem in spaceItems :
                    slashItems = spaceItem.split('/')
                    # Kludge to handle something like xX which should really be x/X
                    if len(slashItems) == 1 and len(slashItems[0]) > 1 and len(slashItems[0]) < 10:
                        s = slashItems[0]
                        slashSet = set()
                        if sum(1 if c.lower() == c else 0 for c in s) == len(s):
                            for i in range(2 ** len(s)):
                                slashSet.add("".join(c.upper() if (i & (1 << j)) != 0 else c for j,c in enumerate(s)))
                            slashSet.remove(s)
                            slashItems.extend(slashSet)
                    #slashItems.sort(key=ducet.keyfn(ducetDict, 3))
                    if simple:
                        if not len(simplelist) or slashItems[0] != simplelist.pop(0):
                            simple = False
                    for s in slashItems:
                        if currBase is not None:
                            try:
                                self[s] = CollElement(currBase, currLevel)
                            except KeyError:
                                continue
                        currLevel = 3
                        currBase = s
                        alphabet.append(s)
                    currLevel = 2
        return alphabet if not simple else None


class CollElement(object):

    def __init__(self, base, level):
        self.base = base
        self.level = level
        self.exp = ""
        self.prefix = ""
        self.shortkey = ""
        self.order = (0,)

    def __repr__(self):
        res = ">>>>"[:self.level] + self.base
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
        
    def sortkey(self, collations, ducetDict, inc):
        if hasattr(self, 'key'):
            return self.key
        self.key = ducetSortKey(ducetDict, self.base)   # stop lookup loops
        b = collations.get(self.base, None)
        if b is not None and b.order <= self.order:
            b.sortkey(collations, ducetDict, inc)
            basekey = b.shortkey.copy()
        else:
            basekey = self.key.copy()
        if self.level < 4 :
            basekey[self.level-1][-1] += inc
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

if __name__ == '__main__':
    import sys
    coll = Collation()
    if len(sys.argv) > 1:
        coll.parse(sys.argv[1])
        alphabet = "a b c d e f g h i j k l m n o p q r s t u v w x y z".split()
        alphabet += coll.keys()
        coll.minimise(alphabet)
        print(coll.asICU())
