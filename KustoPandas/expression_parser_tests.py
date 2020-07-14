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
        x = explode_line(x)
        parsed = parse_math(x)
        #self.assertEqual(str(parsed), "((1 + ((2 * 3) / xx)) - 4)")
        self.assertEqual(-1, parsed.evaluate({"xx": 3}))

    
    def test_parse_math2(self):
        x = explode_line("3 + ") + [parse_math(explode_line("6 / 2"))]
        parsed = parse_math(x)
        #self.assertEqual(str(parsed), "(3 + (6 / 2))")
        self.assertEqual(6, parsed.evaluate(None))
    
    def test_parse_math3(self):
        x = explode_line("3 +") + [parse_math(explode_line("16 - 2"))] + explode_line("/7")
        parsed = parse_math(x)
        #self.assertEqual(str(parsed), "(3 + ((16 - 2) / 7))")
        self.assertEqual(5, parsed.evaluate(None))
    
    def test_parse_parentheses(self):
        x = "a + (y / (b - c) + q)*w + (4/2 - 1) "
        parsed = parse_statement(x)
        #self.assertEqual(str(parsed), "((a + (((y / (b - c)) + q) * w)) + ((4 / 2) - 1))")
        self.assertEqual(4.2, parsed.evaluate({"a": 1, "y": 1, "b": 7, "c": 6, "q": 1, "w":1.1}))

    def test_parse_parentheses_equal(self):
        x = "1 + 3 ==8/2 "
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "((1 + 3) == (8 / 2))")
        self.assertEqual(True, parsed.evaluate(None))
    
    def test_parse_parentheses_not_equal(self):
        x = "1*3!=9/3 "
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "((1 * 3) != (9 / 3))")
        self.assertEqual(False, parsed.evaluate(None))

    def test_parse_parentheses_lt(self):
        x = "1 < (6 - 4) "
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(1 < (6 - 4))")
        self.assertEqual(True, parsed.evaluate(None))
    
    def test_parse_parentheses_gt(self):
        x = "1 > (6 - 4) "
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(1 > (6 - 4))")
        self.assertEqual(False, parsed.evaluate(None))

    def test_parse_parentheses_ge(self):
        x = "1 >= (6 - 5) "
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(1 >= (6 - 5))")
        self.assertEqual(True, parsed.evaluate(None))

    def test_parse_parentheses_le(self):
        x = "1 <= (6 - 4) "
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(1 <= (6 - 4))")
        self.assertEqual(True, parsed.evaluate(None))
    
    def test_explode_line(self):
        x = "x =1<=2"
        exploded = explode_line(x)
        expected = ["x", " ", Assignment, "1", Le, "2"]
        self.assertListEqual(expected, exploded)

    def test_parse_statement_Or(self):
        x = "1 > 1 || 3 > 2"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "((1 > 1) || (3 > 2))")
        self.assertEqual(True, parsed.evaluate(None))

    def test_parse_statement_And(self):
        x = "1 > 1 && 3 > 2"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "((1 > 1) && (3 > 2))")
        self.assertEqual(False, parsed.evaluate(None))
    
    def test_parse_statement_Asignment(self):
        x = "x14 = 1 + 3 == 4"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(x14 = ((1 + 3) == 4))")
        result = parsed.evaluate(None)
        self.assertEqual(True, result["x14"])