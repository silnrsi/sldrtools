#!/usr/bin/env python3

import argparse, codecs, sys
from sldr.collation import Collation, CollElement

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile",help="Input ICU tailoring")
    parser.add_argument("-o","--output",help="Output ICU tailoring")
    parser.add_argument("-a","--alphabet",help="list of chars to minimise against")
    parser.add_argument("-k","--keys",action="store_true",help="output all keys!")
    parser.add_argument("--adddot",action="store_true",help="Add \u1037 rules")
    args = parser.parse_args()

    with codecs.open(args.infile, encoding="utf-8") as f :
        tailor = "".join(f.readlines())

    coll = Collation()
    coll.parse(tailor)
    if args.alphabet :
        alpha = args.alphabet.split()
        alpha += coll.keys()
        coll.minimise(alpha)
    if 0:
        coll._setSortKeys()
        equivs = {}
        for k, v in sorted(coll.items(), key=lambda x:x[1].shortkey):
            if v.exp:
                equivs.setdefault((v.exp, v.level), []).append((k, v))
        for k, v in equivs.items():
            if len(v) <= 1:
                continue
            revs = list(reversed(v))
            last = revs[0]
            for r in revs[1:]:
                r[1].base = last[0]
                r[1].level = k[1] + 1 if k[1] < 4 else 4
                last = r
    coll._setSortKeys()
    if args.adddot:
        count = 0
        # Make this a list, since coll is modified in the loop body
        for k, v in list(coll.items()):
            if k.rstrip().endswith("\u103A"):
                n = CollElement(k, 4)
                n.exp = "\u1037"
                n.order = tuple(list(v.order) + [1])
                n.key = v.key
                n.shortkey = v.shortkey
                key = k[:-1] + "\u1037" + k[-1]
                coll[key] = n
                count += 1
        print("Added {} rules".format(count))

    output = coll.asICU(wrap=80, withkeys=args.keys, ordering=lambda x:x[1].order)

    outf = codecs.open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    outf.write(output)
    outf.close()

if __name__ == "__main__":
    main()