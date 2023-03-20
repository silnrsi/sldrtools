#!/usr/bin/env python3

import argparse, sys, re
from xml.etree import ElementTree as et
from sldr.py3xmlparser import XMLParser, TreeBuilder
from typing import Any, Callable, ClassVar

_elementprotect = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;' }
_attribprotect = dict(_elementprotect)
_attribprotect['"'] = '&quot;'

cldrtns = "{urn://unicode.org/cldr/types/0.1}"

class ETWriter:
    """ General purpose ElementTree pretty printer complete with options for attribute order
        beyond simple sorting, and which elements should use cdata """
    nscount: ClassVar[int] = 0
    indent: ClassVar[str] = "  "

    root: et.Element | None
    namespaces: dict[str,str]
    attributeOrder: dict
    maxAts: int
    takesCData: set

    def __init__(self, root, namespaces = None, attributeOrder = {}, takesCData = set()):
        self.root = root
        if namespaces is None:
            self.namespaces = {'http://www.w3.org/XML/1998/namespaces': 'xml',
                               cldrtns[1:-1]: 'cldr'}
        else:
            self.namespaces = namespaces
        self.attributeOrder = attributeOrder
        self.maxAts = len(attributeOrder)
        self.takesCData = takesCData

    def parse(self, fname, reverse=False):
        if fname is None:
            self.root = getattr(et, '_Element_Py', et.Element)('ldml')
            self.root.document = self # type: ignore
            self.default_draft = 'unconfirmed'
            return
        elif isinstance(fname, str):
            self.fname = fname
            fh = open(self.fname, 'rb')     # expat does utf-8 decoding itself. Don't do it twice
        else:
            fh = fname
        tb = TreeBuilder(element_factory=getattr(et, '_Element_Py', None))
        parser = XMLParser(target=tb, encoding="UTF-8")

        def doComment(data: str):
            parser.parser.StartElementHandler("!--", ['text', data]) # type: ignore
            parser.parser.EndElementHandler("!--") # type: ignore
            # resubmit as new start tag=!-- and sort out in main loop

        parser.parser.CommentHandler = doComment
        last = None
        curr = None
        for event, elem in et.iterparse(fh, events=('start', 'start-ns', 'end'), parser=parser): # type: ignore
            if event == 'start-ns':
                assert elem is not None
                self.namespaces[elem[1]] = elem[0]
            elif event == 'start':
                elem.document = self
                if elem.tag == '!--':
                    self._proc_comment(curr, last, elem.get('text'))
                else:
                    if curr is not None:
                        elem.parent = curr
                    else:
                        self.root = elem
                    curr = elem
            elif elem.tag == '!--':
                if curr is not None:
                    curr.remove(elem)
            else:
                last = curr
                curr = getattr(elem, 'parent', None)
        fh.close()

    def _proc_comment(self, curr, last, text):
        if curr is None:
            return
        m = re.match(r"^\s*@([A-Z]+)\s*(?::(.*?))?\s*$", text)
        if m is None:
            return
        name, value = (m.group(1), (m.group(2) or "true"))
        # if last.tag.find("}") > 0:
        #     ns = last.tag[:last.tag.find("}")+1]
        # else:
        #     ns = ""
        # e = last.find(".//"+ns+"element")
        # if e is None:
        #     e = last.find(".//"+ns+"attribute")
        # if e is not None:
        #    e.set(cldrtns+name.lower(), value)
        last.set(cldrtns+name.lower(), value)

    def _unproc_comment(self, curr, last):
        for k, v in last.attrib.items():
            if k.startswith(cldrtns):
                c = k[len(cldrtns):].upper()
                if v != "true":
                    c += ":"+v
                last.commentsafter = getattr(last, 'commentsafter', []).append(c)

    def _localisens(self, tag: str) -> tuple[str, str | None, str | None]:
        ''' Convert {url}localname into ns:localname'''
        if tag[0] == '{':
            ns, localname = tag[1:].split('}', 1)
            qname = self.namespaces.get(ns, '')
            if qname:
                return (f'{qname}:{localname}', qname, ns)
            else:
                ETWriter.nscount += 1
                return (localname, 'ns' + str(self.nscount), ns)
        else:
            return (tag, None, None)

    def _protect(self, txt, base=_attribprotect):
        ''' Turn key characters into entities'''
        return re.sub('['+"".join(base.keys())+"]", lambda m: base[m.group(0)], txt)

    def _nsprotectattribs(self, attribs, localattribs, namespaces):
        ''' Prepare attributes for output by protecting, converting ns: form
            and collecting any xmlns attributes needing to be added'''
        if attribs is not None:
            for k, v in attribs.items():
                (lt, lq, lns) = self._localisens(k)
                if lns and lns not in namespaces:
                    namespaces[lns] = lq
                    assert lq is not None
                    localattribs['xmlns:'+lq] = lns
                localattribs[lt] = v
        
    def _sortedattrs(self, n, attribs=None):
        ''' Sorts attributes into appropriate attributes order'''
        def getorder(x):
            return self.attributeOrder.get(n.tag, {}).get(x, self.maxAts)
        return sorted((attribs if attribs is not None else n.keys()), key=lambda x:(getorder(x), x))

    def serialize_xml(self, write, base = None, indent = '', topns = True, namespaces = {}):
        """ Output the object using write() in a normalised way:
            topns if set puts all namespaces in root element else put them as low as possible"""
        if base is None:
            base = self.root
            write('<?xml version="1.0" encoding="utf-8"?>\n')
            namespaces['http://www.w3.org/XML/1998/namespace'] = 'xml'
        assert base is not None
        (tag, q, ns) = self._localisens(base.tag)
        localattribs = {}
        if ns and ns not in namespaces:
            namespaces[ns] = q
            assert q is not None
            localattribs['xmlns:'+q] = ns
        if topns:
            if base == self.root:
                for n,q in self.namespaces.items():
                    if q == "xml": continue
                    localattribs[('xmlns:'+q) if q != "" else 'xmlns'] = n
                    namespaces[n] = q
        else:
            for c in base:
                (lt, lq, lns) = self._localisens(c.tag)
                if lns and lns not in namespaces:
                    namespaces[lns] = q
                    assert lq is not None
                    localattribs['xmlns:'+lq] = lns
        self._nsprotectattribs(getattr(base, 'attrib', None), localattribs, namespaces)
        for c in getattr(base, 'comments', []):
            write('{}<!--{}-->\n'.format(indent, c))
        write('{}<{}'.format(indent, tag))
        if len(localattribs):
            def getorder(x):
                return self.attributeOrder.get(tag, {}).get(x, self.maxAts)
            # def cmpattrib(x, y):
            #     return cmp(getorder(x), getorder(y)) or cmp(x, y)
            for k in self._sortedattrs(base, localattribs):
                write(' {}="{}"'.format(self._localisens(k)[0], self._protect(localattribs[k])))
        if len(base):
            write('>\n')
            for b in base:
                self.serialize_xml(write, base=b, indent=indent + self.indent, topns=topns, namespaces=namespaces.copy())
            write('{}</{}>\n'.format(indent, tag))
        elif base.text:
            if tag not in self.takesCData:
                t = self._protect(base.text.replace('\n', '\n' + indent), base=_elementprotect)
            else:
                t = "<![CDATA[\n" + self.indent + indent + base.text.replace('\n', '\n' + self.indent + indent) + "\n" + indent + "]]>"
            write('>{}</{}>\n'.format(t, tag))
        else:
            write('/>\n')
        for c in getattr(base, 'commentsafter', []):
            write('{}<!--{}-->\n'.format(indent, c))

    def save_as(self, fname, base = None, indent = '', topns = True, namespaces = {}):
        """ A more comfortable serialize_xml using a filename"""
        with open(fname, "w", encoding="utf-8") as outf:
            self.serialize_xml(outf.write, base=base, indent=indent, topns=topns, namespaces=namespaces)

    def add_namespace(self, q, ns):
        """ Adds a namespace mapping"""
        if ns in self.namespaces: return self.namespaces[ns]
        self.namespaces[ns] = q
        return q

    def addnode(self, parent, tag, **kw):
        """ Appends a new node to a parent, returning the new node.
            Empty (None) attributes are stripped"""
        kw = {k: v for k, v in kw.items() if v is not None}
        return et.SubElement(parent, tag, **kw)

    def _reverselocalns(self, tag):
        ''' Convert ns:tag -> {url}tag'''
        nsi = tag.find(":")
        if nsi > 0:
            ns = tag[:nsi]
            for k, v in self.namespaces.items():
                if ns == v:
                    tag = "{" + k + "}" + tag[nsi+1:]
                    break
        return tag

    def subelement(self, parent, tag, **kw):
        """ Create a new SubElement and do localns replacement as in ns:tag -> {url}tag"""
        tag = self._reverselocalns(tag)
        kw = {self._reverselocalns(k): v for k, v in kw.items() if v is not None}
        return et.SubElement(parent, tag, **kw)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Input file")
    parser.add_argument("-o","--outfile", help="Output file")
    parser.add_argument("-r","--reverse",action="store_true",help="Convert attributes to comments")
    args = parser.parse_args()

    doc = ETWriter(None)
    doc.parse(args.infile)
    if args.outfile is not None:
        outf = open(args.outfile, "w")
        writer = outf.write
    else:
        outf = None
        writer = sys.stdout.write
    doc.serialize_xml(writer)
    if outf is not None:
        outf.close()

if __name__ == "__main__":
    main()
