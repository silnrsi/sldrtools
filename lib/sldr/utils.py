#!/usr/bin/env python3

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

from langtag import langtag, lookup
import os, json
from sldr.ldml import Ldml, _alldrafts
import requests


def find_parents(langid, to_root = True, needs_sldr = False, match_script = True, match_region = False):    
    """ 
        A way to track down parent(s) of an ldml file based on specific criteria. 

        Parameters: 
            to_root:        If true, will go all the way to the deepest applicable parent. If false, will stop if it can just find one applicable parent file. 
            needs_sldr:     If true, will only output applicable parent(s) with an SLDR file.
            match_script:   If true, will only output applicable parent(s) with a script matching that of the original langtag.
            match_region:   If true, will only output applicable parent(s) with region matching that of the original langtag.

        Returns:
            is_root:        Bool. If true, means that the original langtag is the root file based on arguments given.
            root_tag:       String. Final parent tag based on arguments given.
            root_tagset:    LangTag. Final parent tagset based on arguments given.
            parent_path:    List. An ordered list of each applicable parent tag found, likely only useful if the to_root parameter was True.
    """

    lt = langtag(os.path.splitext(os.path.basename(langid))[0]) #gets basic langtag data based on file name
    tagset = lookup(str(lt).replace("_", "-"), default="", matchRegions=True)
    
    def _has_sldr(root_tagset):
        return getattr(root_tagset, "sldr", None)
    
    # this next section is to deal with variants, private use areas that don't refer back to their non-private versions in langtags, and other weirdness
    if tagset == "":
#        print("no tagset found, shaving last langtag value to try to find it")
        r = str(lt).rfind('-')
        if r == -1:
            return True, str(tagset), tagset, [str(tagset)]
        variant = str(lt)[r+1:]
        lt_trim = str(lt)[:r]
        tagset = lookup(str(lt_trim).replace("_", "-"), default="", matchRegions=True)
        if tagset == "":
            r = str(lt).rfind('-x-')
            lt_trim = str(lt)[:r]
            tagset = lookup(str(lt_trim).replace("_", "-"), default="", matchRegions=True)
            if to_root == False:
                if (needs_sldr and _has_sldr(tagset)) or needs_sldr == False:
                    return False, str(tagset), tagset, [str(tagset)]
        if variant == "001":
            if to_root == False:
                return False, str(tagset), tagset, [str(tagset)]
        if hasattr(tagset, "variants") and variant in tagset.variants:
            if to_root == False:
                if (needs_sldr and _has_sldr(tagset)) or needs_sldr == False:
                    return False, str(tagset), tagset, [str(tagset)]
                
    lt_text = str(tagset) #technically never used, but kept just in case need to compare old & new if test is updated or made more complex later
    root_tag = lt_text
    root_tagset = tagset
    parent_path = [root_tag]
#    print(root_tag.count('-'))
    
#    print("data pre-test")
#    print(root_tag)
#    print(root_tagset)
#    print(root_tagset.script)

    def _remove_private(root_tag):
        r = root_tag.rfind('-x-')
        if r > 0:
            root_tag = root_tag[:r]
        ran_private = True
        return root_tag, ran_private

    def trim_tag(root_tag):
        r = root_tag.rfind('-')
        root_tag_trim = root_tag
        if r > 0:
            root_tag_trim = root_tag[:r]
        c = root_tag_trim.count('-')
        if c > 0:
            trimmable = True
        else:
            trimmable = False
        return root_tag_trim, trimmable

    def mintag_file(langid, prev_tagset):
        mintags = [str(getattr(prev_tagset, "tag", None))]
        tags = getattr(prev_tagset, "tags", None)
        this_file = str(os.path.splitext(os.path.basename(langid).replace("_", "-"))[0])
        redundant = False
        if mintags[0] == this_file:
            return redundant
        for tag in tags:
            mintags.append(str(tag))
        print(mintags)
        for mintag in mintags:
            if mintag != this_file:
                mintag_file = os.path.join("..", "sldr", (mintag[0]), (mintag.replace("-", "_") + ".xml"))
                print(mintag_file)
                print(os.path.isfile(mintag_file))
                print(mintag)
                if os.path.isfile(mintag_file):
                    redundant = True
                    break
        print("is redunant?:" + str(redundant))
        return redundant

    def parent_loop(root_tag:str, root_tagset, to_root = True, needs_sldr = False, match_script = True, match_region = False):
        trimmable = True
        ran_private = False
        redundant = False
        root_tag_temp = root_tag
        while trimmable:
            prev_tagset = lookup(root_tag_temp.replace("_", "-"), default="", matchRegions=False)
            if ran_private == False:
                redundant = False
