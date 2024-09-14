#!/usr/bin/env python3

import unittest
from sldr.collation import Collation, SortKey

class CollationTests(unittest.TestCase):

    maxDiff = None

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
        coll.minimise()
        res = " ".join(coll.asICU().split("\n"))
        self.assertEqual(res, outstr)
        self.assertEqual(tres, instr if testsimple is None else testsimple)

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

    def test_devasimple(self):
        self.runsimple("ँ ;ं ; ः ; ऄ ; अ ; आ ; इ ; ई ; उ ; ऊ ; ऋ ; ऌ ; ऍ ; ऎ ; ए ; ऐ ; ऑ ; ऒ ; ओ ; औ ; क ; ख ; ग ; घ ; ङ ; च ; छ ; ज ; झ ; ञ ; ट ; ठ ; ड ; ढ ; ण ; ण्\u200D ; त ; थ ; द ; ध ; न ; ऩ ; प ; फ ; ब ; भ ; म ; य ; र ; ऱ ; ल ; ळ ; ऴ ; व ; श ; ष ; स ; ष्\u200D ; त्र ; ज्ञ ; रू ; ह़ ; ॽ ; ऽ ;  ; ा ; ू़ ; ृ ; ॄ ;ॅ ; ॆे ; ै ; ॉ ; ॊ ; ो ; ौ;् ;् \u200C ; क्\u200D ; स्\u200D ; क़ ; ख़ ; ग़ ; ज़ ; ड़ ; ढ़ ; फ़ ; य़ ; ॠ ; ॡ ; ’ ; र् ; क्ष ; ब्\u200D ; । ; ? ; १ ; २ ; ३ ; ४ ; ५ ; ६ ; ७ ; ८ ; ९ ; - ; ि ; ी ; अ ; आ ; इ ; ई ; उ ; ऊ ; ऋ ; ऌ ; ऍ ; ऎ ; ए ; ऐ ; ऑ ; ऒ ; ओ ; औ ; क ; ख ; ग ; घ ; ङ ; च ; छ ; ज ; झ ; ञ ; ट ; ठ ; ड ; ढ ; ण ; त ; थ ; द ; ध ; न ; ऩ ; प ; फ ; ब ; भ ; म ; य ; र ; ऱ ; ल ; ळ ; ऴ ; व ; श ; ष ; स ; ह़ ; ऽ ; क़ ; ख़ ; ग़ ; ज़ ; ड़ ; ढ़ ; फ़ ; य़ ; ॠ ; ॡ ; ;ु ; ॱ ; ‘ ; द्य ; श्\u200D ;  ;  ; , ; म्\u200D ; न्\u200D ; ज्\u200D ; व्\u200D ; प्\u200D ; ग्\u200D ; थ्\u200D ; त्\u200D ; च्\u200D ; भ्\u200D ; ध्\u200D ; ल्\u200D ; ख् ; ङ्\u200C ; ये ; बे ; के ; खे ; गे ; घे ; चे ; छे ; जे ; ने ; झे ; ते ; थे ; दे ; धे ; पे ; फे ; भे ; मे ; टे ; ठे ; गु ; गी ; र्\u200D ; द्व",
            "&ण < ण्\u200d &न < ऩ &र < ऱ &ळ < ऴ &स < ष्\u200d < त्र < ज्ञ < रू &ॅ < ॆे &् << \u200c &क < स्\u200d/्\u200d < क़/्\u200d &’ < र्/्\u200d < क्ष/्\u200d < ब्\u200d/्\u200d &‘ < द्य/्\u200d < श्\u200d/्\u200d &\\, < म्\u200d/्\u200d < न्\u200d/्\u200d < ज्\u200d/्\u200d < व्\u200d/्\u200d < प्\u200d/्\u200d < ग्\u200d/्\u200d < थ्\u200d/्\u200d < त्\u200d/्\u200d < च्\u200d/्\u200d < भ्\u200d/्\u200d < ध्\u200d/्\u200d < ल्\u200d/्\u200d < ख्/्\u200d < ङ्\u200c/्\u200d < ये/्\u200d < बे/्\u200d < के/्\u200d < खे/्\u200d < गे/्\u200d < घे/्\u200d < चे/्\u200d < छे/्\u200d < जे/्\u200d < ने/्\u200d < झे/्\u200d < ते/्\u200d < थे/्\u200d < दे/्\u200d < धे/्\u200d < पे/्\u200d < फे/्\u200d < भे/्\u200d < मे/्\u200d < टे/्\u200d < ठे/्\u200d < गु/्\u200d < गी/्\u200d < र्\u200d/्\u200d < द्व/्\u200d",
            testsimple = " ं ँ ः \u200c ; अ ; ऄ ; आ ; इ ; ई ; उ ; ऊ ; ऋ ; ऌ ; ऍ ; ऎ ; ए ; ऐ ; ऑ ; ऒ ; ओ ; औ ; क ; ख ; ग ; घ ; ङ ; च ; छ ; ज ; झ ; ञ ; ट ; ठ ; ड ; ढ ; ण ; ण्\u200d ; त ; थ ; द ; ध ; न ; ऩ ; प ; फ ; ब ; भ ; म ; य ; र ; ऱ ; ल ; ळ ; ऴ ; व ; श ; ष ; स ; ष्\u200d ; त्र ; ज्ञ ; रू ; ह़ ; ॽ ; ऽ ; ा ; ू़ ; ृ ; ॄ ; ॅ ; ॆे ; ै ; ॉ ; ॊ ; ो ; ौ ; ् ; स्\u200d ; क़ ; ख़ ; ग़ ; ज़ ; ड़ ; ढ़ ; फ़ ; य़ ; ॠ ; ॡ ; ’ ; र् ; क्ष ; ब्\u200d ; । ; ? ; १ ; २ ; ३ ; ४ ; ५ ; ६ ; ७ ; ८ ; ९ ; - ; ि ; ी ; ु ; ॱ ; ‘ ; द्य ; श्\u200d ; , ; म्\u200d ; न्\u200d ; ज्\u200d ; व्\u200d ; प्\u200d ; ग्\u200d ; थ्\u200d ; त्\u200d ; च्\u200d ; भ्\u200d ; ध्\u200d ; ल्\u200d ; ख् ; ङ्\u200c ; ये ; बे ; के ; खे ; गे ; घे ; चे ; छे ; जे ; ने ; झे ; ते ; थे ; दे ; धे ; पे ; फे ; भे ; मे ; टे ; ठे ; गु ; गी ; र्\u200d ; द्व") 
 
    def test_khmrsimple(self):
        self.runsimple("ក ; ខ ; គ ; ឃ ; ង ; ច ; ឆ ; ជ ; ឈ ; ញ ; ដ ; ឋ ; ឌ ; ឍ ; ណ ; ត ; ថ ; ទ ; ធ ; ន ; ប ; ផ ; ព ; ភ ; ម ; យ ; រ ; ល ; វ ; ឝ ; ឞ ; ស ; ហ ; ឡ ; អ ; ា;ិ;ី;ឹ;ឺ;ុ;ូ;ួ ; ើ ; ឿ ; ៀ ; េ ; ែ ; ៃ ; ោ ; ៅ;ំ ; ះ ; ៈ;៉;៊;់;៌;៍;៎;៏;័;៑;្;៓;៝",
            '&ៅ << ំ << ះ << ៈ << ៉ << ៊ << ់ << ៌ << ៍ << ៎ << ៏ << ័ << ៑ &្ << ៓ << ៝',
            testsimple = 'ខ ; ក ; គ ; ឃ ; ង ; ច ; ឆ ; ជ ; ឈ ; ញ ; ដ ; ឋ ; ឌ ; ឍ ; ណ ; ត ; ថ ; ទ ; ធ ; ន ; ប ; ផ ; ព ; ភ ; ម ; យ ; រ ; ល ; វ ; ឝ ; ឞ ; ស ; ហ ; ឡ ; អ ; ា ; ិ ; ី ; ឹ ; ឺ ; ុ ; ូ ; ួ ; ើ ; ឿ ; ៀ ; េ ; ែ ; ៃ ; ោ ; ៅ ;  ំ ះ ៈ ៉ ៊ ់ ៌ ៍ ៎ ៏ ័ ៑ ៓ ៝ ; ្')

    def test_deva2simple(self):
        self.runsimple("अ ; अ़ ; आ ; इ ; ई ; उ़ ; उ ; ऊ ; ए ; ऐ ; ओ ; औ ; अं ; क ; क़ ; ख ; ख़ ; ग ; ग़ ; घ ; घ़ ; ङ ; च ; च़ ; छ ; छ़ ; ज ; ज़ ; झ ; झ़ ; ञ ; ट ; ठ ; ड़ ; ढ ; ण ; त ; त़ ; थ ; थ़ ; द ; द़ ; ध ; ध़ ; न ; ऩ ; प ; प़ ; फ ; फ़ ; ब ; ब़ ; भ ; भ़ ; म ; म़ ; य ; य़ ; र ; ऱ ; ल ; ल़ ; व ; व़ ; श ; स ; स़ ; ष ; ह ; ह़ ; क्ष ; ा ; ि;ु;ृ;े;ै ; ो ; ौ;ं;ँ;्\u200D ; ः",
            "&[before 1]आ < अ &उ़ < उ &क < क़ &ख < ख़ &ग < ग़ &घ < घ़ &च < च़ &छ < छ़ &ज < ज़ &झ < झ़ &त < त़ &थ < थ़ &द < द़ &ध < ध़ &न < ऩ &प < प़ &फ < फ़ &ब < ब़ &भ < भ़ &म < म़ &य < य़ &र < ऱ &ल < ल़ &व < व़ &स < स़ &ह < ह़ < क्ष &ौ << ं << ँ &् << ः/\u200d",
            testsimple = 'अ ; आ ; अ़ ; इ ; ई ; उ़ ; उ ; ऊ ; ए ; ऐ ; ओ ; औ ; अं ; क ; क़ ; ख ; ख़ ; ग ; ग़ ; घ ; घ़ ; ङ ; च ; च़ ; छ ; छ़ ; ज ; ज़ ; झ ; झ़ ; ञ ; ट ; ठ ; ड़ ; ढ ; ण ; त ; त़ ; थ ; थ़ ; द ; द़ ; ध ; ध़ ; न ; ऩ ; प ; प़ ; फ ; फ़ ; ब ; ब़ ; भ ; भ़ ; म ; म़ ; य ; य़ ; र ; ऱ ; ल ; ल़ ; व ; व़ ; श ; स ; स़ ; ष ; ह ; ह़ ; क्ष ; ा ; ि ; ु ; ृ ; े ; ै ; ो ; ौ ;  ं ँ ः ; ्')

if __name__ == "__main__":
    unittest.main()
 
