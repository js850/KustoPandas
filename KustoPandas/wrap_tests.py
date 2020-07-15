import unittest
import pandas as pd
from kusto_pandas import Wrap

def create_df():
    df = pd.DataFrame(index=range(5))
    df["A"] = [0.0, 1.0, 2.0, 3.0, 4.0]
    df["B"] = [0, 1, 2, 3, 4]
    df["C"] = ["foo1", "foo2", "foo3", "foo4", "foo5"]
    df["D"] = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])    
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    return df

class TestWrap(unittest.TestCase):
    def test_project(self):
        df = create_df()
        self.assertGreater(len(df.columns), 2)
        print(df.columns)
        w = Wrap(df)
        w = w.project(["A", "B"])
        self.assertEqual(2, len(w.df.columns))
        self.assertListEqual(["A", "B"], list(w.df.columns))
    
    def test_summarize(self):
        df = create_df()
        w = Wrap(df)
        w.summarize("x=count()", "G")

        expected = pd.DataFrame({
            "G" : ["G1", "G2"],
            "x" : [3, 2],
        })
        
        self.assertTrue(w.df.equals(expected))

    def test_summarize_count_sum(self):
        df = create_df()
        w = Wrap(df)
        w.summarize(["x=count()", "z=sum(A)"], "G")

        expected = pd.DataFrame({
            "G" : ["G1", "G2"],
            "x" : [3, 2],
            "z" : [4.0, 6.0],
        })

        print()
        print(w.df)
        
        self.assertTrue(w.df.equals(expected))

    def test_extend(self):
        df = create_df()
        w = Wrap(df)
        w.extend("z =B*2")

        z = w.df["z"]
        expected = [0, 2, 4, 6, 8]
        self.assertListEqual(expected, list(z))