#                print("remove private")
                root_tag_trim, ran_private = _remove_private(root_tag_temp)
#                print(root_tag)
#                print(root_tag_trim) 
            else:
                redundant = mintag_file(langid, prev_tagset)
                if redundant and (to_root == False):
                    return root_tag, redundant
                root_tag_trim, trimmable = trim_tag(root_tag_temp)
#                print("after a tag trim iteration:")
#                print(root_tag)
#                print(root_tag_trim) 
            root_tag_temp = root_tag_trim
            root_tagset_temp = lookup(str(root_tag_trim).replace("_", "-"), default="", matchRegions=False)
#            print(root_tagset_temp)
            if root_tagset_temp == root_tagset or root_tagset_temp == prev_tagset:
#                print("tagsets still match, trim again!")
                continue
            elif match_region and match_script == False:
                if root_tagset_temp.region == root_tagset.region:
                    if (needs_sldr and _has_sldr(root_tagset_temp)) or needs_sldr == False:
#                        print("new parent found")
                        root_tag = root_tag_trim
                        parent_path.append(root_tag)
                        if to_root == False:
                            return root_tag, redundant
                    if to_root or (needs_sldr and (_has_sldr(root_tagset_temp) == False)):
#                        print("regions still match, trim again!")
                        continue
            elif match_script and match_region == False:
                if root_tagset_temp.script == root_tagset.script:
                    if (needs_sldr and _has_sldr(root_tagset_temp)) or needs_sldr == False:
#                        print("new parent found")
                        root_tag = root_tag_trim
                        parent_path.append(root_tag)
                        if to_root == False:
                            return root_tag, redundant
                    if to_root or (needs_sldr and (_has_sldr(root_tagset_temp) == False)):
#                        print("scripts still match, trim again!")
                        continue
            elif match_region and match_script:
                if (root_tagset_temp.script == root_tagset.script) and (root_tagset_temp.region == root_tagset.region):
                    if (needs_sldr and _has_sldr(root_tagset_temp)) or needs_sldr == False:
#                        print("new parent found")
                        root_tag = root_tag_trim
                        parent_path.append(root_tag)
                        if to_root == False:
                            return root_tag, redundant
                    if to_root or (needs_sldr and (_has_sldr(root_tagset_temp) == False)):
#                        print("scripts and regions still match, trim again!")
                        continue
            elif root_tagset_temp == "":
#                print("no tagset found that matches, idk how bc that's not how it works but this error is here anyway just in case")
                continue
        else:
#            print("no more trimming, final parent is the last one we trimmed!")
            return root_tag, redundant

    root_tag, redundant = parent_loop(root_tag, root_tagset, to_root, needs_sldr, match_script, match_region)
    root_tagset = lookup(str(root_tag).replace("_", "-"), default="", matchRegions=False)
    is_root = False
    if root_tagset == tagset and redundant == False:
        is_root = True

#    print("final results")
#    print("is root?:" + str(is_root))
#    print(root_tag)
#    print(root_tagset)
#    print(parent_path)
    return is_root, root_tag, root_tagset, parent_path

        #end results key:
        # lt = LangTag. original langtag, even if it doesnt have a tagset to match
        # tagset = LangTag. original tagset, or the closest one if there is variant weirdness
        # lt_text = String. tagset in string form
        # root_tag = String. parent tag based on arguments given 
        # root_tagset = LangTag. parent tagset based on arguments given
        # is_root = Bool. if true, means that the original langtag is the root file based on arguments given
        # parent_path = List. an ordered list of each applicable parent tag found, only potentially useful if to_root == True.

#the next thing is emily playing around with trying to get keyboard info from keyman

