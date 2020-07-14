import unittest
from expression_parser import *

class TestExpressionParser(unittest.TestCase):
    def test_find_matching_parens(self):
        x = "hi(b) there(c + d(x))"
        matches = find_matching_parentheses(x)
        expected = np.array([0,0,2,0,-2,0,0,0,0,0,0,9,0,0,0,0,0,2,0,-2,-9])
        self.assertListEqual(list(expected), list(matches))

    def test_parse_math(self):
        x = "1 + 2*3/xx - 4"
        parsed = parse_math(x)
        #self.assertEqual(str(parsed), "((1 + ((2 * 3) / xx)) - 4)")
        self.assertEqual(-1, parsed.evaluate({"xx": 3}))

    
    def test_parse_math2(self):
        x = [Partial("3 + "), parse_math("6 / 2")]
        parsed = parse_math(x)
        #self.assertEqual(str(parsed), "(3 + (6 / 2))")
        self.assertEqual(6, parsed.evaluate(None))
    
    def test_parse_math3(self):
        x = [Partial("3 + "), parse_math("16 - 2"), Partial("/7")]
        parsed = parse_math(x)
        #self.assertEqual(str(parsed), "(3 + ((16 - 2) / 7))")
        self.assertEqual(5, parsed.evaluate(None))
    
    def test_parse_parentheses(self):
        x = "a + (y / (b - c) + q)*w + (4/2 - 1) "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        #self.assertEqual(str(parsed), "((a + (((y / (b - c)) + q) * w)) + ((4 / 2) - 1))")
        self.assertEqual(4.2, parsed.evaluate({"a": 1, "y": 1, "b": 7, "c": 6, "q": 1, "w":1.1}))

    def test_parse_parentheses_equal(self):
        x = "1 + 3 ==8/2 "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        self.assertEqual(str(parsed), "((1 + 3) == (8 / 2))")
        self.assertEqual(True, parsed.evaluate(None))
    
    def test_parse_parentheses_not_equal(self):
        x = "1*3!=9/3 "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        self.assertEqual(str(parsed), "((1 * 3) != (9 / 3))")
        self.assertEqual(False, parsed.evaluate(None))

    def test_parse_parentheses_lt(self):
        x = "1 < (6 - 4) "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        self.assertEqual(str(parsed), "(1 < (6 - 4))")
        self.assertEqual(True, parsed.evaluate(None))
    
    def test_parse_parentheses_gt(self):
        x = "1 > (6 - 4) "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        self.assertEqual(str(parsed), "(1 > (6 - 4))")
        self.assertEqual(False, parsed.evaluate(None))

    def test_parse_parentheses_ge(self):
        x = "1 >= (6 - 5) "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        self.assertEqual(str(parsed), "(1 >= (6 - 5))")
        self.assertEqual(True, parsed.evaluate(None))

    def test_parse_parentheses_le(self):
        x = "1 <= (6 - 4) "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        self.assertEqual(str(parsed), "(1 <= (6 - 4))")
        self.assertEqual(True, parsed.evaluate(None))


