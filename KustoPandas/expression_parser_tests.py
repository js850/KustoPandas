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
        self.assertEqual(str(parsed), "((1 + ((2 * 3) / xx)) - 4)")
    
    def test_parse_math2(self):
        x = [Partial("3 + "), parse_math("6 / 2")]
        parsed = parse_math(x)
        self.assertEqual(str(parsed), "(3 + (6 / 2))")
    
    def test_parse_math3(self):
        x = [Partial("3 + "), parse_math("6 - 2"), Partial("/7")]
        parsed = parse_math(x)
        self.assertEqual(str(parsed), "(3 + ((6 - 2) / 7))")
    
    def test_parse_parentheses(self):
        x = "a + (y / (b - c) + q)*w + (4/2 - 1) "
        matches = find_matching_parentheses(x)
        parsed = parse_parentheses(x, matches)
        self.assertEqual(str(parsed), "((a + (((y / (b - c)) + q) * w)) + ((4 / 2) - 1))")



