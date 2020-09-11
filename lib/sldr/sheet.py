from sldr.ldml import Ldml
from odf.opendocument import load
from odf.table import Table, TableCell, TableColumn, TableRow ### only TableCell is used currently
from odf.text import P
import csv
import re
import sys

estring = re.compile(r"""
    (?P<elname>[^\[]+)         # element name 
    (\[@                       # beginning of optional attribute
    (?P<atname>[^=]+)          # attribute name
    (=                         # beginning of optional attribute value
    (["'])                     # opening quote of attribute value
    (?P<atvalue>.+)            # attribute value
    \5)?                       # matching closing quote ends optional value
    \])?                       # end of optional attribute
    """,re.VERBOSE)
 
t1string = re.compile(r"""
    (?P<beg>[^$]+)
    \$row
    (?P<end>.*)
    $""",re.VERBOSE)

t2string = re.compile(r"""
    (?P<beg>[^$]+)
    \$col
    (?P<mid>[^$]+)
    \$row
    (?P<end>.*)
    $""",re.VERBOSE)

t2rstring = re.compile(r"""
    (?P<beg>[^$]+)
    \$row
    (?P<mid>[^$]+)
    \$col
    (?P<end>.*)
    $""",re.VERBOSE)

class Sheet(object):
    def __init__(self, tsvfile=None, odsfile=None, ldmlfile=None):
        if tsvfile:
            self.input = csv.reader(open(tsvfile, newline='', encoding='utf-8'),dialect='excel-tab')
            self.nextrow = self._nexttsvrow
        elif odsfile:
            self.input = self._odssetup(odsfile)
            self.nextrow = next
        self.currentrow = None
        if ldmlfile: # then the LDML file is input and we write to ods file
            self.action = self._action_ods
            self.action1d = self._action1d_ods
            self.action2d = self._action2d_ods
            self.action2dr = self._action2dr_ods
            self.action2dx = self._action2dx_ods
        else: # if no LDML input file, then we write to an LDML output file
            self.action = self._action_ldml
            self.action1d = self._action1d_ldml
            self.action2d = self._action2d_ldml
            self.action2dr = self._action2dr_ldml
            self.action2dx = self._action2dx_ldml
        self.ldml = Ldml(ldmlfile) ### catch "FileNotFoundError" exception and terminate gracefully

    def _odssetup(self, f):
        self.ods = load(f) ### catch "FileNotFoundError" exception and terminate gracefully
        data = []
        for s in self.ods.topnode.lastChild.childNodes[0].childNodes:
            if s.tagName != "table:table": continue
            if s.getAttribute('name') not in ['Core','Posix','Minimal','Basic']: continue ### put list in constant
            for r in s.childNodes:
                if r.tagName != 'table:table-row': continue
                nodes = []
                for c in r.childNodes:
                    if c.tagName != 'table:table-cell': continue
                    count = 1
                    repeatedcols = c.getAttribute('numbercolumnsrepeated')
                    if repeatedcols:
                        repcount = int(repeatedcols)
                        if repcount < 10: # avoid 1000+ counts of empty cells at end of row
                            count = repcount
                    n = ""
                    if c.hasChildNodes():
                        for e in c.childNodes:
                            if e.tagName != 'text:p': continue
                            if e.hasChildNodes():
                                for t in e.childNodes:
                                    if t.tagName != 'Text': continue
                                    n = t.data
                                    break
                            break ### check position
                    for repcount in range(count):
                        nodes.append(n)
                self.currentrow = r
                yield nodes[1:]
        self.currentrow = None
        yield None

    def _nexttsvrow(self, x):
        try:
            return next(x)[1:]
        except StopIteration:
            return None

    def _writeldmlitem(self, path, value, writevalue=True):
        """Uses path, value and writevalue flag to make entry in Ldml object"""
        # If "writevalue" flag is set False, then value is already in path and doesn't need to be written
        el = self.ldml.ensure_path(path)[0]
        if writevalue:
            el.text = value

    def _action_ldml(self, path, value, attronly, atname):
        if value != "":
            if attronly:
                self._writeldmlitem(path[:-1] + "='" + value + "']", None, False)
            else:
                self._writeldmlitem(path, value)

    def _action1d_ldml(self, datarow, p1, p2):
        if len(datarow) > 2 and datarow[2] != "":
            self._writeldmlitem(p1 + datarow[0] + p2, datarow[2])

    def _action2d_ldml(self, datarow, p1, p2, p3, colhead):
        for colnum, col in enumerate(colhead,2):
            if len(datarow) > colnum and datarow[colnum] != "":
                self._writeldmlitem(p1 + col + p2 + datarow[0] + p3, datarow[colnum])

    def _action2dr_ldml(self, datarow, p1, p2, p3, colhead):
        for colnum, col in enumerate(colhead,2):
            if len(datarow) > colnum and datarow[colnum] != "":
                self._writeldmlitem(p1 + datarow[0] + p2 + col + p3, datarow[colnum])

    def _action2dx_ldml(self, datarow, p1, p2):
        rowitem = datarow[1]
        if rowitem  == "": return
        datarowlimit = len(datarow)
        for colnum in range(len(p1)):
            if colnum + 2 >= datarowlimit: return
            dataitem = datarow[colnum + 2]
            if dataitem != "":
                self._writeldmlitem(p1[colnum] + rowitem + p2[colnum], datarow[colnum + 2])

    def _writeodsitem(self, col, value):
        """Uses col and value to make entry in ods file (using self.currentrow)"""
        # column numbering starts at 1 for spreadsheet column A
        curcol = 0 ### restarts at beginning of row for each entry
        targetcol = col
        r = self.currentrow
        for c in r.childNodes:
            if c.tagName != 'table:table-cell': continue
            repeatedcols = c.getAttribute('numbercolumnsrepeated')
            repcount = int(repeatedcols) if repeatedcols else 1
            if curcol + repcount >= targetcol: break
            curcol += repcount
        else:
            pass ### got to end of row without finding desired column; add more cells? or report bad col?
        ### doesn't preserve background color (see Time Zones for example)
        countbefore = targetcol - curcol - 1
        countafter = curcol + repcount - targetcol
        if countbefore > 0:
            c1 = TableCell()
            c1.setAttribute('numbercolumnsrepeated', str(countbefore))
            c.setAttribute('numbercolumnsrepeated', str(countafter + 1))
            x = r.insertBefore(c1, c)
        if countafter > 0:
            c.setAttribute('numbercolumnsrepeated', '1')
            c2 = TableCell()
            c2.setAttribute('numbercolumnsrepeated', str(countafter))
            if c == r.lastChild:
                x = r.appendChild(c2)
            else:
                x = r.insertBefore(c2, c.nextSibling)
        if c.hasChildNodes():
            ### perhaps should test that child is text:p and its child is Text
            c.firstChild.firstChild.data = value
        else:
            c.addElement(P(text=value))

    def _action_ods(self, path, value, attronly, atname):
        e = self.ldml.find(path)
        if e != None:
            if attronly:
                v = e.attrib[atname] if atname in e.attrib else ""
            else:
                v = e.text
            if v != "":
                self._writeodsitem(4, v)

    def _action1d_ods(self, datarow, p1, p2):
        v = self.ldml.find(p1 + datarow[0] + p2)
        if v is not None:
            value = v.text
            if value != "":
                self._writeodsitem(4, value)

    def _action2d_ods(self, datarow, p1, p2, p3, colhead):
        for colnum, col in enumerate(colhead, 4):
            v = self.ldml.find(p1 + col + p2 + datarow[0] + p3)
            if v is not None:
                value = v.text
                if value != "":
                    self._writeodsitem(colnum, value)

    def _action2dr_ods(self, datarow, p1, p2, p3, colhead):
        for colnum, col in enumerate(colhead, 4):
            v = self.ldml.find(p1 + datarow[0] + p2 + col + p3)
            if v is not None:
                value = v.text
                if value != "":
                    self._writeodsitem(colnum, value)

    def _action2dx_ods(self, datarow, p1, p2):
        rowitem = datarow[1]
        if rowitem  == "": return
        for colnum in range(len(p1)):
            v = self.ldml.find(p1[colnum] + rowitem + p2[colnum])
            if v is not None:
                value = v.text
                if value != "":
                    self._writeodsitem(colnum + 4, value)

    def writeldml(self, ldmloutputfile):
        self.ldml.normalise()
        self.ldml.save_as(ldmloutputfile)

    def writeods(self, odsoutputfile):
        self.ods.save(odsoutputfile) ### need to catch "Permission denied" exception if file exists and is open

    def process(self, verbose = False):
        datarow = self.nextrow(self.input)
        while datarow != None:
            if verbose: print("processing row " + ",".join(datarow))  ### debug
            typecheck = datarow[0] if len(datarow) > 0 else ""
            if typecheck == "":
                datarow = self.nextrow(self.input)
            elif typecheck[0:8] == "table1d(":
                result = t1string.match(typecheck[8:-1])
                datarow = self.nextrow(self.input)
                while datarow != None and len(datarow) > 0 and datarow[0] != "":
                    self.action1d(datarow, result.group('beg'), result.group('end'))
                    datarow = self.nextrow(self.input)
            elif typecheck[0:8] == "table2d(":
                result = t2string.match(typecheck[8:-1])
                colhead = []         # get column headings
                for colnum in range(2,len(datarow)):
                    if datarow[colnum] == "": break
                    colhead.append(datarow[colnum])
                datarow = self.nextrow(self.input)
                while datarow != None and len(datarow) > 0 and datarow[0] != "":
                    self.action2d(datarow, result.group('beg'), result.group('mid'), result.group('end'), colhead)
                    datarow = self.nextrow(self.input)
            elif typecheck[0:9] == "table2dr(": ### this is largely copy of above, perhaps refactor?
                result = t2rstring.match(typecheck[9:-1])
                colhead = []         # get column headings
                for colnum in range(2,len(datarow)):
                    if datarow[colnum] == "": break
                    colhead.append(datarow[colnum])
                datarow = self.nextrow(self.input)
                while datarow != None and len(datarow) > 0 and datarow[0] != "":
                    self.action2dr(datarow, result.group('beg'), result.group('mid'), result.group('end'), colhead)
                    datarow = self.nextrow(self.input)
            elif typecheck[0:9] == "table2dx(":
                # Between "^table2dx(" and ")$" are comma-separated paths each containing $row, which is replaced by values from column C (datarow[1])
                colpath = typecheck[9:-1].split(',')
                beg = []
                end = []
                for cp in colpath:
                    result = t1string.match(cp)
                    beg.append(result.group('beg'))
                    end.append(result.group('end'))
                datarow = self.nextrow(self.input)
                while datarow != None and len(datarow) > 1 and datarow[0] == "":
                    self.action2dx(datarow, beg, end)
                    datarow = self.nextrow(self.input)
            else:
                result = estring.match(typecheck.split('/')[-1])
                elname = result.group('elname')
                atname = result.group('atname')
                atvalue = result.group('atvalue')
                self.action(typecheck, datarow[2], atname != None and atvalue == None, atname)
                datarow = self.nextrow(self.input)

