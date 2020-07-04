import unittest
import pandas as pd
from kusto_pandas import Wrap

class TestWrap(unittest.TestCase):
    def test_project(self):
        df = pd.util.testing.makeDataFrame()
        self.assertEqual(4, len(df.columns))
        print(df.columns)
        w = Wrap(df)
        w = w.project(["A", "B"])
        self.assertEqual(2, len(w.df.columns))
        self.assertListEqual(["A", "B"], list(w.df.columns))
    
