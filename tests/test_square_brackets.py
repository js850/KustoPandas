import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from KustoPandas.expression_parser.expression_parser import parse_expression
from KustoPandas.expression_parser.expression_tree import find_matching_parentheses
from KustoPandas.dynamic_methods import todynamic

class TestSquareBrackets(unittest.TestCase):
    def test_eval_square_brackets(self):
        x = 'A[1]'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), 'A[1]')
        result = parsed.evaluate({"A": ["aa", "ab"]})
        self.assertEqual("ab", result)

    def test_eval_square_brackets_series(self):
        x = 'A[1]'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), 'A[1]')
        result = parsed.evaluate({"A": pd.Series([[1, 2], [3, 4]])})
        self.assertListEqual(list(result), [2, 4])

    def test_eval_square_brackets_dynamic(self):
        x = 'A["k1"]'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), 'A["k1"]')
        result = parsed.evaluate({"A": todynamic(pd.Series([
            '{"k1":"v1"}',
            '{"k1" : "v2"}'
        ]))})
        self.assertListEqual(list(result), ["v1", "v2"])

    def test_eval_square_brackets_dynamic_two_series(self):
        x = 'A[keys]'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), 'A[keys]')
        result = parsed.evaluate({
            "A": todynamic(pd.Series([
            '{"k1":"v1"}',
            '{"k2" : "v2"}'])),
            "keys": pd.Series([
            'k1',
            'k2']),
        })
        self.assertListEqual(list(result), ["v1", "v2"])

    def test_eval_square_brackets_key_exception(self):
        x = 'A["k1"]'
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), 'A["k1"]')
        result = parsed.evaluate({"A": todynamic(pd.Series([
            '{"k1":"v1"}',
            '{"k2" : "v2"}'
        ]))})
        self.assertListEqual(list(result), ["v1", None])