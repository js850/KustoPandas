import unittest
import pandas as pd
from kusto_pandas import Aggregate


class TestAggregate(unittest.TestCase):
    def test_parse(self):
        a = Aggregate("x=count()")
        self.assertEqual("x", a.new_col)
        self.assertEqual("count", a.aggregate_func.name)
        self.assertEqual("", a.aggregate_func.arg)
        a.validate(pd.DataFrame())

    def test_parse_default_name(self):
        a = Aggregate("count()")
        self.assertEqual("count_", a.new_col)
        self.assertEqual("count", a.aggregate_func.name)
        self.assertEqual("", a.aggregate_func.arg)
        a.validate(pd.DataFrame())
    
    def test_parse_sum(self):
        a = Aggregate("x=sum(y)")
        self.assertEqual("x", a.new_col)
        self.assertEqual("sum", a.aggregate_func.name)
        self.assertEqual("y", a.aggregate_func.arg)
        a.validate(pd.DataFrame({"y": [1, 2]}))
    
    def test_parse_sum_default_name(self):
        a = Aggregate("sum(y)")
        self.assertEqual("sum_y", a.new_col)
        self.assertEqual("sum", a.aggregate_func.name)
        self.assertEqual("y", a.aggregate_func.arg)
        a.validate(pd.DataFrame({"y": [1, 2]}))

        