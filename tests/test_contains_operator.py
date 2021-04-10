import unittest
import pandas as pd
import numpy as np
from context import expression_parser as ep

from KustoPandas.expression_parser import parse_expression
from KustoPandas.expression_parser.expression_tree import find_matching_parentheses

class TestContainsOperator(unittest.TestCase):
    def test_contains_ignores_case(self):
        x = "y = A contains \"hello\""
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = (A contains \"hello\"))")

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result["y"], True)
    
    def test_notcontains(self):
        x = "y = A !contains \"hello\""
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = (A !contains \"hello\"))")

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result["y"], False)

    def test_contains_cs(self):
        x = "y = A contains \"hello\""
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = (A contains \"hello\"))")

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result["y"], True)
    
    def test_notcontains_cs(self):
        x = "y = A !contains \"hello\""
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(y = (A !contains \"hello\"))")

        result = parsed.evaluate({"A": "Hello there"})
        self.assertEqual(result["y"], False)


    def test_contains_ignores_nan(self):
        x = "A contains \"h\""
        parsed = parse_expression(x)
        self.assertEqual(str(parsed), "(A contains \"h\")")

        A = pd.Series(["hi", np.nan, "b", "", "H"])
        result = parsed.evaluate({"A": A})
        self.assertListEqual(list(result), [True, False, False, False, True])
