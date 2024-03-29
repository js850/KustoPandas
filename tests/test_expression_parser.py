import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from kusto_pandas.expression_parser import parse_expression
from kusto_pandas.expression_parser.expression_tree import find_matching_parentheses

class TestExpressionParser(unittest.TestCase):
    def test_find_matching_parens(self):
        x = "hi(b) there(c + d(x))"
        matches = find_matching_parentheses(x)
        expected = np.array([0,0,2,0,-2,0,0,0,0,0,0,9,0,0,0,0,0,2,0,-2,-9])
        self.assertListEqual(list(expected), list(matches))

    def test_parse_parentheses(self):
        x = "a + (y / (b - c) + q)*w + (4/2 - 1) "
        parsed = parse_expression(x)
        #self.assertEqual(str(parsed), "((a + (((y / (b - c)) + q) * w)) + ((4 / 2) - 1))")
        self.assertEqual(4.2, parsed.evaluate({"a": 1, "y": 1, "b": 7, "c": 6, "q": 1, "w":1.1}))

    def test_parse_parentheses_equal(self):
        x = "1 + 3 ==8/2 "
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "((1 + 3) == (8 / 2))")
        self.assertEqual(True, parsed.evaluate(None))
    
    def test_parse_parentheses_not_equal(self):
        x = "1*3!=9/3 "
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "((1 * 3) != (9 / 3))")
        self.assertEqual(False, parsed.evaluate(None))

    def test_parse_parentheses_lt(self):
        x = "1 < (6 - 4) "
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(1 < (6 - 4))")
        self.assertEqual(True, parsed.evaluate(None))
    
    def test_parse_parentheses_gt(self):
        x = "1 > (6 - 4) "
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(1 > (6 - 4))")
        self.assertEqual(False, parsed.evaluate(None))

    def test_parse_parentheses_ge(self):
        x = "1 >= (6 - 5) "
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(1 >= (6 - 5))")
        self.assertEqual(True, parsed.evaluate(None))

    def test_parse_parentheses_le(self):
        x = "1 <= (6 - 4) "
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(1 <= (6 - 4))")
        self.assertEqual(True, parsed.evaluate(None))
    
    # def test_explode_line(self):
    #     x = "x =1<=2"
    #     exploded = explode_line(x)
    #     expected = ["x", " ", Assignment, "1", Le, "2"]
    #     self.assertListEqual(expected, exploded)

    def test_parse_square_brackets(self):
        x = "x[4 ]"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "x[4]")
        #self.assertEqual(True, parsed.evaluate(None))

    def test_parse_square_brackets_assignment(self):
        x = "a = x[4 ]"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(a = x[4])")
        #self.assertEqual(True, parsed.evaluate(None))

    def test_parse_square_brackets_with_parentheses(self):
        x = "a = (x[y(2) + (4 - 1)] - 1)"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(a = (x[(y(2) + (4 - 1))] - 1))")
        #self.assertEqual(True, parsed.evaluate(None))

    # def test_parse_square_brackets_applied_to_non_var_throws(self):
    #     x = "a = 4[5]"
    #     with self.assertRaises(Exception) as context:
    #         parse_expression(x)

    def test_parse_square_brackets_negative_index(self):
        x = "x[-2]"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "x[(-2)]")
        self.assertEqual(1, parsed.evaluate({"x": [1, 2]}))

    def test_parse_expression_Or(self):
        x = "1 > 1 or 3 > 2"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "((1 > 1) or (3 > 2))")
        self.assertEqual(True, parsed.evaluate(None))

    def test_parse_expression_And(self):
        x = "1 > 1 and 3 > 2"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "((1 > 1) and (3 > 2))")
        self.assertEqual(False, parsed.evaluate(None))
    
    def test_parse_expression_Asignment(self):
        x = "x14 = 1 + 3 == 4"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(x14 = ((1 + 3) == 4))")
        result = parsed.evaluate(None)
        self.assertEqual(True, result["x14"])
    
    def test_parse_parens_on_left(self):
        x = "(1 + 2) / 3"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "((1 + 2) / 3)")
        self.assertEqual(1, parsed.evaluate(None))
    
    def test_parse_methods(self):
        x = "2 * xx(5)"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(2 * xx(5))")
        self.assertEqual(12, parsed.evaluate({"xx": lambda x: (x + 1)}))

    def test_parse_method_multiple_args(self):
        x = "2 * xx(1, 2, 3, 4)"
        parsed = parse_expression(x)
        def xx(a, b, c, d):
            return a + b + c + d
        self.assertEqual(str(parsed), "(2 * xx(1, 2, 3, 4))")
        self.assertEqual(20, parsed.evaluate({"xx": xx}))
    
    def test_parse_methods3(self):
        x = "iff(W > 0, B, C)"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "iff((W > 0), B, C)")
        def iff(a, b, c):
            if a:
                return b
            else:
                return c
        self.assertEqual(2, parsed.evaluate({"W": 1, "B": 2, "C": 3, "iff": iff}))

    # def test_method_expression(self):
    #     x = "y = (1, 2, 3)"
    #     parsed = parse_expression(x)
    #     self.assertEqual(str(parsed), "(y = (1, 2, 3))")
    #     result = parsed.evaluate(None)
    #     self.assertListEqual(list(result["y"]), [1, 2, 3])

    def test_parse_methods_sub_method(self):
        x = "1 + z(a(), b(3))"
        parsed = parse_expression(x)
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
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(2 * xx())")
        def f():
            return 7
        self.assertEqual(14, parsed.evaluate({"xx": f}))

    def test_parse_expression3(self):
        x = "1.0 + xx + yy*(a + b) + zz(3, w) + (1 >= 2)"
        parsed = parse_expression(x)
        print(x)
        print(parsed)
    
    # def test_two_operators_in_a_row(self):
    #     x = "1 + + 2"
    #     with self.assertRaisesRegex(Exception, "Parsing error: Found two operators in a row.*"):
    #         parse_expression(x)
    
    def test_string_literal(self):
        x = "y = \"hello \""
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = \"hello \")")
        result = parsed.evaluate(None)
        self.assertEqual(result["y"], "hello ")

    def test_string_literal2(self):
        x = "y = xx(\"hello there\")"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = xx(\"hello there\"))")

        def xx(s):
            return s + "_suffix"
        result = parsed.evaluate({"xx": xx})
        self.assertEqual(result["y"], "hello there_suffix")
    
    def test_unary_minus(self):
        x = "y = -1 + (-xx)"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = ((-1) + (-xx)))")

        result = parsed.evaluate({"xx": -1})
        self.assertEqual(result["y"], 0)
    
    def test_unary_minus2(self):
        x = "y = -1 + -(-xx)"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = ((-1) + (-(-xx))))")

        result = parsed.evaluate({"xx": 1})
        self.assertEqual(result["y"], 0)

    def test_unary_minus_comma(self):
        x = "y = xx(A, -B)"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = xx(A, (-B)))")
        def xx(a, b):
            return a + b
        result = parsed.evaluate({"xx": xx, "A": 1, "B": 2 })
        self.assertEqual(result["y"], -1)

    def test_timespan_literal(self):
        x = "y = C + 1d"
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = (C + 1d))")

        result = parsed.evaluate({"C": pd.to_datetime("2020-01-02")})
        self.assertEqual(result["y"], pd.to_datetime("2020-01-03"))

    # def test_unary_not(self):
    #     x = "y = not x"
    #     parsed = parse_expression(x)
    #     self.assertEqual(str(parsed), "(y = (not x))")

    #     result = parsed.evaluate({"x": False})
    #     self.assertEqual(result["y"], True)
    
    # def test_unary_not_series(self):
    #     x = "y = not x"
    #     parsed = parse_expression(x)
    #     self.assertEqual(str(parsed), "(y = (not x))")
    #     s = pd.Series([True, False])
    #     result = parsed.evaluate({"x": s})
    #     self.assertListEqual(list(result["y"]), [False, True])
    
    # def test_list_expression(self):
    #     x = "y = (1, 2, 3)"
    #     parsed = parse_expression(x)
    #     self.assertEqual(str(parsed), "(y = (1, 2, 3))")
    #     result = parsed.evaluate(None)
    #     self.assertListEqual(list(result["y"]), [1, 2, 3])

    # def test_by(self):
    #     x = "A, count(B) by bin(C, 1h), D"
    #     parsed = parse_expression(x)
    #     self.assertEqual(str(parsed), "((A, count(B)) by (bin(C, 1h), D))")

    # def test_comma_evaluate(self):
    #     x = "1, 2, 3, A"
    #     parsed = parse_expression(x)
    #     self.assertEqual(str(parsed), "(1, 2, 3, A)")

    #     result = parsed.evaluate({"A": 4})
    #     self.assertListEqual([1, 2, 3, 4], result)

