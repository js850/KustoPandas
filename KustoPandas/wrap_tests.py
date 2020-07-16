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
        wnew = w.project("A", "B")
        self.assertListEqual(["A", "B"], list(wnew.df.columns))
        self.assertGreater(len(w.df.columns), 2)

    def test_project_kwargs(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.project("A", Z="B * 2")
        self.assertListEqual(["A", "Z"], list(wnew.df.columns))
        self.assertListEqual([0, 2, 4, 6, 8], list(wnew.df["Z"]))
        self.assertGreater(len(w.df.columns), 2)
    
    def test_project_kwargs2(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.project("A", **{"Z col": "B * 2"})
        self.assertListEqual(["A", "Z col"], list(wnew.df.columns))
        self.assertListEqual([0, 2, 4, 6, 8], list(wnew.df["Z col"]))
        self.assertGreater(len(w.df.columns), 2)

    def test_summarize(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize("x=count()", "G")

        expected = pd.DataFrame({
            "G" : ["G1", "G2"],
            "x" : [3, 2],
        })
        
        self.assertTrue(w.df.equals(expected))

    def test_summarize_count_sum(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["x=count()", "z=sum(A)"], "G") 

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
        w = w.summarize(["percentiles(B, 50, 75)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["percentiles_50"]))
        self.assertListEqual([2.0, 3.5], list(w.df["percentiles_75"]))

    def test_summarize_percentile2(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["myperc = percentiles(B, 50, 75)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["myperc_50"]))
        self.assertListEqual([2.0, 3.5], list(w.df["myperc_75"]))

    def test_summarize_percentile_one_arg(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["myperc = percentiles(B, 50)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["myperc_50"]))
        self.assertListEqual(["G", "myperc_50"], list(w.df.columns))
    
    def test_summarize_dcount(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["dcount(F)"], "G")

        print(w.df)

        self.assertListEqual([2, 1], list(w.df["dcount_F"]))
        self.assertListEqual(["G", "dcount_F"], list(w.df.columns))
    
    def test_summarize_countif(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["countif(F > 2)"], "G")

        print(w.df)

        self.assertListEqual([1, 2], list(w.df["countif_"]))
        self.assertListEqual(["G", "countif_"], list(w.df.columns))

    def test_summarize_avg(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["avg(F)"], "G")

        self.assertListEqual([2, 3], list(w.df["avg_F"]))
        self.assertListEqual(["G", "avg_F"], list(w.df.columns))

    def test_summarize_std(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["stdev(F)"], "G")
    
        print(w.df)
        np.testing.assert_almost_equal(w.df["stdev_F"], [1.732051, 0], 3)
        self.assertListEqual(["G", "stdev_F"], list(w.df.columns))

    def test_summarize_var(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["variance(F)"], "G")
        
        print(w.df)
        
        np.testing.assert_almost_equal(w.df["variance_F"], [3, 0], 3)
        self.assertListEqual(["G", "variance_F"], list(w.df.columns))

    def test_extend(self):
        df = create_df()
        w = Wrap(df)
        w = w.extend("z =B*2")

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
    
    def test_extend_iff_string_literal(self):
        df = create_df()
        w = Wrap(df)
        w = w.extend("Z = iff(C == \"foo1\", B, C)")
        self.assertListEqual([0, "foo2", "foo3", "foo4", "foo5"], list(w.df["Z"]))
    
    def test_where_datetime(self):
        df = create_df()
        w = Wrap(df)
        w = w.where("D >= \"2009-01-06\"")
        self.assertListEqual([3, 4], list(w.df["B"]))
    
    def test_where_contains(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C contains \"hi\"")
        self.assertListEqual(["hi", "HI there", "this"], list(w.df["C"]))
    
    def test_where_notcontains(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C !contains \"hi\"")
        self.assertListEqual(["today", "what"], list(w.df["C"]))
    
    def test_take(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.take(2)
        self.assertListEqual([0, 1], list(wnew.df["B"]))
        self.assertEqual(5, len(w.df["B"]))
    
    def test_sort(self):
        df = create_df()
        df["U"] = [9, 1, 7, 1, 2]
        expected = [1, 3, 4, 2, 0]
        w = Wrap(df)
        wnew = w.sort(["U + 1", "B"], [False, False])
        self.assertListEqual(expected, list(wnew.df["B"]))
        self.assertListEqual(list(range(5)), list(w.df["B"]))

    def test_sort_1(self):
        df = create_df()
        df["U"] = [9, 8, 7, 1, 2]
        w = Wrap(df)
        wnew = w.sort("U + 1")
        self.assertListEqual([0, 1, 2, 4, 3], list(wnew.df["B"]))
        self.assertListEqual(list(range(5)), list(w.df["B"]))

    def test_top(self):
        df = create_df()
        df["U"] = [9, 8, 7, 1, 2]
        w = Wrap(df)
        wnew = w.top(4, "U + 1")
        self.assertListEqual([0, 1, 2, 4], list(wnew.df["B"]))
        self.assertListEqual(list(range(5)), list(w.df["B"]))

    
    def test_let(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.let(xx=2).let(yy=3).extend("Z = B + xx + yy")
        self.assertListEqual([5, 6, 7, 8, 9], list(wnew.df["Z"]))

    def test_let_method(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.let(xx=lambda x: x + 1).extend("Z = B + xx(4)")
        self.assertListEqual([5, 6, 7, 8, 9], list(wnew.df["Z"]))



