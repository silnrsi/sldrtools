#!/usr/bin/env python3

import argparse, os, json, sys
from sldr.ldml import Ldml
from numpy import ndarray
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier
from langtag import lookup, langtag
from itertools import combinations

def fontid(s, feat=""):
    #return s.replace(" ", "").lower() + "|" + " ".join(sorted([f for f in feat.split() if not f.endswith("=0")]))
    return s + "|" + " ".join(sorted([f for f in feat.split() if not f.endswith("=0")]))

class Classifier:
    """ Creates a decision tree from a dict of key values. The key is split
        into feature values. """
    def __init__(self, mapdata):
        self.mapdata = mapdata
        self.X, self.Y = zip(*map(self._splitkey, mapdata.items()))
        self.ohe = OneHotEncoder()
        self.ohe.fit(self.X)
        m = self.ohe.transform(self.X)
        self.X_ohe = m if isinstance(m, ndarray) else m.toarray()
        self.feat_names = self.ohe.get_feature_names_out(["lang", "scr", "reg"])
        self.clf = DecisionTreeClassifier()
        self.clf.fit(self.X_ohe, self.Y)
        indices = self.clf.apply(self.X_ohe)
        self.values = {indices[i]: self.Y[i] for i in range(len(self.X_ohe))}

    def _splitkey(self, x):
        """ Splits according to a language tag. Subclass and override
            appropriately """
        l = langtag(x[0])
        k = [l.lang or "", l.script or "", l.region or ""]
        return (k[:3], x[1])

    def treerules(self, node, feats):
        """ Yields (dict value, list of features) for each leaf in the tree """
        newfeat = self.clf.tree_.feature[node]
        left = self.clf.tree_.children_left[node]
        right = self.clf.tree_.children_right[node]
        val = self.values.get(node, None)
        if left == -1:
                yield ((val, feats))
        else:
            yield from self.treerules(left, feats)
        if left == right:
            return
        #newf = self.ohe.inverse_transform([self.X_ohe[newfeat]])
        feats = feats[:] + [self.feat_names[newfeat]]
        if right == -1:
                yield ((val, feats))
        else:
            yield from self.treerules(right, feats)

    def simplerules(self):
        """ Convert a decision tree into a set of rules that test features and
            values. dict(result: list(match)) each match is a
            dict(feature: list(values)). """
        already = {}
        vals = {}
        skipcount = 0
        for v, s in self.treerules(0, []):
            f = [a for a in s if a.split("_")[1] != ""]
            x = frozenset(f)
            # test to see if this or a lesser rule gives the same result
            skipme = None
            for i in range(len(f)-1, 0, -1):
                for y in combinations(f, i):
                    curr = already.get(frozenset(y), None)
                    if curr == v:
                        skipme = False if skipme is False else True
                    elif curr is not None:
                        skipme = False
                if skipme is False:
                    break
            if skipme:
                skipcount += 1
                continue
            already[x] = v

            # can we merge this rule with another giving the same result?
            if v in vals:
                best = None
                bestscore = -1
                for k in vals[v]:
                    # different length so clearly can't match
                    if len(f) != len(k):
                        continue
                    # find the key that has a list of match values
                    mindex = None
                    for i, kx in k.items():
                        if len(kx) > 1:
                            mindex = i
                            break
                    # how many match values align?
                    score = 0
                    for vl in f:
                        i, vv = vl.split("_")
                        if i == mindex:
                            if vv in k[i]:
                                score += 1
                        elif i not in k:
                            score = -1
                            break
                        elif vv == k[i][0]:
                            score += 1
                        elif mindex is None:
                            mindex = i
                        else:
                            score = -1
                            break
                    # if one difference or perfect match then keep the score
                    if score < len(k) - 1:
                        score = -1
                    if score > bestscore:
                        bestscore = score
                        best = k
                # found a rule worth merging into
                if bestscore > -1:
                    assert best is not None
                    for i, vv in dict((x.split("_") for x in f)).items():
                        if vv not in best[i] and vv != "":
                            best[i].append(vv)
                    continue
            # add a new rule for this result
            vals.setdefault(v, []).append({vv.split("_")[0]:[vv.split("_")[1]] for vv in f})
        print(f"Skipped {skipcount}")
        return vals

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("indir",help="Directory of files to process")
    parser.add_argument("-o","--outfile",default="fontrules.json",help="Output fontrules.json")
    parser.add_argument("--intermediate",help="Output interim results")
    parser.add_argument("--min",action="store_true",help="Use a minimal tag rather than maximal")
    parser.add_argument("-R","--resultsort",action="store_true",help="Sort by results, which is inaccurate but helpful for review")
    parser.add_argument("-L","--literal",action="store_true",help="Unsorted straight from the tree")
    args=parser.parse_args()

    jobs = []
    if os.path.isdir(args.indir):
        for dp, dn, fn in os.walk(args.indir):
            for f in fn:
                if f.endswith('.xml'):
                    jobs.append(os.path.join(dp, f))
        ltagmap = {}
    else:
        with open(args.indir) as inf:
            ltagmap = json.load(inf)

    print(f"{len(jobs)} files to test")
    for j in jobs:
        l = Ldml(j)
        langn = l.find("identity/language")
        if langn is None:
            continue
        lang = langn.get("type", None)
        inf = l.find("identity/special/sil:identity")
        if inf is None:
            continue
        script = inf.get("script")
        region = inf.get("defaultRegion")
        ltag = "{}-{}-{}".format(lang, script, region).lower().replace("-none", "")
        try:
            ltagset = lookup(ltag)
        except KeyError:
            continue
        ltag = str(ltagset.tag if args.min else ltagset.full).lower()

        fallback = None
        for f in l.findall("special/sil:external-resources/sil:font"):
            t = f.get("types", "")
            if t == "":
                fallback = fontid(f.get("name"), f.get("features", ""))
            elif "default" in t:
                ltagmap[ltag] = fontid(f.get("name"), f.get("features", ""))
                break
        else:
            if fallback is not None:
                ltagmap[ltag] = fallback

    print(f"Found {len(ltagmap)} entries")
    if args.intermediate:
        with open(args.intermediate, "w") as outf:
            json.dump(ltagmap, outf)

    #invltagmap = {}
    #for k, v in ltagmap.items():
    #    invltagmap.setdefault(v, []).append(k)
    #print(invltagmap)
    c = Classifier(ltagmap)
    vals = c.simplerules()

    if args.literal:
        for v, r in reversed(list(c.treerules(0, []))):
            print(f"{v} -> {r}")
        sys.exit(0)

    rules = []
    for k, v in vals.items():
        for r in v:
            results = k.split("|")
            rule = { "result" : {"fontid": results[0]}, "match": {}}
            if len(results) > 1 and len(results[1]):
                rule["result"]["features"] = results[1]
            for b, vals in sorted(r.items()):
                if not len(vals) or len(vals) == 1 and vals[0] == "":
                    continue
                rule["match"][b] = vals if len(vals) > 1 else vals[0]
            if len(rule["match"]):
                rules.append(rule)

    if args.resultsort:
        rules.sort(key=lambda x: (x["result"]["fontid"], x["result"].get("features", ""), -len(x["match"]),
                                x["match"].get("scr", [""])[0], x["match"].get("reg", [""])[0]))
    else:
        rules.sort(key=lambda x: (-len(x["match"]), x["result"]["fontid"], x["result"].get("features", ""),
                                x["match"].get("scr", [""])[0], x["match"].get("reg", [""])[0]))

    print(f"{len(rules)} rules")
    if args.outfile:
        with open(args.outfile, "w", encoding="utf-8") as outf:
            outf.write("[\n")
            for i, r in enumerate(rules):
                json.dump(r, outf, ensure_ascii=False)
                outf.write("\n" if i == len(rules) - 1 else ",\n")
            outf.write("]\n")

if __name__ == "__main__":
    main()