def test_star():
    x = "any(*)"
    parsed = parse_expression(x)
    assert str(parsed) == "any(*)"

# def test_asc():
#     x = "A asc"
#     parsed = parse_expression(x)
#     assert str(parsed) == "(A asc)"

#     assert isinstance(parsed, ep.Asc)

# def test_desc():
#     x = "A desc"
#     parsed = parse_expression(x)
#     assert str(parsed) == "(A desc)"

#     assert isinstance(parsed, ep.Desc)

# def test_asc_desc():
#     x = "A desc, B asc, C"
#     parsed = parse_expression(x)
#     assert str(parsed) == "((A desc), (B asc), C)"

# def test_desc_evaluate():
#     x = "y = A desc"
#     parsed = parse_expression(x)
#     assert str(parsed) == "(y = (A desc))"

#     result = parsed.evaluate({"A": 4})
#     assert 4 == result["y"] 

# def test_asc_evaluate():
#     x = "y = A asc"
#     parsed = parse_expression(x)
#     assert str(parsed) == "(y = (A asc))"

#     result = parsed.evaluate({"A": 4})
#     assert 4 == result["y"] 

# def test_asc_with_math_evaluate():
#     x = "y = A + 1 asc"
#     parsed = parse_expression(x)
#     assert str(parsed) == "(y = ((A + 1) asc))"

#     result = parsed.evaluate({"A": 4})
#     assert 5 == result["y"] 

def test_dot():
    x = "y = A.b"
    parsed = parse_expression(x)
    assert str(parsed) == "(y = (A.b))"

def test_dot_with_math():
    x = "y = 1 + A.b * 2"
    parsed = parse_expression(x)
    assert str(parsed) == "(y = (1 + ((A.b) * 2)))"

def test_dot_left_to_right():
    x = "y = A.b.c"
    parsed = parse_expression(x)
    assert str(parsed) == "(y = ((A.b).c))"