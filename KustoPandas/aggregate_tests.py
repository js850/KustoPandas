import unittest

from kusto_pandas import Aggregate


class TestAggregate(unittest.TestCase):
    def test_parse(self):
        a = Aggregate("x=count(y)")
        print("testpass")
        self.assertEqual("x", a.new_col)
        self.assertEqual("count", a.aggregate_func.name)
        self.assertEqual("y", a.aggregate_func.arg)