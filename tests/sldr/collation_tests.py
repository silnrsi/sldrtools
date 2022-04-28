#!/usr/bin/env python3

import unittest
try:
    from sldr.collation import Collation, SortKey
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lib')))
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

    def test_convert(self):
        coll = Collation()
        test = """b/B
a/A á/Á
c/C"""
        alpha = coll.convertSimple(test.splitlines())
        coll.minimise(alpha)
        res = coll.asICU()
        self.assertEqual(res, "Fred")

if __name__ == "__main__":
    unittest.main()

