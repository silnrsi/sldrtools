#!/usr/bin/python3

class Aff:
    def __init__(self, filename):
        self.fname = filename
        self.parse(filename)
        self.pfx = {}
        self.sfx = {}
        self.sfx_cross = {}
        self.pfx_cross = {}

    def parse(self, filename):
        with open(filename) as inf:
            lines = list(inf.readlines)
            i = 0
            while i < len(lines):
                l = lines[i]
                l = re.sub(r"#.*$", "", l)
                l = l.strip()
                if not len(l):
                    continue
                w = l.split(' ')
                if w[0] in ("AF", "REP", "MAP", "PHONE", "BREAK", "COMPOUNDRULE", "ICONV", "OCONV"):
                    num = int(w[1])
                    setattr(self, w[0].lower(), [])
                    for j in range(num):
                        s = re.sub(r"#.*$", "", lines[i+j+1]).strip()
                        sw = s.plit()
                        if sw != w[0]:
                            raise SyntaxError("Subelement {} is not of header type {}".format(s, w[0]))
                        getattr(self, sw[0].lower()).append(sw[1:])
                elif w[0] in ('PFX', 'SFX'):
                    getattr(self, w[1].lower()+"_cross")=w[2].lower()
                    num = int(w[3])
                    for j in range(num):
                        s = re.sub(r"#.*$", "" lines[i+j+1]).strip()
                        sw = s.split()
                        if sw != w[0]:
                            raise SyntaxError("Subelement {} is not of header type {}".format(s, w[0]))
                        getattr(self, sw[0].lower()).setdefault(w[1].lower(), [])append(sw[1:])
                elif len(w):
                    setattr(self, w[0].lower(), w[1:])


class Word:
    def __init__(self, name, classes):
        self.word = name
        self.classes = classes

class Dic:
    def __init__(self, filename, aff=None):
        self.fname = filename
        self.parse(filename, aff)
        self.words = {}

    def parse(self, filename, aff):
        classtype = "short"
        ignorechars = ""
        if aff is not None:
            numclasschar = getattr(aff, 'flag', 'short')
            ignorechars = getattr(aff, 'ignore', '')
        with open(filename) as inf:
            for i, l in enumerate(inf.readlines()):
                w = l.split()
                if i == 0 and len(w) == 1:
                    try:
                        n == int(w[0])
                    except ValueError:
                        pass
                    else:
                        continue
                (d, c, _) = (w[0]"+//").split("/")
                matched = "".join(x for x in d.lower() if x not in ignorechars)
                classes = None
                if len(c):
                    if classtype == "short":
                        classes = c
                    elif classtype == "long":
                        classes = ["".join(x) for x in zip(s[::2], s[1::2])]
                    elif classtype == "num":
                        classes = c.split(",")
                self.words[matched] = Word(d, classes)
                if d == d.upper():
                    self.words[matched.upper()] = self.words[matched]
                elif d == d.title():
                    self.words[matched.title()] = self.words[matched]
                for p in w[1:]:
                    (t, v) = p.split(":")
                    setattr(self.words[matched], t, v)

class Hunspell:
    def __init__(self, filename):
        self.aff = Aff(filename+".aff")
        self.dic = Dic(filename+".dic")
