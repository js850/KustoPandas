import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from kusto_pandas.expression_parser import parse_expression
from kusto_pandas.expression_parser.expression_tree import find_matching_parentheses

class TestStartsWithOperator(unittest.TestCase):
    def test_startswith(self):
        x = 'A startswith "he"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A startswith "he")')

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result, True)

    def test_not_startswith(self):
        x = 'A !startswith "he"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A !startswith "he")')

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result, False)

    def test_startswith_cs(self):
        x = 'A startswith_cs "he"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A startswith_cs "he")')

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result, False)

    def test_not_startswith_cs(self):
        x = 'A !startswith_cs "he"'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A !startswith_cs "he")')

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result, True)

    def test_startswith_both_series(self):
        x = 'A startswith B'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '(A startswith B)')

        A = pd.Series(["Hello", "there"])
        B = pd.Series(["He", "Th"])

        result = parsed.evaluate(dict(A=A, B=B))
        assert [True, True] == list(result)

    def test_startswith_right_series(self):
        x = '"hello" startswith B'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), '("hello" startswith B)')

        B = pd.Series(["He", "he", " he", "th"])

        result = parsed.evaluate(dict(B=B))
        assert [True, True, False, False] == list(result)