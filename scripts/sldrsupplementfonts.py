import sys, traceback
import codecs, copy
import os, re, argparse
import logging
import multiprocessing
from sldr.ldml import Ldml, draftratings, iterate_files

silns = {'sil' : "urn://www.sil.org/ldml/0.1" }
gendraft = draftratings.get('generated', 5)

lffUrls = {
    "Charis" : "charis",
    "Aboriginal Sans" : "aboriginalsans",
    "Abyssinica SIL" : "abyssinicasil",
    "Akatab" : "akatab",
    "Alkalami" : "alkalami",
    "Andika" : "andika",
    "Annapurna SIL" : "annapurnasil",
    "Annapurna SIL Nepal" : "annapurnasilnepal",
    "Awami Nastaliq" : "awaminastaliq",
    "BJCree" : "bjcree",
    "Dai Banna SIL" : "daibannasil",
    "Doulos SIL" : "doulossil",
    "Dukor" : "dukor",
    "Ezra SIL" : "ezrasil",
    "Galatia SIL" : "galatiasil",
    "Gentium" : "gentium",
    "Harmattan" : "harmattan",
    "Badami" : "badami",
    "Lateef" : "lateef",
    "Lisu Bosa" : "lisubosa",
    "Mingzat" : "mingzat",
    "Khmer Mondulkiri" : "khmermondulkiri",
    "Namdhinggo" : "namdhinggosil",
    "Nokyung" : "nokyung",
    "Noto Sans Mongolian" : "notosansmongolian",
    "Noto Sans Sundanese" : "notosanssundanese",
    "Nuosu SIL" : "nuosusil",
    "Padauk" : "padauk",
    "Payap Lanna" : "payaplanna",
    "Scheherazade New" : "scheherazadenew",
    "Sapushan" : "sapushan",
    "Shimenkan" : "shimenkan",
    "Sophia Nubian" : "sophianubian",
    "Tai Heritage Pro" : "taiheritagepro",
    "ThiruValluvarCTT" : "thiruvalluvar",
    "Khmer Busra": "khmerbusra",
    "Kay Pho Du": "kayphodu",
    "Surma": "surma",
    "Tagmukay": "tagmukay",
    "Japa Sans Oriya": "japasansoriya",
    "Sarabun":"sarabun",
    "Saysettha":"saysettha",
    "Jomolhari":"jomolhari"
}

notLffUrls = {
    #note: these links seem to lead to a read-only version of the noto fonts repo. in future, may shift so that these instead direct to lff versions of these links
    "Noto Sans Telugu": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf",
    "Noto Sans": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
    "Noto Serif Tibetan": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSerifTibetan/NotoSerifTibetan-Regular.ttf",
    "Noto Sans Thai": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansThai/NotoSansThai-Regular.ttf",
    "Noto Sans Malayalam": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf",
    "Noto Sans Syloti Nagri": "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansSylotiNagri/NotoSansSylotiNagri-Regular.ttf",
    "Noto Sans Kannada": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf",
    "Noto Serif Kannada": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSerifKannada/NotoSerifKannada-Regular.ttf"
}

fontgroups = {
    # fonts that should always appear in a script's options
    # add more later, but be careful! Other SIL fonts might not have the same feature cross-compatibility that CGA have 
    "Latn": ["Charis", "Gentium", "Andika"]
}


def processOneFile(fname, sldrPath):

    fpath = None
    ldml = None
    script = None
    fonts = None

    fpath = os.path.join(sldrPath, fname[0], fname)
    ldml = Ldml(fpath)
    # we have ldml file

    s = ldml.find('identity/script')
    i = ldml.root.find(".//identity/special/sil:identity", {v:k for k,v in ldml.namespaces.items()})
    if s is not None:
        script = s.text
    elif i is not None:
        script = i.get("script")

    # we have script of file

    fonts =  ldml.root.findall('special/sil:external-resources/sil:font', {v:k for k,v in ldml.namespaces.items()})

    #we have fonts of file

    def _addLink(font, fontElem):
        # copy pasted directly from dbl import script in wstools
        urlEl = ldml.addnode(fontElem, 'sil:url', returnnew=True)
        if font in lffUrls.keys():
            urlEl.text = "https://lff.api.languagetechnology.org/family/" + lffUrls[font]
            return False
        elif font in notLffUrls.keys():
            urlEl.text = notLffUrls[font]
            return False
        else:
            fontElem.remove(urlEl)
            return True
        
    # ^ that's a surprise tool that will help us later :)

    fontList = {}
    for fontElement in fonts:
        name = fontElement.get("name")
        features = fontElement.get("features")
        fontList[name]=[fontElement, features]

    # we have handy dict of fonts and their features 

    if script in fontgroups.keys():
        neededfonts = fontgroups[script]
        neededfeature = None
        newfont = None

        for font in neededfonts:
            if font in fontList.keys():
                neededfeature = fontList[font][1]
                    #note: this will fall apart if multiple fonts are listed with different features, but that's not supposed to happen anyway?
                
                #this bit is in case multiple of these fonts are already in there, need to add the new priority
                priority = fontList[font][0].get("types")
                if priority is None:
                    fontList[font][0].set("types", "default=2")
                pass
            else:
                newfont = ldml.ensure_path('special/sil:external-resources/sil:font[@name="{}"][@types="default=2"][@features="{}"]'.format(font, neededfeature))[0]
                _addLink(font, newfont)
                fontList[font] = newfont
                #we have now added the fonts that aren't there into the ldml file, along with the features and the priority
                #we've also given it its link child node
                #and we've added it to the font list we made earlier just in case (currently not necessary but again, just in case)

    ldml.normalise()
    ldml.save_as(fpath)
    #and now it has saved the new stuff to the actual file and all is right in the world :)


parser = argparse.ArgumentParser()
parser.add_argument("indir",help="Root of SLDR file tree")
parser.add_argument("-l","--ldml",help="ldml file identifier (without .xml)")
args = parser.parse_args()

if args.ldml:
    allfiles = [os.path.join(args.indir, args.ldml[0], args.ldml+".xml")]
else:
    allfiles = iterate_files(args.indir)

for file in allfiles:
    fname = os.path.splitext(os.path.basename(file))[0]+".xml"
    processOneFile(fname, args.indir)

    # run with :/mnt/c/Users/emily_roth/Documents/GitHub/SLDRTools$ python3 scripts/sldrsupplementfonts.py ../SLDR/sldr 