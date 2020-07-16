import unittest
import pandas as pd
import numpy as np
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
    
    def test_summarize_percentile(self):
        df = create_df()
        w = Wrap(df)
        w.summarize(["percentiles(B, 50, 75)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["percentiles_50"]))
        self.assertListEqual([2.0, 3.5], list(w.df["percentiles_75"]))

    def test_summarize_percentile2(self):
        df = create_df()
        w = Wrap(df)
        w.summarize(["myperc = percentiles(B, 50, 75)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["myperc_50"]))
        self.assertListEqual([2.0, 3.5], list(w.df["myperc_75"]))

    def test_summarize_percentile_one_arg(self):
        df = create_df()
        w = Wrap(df)
        w.summarize(["myperc = percentiles(B, 50)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["myperc_50"]))
        self.assertListEqual(["G", "myperc_50"], list(w.df.columns))

    def test_extend(self):
        df = create_df()
        w = Wrap(df)
        w.extend("z =B*2")

        z = w.df["z"]
        expected = [0, 2, 4, 6, 8]
        self.assertListEqual(expected, list(z))
    
    def test_where(self):
        df = create_df()
        w = Wrap(df)
        w = w.where("B > 2")
        self.assertListEqual([3, 4], list(w.df["B"]))
    
    def test_where_and(self):
        df = create_df()
        w = Wrap(df)
        w = w.where("(B > 1) && (B < 4)")
        self.assertListEqual([2, 3], list(w.df["B"]))
    
    def test_where_or(self):
        df = create_df()
        w = Wrap(df)
        w = w.where("(B >= 3) || (B < 1)")
        self.assertListEqual([0, 3, 4], list(w.df["B"]))
    
    def test_where_equiv(self):
        df = create_df()
        df["O"] = [-1, 1, -1, 3, -1] 
        w = Wrap(df)
        w = w.where("(B == O)")
        self.assertListEqual([1, 3], list(w.df["B"]))

    def test_extend_iff(self):
        df = create_df()
        df["W"] = [-1, 1, -1, 1, -1] 
        w = Wrap(df)
        w = w.extend("Z = iff(W > 0, B, C)")
        self.assertListEqual(["foo1", 1, "foo3", 3, "foo5"], list(w.df["Z"]))
    





