import unittest
from expression_parser import *

class TestExpressionParser(unittest.TestCase):
    def test_find_matching_parens(self):
        x = "hi(b) there(c + d(x))"
        matches = find_matching_parentheses(x)
        expected = np.array([0,0,2,0,-2,0,0,0,0,0,0,9,0,0,0,0,0,2,0,-2,-9])
        self.assertListEqual(list(expected), list(matches))

    # def test_parse_math(self):
    #     x = "1 + 2*3/xx - 4"
    #     x = explode_line(x)
    #     parsed = parse_math(x)
    #     #self.assertEqual(str(parsed), "((1 + ((2 * 3) / xx)) - 4)")
    #     self.assertEqual(-1, parsed.evaluate({"xx": 3}))

    
    # def test_parse_math2(self):
    #     x = explode_line("3 + ") + [parse_math(explode_line("6 / 2"))]
    #     parsed = parse_math(x)
    #     #self.assertEqual(str(parsed), "(3 + (6 / 2))")
    #     self.assertEqual(6, parsed.evaluate(None))
    
    # def test_parse_math3(self):
    #     x = explode_line("3 +") + [parse_math(explode_line("16 - 2"))] + explode_line("/7")
    #     parsed = parse_math(x)
    #     #self.assertEqual(str(parsed), "(3 + ((16 - 2) / 7))")
    #     self.assertEqual(5, parsed.evaluate(None))
    
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
    
    # def test_explode_line(self):
    #     x = "x =1<=2"
    #     exploded = explode_line(x)
    #     expected = ["x", " ", Assignment, "1", Le, "2"]
    #     self.assertListEqual(expected, exploded)

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
    
    def test_parse_parens_on_left(self):
        x = "(1 + 2) / 3"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "((1 + 2) / 3)")
        self.assertEqual(1, parsed.evaluate(None))
    
    def test_parse_methods(self):
        x = "2 * xx(5)"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(2 * xx(5))")
        self.assertEqual(12, parsed.evaluate({"xx": lambda x: (x + 1)}))
    
    def test_parse_methods2(self):
        x = "(1 + 3) * x_1(5) + y(6, 7)"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(((1 + 3) * x_1(5)) + y(6, 7))")
        def y(a, b):
            return a + b
        self.assertEqual(37, parsed.evaluate({"x_1": lambda x: (x + 1), "y": y}))
    
    def test_parse_methods_sub_method(self):
        x = "1 + z(a(), b(3))"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(1 + z(a(), b(3)))")
        def z(a, b):
            return a + b
        def a():
            return 3
        def b(i):
            return 2*i
        self.assertEqual(10, parsed.evaluate({"z": z, "a": a, "b": b}))
 
    def test_parse_method_no_args(self):
        x = "2 * xx()"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(2 * xx())")
        def f():
            return 7
        self.assertEqual(14, parsed.evaluate({"xx": f}))

    def test_parse_parts_of_line(self):
        x = "1.0 + xx + yy*(a + b) + zz(3, w) + (1 >= 2)"
        parsed = parse_parts_of_line(x)
        print(x)
        print(parsed)
    
    # def test_two_operators_in_a_row(self):
    #     x = "1 + + 2"
    #     with self.assertRaisesRegex(Exception, "Parsing error: Found two operators in a row.*"):
    #         parse_statement(x)
    
    def test_string_literal(self):
        x = "y = \"hello \""
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(y = \"hello \")")
        result = parsed.evaluate(None)
        self.assertEqual(result["y"], "hello ")

    def test_string_literal2(self):
        x = "y = xx(\"hello there\")"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(y = xx(\"hello there\"))")

        def xx(s):
            return s + "_suffix"
        result = parsed.evaluate({"xx": xx})
        self.assertEqual(result["y"], "hello there_suffix")
    
    def test_contains_ignores_case(self):
        x = "y = A contains \"hello\""
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(y = (A contains \"hello\"))")

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result["y"], True)
    
    def test_notcontains(self):
        x = "y = A !contains \"hello\""
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(y = (A !contains \"hello\"))")

        result = parsed.evaluate({"A": "hello there"})
        self.assertEqual(result["y"], False)
    
    def test_unary_minus(self):
        x = "y = -1 + (-xx)"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(y = ((-1) + (-xx)))")

        result = parsed.evaluate({"xx": -1})
        self.assertEqual(result["y"], 0)
    
    def test_unary_minus2(self):
        x = "y = -1 + -(-xx)"
        parsed = parse_statement(x)
        self.assertEqual(str(parsed), "(y = ((-1) + (-(-xx))))")

        result = parsed.evaluate({"xx": 1})
        self.assertEqual(result["y"], 0)

    def test_parse_rest_parts(self):
        x = "y = -1 + \"hi\" + (-xx)"
        parsed = parse_string_literals_parts(x)
        print("\n" + str(parsed))
        parsed2 = parse_rest_parts(parsed)

        print("\n" + str(parsed2))