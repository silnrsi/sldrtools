#!/usr/bin/env python3

import unittest
from sldr.collation import Collation, SortKey
import unicodedata as ud

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
        self.assertEqual(ud.normalize("NFC", res), ud.normalize("NFC", outstr))
        self.assertEqual(ud.normalize("NFC", tres), ud.normalize("NFC", instr) if testsimple is None else ud.normalize("NFC", testsimple))

    def runtailor(self, instr, outstr):
        coll = Collation()
        coll.parse(instr)
        coll.minimise()
        asicu = coll.asICU()
        res = " ".join(asicu.split("\n"))
        self.assertEqual(res, outstr)

    def test_short(self):
        self.runsimple(r"b/B ; a/A ; á/Á ; c/C ; d/D",
            r"&[before 1]a < b <<< B &A < á <<< Á")

    def test_beforeaSimple(self):
        self.runsimple(r"ꞌ/Ꞌ ; a/A ; b/B ; bb/Bb/BB ; c/C ; d/D ; e/E ; ë/Ë ; f/F",
            r"&[before 1]a < ꞌ <<< Ꞌ &B < bb <<< Bb <<< BB &E < ë <<< Ë")

    def test_ngexpandSimple(self):
        self.runsimple(r"ꞌ/Ꞌ ; a/A ; b/B ; c/C ; d/D ; e/E ; f/F; g/G; NGY; h/H",
                r"&[before 1]a < ꞌ <<< Ꞌ &G < ngy <<< Ngy <<< NGy <<< NGY",
                testsimple = r"ꞌ/Ꞌ ; a/A ; b/B ; c/C ; d/D ; e/E ; f/F ; g/G ; ngy/Ngy/NGy/NGY ; h/H")

    def test_lotsSimple(self):
        self.runsimple(r"a/A á/Á; b/B ꞌb; c/C; d/D ꞌd dr; e/E é/É; f/F; g/G gb gbr; i/I í/Í ị/Ị ị́ ɨ/Ɨ ɨ; k/K kp kpr; l/L; m/M mb; n/N nd ndr ng ṇg ṇ/Ṇ ngb ngbr nv ny nz; o/O ó/Ó; p/P ph; r/R ṛ/Ṛ; s/S; t/T tr; u/U ú/Ú ụ/Ụ ụ; v/V ṿ/Ṿ; w/W; y/Y ꞌy; z/Z",
            r"&B << ꞌb <<< Ꞌb <<< ꞋB &D << ꞌd <<< Ꞌd <<< ꞋD << dr <<< Dr <<< DR &G << gb <<< Gb <<< GB << gbr <<< Gbr <<< GBr <<< GBR &Ị << ị́ <<< Ị́ << ɨ <<< Ɨ &K << kp <<< Kp <<< KP << kpr <<< Kpr <<< KPr <<< KPR &M << mb <<< Mb <<< MB &N << nd <<< Nd <<< ND << ndr <<< Ndr <<< NDr <<< NDR << ng <<< Ng <<< NG << ṇg <<< Ṇg <<< ṆG << ṇ <<< Ṇ << ngb <<< Ngb <<< NGb <<< NGB << ngbr <<< Ngbr <<< NGbr <<< NGBr <<< NGBR << nv <<< Nv <<< NV << ny <<< Ny <<< NY << nz <<< Nz <<< NZ &P << ph <<< Ph <<< PH &T << tr <<< Tr <<< TR &Ú << ụ <<< Ụ &Y << ꞌy <<< Ꞌy <<< ꞋY",
            testsimple = r"a/A á/Á ; b/B ꞌb/Ꞌb/ꞋB ; c/C ; d/D ꞌd/Ꞌd/ꞋD dr/Dr/DR ; e/E é/É ; f/F ; g/G gb/Gb/GB gbr/Gbr/GBr/GBR ; i/I í/Í ị/Ị ị́/Ị́ ɨ/Ɨ ; k/K kp/Kp/KP kpr/Kpr/KPr/KPR ; l/L ; m/M mb/Mb/MB ; n/N nd/Nd/ND ndr/Ndr/NDr/NDR ng/Ng/NG ṇg/Ṇg/ṆG ṇ/Ṇ ngb/Ngb/NGb/NGB ngbr/Ngbr/NGbr/NGBr/NGBR nv/Nv/NV ny/Ny/NY nz/Nz/NZ ; o/O ó/Ó ; p/P ph/Ph/PH ; r/R ṛ/Ṛ ; s/S ; t/T tr/Tr/TR ; u/U ú/Ú ụ/Ụ ; v/V ṿ/Ṿ ; w/W ; y/Y ꞌy/Ꞌy/ꞋY ; z/Z")

    def test_beforeTailor(self):
        self.runtailor(r"&[before 1]a < â < Å < b <<< B < b̃ <<< B̃ < |e <<< |E < c <<< C < d <<< D < e <<< E < È << ê <<< Ê << é <<< É << ë <<< Ë << ē <<< Ē << è < f <<< F < g <<< G < Gb < h <<< H < i <<< I < j <<< J < k <<< K < l <<< L < m <<< M < n <<< N < ½ < o <<< O < ô <<< Ô << ö <<< Ö < p <<< P < q <<< Q < r <<< R < s <<< S < t <<< T < u <<< U < ü <<< Ü < v <<< V < w <<< W < x <<< X < y <<< Y < × < z <<< Z < ɓ <<< Ɓ << Û < ɗ <<< Ɗ << ¬ < ɨ <<< Ɨ < ? < ' < m̃ <<< M̃",
            r"&[before 1]a < â < Å &B < b̃ <<< B̃ < \|e <<< \|E &E < È << ê <<< Ê << é <<< É << ë <<< Ë << ē <<< Ē << è &G < Gb &N < ½ &O < ô <<< Ô << ö <<< Ö &U < ü <<< Ü &Y < × &Z < ɓ <<< Ɓ << Û < ɗ <<< Ɗ << ¬ < ɨ <<< Ɨ < \? < '' < m̃ <<< M̃")

    def test_devasimple(self):
        self.runsimple("ँ ;ं ; ः ; ऄ ; अ ; आ ; इ ; ई ; उ ; ऊ ; ऋ ; ऌ ; ऍ ; ऎ ; ए ; ऐ ; ऑ ; ऒ ; ओ ; औ ; क ; ख ; ग ; घ ; ङ ; च ; छ ; ज ; झ ; ञ ; ट ; ठ ; ड ; ढ ; ण ; ण्\u200D ; त ; थ ; द ; ध ; न ; ऩ ; प ; फ ; ब ; भ ; म ; य ; र ; ऱ ; ल ; ळ ; ऴ ; व ; श ; ष ; स ; ष्\u200D ; त्र ; ज्ञ ; रू ; ह़ ; ॽ ; ऽ ;  ; ा ; ू़ ; ृ ; ॄ ;ॅ ; ॆे ; ै ; ॉ ; ॊ ; ो ; ौ;् ;् \u200C ; क्\u200D ; स्\u200D ; क़ ; ख़ ; ग़ ; ज़ ; ड़ ; ढ़ ; फ़ ; य़ ; ॠ ; ॡ ; ’ ; र् ; क्ष ; ब्\u200D ; । ; ? ; १ ; २ ; ३ ; ४ ; ५ ; ६ ; ७ ; ८ ; ९ ; - ; ि ; ी ; अ ; आ ; इ ; ई ; उ ; ऊ ; ऋ ; ऌ ; ऍ ; ऎ ; ए ; ऐ ; ऑ ; ऒ ; ओ ; औ ; क ; ख ; ग ; घ ; ङ ; च ; छ ; ज ; झ ; ञ ; ट ; ठ ; ड ; ढ ; ण ; त ; थ ; द ; ध ; न ; ऩ ; प ; फ ; ब ; भ ; म ; य ; र ; ऱ ; ल ; ळ ; ऴ ; व ; श ; ष ; स ; ह़ ; ऽ ; क़ ; ख़ ; ग़ ; ज़ ; ड़ ; ढ़ ; फ़ ; य़ ; ॠ ; ॡ ; ;ु ; ॱ ; ‘ ; द्य ; श्\u200D ;  ;  ; , ; म्\u200D ; न्\u200D ; ज्\u200D ; व्\u200D ; प्\u200D ; ग्\u200D ; थ्\u200D ; त्\u200D ; च्\u200D ; भ्\u200D ; ध्\u200D ; ल्\u200D ; ख् ; ङ्\u200C ; ये ; बे ; के ; खे ; गे ; घे ; चे ; छे ; जे ; ने ; झे ; ते ; थे ; दे ; धे ; पे ; फे ; भे ; मे ; टे ; ठे ; गु ; गी ; र्\u200D ; द्व",
            "&ण < ण्‍ &न < ऩ &र < ऱ &ळ < ऴ &स < ष्‍ < त्र < ज्ञ < रू < ह़ < ॽ &ा < ू़ &ॅ < ॆे &् << ‌ &क < स्‍/्‍ < क़/्‍ < ख़/्‍ < ग़/्‍ < ज़/्‍ < ड़/्‍ < ढ़/्‍ < फ़/्‍ < य़/्‍ < ॠ/्‍ < ॡ/्‍ < ’/्‍ < र्/्‍ < क्ष/्‍ < ब्‍/्‍ < ।/्‍ < \\?/्‍ < १/्‍ < २/्‍ < ३/्‍ < ४/्‍ < ५/्‍ < ६/्‍ < ७/्‍ < ८/्‍ < ९/्‍ < \\-/्‍ < ि/्‍ < ी/्‍ < ु/्‍ < ॱ/्‍ < ‘/्‍ < द्य/्‍ < श्‍/्‍ < \\,/्‍ < म्‍/्‍ < न्‍/्‍ < ज्‍/्‍ < व्‍/्‍ < प्‍/्‍ < ग्‍/्‍ < थ्‍/्‍ < त्‍/्‍ < च्‍/्‍ < भ्‍/्‍ < ध्‍/्‍ < ल्‍/्‍ < ख्/्‍ < ङ्‌/्‍ < ये/्‍ < बे/्‍ < के/्‍ < खे/्‍ < गे/्‍ < घे/्‍ < चे/्‍ < छे/्‍ < जे/्‍ < ने/्‍ < झे/्‍ < ते/्‍ < थे/्‍ < दे/्‍ < धे/्‍ < पे/्‍ < फे/्‍ < भे/्‍ < मे/्‍ < टे/्‍ < ठे/्‍ < गु/्‍ < गी/्‍ < र्‍/्‍ < द्व/्‍",
            testsimple = " ं ँ ः \u200c ; अ ; ऄ ; आ ; इ ; ई ; उ ; ऊ ; ऋ ; ऌ ; ऍ ; ऎ ; ए ; ऐ ; ऑ ; ऒ ; ओ ; औ ; क ; ख ; ग ; घ ; ङ ; च ; छ ; ज ; झ ; ञ ; ट ; ठ ; ड ; ढ ; ण ; ण्\u200d ; त ; थ ; द ; ध ; न ; ऩ ; प ; फ ; ब ; भ ; म ; य ; र ; ऱ ; ल ; ळ ; ऴ ; व ; श ; ष ; स ; ष्\u200d ; त्र ; ज्ञ ; रू ; ह़ ; ॽ ; ऽ ; ा ; ू़ ; ृ ; ॄ ; ॅ ; ॆे ; ै ; ॉ ; ॊ ; ो ; ौ ; ् ; स्\u200d ; क़ ; ख़ ; ग़ ; ज़ ; ड़ ; ढ़ ; फ़ ; य़ ; ॠ ; ॡ ; ’ ; र् ; क्ष ; ब्\u200d ; । ; ? ; १ ; २ ; ३ ; ४ ; ५ ; ६ ; ७ ; ८ ; ९ ; - ; ि ; ी ; ु ; ॱ ; ‘ ; द्य ; श्\u200d ; , ; म्\u200d ; न्\u200d ; ज्\u200d ; व्\u200d ; प्\u200d ; ग्\u200d ; थ्\u200d ; त्\u200d ; च्\u200d ; भ्\u200d ; ध्\u200d ; ल्\u200d ; ख् ; ङ्\u200c ; ये ; बे ; के ; खे ; गे ; घे ; चे ; छे ; जे ; ने ; झे ; ते ; थे ; दे ; धे ; पे ; फे ; भे ; मे ; टे ; ठे ; गु ; गी ; र्\u200d ; द्व")

    def test_khmrsimple(self):
        self.runsimple("ក ; ខ ; គ ; ឃ ; ង ; ច ; ឆ ; ជ ; ឈ ; ញ ; ដ ; ឋ ; ឌ ; ឍ ; ណ ; ត ; ថ ; ទ ; ធ ; ន ; ប ; ផ ; ព ; ភ ; ម ; យ ; រ ; ល ; វ ; ឝ ; ឞ ; ស ; ហ ; ឡ ; អ ; ា;ិ;ី;ឹ;ឺ;ុ;ូ;ួ ; ើ ; ឿ ; ៀ ; េ ; ែ ; ៃ ; ោ ; ៅ;ំ ; ះ ; ៈ;៉;៊;់;៌;៍;៎;៏;័;៑;្;៓;៝",
            '&ៅ << ំ << ះ << ៈ << ៉ << ៊ << ់ << ៌ << ៍ << ៎ << ៏ << ័ << ៑ &្ << ៓ << ៝',
            testsimple = 'ខ ; ក ; គ ; ឃ ; ង ; ច ; ឆ ; ជ ; ឈ ; ញ ; ដ ; ឋ ; ឌ ; ឍ ; ណ ; ត ; ថ ; ទ ; ធ ; ន ; ប ; ផ ; ព ; ភ ; ម ; យ ; រ ; ល ; វ ; ឝ ; ឞ ; ស ; ហ ; ឡ ; អ ; ា ; ិ ; ី ; ឹ ; ឺ ; ុ ; ូ ; ួ ; ើ ; ឿ ; ៀ ; េ ; ែ ; ៃ ; ោ ; ៅ ;  ំ ះ ៈ ៉ ៊ ់ ៌ ៍ ៎ ៏ ័ ៑ ៓ ៝ ; ្')

    def test_deva2simple(self):
        self.runsimple("अ ; अ़ ; आ ; इ ; ई ; उ़ ; उ ; ऊ ; ए ; ऐ ; ओ ; औ ; अं ; क ; क़ ; ख ; ख़ ; ग ; ग़ ; घ ; घ़ ; ङ ; च ; च़ ; छ ; छ़ ; ज ; ज़ ; झ ; झ़ ; ञ ; ट ; ठ ; ड़ ; ढ ; ण ; त ; त़ ; थ ; थ़ ; द ; द़ ; ध ; ध़ ; न ; ऩ ; प ; प़ ; फ ; फ़ ; ब ; ब़ ; भ ; भ़ ; म ; म़ ; य ; य़ ; र ; ऱ ; ल ; ल़ ; व ; व़ ; श ; स ; स़ ; ष ; ह ; ह़ ; क्ष ; ा ; ि;ु;ृ;े;ै ; ो ; ौ;ं;ँ;्\u200D ; ः",
            "&[before 1]आ < अ < अ़ &ई < उ़ &औ < अं &क < क़ &ख < ख़ &ग < ग़ &घ < घ़ &च < च़ &छ < छ़ &ज < ज़ &झ < झ़ &ठ < ड़ &त < त़ &थ < थ़ &द < द़ &ध < ध़ &न < ऩ &प < प़ &फ < फ़ &ब < ब़ &भ < भ़ &म < म़ &य < य़ &र < ऱ &ल < ल़ &व < व़ &श < स < स़ &ह < ह़ < क्ष &ौ << ं << ँ &् << ः/‍",
            testsimple = 'अ ; आ ; अ़ ; इ ; ई ; उ़ ; उ ; ऊ ; ए ; ऐ ; ओ ; औ ; अं ; क ; क़ ; ख ; ख़ ; ग ; ग़ ; घ ; घ़ ; ङ ; च ; च़ ; छ ; छ़ ; ज ; ज़ ; झ ; झ़ ; ञ ; ट ; ठ ; ड़ ; ढ ; ण ; त ; त़ ; थ ; थ़ ; द ; द़ ; ध ; ध़ ; न ; ऩ ; प ; प़ ; फ ; फ़ ; ब ; ब़ ; भ ; भ़ ; म ; म़ ; य ; य़ ; र ; ऱ ; ल ; ल़ ; व ; व़ ; श ; स ; स़ ; ष ; ह ; ह़ ; क्ष ; ा ; ि ; ु ; ृ ; े ; ै ; ो ; ौ ;  ं ँ ः ; ्')

    def test_latnsimple(self):
        self.runsimple(r"a/A á/Á ; b/B ; c/C ; d/D ; e/E é/É ; f/F ; g/G ; h/H ; i/I í/Í ; ɨ/Ɨ ɨ́/Ɨ́ ; p/P ; k/K ; j/J ; l/L ; m/M ; n/N ; ŋ/Ŋ ; o/O ó/Ó ; q/Q ; r/R ; s/S ; t/T ; u/U ú/Ú ; v/V ; w/W ; x/X ; y/Y ; z/Z",
            r"&Ɨ << ɨ́ <<< Ɨ́ < p <<< P < k <<< K")
        
    def test_latnsimple2(self):
        self.runsimple("e/E; ḗ; ḕ/Ḕ",
            "&E < ḗ <<< Ḗ < ḕ <<< Ḕ",
            testsimple = "e/E ; ḗ/Ḗ ; ḕ/Ḕ")

    def test_latnsimple3(self):
        self.runsimple("z/Z ; \'",
            "&[before 1]'' < z <<< Z")
    
    def test_latnsimple4(self):
        self.runsimple("w/W; ẅ",
            "&ẅ <<< Ẅ",
            testsimple = "w/W ; ẅ/Ẅ")
        
    def test_latnsimple5(self):
        self.runsimple("a/A à À á Á â Â ǎ Ǎ a̧ A̧ ã Ã ā Ā ä Ä a̍ A̍ a̰ A̰; æ/Æ æ̀ Æ̀ æ̂ Æ̂",
            "&A << à <<< À << á <<< Á << â <<< Â << ǎ <<< Ǎ << a̧ <<< A̧ << ã <<< Ã << ā <<< Ā << ä <<< Ä << a̍ <<< A̍ << a̰ <<< A̰ &Æ << æ̀ <<< Æ̀ << æ̂ <<< Æ̂",
            testsimple = "a/A à/À á/Á â/Â ǎ/Ǎ a̧/A̧ ã/Ã ā/Ā ä/Ä a̍/A̍ a̰/A̰ ; æ/Æ æ̀/Æ̀ æ̂/Æ̂")

if __name__ == "__main__":
    unittest.main()
 
