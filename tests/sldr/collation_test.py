#!/usr/bin/env python3

import unittest
from sldr.collation import Collation, SortKey

class CollationTests(unittest.TestCase):

    def test_sortkeycmp(self):
        coll = Collation()
        for t in (  ("a", "b"),
                    ("a", "a\u0301"),
                    ("a", "A"),
                 ):
            keya = coll.getSortKey(t[0])
            keyb = coll.getSortKey(t[1])
            self.assertLess(keya, keyb, msg="{} < {}".format(t[0], t[1]))

    def runsimple(self, instr, outstr, testsimple=None):
        coll = Collation()
        test = [r.strip() for r in instr.split(";")]
        coll.convertSimple(test)
        sres = coll.asSimple()
        tres = " ; ".join(sres.split("\n"))
        self.assertEqual(tres, instr if testsimple is None else testsimple)
        coll.minimise()
        res = " ".join(coll.asICU().split("\n"))
        self.assertEqual(res, outstr)

    def runtailor(self, instr, outstr):
        coll = Collation()
        coll.parse(instr)
        coll.minimise()
        asicu = coll.asICU()
        res = " ".join(asicu.split("\n"))
        self.assertEqual(res, outstr)

    def test_short(self):
        self.runsimple(r"b/B ; a/A ; á/Á ; c/C",
            r"&[before 1]a < b <<< B &a < á <<< Á")

    def test_beforeaSimple(self):
        self.runsimple(r"ꞌ/Ꞌ ; a/A ; b/B ; bb/Bb/BB ; c/C ; d/D ; e/E ; ë/Ë ; f/F",
            r"&[before 1]a < ꞌ <<< Ꞌ &b < bb <<< Bb <<< BB &e < ë <<< Ë")

    def test_ngexpandSimple(self):
        self.runsimple(r"ꞌ/Ꞌ ; a/A ; b/B ; c/C ; d/D ; e/E ; f/F; g/G; NGY; h/H",
                r"&[before 1]a < ꞌ <<< Ꞌ &g < ngy <<< Ngy <<< NGy <<< NGY",
                testsimple = r"ꞌ/Ꞌ ; a/A ; b/B ; c/C ; d/D ; e/E ; f/F ; g/G ; ngy/Ngy/NGy/NGY ; h/H")

    def test_lotsSimple(self):
        self.runsimple(r"a/A á/Á; b/B ꞌb; c/C; d/D ꞌd dr; e/E é/É; f/F; g/G gb gbr; i/I í/Í ị/Ị ị́ ɨ/Ɨ ɨ; k/K kp kpr; l/L; m/M mb; n/N nd ndr ng ṇg ṇ/Ṇ ngb ngbr nv ny nz; o/O ó/Ó; p/P ph; r/R ṛ/Ṛ; s/S; t/T tr; u/U ú/Ú ụ/Ụ ụ; v/V ṿ/Ṿ; w/W; y/Y ꞌy; z/Z",
            r"&a << á <<< Á &b << ꞌb <<< Ꞌb <<< ꞋB &d << ꞌd <<< Ꞌd <<< ꞋD << dr <<< Dr <<< DR &e << é <<< É &g << gb <<< Gb <<< GB << gbr <<< Gbr <<< GBr <<< GBR &i << í <<< Í << ị <<< Ị << ị́ <<< Ị́ << ɨ <<< Ɨ &k << kp <<< Kp <<< KP << kpr <<< Kpr <<< KPr <<< KPR &m << mb <<< Mb <<< MB &n << nd <<< Nd <<< ND << ndr <<< Ndr <<< NDr <<< NDR << ng <<< Ng <<< NG << ṇg <<< Ṇg <<< ṆG << ṇ <<< Ṇ << ngb <<< Ngb <<< NGb <<< NGB << ngbr <<< Ngbr <<< NGbr <<< NGBr <<< NGBR << nv <<< Nv <<< NV << ny <<< Ny <<< NY << nz <<< Nz <<< NZ &o << ó <<< Ó &p << ph <<< Ph <<< PH &r << ṛ <<< Ṛ &t << tr <<< Tr <<< TR &u << ú <<< Ú << ụ <<< Ụ &v << ṿ <<< Ṿ &y << ꞌy <<< Ꞌy <<< ꞋY",
            testsimple = r"a/A ; á/Á ; b/B ; ꞌb/Ꞌb/ꞋB ; c/C ; d/D ; ꞌd/Ꞌd/ꞋD ; dr/Dr/DR ; e/E ; é/É ; f/F ; g/G ; gb/Gb/GB ; gbr/Gbr/GBr/GBR ; i/I ; í/Í ; ị/Ị ; ị́/Ị́ ; ɨ/Ɨ ; k/K ; kp/Kp/KP ; kpr/Kpr/KPr/KPR ; l/L ; m/M ; mb/Mb/MB ; n/N ; nd/Nd/ND ; ndr/Ndr/NDr/NDR ; ng/Ng/NG ; ṇg/Ṇg/ṆG ; ṇ/Ṇ ; ngb/Ngb/NGb/NGB ; ngbr/Ngbr/NGbr/NGBr/NGBR ; nv/Nv/NV ; ny/Ny/NY ; nz/Nz/NZ ; o/O ; ó/Ó ; p/P ; ph/Ph/PH ; r/R ; ṛ/Ṛ ; s/S ; t/T ; tr/Tr/TR ; u/U ; ú/Ú ; ụ/Ụ ; v/V ; ṿ/Ṿ ; w/W ; y/Y ; ꞌy/Ꞌy/ꞋY ; z/Z")

    def test_beforeTailor(self):
        self.runtailor(r"&[before 1]a < â < Å < b <<< B < b̃ <<< B̃ < |e <<< |E < c <<< C < d <<< D < e <<< E < È << ê <<< Ê << é <<< É << ë <<< Ë << ē <<< Ē << è < f <<< F < g <<< G < Gb < h <<< H < i <<< I < j <<< J < k <<< K < l <<< L < m <<< M < n <<< N < ½ < o <<< O < ô <<< Ô << ö <<< Ö < p <<< P < q <<< Q < r <<< R < s <<< S < t <<< T < u <<< U < ü <<< Ü < v <<< V < w <<< W < x <<< X < y <<< Y < × < z <<< Z < ɓ <<< Ɓ << Û < ɗ <<< Ɗ << ¬ < ɨ <<< Ɨ < ? < ' < m̃ <<< M̃",
            r"&[before 1]a < â < Å &b < b̃ <<< B̃ < \|e <<< \|E &e < È << ê <<< Ê << é <<< É << ë <<< Ë << ē <<< Ē << è &g < Gb &n < ½ &o < ô <<< Ô << ö <<< Ö &u < ü <<< Ü &ɓ << Û")

if __name__ == "__main__":
    unittest.main()

