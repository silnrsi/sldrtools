#!/usr/bin/env python3

import re, copy, os
import unicodedata as ud
from math import log10
from itertools import groupby, zip_longest
from difflib import SequenceMatcher
from collections import UserDict

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

def ducetSortKey(d, k, extra=None, fn=None):
    '''Turn a sequence of sort keys for the given string into a single
        SortKey (array of 3 arrays)'''
    dlambda = lambda k: list(zip(*d.get(k, [])))
    if fn is None:
        fn = dlambda
    res = [[], [], []]
    i = len(k)
    singlechar = False
    if len(k) == 1:
        singlechar = True
    while i > 0:
        if extra and k[:i] in extra:
            key = extra[k[:i]].key
        else:
            key = fn(k[:i])
        if key is None or not len(key):
            if k[:i] in d:
                key = dlambda(k[:i])
        if key is None or not len(key):
            i -= 1
            continue
        try:
            res = [res[j]+list(key[j]) for j in range(3)]
        except IndexError:
            breakpoint()
        k = k[i:]
        i = len(k)
    if singlechar:
        return SortKey([[v for v in r] for r in res])  # don't strip 0s if the only item in the string features a zero
    return SortKey([[v for v in r if v != 0] for r in res])  # strip 0s

def stripzero(l):
    if l is None:
        return [[], [], []]
    res = list(l)[:]
    while len(res):
        if res[-1] == 0:
            res.pop()
        else:
            break
    return res

def cmpKey(a, b, level):
    if a is None or b is None or len(a) < level or len(b) < level:
        return False
    for i in range(level):
        if stripzero(a[i]) != stripzero(b[i]):
            return False
    return True 

def diffLevel(a, b):
    if a is None or b is None:
        return 0
    for i in range(3):
        x = stripzero(a[i])
        y = stripzero(b[i])
        if x < y:
            return (i + 1)
        elif x > y:
            return -(i + 1)
    return 4

def lenKey(a, b, level):
    for i in range(level):
        if len(stripzero(a[i])) != len(stripzero(b[i])):
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
    def add(self, other):
        if other is None:
            return self[:]
        return [a[0]+a[1] for a in zip_longest(self, other)]

    def append(self, other):
        self[:] = self.add(other)

    def __add__(self, other):
        return self.add(other)

    def cmp(self, other):
        ''' Returns the level of the difference and negative if self < other '''
        return diffLevel(other, self)
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