# def find_keymans(keymanspath):
#     """ 
#         Parameters:
#             keymans = path to json file from the keyman api downloaded from https://api.keyman.com/cloud/4.0/keyboards/?languageidtype=bcp47
#             The languageidtype set to "bcp47" is very important
#     """
#     apiurl = "https://api.keyman.com/cloud/4.0/keyboards/?languageidtype=bcp47"
#     response = requests.get(apiurl)
#     print(response.content)

#     badtags = {
#         # for tags that need to be swapped
#     }

#     dirname = os.path.dirname(__file__)
#     if keymanspath:
#         keymanspath == "../../../../SourceFiles/keyman2025/keyboards.json"
#     keymanslocation = os.path.realpath(os.path.join(dirname, keymanspath))
#     #alldat = json.load(open(keymanslocation))
#     alldat = json.loads(response.content)
#     print(alldat)
#     dat = ""
#     id = ""
#     results = {}
#     for a in alldat["keyboard"]:
#         #this is now like we opened the file system and found all the different instances of keyboard info. every instance of "a" is an instance of keyboard info now
#         dat = a
#         id = a["id"]
#         for k in dat['languages']:
#             lang = k["id"]
#             entry = {'langtag': lang, 'id': id}
#             results.setdefault(lang, []).append(entry)
#             for s in ('font', 'oskfont'):
#                 if s in k.keys():
#                     entry[s+'family'] = k[s]['family']
#                     entry[s+'source'] = k[s]['source'][0]
#     print(results)
#     for tag in results.keys():
#         try:
#             lt = lookup(tag, use639=True)
#         except KeyError:
#             if tag in badtags.keys():
#                 tag2 = badtags[tag]
#                 try: 
#                     lt = lookup(tag2)
#                 except KeyError:
#                     print("Can't find {} ...........................".format(tag))
#                     continue
#             else: 
#                 print("Can't find {} ...........................".format(tag))
#                 continue
#         print(lt.asSldr())
    
#     #problem children: 
#     # - as-Latn (sil_indic_roman, might actually be nag? no tag for as-Latn in langtags), 
#     # - mul-Ethi (multiple ethiopic, sil_ethiopic, sil_ethiopic_power_g), 
#     # - dgo-arab-pk (rac_dogri, there is a dgo-arab-in tag, is there a dif for pk?), 
#     # - en-qp (english, northern africa = qp, region is left out of langtags intentionally)
#     # - yor, (naijatype, "yor" is the 3 digit tag for "yo" in nigeria, which works bc it's nigerian language keyboard)
#     # - kau, (also naijatype, actual tag is "kr")
#     # - ibo, (same as above 2, actual tag is "ig")
#     # - hau, (same as above 3, actual tag is "ha")
#     # - xal-mong, (actually right? not sure why there's only a variant listed in langtags "xal-Mong-CN-x-todo")
#     # - pes, (microlanguage that already is under fa, which already has the thingy listed. fa-AF however does not, should also have it)

#     #elements needed for full setup:
#     #-full langtag (requires identifying script) (problem: using keyboard info files did let us find actual langtag. this is gonna be trickier)
#     #-font for identifying script? not every keyboard has an associated font
#     #-id (for constructing keyboard link)
#     #-keyboard link (NOT the github one in the api, requires construction. https://keyman.com/go/keyboard/id/download/kmp (CHECK AND MAKE SURE FILES AREN'T SAYING https://keyman.com/keyboards/install/id)
#     #-type=kmp

def fixsldr(sldr=None):
    """rerun normalise on the whole sldr to remove thingies that shouldnt be there"""
    dirname = os.path.dirname(__file__)
    if sldr == None:
        sldr = os.path.realpath(os.path.join(dirname, "../../../SLDR/sldr"))
    for dp, dn, fn in os.walk(sldr):
        for fname in fn:
            print(fname)
            fpath = os.path.join(sldr, fname)
            if not os.path.exists(fpath):
                fpath = os.path.join(sldr, fname[0].lower(), fname)
                if not os.path.exists(fpath):
                    print("Failed: {}".format(fname))
                    continue
            l = Ldml(fpath)
            l.save_as(fpath)

fixsldr()