import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from KustoPandas.expression_parser import parse_expression

class TestInOperator(unittest.TestCase):
    def test_in(self):
        x = '"hi" in (1, "b", "hi")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" in (1, "b", "hi"))')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_notin(self):
        x = '"hi" !in (1, "b", "hi")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" !in (1, "b", "hi"))')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_in_passed_in_list_right(self):
        x = '"hi" in A'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" in A)')
        result = parsed.evaluate({"A": [1, "hi", "there"]})
        self.assertEqual(result, True)

    def test_in_series_left(self):
        x = 'A in ("1", "2", "33", "a")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A in ("1", "2", "33", "a"))')
        result = parsed.evaluate({"A": pd.Series(["1", "2", "3", "22", "A"])})
        self.assertListEqual(list(result), [True, True, False, False, False])

    def test_in_left_series_numbers(self):
        x = 'A in (1, 2)'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A in (1, 2))')
        result = parsed.evaluate({"A": pd.Series([1, 2, 3])})
        self.assertListEqual(list(result), [True, True, False])

    def test_in_case_sensitive(self):
        x = '"hi" in (1, "b", "Hi")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" in (1, "b", "Hi"))')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_in_cis(self):
        x = '"hi" in~ ("1", "b", "HI")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" in~ ("1", "b", "HI"))')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_in_cis_false(self):
        x = '"hi" in~ ("1", "b")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" in~ ("1", "b"))')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)
    
    def test_notin_cis(self):
        x = '"hi" !in~ ("1", "b", "HI")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" !in~ ("1", "b", "HI"))')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_in_notcis_false(self):
        x = '"hi" !in~ ("1", "b")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi" !in~ ("1", "b"))')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_in_cis_left_series(self):
        x = 'A in~ ("1", "2", "33", "a")'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A in~ ("1", "2", "33", "a"))')
        result = parsed.evaluate({"A": pd.Series(["1", "2", "3", "22", "A"])})
        self.assertListEqual(list(result), [True, True, False, False, True])