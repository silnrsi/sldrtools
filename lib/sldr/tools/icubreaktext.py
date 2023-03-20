#!/usr/bin/env python3

import icu
import argparse, sys, graphlib, re
from sldr.ldml_merge import flattenlocale, getldml

breaktypes = {
    'lb': ("LineBreak", icu.BreakIterator.createLineInstance), # type: ignore
    'gb': ("GraphemeClusterBreak", icu.BreakIterator.createCharacterInstance), # type: ignore
    'wb': ("WordBreak", icu.BreakIterator.createWordInstance), # type: ignore
    'sb': ("SentenceBreak", icu.BreakIterator.createSentenceInstance) # type: ignore
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile",help="Input text lines")
    parser.add_argument("-o","--outfile",help="Output results here")
    parser.add_argument("-t","--type",default="lb",help="Segmentation type [lb*, gb, wb, sb]")
    parser.add_argument("-l","--lang",help="Language sort rules to use")
    parser.add_argument("-d","--dir",help="Root of LDML tree to read the lang from")
    parser.add_argument("-F","--noflatten",action="store_true",help="Do not flatten the ldml file")
    parser.add_argument("-D","--debug",action="store_true",help="Say what we are doing")
    args = parser.parse_args()

    brk = None
    if args.dir is not None:
        if args.noflatten:
            doc = getldml(args.lang, [args.dir])
        else:
            doc = flattenlocale(args.lang, [args.dir])
            c = doc.find('./segmentations/segmentation[@type="{}"]'.format(breaktypes[args.type][0]))
            if c is None:
                print(f"Can't find segmentations in {args.lang}", file=sys.stderr)
            else:
                lines = []
                ts = graphlib.TopologicalSorter()
                vars = {}
                for var in c.findall('variables/variable'):
                    i = var.get('id')
                    vars[i] = var.text.strip()
                    ts.add(i)
                    for m in re.findall(r"(\$[a-zA-Z]+)", var.text):
                        ts.add(i, m)
                for k in ts.static_order():
                    lines.append("{}=[{}]".format(k, vars[k]))
                rules = list(c.findall('segmentRules/rule'))
                for r in sorted(rules, key=lambda x:float(x.get('id'))):
                    lines.append(r.text.strip())
                r = ";\n".join(lines) + ";\n"
                if args.debug:
                    print(r)
                brk = icu.RuleBasedBreakIterator(r) # type: ignore
    elif args.lang is not None:
        loc = icu.Locale.createFromName(args.lang) # type: ignore
        brk = breaktypes[args.type][1](loc)

    if brk is not None:
        if args.outfile is not None:
            outf = open(args.outfile, "w", encoding="utf-8")
        else:
            outf = sys.stdout

        with open(args.infile, encoding="utf-8") as inf:
            for data in inf.readlines():
                l = data.strip()
                brk.setText(l)
                last = 0
                res = []
                for b in brk:
                    res.append(l[last:b])
                    last = b
                outf.write("|".join(res) + "\n")

        if args.outfile is not None:
            outf.close()

if __name__ == "__main__":
    main()