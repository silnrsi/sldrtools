#!/usr/bin/env python3

import re, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile",help="Input rnc file")
    parser.add_argument("outfile",help="Output rnc file")
    args = parser.parse_args()

    outf = open(args.outfile, "wb")
    inf = open(args.infile, "rb")
    for l in inf.readlines():
        if b"attribute draft" in l:
            outf.write(l)
            outf.write(b'    "proposed" | "tentative" | "generated" | "suspect" |\n')
        else:
            outf.write(l)
    inf.close()
    outf.close()

if __name__ == "__main__":
    main()