import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from KustoPandas.expression_parser.expression_parser import parse_expression
from KustoPandas.expression_parser.expression_tree import find_matching_parentheses

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