class Collation(UserDict):
    """ Dict keyed by sort element string with value a CollElement of the base 
        and corresponding level """

    def __init__(self, ducetDict=None):
        super().__init__()
        if ducetDict is None:
            ducetDict = readDucet()
        self.ducet = ducetDict
        self.issorted = False

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
        super().__setitem__(key, val)

    def _setSortKeys(self, force=False):
        '''Calculates tailored sort keys for everything in this collation'''
        if (not self.issorted or force) and len(self) > 0 :
            numbefores = sum((1 for c in self.values() if c.before > 0))
            inc = 1. / pow(10, int(log10((numbefores + 1) * len(self)))+1)
            for v in sorted(self.values(), key=lambda x:x.order):
                v.expand(self, self.ducet)
                v.sortkey(self, self.ducet, inc, (1./(numbefores+1)), force=force)
            self.issorted = True

    def cmpKeys(self, a, b, level):
        av = self.get(a, None)
        bv = self.get(b, None)
        if av is None or bv is None:
            return False
        return cmpKey(av.key, bv.key, level)

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
            if not self.cmpKeys(v.base, lastk, v.level) and v.base != eqchain or v.before != lastbefore:
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

    def asSimple(self, ordering=lambda x:x[1].shortkey):
        """ Creates simple collation specification """
        def getparents(v, level):
            lastb = v
            base = self.get(v, None)
            while base is not None and base.level == 3:
                lastb = base.base
                level = base.level
                base = self.get(base.base, None)
            if base is None or level == 1:
                return (lastb, lastb)
            second = lastb
            level = base.level
            while base is not None and base.level != 1:
                level = base.level
                lastb = base.base
                base = self.get(base.base, None)
            return (lastb, second)

        tree = {}
        lastk = None
        for k, v in sorted(self.items(), key=ordering):
            if v.level == 3:
                top, second = getparents(v.base, 3)
                tree.setdefault(top, {}).setdefault(second, []).append(k)
            elif v.level == 2:
                top, second = getparents(k, 2)
                if not stripzero(ducetSortKey(self.ducet, k)[0]):
                    top = ""
                tree.setdefault(top, {}).setdefault(second, [])
            elif v.level == 1:
                tree.setdefault(k, {})
            if v.base is not None and v.base not in self:
                if not stripzero(ducetSortKey(self.ducet, v.base)[0]):
                    tree.setdefault("", {}).setdefault(v.base, [])
                else:
                    tree.setdefault(v.base, {})
        lines = []
        for k, v in tree.items():
            s = [k]
            if len(tree[k]):
                if k in tree[k] and len(tree[k][k]):
                    s.append("/"+"/".join(tree[k][k]))
                for a in tree[k].keys():
                    if a == k:
                        continue
                    s.append(" "+a)
                    if len(tree[k][a]):
                        s.append("/"+"/".join(tree[k][a]))
            lines.append("".join(s))
        return "\n".join(lines)

    def getnext(self, k, charlist, direction=1):
        if k not in self:
            bk = ducetSortKey(self.ducet, k)
        else:
            bk = self[k].key
        if k not in charlist:
            for i, c in enumerate(charlist):
                if bk <= ducetSortKey(self.ducet, c):
                    break
        else:
            i = charlist.index(k)
        while (i > 0) if direction < 0 else (i < len(charlist) - 1):
            n = charlist[i + direction]
            if len(n) == 1:
                nb = self.get(n, None)
                if nb is not None and diffLevel(nb.key, bk) == -direction:
                    return n
            i += direction
        return None

    def sortKey(self, k):
        return ducetSortKey(self.ducet, k, fn=lambda k:self[k].key if k in self else None)

    def minimise(self, alphabet=[]):
        self._setSortKeys()
        alphabet = alphabet[:]
        chains = {}
        res = []
        allkeys = set()
        allsorts = sorted(self.keys(), key=lambda s:self[s].key)
        for k, v in self.items():
            if v.before or len(k) > 1:
                res.append((k, v))
            else:
                chains.setdefault(v.head(k, self), []).append((k, v))
        for k, v in chains.items():
            v.append((k, None))
        ksorts = set(sum(chains.values(), []))
        if not len(ksorts):
            return
        torder = [y[0] for y in sorted(ksorts, key=lambda x:ducetSortKey(self.ducet, x[0]))]
        korder = sorted(ksorts, key=lambda x:self.sortKey(x[0]))
        dorder = sorted(ksorts, key=lambda x:ducetSortKey(self.ducet, x[0]))
        klist = [a + (">>>>"[:x.level] if x is not None else ">") for a, x in korder]
        dlast = ducetSortKey(self.ducet, dorder[0][0])
        dlist = [dorder[0][0]+">"]
        for d in dorder[1:]:
            dn = ducetSortKey(self.ducet, d[0])
            dl = diffLevel(dlast, dn)
            dlist.append(d[0] + (">>>>"[:dl]))
            dlast = dn
        # dlist = [a + (">>>>"[:x.level] if x is not None else ">") for a, x in dorder]
        ops = SequenceMatcher(a=dlist, b=klist).get_opcodes()
        for op in ops:
            if op[0] in ('insert', 'replace'):
                res.extend(korder[op[3]:op[4]])
            #elif op[0] == "delete" and op[4] < len(korder) - 1:
            #    res.append(korder[op[4]])
        keeps = set()
        for a, x in res:
            if x is not None:
                keeps.update(x.all_children(a, x.level, self))
            else:
                keeps.add(a)
        for k in list(self.keys()):
            if k not in keeps:
                del self[k]

    def minimise_old(self):
        self._setSortKeys()
        allkeys = set(self.keys()) | set([v.base for v in self.values() if v.base is not None])
        order = sorted(self.keys(), key=lambda k:self[k].key)
        kducet = {k: ducetSortKey(self.ducet, k) for k in allkeys}
        korder = sorted(kducet.keys(), key=lambda k:kducet[k])
        for v in self.values():
            v.inDucet = None

        def parents(key, level, base=None):
            # return all the keys that immediately precede key in the ducet at the given level
            currd = kducet[key]
            if base is None:
                curr = korder.index(key)
                curr -= 1
            else:
                curr = korder.index(base)
            if curr < 0:
                return []
            based = kducet[korder[curr]]
            if cmpKey(based, currd, level) or not lenKey(based, currd, level):
                return []
            res = [korder[curr]]
            while curr > 0:
                curr -= 1
                if not cmpKey(kducet[korder[curr]], based, level):
                    break
                res.append(korder[curr])
            return res

        def isInDucet(ce, key):
            if ce.inDucet is not None:
                return ce.inDucet
            base = ce.base
            # allow strips for level 1 or level 2 for combining characters
            if ce.level == 1 or (ce.level == 2 and not stripzero(kducet[key][0])):
                while base in self and not isInDucet(self[base], base):
                    base = self[base].base
            if base is None:
                res = True
            # a possible reset point
            elif base not in self or isInDucet(self[base], base):
                res = base in parents(key, ce.level, base=None) and not ce.before
            else:
                res = False
            ce.inDucet = res
            return res

        def resetparent(v, k):
            b = v.base
            base = self.get(b, None)
            while base is not None and base.level > v.level:
                b = base.base
                base = self.get(b, None)
            v.base = b

        # calculate all the ducet states first
        for k, v in list(self.items()):
            isInDucet(v, k)
            resetparent(v, k)
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
                if not strict and len(spaceItems) == 2 and spaceItems[0].lower() == spaceItems[1].lower():
                    # Kludge: deal with a limitation of Paratext. Since these items are case equivalent, the user probably
                    # intended x/X rather than x X and was not permitted by Paratext.
                    spaceItems = ["{}/{}".format(*spaceItems)]
                s = spaceItems[0] if len(spaceItems) else None
                currLevel = 1
                if s is not None and not stripzero(ducetSortKey(self.ducet, s)[0]):
                    currLevel = 2
                elif currBase is None or not stripzero(ducetSortKey(self.ducet, currBase)[0]):
                    currBase = None
                for spaceItem in spaceItems :
                    slashItems = [s.strip() for s in spaceItem.split('/')]
                    # Kludge to handle something like x which should really be x/X and ngy/NGY -> ngy/Ngy/NGy/NGY
                    s = slashItems[0] if len(slashItems) else ""
                    if not strict and s.upper() != s.lower() and \
                            (s.lower() == s and len(s) > 1 and all((c.lower() == s.lower() for c in slashItems[1:]))) \
                            or (len(s) > 1 and len(slashItems) == 1):
                        slashItems = sorted(set([s[:i].upper() + s[i:].lower() for i in range(len(s)+1)]), reverse=True)
                    if len(slashItems) == 1 and len(s) == 1 and s.upper() != s.lower():
                        slashItems.append(s.upper() if s == s.lower() else s.lower())
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
        inlist = sorted(set((k for k in self.keys() if k in self.ducet)), key=lambda k:ducetSortKey(self.ducet, k))
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
        self.base = base            # parent element we are defined in relation to
        self.level = level          # following (or before) parent at what level
        self.before = before        # before level (should be the same a .level
        self.exp = ""               # expansion. Everything after the / (e in a/e)
        self.prefix = ""            # everything before the / in an expansion (a in a/e)
        self.shortkey = ""          # The key before expansion added (used by children)
        # self.key = None           # calculated sort key to interact with ducet (not the ducet key)
        self.order = (0,)           # order in defn [reset index, element index within reset]
        self.inDucet = None         # cache of whether we correspond to our position in the ducet
        self._head = None           # the top of our chain, that itself is not in the collation
        self.children = [[], [], []]    # children at each level

    def __repr__(self):
        res = ">>>>"[:self.level] + self.base
        res += f"[before {self.before}]" if self.before else ""
        if self.exp:
            return res + "/" + self.exp
        else:
            return res

    def head(self, k, coll):
        if self._head is not None:
            return self._head
        if self.base in coll:
            self._head = coll[self.base].head(self.base, coll)
            coll[self.base].children[self.level-1].append(k)
        #elif self.before:
        #    self._head = f"[before {self.before}]{self.base}"
        else:
            self._head = self.base
        return self._head

    def all_children(self, k, level, coll):
        res = []
        for i in range(2 if level == 1 else level, 4):
            res.extend(sum([coll[x].all_children(x, level, coll) for x in getattr(self, 'children', [] * 3)[i-1]], []))
        res.append(k)
        return res

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
        """ Calculate a SortKey """
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
                self.shortkey = expkey.copy() + SortKey([[1], [0], [0]])
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
