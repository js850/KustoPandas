import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from KustoPandas.expression_parser import parse_expression

class TestHasOperator(unittest.TestCase):
    def test_has(self):
        x = '"hi there" has "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi there" has "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_has_case(self):
        x = '"HI there" has "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("HI there" has "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_has_false_not_whole(self):
        x = '"hitthere" has "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hitthere" has "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_not_has(self):
        x = '"hi there" !has "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi there" !has "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_has_series_left(self):
        x = 'A has "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A has "hi")')
        result = parsed.evaluate({"A": pd.Series(["hi", "hit", "thi", "hi there", "HI"])})
        self.assertListEqual(list(result), [True, False, False, True, True])

    def test_has_cs(self):
        x = '"hi there" has_cs "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi there" has_cs "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, True)

    def test_has_cs_false_case(self):
        x = '"HI there" has_cs "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("HI there" has_cs "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_has_cs_false_not_whole(self):
        x = '"hitthere" has_cs "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hitthere" has_cs "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_not_has_cs(self):
        x = '"hi there" !has_cs "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hi there" !has_cs "hi")')
        result = parsed.evaluate(None)
        self.assertEqual(result, False)

    def test_has_cs_series_left(self):
        x = 'A has_cs "hi"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A has_cs "hi")')
        result = parsed.evaluate({"A": pd.Series(["hi", "hit", "thi", "hi there", "HI"])})
        self.assertListEqual(list(result), [True, False, False, True, False])