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
            r"&B << ꞌb <<< Ꞌb <<< ꞋB &D << ꞌd <<< Ꞌd <<< ꞋD << dr <<< Dr <<< DR &G << gb <<< Gb <<< GB << gbr <<< Gbr <<< GBR &Ị << ị́ <<< Ị́ << ɨ <<< Ɨ &K << kp <<< Kp <<< KP << kpr <<< Kpr <<< KPR &M << mb <<< Mb <<< MB &N << nd <<< Nd <<< ND << ndr <<< Ndr <<< NDR << ng <<< Ng <<< NG << ṇg <<< Ṇg <<< ṆG << ṇ <<< Ṇ << ngb <<< Ngb <<< NGB << ngbr <<< Ngbr <<< NGBR << nv <<< Nv <<< NV << ny <<< Ny <<< NY << nz <<< Nz <<< NZ &P << ph <<< Ph <<< PH &T << tr <<< Tr <<< TR &Ú << ụ <<< Ụ &Y << ꞌy <<< Ꞌy <<< ꞋY",
            testsimple = r"a/A á/Á ; b/B ꞌb/Ꞌb/ꞋB ; c/C ; d/D ꞌd/Ꞌd/ꞋD dr/Dr/DR ; e/E é/É ; f/F ; g/G gb/Gb/GB gbr/Gbr/GBR ; i/I í/Í ị/Ị ị́/Ị́ ɨ/Ɨ ; k/K kp/Kp/KP kpr/Kpr/KPR ; l/L ; m/M mb/Mb/MB ; n/N nd/Nd/ND ndr/Ndr/NDR ng/Ng/NG ṇg/Ṇg/ṆG ṇ/Ṇ ngb/NgbNGB ngbr/Ngbr/NGBR nv/Nv/NV ny/Ny/NY nz/Nz/NZ ; o/O ó/Ó ; p/P ph/Ph/PH ; r/R ṛ/Ṛ ; s/S ; t/T tr/Tr/TR ; u/U ú/Ú ụ/Ụ ; v/V ṿ/Ṿ ; w/W ; y/Y ꞌy/Ꞌy/ꞋY ; z/Z")

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
        self.runsimple("a/A; á/Á; à/À; â/Â; ä/Ä; Ā; ā̀/Ā̀; b/B; c/C; d/D; e/E; é/É; è/È; ê/Ê; ë/Ë; ē/Ē; ḗ; ḕ/Ḕ; f/F; g/G; g̱/G̱; ǥ/Ǥ; h/H; i/I; í/Í; ì/Ì; î/Î; ï/Ï; ī/Ī; ī̀/Ī̀; ɨ; j/J; k/K; ˈ; l/L; ḻ/Ḻ; m/M; n/N; ñ/Ñ; ng Ng; o/O; ó/Ó; ò/Ò; ô/Ô; ö/Ö; ō/Ō; ṑ/Ṑ; õ/Õ; p/P; ₱; q/Q; r/R; ṟ/Ṟ; s/S; t/T; u/U; ú/Ú; ù/Ù; û/Û; ü/Ü; ū/Ū; ū̀/Ū̀; v/V; w/W; w̱/W̱; x/X; y/Y; ɏ/Ɏ; z/Z, \'",
            "&A < á <<< Á < à <<< À < â <<< Â < ä <<< Ä < ā <<< Ā < ā̀ <<< Ā̀ &E < é <<< É < è <<< È < ê <<< Ê < ë <<< Ë < ē <<< Ē < ḗ <<< Ẽ́ < ḕ <<< Ḕ &G < g̱ <<< G̱ &I < í <<< Í < ì <<< Ì < î <<< Î < ï <<< Ï < ī <<< Ī < ī̀ <<< Ī̀ &K < ˈ &L < ḻ <<< Ḻ &N < ñ <<< Ñ < ng <<< Ng <<< NG &O < ó <<< Ó < ò <<< Ò < ô <<< Ô < ö <<< Ö < ō <<< Ō < ṑ <<< Ṑ < õ <<< Õ &P < ₱ &R < ṟ <<< Ṟ &U < ú <<< Ú < ù <<< Ù < û <<< Û < ü <<< Ü < ū <<< Ū < ū̀ <<< Ū̀ &W < w̱ <<< W̱ &Z < ''")
            # lonely stacked diacritic not given its capital counterpart (ẽ́)
            # lonely capitalized diacritic not given its lowercase counterpart (Ã)
            # incorrectly escaped apostrophe in simple sort should have its escaping corrected (backslash removed, extra apostrophe added). Currently the process adds an extra backslash and an extra apostrophe, resulting in &Z < \\''
        
    def test_latnsimple3(self):
        self.runsimple("a/A à À á Á â Â ǎ Ǎ a̧ A̧ ã Ã ā Ā ä Ä a̍ A̍ a̰ A̰; æ/Æ æ̀ Æ̀ æ̂ Æ̂; α/Ɑ; b/B; bh Bh; ɓ/Ɓ; c/C; ch Ch; d/D; ɗ/Ɗ; e/E è È é É ê Ê ě Ě ȩ Ȩ ẽ Ẽ ē Ē ë Ë e̍ E̍ ḛ Ḛ; ɛ/Ɛ ɛ̀ Ɛ̀ ɛ́ Ɛ́ ɛ̂ Ɛ̂ ɛ̌ Ɛ̌ ɛ̧ Ɛ̧ ɛ̃ Ɛ̃ ɛ̄ Ɛ̄ ɛ̈ Ɛ̈ ɛ̍ Ɛ̍ ɛ̰ Ɛ̰; f/F; g/G; gb Gb; gh Gh; h/H; i/I ì Ì í Í î Î ǐ Ǐ i̧ I̧ ĩ Ĩ ī Ī ï Ï i̍ I̍ ḭ Ḭ; ə/Ə ə̀ Ə̀ ə́ Ə́ ə̂ Ə̂ ə̌ Ə̌ ə̧ Ə̧ ə̃ Ə̃ ə̄ Ə̄ ə̈ Ə̈ ə̍ Ə̍ ə̰ Ə̰; ɨ/Ɨ ɨ̀ Ɨ̀ ɨ́ Ɨ́ ɨ̂ Ɨ̂ ɨ̌ Ɨ̌ ɨ̧ Ɨ̧ ɨ̃ Ɨ̃ ɨ̄ Ɨ̄ ɨ̈ Ɨ̈ ɨ̍ Ɨ̍ ɨ̰ Ɨ̰; j/J; '; k/K; kp Kp; l/L; m/M; n/N; ŋ/Ŋ; ny Ny; o/O ò Ò ó Ó ô Ô ǒ Ǒ o̧ O̧ õ Õ ō Ō ö Ö o̍ O̍ o̰ O̰; ɔ/Ɔ ɔ̀ Ɔ̀ ɔ́ Ɔ́ ɔ̂ Ɔ̂ ɔ̌ Ɔ̌ ɔ̧ Ɔ̧ ɔ̃ Ɔ̃ ɔ̄ Ɔ̄ ɔ̈ Ɔ̈ ɔ̍ Ɔ̍ ɔ̰ Ɔ̰; œ/Œ œ̀ Œ̀ œ́ Œ́ œ̂ Œ̂ œ̌ Œ̌ œ̧ Œ̧ œ̃ Œ̃ œ̄ Œ̄ œ̍ Œ̍ œ̰ Œ̰; ø/Ø; p/P; q/Q; r/R; s/S; sh Sh; t/T; u/U ù Ù ú Ú û Û ǔ Ǔ u̧ U̧ ũ Ũ ū Ū ü Ü u̍ U̍ ṵ Ṵ; ue UE ùe ÙE ûe ÛE ǔe ǓE; ʉ/Ʉ ʉ̀ Ʉ̀ ʉ́ Ʉ́ ʉ̂ Ʉ̂ ʉ̌ Ʉ̌ ʉ̧ Ʉ̧ ʉ̃ Ʉ̃ ʉ̄ Ʉ̄ ʉ̈ Ʉ̈ ʉ̍ Ʉ̍ ʉ̰ Ʉ̰ Ʉ̀ Ʉ́ Ʉ̌; v/V; w/W; ẅ; x/X; y/Y ỳ Ỳ ý Ý ŷ Ŷ y̌ Y̌ y̧ Y̧ ỹ Ỹ ȳ Ȳ y̍ Y̍ y̰ Y̰; ƴ/Ƴ; z/Z",
            "&A << à <<< À << á <<< Á << â <<< Â << ǎ <<< Ǎ << a̧ <<< A̧ << ã <<< Ã << ā <<< Ā << ä <<< Ä << a̍ <<< A̍ << a̰ <<< A̰ &Æ << æ̀ <<< Æ̀ << æ̂ <<< Æ̂ < ɑ <<< Ɑ &B < bh <<< Bh <<< BH &C < ch <<< Ch <<< CH &E << è <<< È << é <<< É << ê <<< Ê << ě <<< Ě << ȩ <<< Ȩ << ẽ <<< Ẽ << ē <<< Ē << ë <<< Ë << e̍ <<< E̍ << ḛ <<< Ḛ &Ɛ << ɛ̀ <<< Ɛ̀ << ɛ́ <<< Ɛ́ << ɛ̂ <<< Ɛ̂ << ɛ̌ <<< Ɛ̌ << ɛ̧ <<< Ɛ̧ << ɛ̃ <<< Ɛ̃ << ɛ̄ <<< Ɛ̄ << ɛ̈ <<< Ɛ̈ << ɛ̍ <<< Ɛ̍ << ɛ̰ <<< Ɛ̰ &G < gb <<< Gb <<< GB < gh <<< Gh <<< GH &I << ì <<< Ì << í <<< Í << î <<< Î << ǐ <<< Ǐ << i̧ <<< I̧ << ĩ <<< Ĩ << ī <<< Ī << ï <<< Ï << i̍ <<< I̍ << ḭ <<< Ḭ < ə <<< Ə << ə̀ <<< Ə̀ << ə́ <<< Ə́ << ə̂ <<< Ə̂ << ə̌ <<< Ə̌ << ə̧ <<< Ə̧ << ə̃ <<< Ə̃ << ə̄ <<< Ə̄ << ə̈ <<< Ə̈ << ə̍ <<< Ə̍ << ə̰ <<< Ə̰ &Ɨ << ɨ̀ <<< Ɨ̀ << ɨ́ <<< Ɨ́ << ɨ̂ <<< Ɨ̂ << ɨ̌ <<< Ɨ̌ << ɨ̧ <<< Ɨ̧ << ɨ̃ <<< Ɨ̃ << ɨ̄ <<< Ɨ̄ << ɨ̈ <<< Ɨ̈ << ɨ̍ <<< Ɨ̍ << ɨ̰ <<< Ɨ̰ &J < '' &K < kp <<< Kp <<< KP &Ŋ < ny <<< Ny <<< NY &O << ò <<< Ò << ó <<< Ó << ô <<< Ô << ǒ <<< Ǒ << o̧ <<< O̧ << õ <<< Õ << ō <<< Ō << ö <<< Ö << o̍ <<< O̍ << o̰ <<< O̰ < ɔ <<< Ɔ << ɔ̀ <<< Ɔ̀ << ɔ́ <<< Ɔ́ << ɔ̂ <<< Ɔ̂ << ɔ̌ <<< Ɔ̌ << ɔ̧ <<< Ɔ̧ << ɔ̃ <<< Ɔ̃ << ɔ̄ <<< Ɔ̄ << ɔ̈ <<< Ɔ̈ << ɔ̍ <<< Ɔ̍ << ɔ̰ <<< Ɔ̰ &Œ << œ̀ <<< Œ̀ << œ́ <<< Œ́ << œ̂ <<< Œ̂ << œ̌ <<< Œ̌ << œ̧ <<< Œ̧ << œ̃ <<< Œ̃ << œ̄ <<< Œ̄ << œ̍ <<< Œ̍ << œ̰ <<< Œ̰ < ø <<< Ø &S < sh <<< Sh <<< SH &U << ù << Ù << ú << Ú << û << Û << ǔ << Ǔ << u̧ <<< U̧ << ũ << Ũ << ū << Ū << ü << Ü << u̍ <<< U̍ << ṵ << Ṵ < ue <<< Ue <<< UE << ùe <<< Ùe <<< ÙE << ûe <<< Ûe <<< ÛE << ǔe <<< Ǔe <<< ǓE &Ʉ << ʉ̀ <<< Ʉ̀ << ʉ́ <<< Ʉ́ << ʉ̂ <<< Ʉ̂ << ʉ̌ <<< Ʉ̌ << ʉ̧ <<< Ʉ̧ << ʉ̃ <<< Ʉ̃ << ʉ̄ <<< Ʉ̄ << ʉ̈ <<< Ʉ̈ << ʉ̍ <<< Ʉ̍ << ʉ̰ <<< Ʉ̰ &W < ẅ < Ẅ &Y << ỳ <<< Ỳ << ý <<< Ý << ŷ <<< Ŷ << y̌ <<< Y̌ << y̧ <<< Y̧ << ỹ <<< Ỹ << ȳ <<< Ȳ << y̍ <<< Y̍ << y̰ <<< Y̰")
            # if greek alpha appears in collation with latn characters swap for latin alpha
            # spaced-out secondary sorted capital pairs that aren't made of two or more codepoints (i.e. "á Á") need to have correct triple arrow 
            # digraphs bh and gb were removed during minimizing
            # ẅ by itself, was not given the appropriate capitalized counterpart

if __name__ == "__main__":
    unittest.main()
 
