import sys, traceback
import codecs, copy
import os, re, argparse
import logging
import multiprocessing
from sldr.ldml import Ldml, draftratings, iterate_files
import xml.etree.cElementTree as et


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
    "Noto Serif": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSerif/NotoSerif-Regular.ttf",
    "Noto Serif Tibetan": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSerifTibetan/NotoSerifTibetan-Regular.ttf",
    "Noto Sans Thai": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansThai/NotoSansThai-Regular.ttf",
    "Noto Sans Malayalam": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf",
    "Noto Sans Syloti Nagri": "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansSylotiNagri/NotoSansSylotiNagri-Regular.ttf",
    "Noto Sans Kannada": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf",
    "Noto Serif Kannada": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSerifKannada/NotoSerifKannada-Regular.ttf"
}

mainfontgroups = {
    # fonts that should always appear in a script's options, and should be either default or second to default
    # add more later, but be careful! Other SIL fonts might not have the same feature cross-compatibility that CGA have 
    "Latn": ["Charis", "Gentium", "Andika"],
    "Cyrl": ["Charis", "Gentium", "Andika"]
}

lowestfontgroups = {
    # fonts that should also always appear, but should be lower tier than the ones listed in 'mainfontgroups'
    # these are often non-sil fonts 
    # these should be without the default tag at all (implied default=100)
    "Latn": ["Noto Sans", "Noto Serif"],
    "Cyrl": ["Noto Sans", "Noto Serif"]
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

    def _addMissingFonts(fontgroup, priority=None):
        if script in fontgroup.keys():
            neededfonts = fontgroup[script]
            neededfeature = None
            newfont = None

            if neededfonts is not None:
                for font in neededfonts:
                    if font in fontList.keys():
                        if font == "Andika":
                            #need to make this gentium/charis friendly
                            neededfeature = fontList[font][1]
                            for feature in ["ss01=1", "ss13=1", "ss14=1"]:
                                if feature in neededfeature:
                                    editedfeature = neededfeature.replace(feature, "")
                                    neededfeature = editedfeature
                            if len(neededfeature) == 0:
                                neededfeature = None
                        else:
                            neededfeature = fontList[font][1]
                            #note: this will fall apart if multiple fonts are listed with different features, but that's not supposed to happen anyway?
                        
                        #this bit is in case multiple of these fonts are already in there, need to add the new priority
                        currentpriority = fontList[font][0].get("types")
                        if currentpriority is None and priority==2 and len(fontList)==1:
                            # if only one font is listed in the current file, but doesn't have a priority listed, 
                            # but IS in the list of the main fonts (aka we are running this with the priority==2 arg)
                            # make it the main default
                            fontList[font][0].set("types", "default")
                            # this doesn't handle if multiple fonts are listed with no priorities. 
                            # In theory, it would make all of them default=2. which isn't bad bc there would be no normal default, so basicaly all of them are highest priority
                            # but should i make it so that if NOTHING has a default tag, give all of them a default before filling in blanks?
                        elif currentpriority is None and priority is not None:
                            fontList[font][0].set("types", "default={}".format(priority))
                            # this is not equiped to handle multiple different priorities for different roles. 
                            # it overrides the type rather than adds to the value inside it
                            # if new roles get added, this whole 'add missing fonts' function will need to be made smart enough to handle that
                            # maybe add argument for the role (i.e. default, ui, etc) 
                            # and when asking for currentpriority, actually read the text instead of just looking for if it exists
                            # and determine if that SPECIFIC ROLE is present in text, and go from there
                        pass
                    else:
                        if font == "Andika" and neededfeature is not None:
                            # make font features from charis/gentium friendly for andika
                            for feature in ["ss01=1", "ss11=1", "ss12=1"]:
                                if feature in neededfeature:
                                    editedfeature = neededfeature.replace(feature, "")
                                    neededfeature = editedfeature
                            if len(neededfeature) == 0:
                                neededfeature = None
                        if priority is not None and neededfeature is not None: 
                            newfont = ldml.ensure_path('special/sil:external-resources/sil:font[@name="{}"][@types="default={}"][@features="{}"]'.format(font, priority, neededfeature))[0]
                        elif neededfeature is not None:
                            newfont = ldml.ensure_path('special/sil:external-resources/sil:font[@name="{}"][@features="{}"]'.format(font, neededfeature))[0]
                        elif priority is not None:
                            newfont = ldml.ensure_path('special/sil:external-resources/sil:font[@name="{}"][@types="default={}"]'.format(font, priority))[0]
                        else: 
                            newfont = ldml.ensure_path('special/sil:external-resources/sil:font[@name="{}"]'.format(font))[0]
                        _addLink(font, newfont)
                        fontList[font] = newfont
                        #we have now added the fonts that aren't there into the ldml file, along with the features and the priority
                        #we've also given it its link child node
                        #and we've added it to the font list we made earlier just in case (currently not necessary but again, just in case)

    _addMissingFonts(mainfontgroups, 2)
    _addMissingFonts(lowestfontgroups)

    ldml.normalise()
    ldml.save_as(fpath)
    #and now it has saved the new stuff to the actual file and all is right in the world :)


    # this is a hack to add in that comment <!--types="ui"--> in the child node of noto sans
    with open(fpath, 'r+', encoding="utf8") as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        for line in lines:
            oldline = line
            if "Noto Sans" in line:
                line = line + '\t\t\t\t<!--types="ui"-->\n'
            if '<!--types="ui"-->' in oldline:
                line = line.replace('\t\t\t\t<!--types="ui"-->\n', " ")
            f.write(line)
    

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