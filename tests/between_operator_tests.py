import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from KustoPandas.expression_parser.expression_parser import parse_expression
from KustoPandas.expression_parser.expression_tree import find_matching_parentheses

class TestBetweenOperator(unittest.TestCase):
    def test_between(self):
        x = '2 between (1 .. 3)'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(2 between (1 .. 3))')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_between_inclusive(self):
        x = '2 between (1 .. 2)'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(2 between (1 .. 2))')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_between_inclusive_left(self):
        x = '1 between (1 .. 2)'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(1 between (1 .. 2))')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_between_fail_left(self):
        x = '0 between (1 .. 2)'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(0 between (1 .. 2))')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_between_fail_right(self):
        x = '4 between (1 .. 2)'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(4 between (1 .. 2))')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_between_series(self):
        x = 'A between (1 .. 3)'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A between (1 .. 3))')
        result = parsed.evaluate({"A": pd.Series([0, 1, 2, 3, 4])})
        self.assertListEqual(list(result), [False, True, True, True, False])
    
    def test_between_no_DotDot(self):
        x = '1 between 2'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(1 between 2)')
        with self.assertRaises(Exception) as context:
            parsed.evaluate(None)