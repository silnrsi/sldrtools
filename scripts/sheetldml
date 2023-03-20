#!/usr/bin/env python3
__doc__ = 'read LO .ods sheet (or TSV file) and generate LDML'
__url__ = 'http://github.com/silnrsi/sldrtools'
__copyright__ = 'Copyright (c) 2019-2020, SIL International  (http://www.sil.org)'
__license__ = 'Released under the MIT License (http://opensource.org/licenses/MIT)'
__author__ = 'David Rowe'

import argparse
import sys
from sldr.sheet import Sheet

def main():
    # define command line arguments 
    parser = argparse.ArgumentParser(description="Spreadsheet to LDML file")
    parser.add_argument("sheetname",help="LibreOffice calc file (or, if -t specified, a tab separated value file)")
    parser.add_argument("ldmlname",help="name of LDML file")
    parser.add_argument("-v","--verbose",help="print processing details",action='store_true')
    parser.add_argument("-t","--tsv",help="sheetname is a tab separated value file (cannot be used with -o)",action='store_true')
    parser.add_argument("-o","--output",help="new LibreOffice calc file (cannot be used with -t)")
    args = parser.parse_args()

    # three scenarios:
    # (1) read from TSV file (args.sheetname), create LDML file
    # -t input.tsv output.ldml
    # (2) read from ods file (args.sheetname), create LDML file
    # input.ods output.ldml
    # (3) read ods template file, read from LDML file, create new ods file
    # -o output.ods template.ods input.ldml
    ### Possibly expand option (1) to allow for reading multiple .tsv files, which have been exported for each sheet of the spreadsheet file

    if args.tsv:
        tsvfile = args.sheetname
        odsfile = None
    else:
        tsvfile = None
        odsfile = args.sheetname

    if args.output:
        if args.tsv:
            print("Cannot combine -t and -o options")
            sys.exit(2)
        ldmlfile = args.ldmlname
        ldmloutputfile = None
        odsoutputfile = args.output
    else:
        ldmlfile = None # to create new empty LDML file, which eventually will be written to args.ldmlname
        ldmloutputfile = args.ldmlname
        odsoutputfile = None

    s = Sheet(tsvfile, odsfile, ldmlfile)

    s.process(args.verbose)

    if ldmloutputfile:
        s.writeldml(ldmloutputfile)
    if odsoutputfile:
        s.writeods(odsoutputfile)

if __name__ == "__main__":
    main()
