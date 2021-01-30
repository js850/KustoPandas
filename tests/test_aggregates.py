import unittest
import pandas as pd
import numpy as np
from context import Wrap

def create_df():
    df = pd.DataFrame(index=range(5))
    df["A"] = [0.0, 1.0, 2.0, 3.0, 4.0]
    df["B"] = [0, 1, 2, 3, 4]
    df["C"] = ["foo1", "foo2", "foo3", "foo4", "foo5"]
    df["D"] = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])    
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    return df

class TestAggregates(unittest.TestCase):
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

    def test_summarize_count_noby(self):
        df = create_df()
        w = Wrap(df)
        c = w.summarize("count()")

        print()
        print(c.df)

        assert ["count_"] == list(c.df.columns)
        assert [5] == list(c.df["count_"])
    
    def test_summarize_max_noby(self):
        df = create_df()
        w = Wrap(df)
        c = w.summarize("max(B)") 

        print()
        print(c.df)

        self.assertListEqual(["max_B"], list(c.df.columns))
        self.assertListEqual([4], list(c.df["max_B"]))

    def test_summarize_max_count_noby(self):
        df = create_df()
        w = Wrap(df)
        c = w.summarize("M=max(B), C=count()") 

        print()
        print(c.df)

        self.assertListEqual(["M", "C"], list(c.df.columns))
        self.assertListEqual([4], list(c.df["M"]))
        self.assertListEqual([5], list(c.df["C"]))

    def test_summarize_percentile(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["percentiles(B, 50, 75)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["percentiles_B_50"]))
        self.assertListEqual([2.0, 3.5], list(w.df["percentiles_B_75"]))

    # def test_summarize_percentiles_2args_1name(self):
    #     # multiple name is not supported yet. this will fail until then
    #     df = create_df()
    #     w = Wrap(df)
    #     w = w.summarize(["myperc = percentiles(B, 50, 75)"], "G")

    #     print(w.df)

    #     self.assertListEqual([1.0, 3.0], list(w.df["myperc"]))
    #     self.assertListEqual([2.0, 3.5], list(w.df["percentiles_B_75"]))

    def test_summarize_percentile2(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["percentiles(B, 50, 75)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["percentiles_B_50"]))
        self.assertListEqual([2.0, 3.5], list(w.df["percentiles_B_75"]))

    def test_summarize_percentile_one_arg(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["myperc = percentiles(B, 50)"], "G")

        print(w.df)

        self.assertListEqual([1.0, 3.0], list(w.df["myperc"]))
        self.assertListEqual(["G", "myperc"], list(w.df.columns))

    def test_summarize_percentile_noby(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["percentiles(B, 50, 75)"])

        print()
        print(w.df)

        self.assertListEqual(["percentiles_B_50", "percentiles_B_75"], list(w.df.columns))
        self.assertListEqual([2.0], list(w.df["percentiles_B_50"]))
        self.assertListEqual([3.0], list(w.df["percentiles_B_75"]))

    def test_summarize_percentile_singlepercentile_noby(self):
        df = create_df()
        w = Wrap(df)
        w = w.summarize(["percentiles(B, 50)"])

        print()
        print(w.df)

        self.assertListEqual(["percentiles_B_50"], list(w.df.columns))
        self.assertListEqual([2.0], list(w.df["percentiles_B_50"]))
    
    def test_summarize_dcount(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["dcount(F)"], "G")

        print(w.df)

        self.assertListEqual([2, 1], list(w.df["dcount_F"]))
        self.assertListEqual(["G", "dcount_F"], list(w.df.columns))

    def test_summarize_dcount_noby(self):
        df = create_df()
        w = Wrap(df)
        c = w.summarize("dcount(G)") 

        print()
        print(c.df)

        self.assertListEqual(["dcount_G"], list(c.df.columns))
        self.assertListEqual([2], list(c.df["dcount_G"]))

    def test_summarize_dcountif(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G1"]
        df["F"] = [1, 1, 3, 4, 3]
        df["P"] = [True, True, True, False, True]

        w = Wrap(df)
        w = w.summarize(["dcountif(F, P)"], "G")

        print(w.df)

        self.assertListEqual([2, 1], list(w.df["dcountif_F_P"]))
        self.assertListEqual(["G", "dcountif_F_P"], list(w.df.columns))

    def test_summarize_dcountif_noby(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G1"]
        df["F"] = [1, 1, 3, 4, 3]
        df["P"] = [False, False, True, True, True]

        w = Wrap(df)
        w = w.summarize(["dcountif(F, P)"])

        print(w.df)

        self.assertListEqual([2], list(w.df["dcountif_F_P"]))
        self.assertListEqual(["dcountif_F_P"], list(w.df.columns))

    def test_summarize_dcountif_predicatefalse(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G1"]
        df["F"] = [1, 1, 3, 4, 3]
        df["P"] = [True, True, False, False, True]

        w = Wrap(df)
        w = w.summarize(["dcountif(F, P)"], "G")

        print(w.df)

        # np.nan == np.nan evaluates to false
        result = w.df["dcountif_F_P"]
        result = np.where(np.isnan(result), -1, result)

        self.assertListEqual([2, -1], list(result))
        self.assertListEqual(["G", "dcountif_F_P"], list(w.df.columns))

    def test_summarize_dcountif_noby_predicatefalse(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G1"]
        df["F"] = [1, 1, 3, 4, 3]
        df["P"] = [False, False, False, False, False]

        w = Wrap(df)
        w = w.summarize(["dcountif(F, P)"])

        print(w.df)

        self.assertListEqual([None], list(w.df["dcountif_F_P"]))
        self.assertListEqual(["dcountif_F_P"], list(w.df.columns))
    
    def test_summarize_countif(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["countif(F > 2)"], "G")

        print(w.df)

        self.assertListEqual([1, 2], list(w.df["countif_"]))
        self.assertListEqual(["G", "countif_"], list(w.df.columns))

    def test_summarize_countif_noby(self):
        df = create_df()
        df["F"] = [1, 1, 2, 4, 3]
        w = Wrap(df)
        c = w.summarize("C=countif(F > 2)") 

        self.assertListEqual(["C"], list(c.df.columns))
        self.assertListEqual([2], list(c.df["C"]))

    def test_summarize_avg(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["avg(F)"], "G")

        self.assertListEqual([2, 3], list(w.df["avg_F"]))
        self.assertListEqual(["G", "avg_F"], list(w.df.columns))

    def test_summarize_avg_noby(self):
        df = create_df()
        df["F"] = [1, 1, 2, 3, 3]
        w = Wrap(df)
        c = w.summarize("avg(F)") 

        self.assertListEqual(["avg_F"], list(c.df.columns))
        self.assertListEqual([2], list(c.df["avg_F"]))

    def test_summarize_std(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["stdev(F)"], "G")
    
        print(w.df)
        np.testing.assert_almost_equal(w.df["stdev_F"], [1.732051, 0], 3)
        self.assertListEqual(["G", "stdev_F"], list(w.df.columns))

    def test_summarize_std_noby(self):
        df = create_df()
        df["F"] = [1, 1, 2, 3, 3]
        w = Wrap(df)
        c = w.summarize("stdev(F)") 

        self.assertListEqual(["stdev_F"], list(c.df.columns))
        self.assertListEqual([1], list(c.df["stdev_F"]))

    def test_summarize_var(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 1, 3, 4, 3]

        w = Wrap(df)
        w = w.summarize(["variance(F)"], "G")
        
        print(w.df)
        
        np.testing.assert_almost_equal(w.df["variance_F"], [3, 0], 3)
        self.assertListEqual(["G", "variance_F"], list(w.df.columns))

    def test_summarize_var_noby(self):
        df = create_df()
        df["F"] = [1, 1, 2, 3, 3]
        w = Wrap(df)
        c = w.summarize("variance(F)") 

        self.assertListEqual(["variance_F"], list(c.df.columns))
        self.assertListEqual([1], list(c.df["variance_F"]))
    
    def test_summarize_min(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 0, 9, 4, 8]

        w = Wrap(df)
        wnew = w.summarize(["min(F)"], "G")
        
        print(w.df)
        
        self.assertListEqual(list(wnew.df["min_F"]), [0, 8])
        self.assertListEqual(["G", "min_F"], list(wnew.df.columns))

    def test_summarize_min_noby(self):
        df = create_df()
        df["F"] = [1, 8, 2, 3, 3]
        w = Wrap(df)
        c = w.summarize("min(F)") 

        self.assertListEqual(["min_F"], list(c.df.columns))
        self.assertListEqual([1], list(c.df["min_F"]))

    def test_summarize_max(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 0, 9, 4, 8]

        w = Wrap(df)
        wnew = w.summarize(["max(F)"], "G")
        
        print(w.df)
        
        self.assertListEqual(list(wnew.df["max_F"]), [4, 9])
        self.assertListEqual(["G", "max_F"], list(wnew.df.columns))

    def test_summarize_argmin(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 0, 9, 4, 8]

        w = Wrap(df)
        wnew = w.summarize(["argmin(F, C)"], "G")
        
        print(wnew.df)
        
        self.assertListEqual(list(wnew.df["argmin_F_C"]), ["foo2", "foo5"])
        self.assertListEqual(["G", "argmin_F_C"], list(wnew.df.columns))

    def test_summarize_argmin_noby(self):
        df = create_df()
        df["F"] = [8, 1, 2, 3, 3]
        w = Wrap(df)
        c = w.summarize("argmin(F, C)") 

        print()
        print(c.df)

        self.assertListEqual(["argmin_F_C"], list(c.df.columns))
        self.assertListEqual(["foo2"], list(c.df["argmin_F_C"]))

    def test_summarize_argmax(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 0, 9, 4, 8]

        w = Wrap(df)
        wnew = w.summarize(["argmax(F, C)"], "G")
        
        print(wnew.df)
        
        self.assertListEqual(list(wnew.df["argmax_F_C"]), ["foo4", "foo3"])
        self.assertListEqual(["G", "argmax_F_C"], list(wnew.df.columns))

    def test_summarize_argmax_noby(self):
        df = create_df()
        df["F"] = [8, 1, 2, 3, 3]
        w = Wrap(df)
        c = w.summarize("argmax(F, C)") 

        print()
        print(c.df)

        self.assertListEqual(["argmax_F_C"], list(c.df.columns))
        self.assertListEqual(["foo1"], list(c.df["argmax_F_C"]))

    def test_summarize_argmax_math(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 0, 9, 4, 8]
        df["H"] = [1, 1, 0, 0, 1]

        w = Wrap(df)
        wnew = w.summarize(["argmax(F*H, B+1)"], "G")
        
        print(wnew.df)
        
        self.assertListEqual(list(wnew.df["argmax_"]), [1, 5])
        self.assertListEqual(["G", "argmax_"], list(wnew.df.columns))

    def test_summarize_two_outputs_same_name(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["F"] = [1, 0, 9, 4, 8]

        w = Wrap(df)
        wnew = w.summarize(["max(F+1)", "max(F+2)"], "G")
        
        print(w.df)
        
        self.assertListEqual(list(wnew.df["max_"]), [5, 10])
        self.assertListEqual(list(wnew.df["max__"]), [6, 11])
        self.assertListEqual(["G", "max_", "max__"], list(wnew.df.columns))

    def test_summarize_bin(self):
        df = create_df()
        df["D"] = pd.to_datetime(["2009-01-01T08:20", "2009-01-02T08:51", "2009-01-01", "2009-01-06", "2009-01-01T22:00"])    
        w = Wrap(df)
        wnew = w.summarize("Z=count()", "bin(D, 1d)")
        self.assertListEqual(list([3, 1, 1]), list(wnew.df["Z"]))
        self.assertListEqual(["bin_D", "Z"], list(wnew.df.columns))
    
    def test_summarize_full_expression(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G1", "G2", "G2"]
        df["H"] = ["H1", "H2", "H2", "H3", "H3"]

        w = Wrap(df)
        wnew = w.summarize("count(), max(B) by G, H")
        self.assertListEqual(list(["G1", "G1", "G2"]), list(wnew.df["G"]))
        self.assertListEqual(list(["H1", "H2", "H3"]), list(wnew.df["H"]))
        self.assertListEqual(list([1, 2, 2]), list(wnew.df["count_"]))
        self.assertListEqual(list([0, 2, 4]), list(wnew.df["max_B"]))
        self.assertListEqual(["G", "H", "count_", "max_B"], list(wnew.df.columns))

    def test_summarize_by_array(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G1", "G2", "G2"]
        df["H"] = ["H1", "H2", "H2", "H3", "H3"]

        w = Wrap(df)
        w2 = w.summarize("count(), max(B) by G, H")
        warrays = w.summarize(["count()", "max(B)"], ["G", "H"])

        print(w2.df)
        print(warrays.df)

        pd.testing.assert_frame_equal(w2.df, warrays.df)

    def test_summarize_any(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]

        w = Wrap(df)
        wnew = w.summarize("any(B) by G")

        print()
        print(wnew.df)

        self.assertListEqual(list(["G1", "G2"]), list(wnew.df["G"]))
        self.assertListEqual(list([0, 2]), list(wnew.df["any_B"]))
        self.assertEqual(2, len(wnew.df.columns))

    def test_summarize_any_noby(self):
        df = create_df()
        df["F"] = [8, 1, 2, 3, 3]
        w = Wrap(df)
        c = w.summarize("any(F)") 

        print()
        print(c.df)

        assert ["any_F"] == list(c.df.columns)
        assert [8] == list(c.df["any_F"])

    def test_summarize_any_noby_2args(self):
        df = create_df()
        df["F"] = [8, None, 2, 3, 4]
        df["C"] = [None, 11, np.nan, 1, None]
        w = Wrap(df)
        c = w.summarize("any(F, C)") 

        print()
        print(c.df)

        assert ["any_F", "any_C"] == list(c.df.columns)
        assert [3] == list(c.df["any_F"])
        assert [1] == list(c.df["any_C"])

    def test_summarize_any_noby_2args_allNone(self):
        df = create_df()
        df["F"] = [80, None, 20, 30, 40]
        df["C"] = [None, None, np.nan, None, None]
        df["D"] = [None, 2, 3, 4, 5]
        w = Wrap(df)
        c = w.summarize("any(F, C, D)") 

        print()
        print(c.df)

        assert ["any_F", "any_C", "any_D"] == list(c.df.columns)
        assert [20] == list(c.df["any_F"])
        assert [3] == list(c.df["any_D"])

    def test_summarize_any_nonull(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["B"] = [None, 1, 2, 3, 4]

        w = Wrap(df)
        wnew = w.summarize("any(B) by G")
        self.assertListEqual(list(["G1", "G2"]), list(wnew.df["G"]))
        self.assertListEqual(list([1, 2]), list(wnew.df["any_B"]))
        self.assertEqual(2, len(wnew.df.columns))
    
    def test_summarize_any_2args(self):
        df = create_df()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["B"] = [None, 10, 20, 30, 40]
        df["C"] = [0, None, None, 3, 4]

        w = Wrap(df)
        wnew = w.summarize("any(B, C) by G")
        self.assertListEqual(list(["G1", "G2"]), list(wnew.df["G"]))
        self.assertListEqual(list([30, 40]), list(wnew.df["any_B"]))
        self.assertListEqual(list([3, 4]), list(wnew.df["any_C"]))
        self.assertEqual(3, len(wnew.df.columns))
    
    def test_summarize_any_star(self):
        df = pd.DataFrame()
        df["G"] = ["G1", "G1", "G2", "G1", "G2"]
        df["B"] = [None, 10, 20, 30, 40]
        df["C"] = [0, None, None, 3, 4]

        w = Wrap(df)
        wnew = w.summarize("any(*) by G")
        print()
        print(wnew)
        self.assertListEqual(list(["G1", "G2"]), list(wnew.df["G"]))
        self.assertListEqual(list([30, 40]), list(wnew.df["any_B"]))
        self.assertListEqual(list([3, 4]), list(wnew.df["any_C"]))
        self.assertEqual(3, len(wnew.df.columns))

    def test_summarize_any_star_noby(self):
        df = pd.DataFrame()
        df["B"] = [None, 10, 20, 30, 40]
        df["C"] = [0, None, None, 3, 4]

        w = Wrap(df)
        wnew = w.summarize("any(*)")
        print()
        print(wnew)
        self.assertListEqual(list([30]), list(wnew.df["any_B"]))
        self.assertListEqual(list([3]), list(wnew.df["any_C"]))
        self.assertEqual(2, len(wnew.df.columns))

def test_summarize_avgif_noby():
    df = pd.DataFrame()
    df["B"] = [None, 10, 11, 1, 3]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("avgif(B, C)")
    print()
    print(wnew)
    assert list([2]) == list(wnew.df["avgif_B_C"])
    assert 1 == len(wnew.df.columns)

def test_summarize_avgif():
    df = pd.DataFrame()
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    df["B"] = [12, 10, 111, 1, 3]
    df["C"] = [True, True, True, False, False]

    w = Wrap(df)
    wnew = w.summarize("avgif(B, C) by G")
    print()
    print(wnew)
    assert ["G1", "G2"] == list(wnew.df["G"])
    assert [11, 111] == list(wnew.df["avgif_B_C"])
    assert 2 == len(wnew.df.columns)

def test_summarize_sumif_noby():
    df = pd.DataFrame()
    df["B"] = [None, 10, 11, 1, 3]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("sumif(B, C)")
    print()
    print(wnew)
    assert list([4]) == list(wnew.df["sumif_B_C"])
    assert 1 == len(wnew.df.columns)

def test_summarize_sumif():
    df = pd.DataFrame()
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    df["B"] = [12, 10, 111, 1, 3]
    df["C"] = [True, True, True, False, False]

    w = Wrap(df)
    wnew = w.summarize("sumif(B, C) by G")
    print()
    print(wnew)
    assert ["G1", "G2"] == list(wnew.df["G"])
    assert [22, 111] == list(wnew.df["sumif_B_C"])
    assert 2 == len(wnew.df.columns)

def test_summarize_stdevif_noby():
    df = pd.DataFrame()
    df["B"] = [None, 10, 11, 1, 0]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("stdevif(B, C)")
    print()
    print(wnew)
    np.testing.assert_almost_equal(wnew.df["stdevif_B_C"], [0.70710678], 3)
    assert 1 == len(wnew.df.columns)

def test_summarize_stdevif():
    df = pd.DataFrame()
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    df["B"] = [1, 0, 3, 10, 3]
    df["C"] = [True, True, True, False, True]

    w = Wrap(df)
    wnew = w.summarize("stdevif(B, C) by G")
    print()
    print(wnew)
    assert ["G1", "G2"] == list(wnew.df["G"])
    np.testing.assert_almost_equal(wnew.df["stdevif_B_C"], [0.70710678, 0], 3)
    assert 2 == len(wnew.df.columns)

def test_summarize_varianceif_noby():
    df = pd.DataFrame()
    df["B"] = [None, 10, 11, 1, 0]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("varianceif(B, C)")
    print()
    print(wnew)
    np.testing.assert_almost_equal(wnew.df["varianceif_B_C"], [0.5], 3)
    assert 1 == len(wnew.df.columns)

def test_summarize_varianceif():
    df = pd.DataFrame()
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    df["B"] = [1, 0, 3, 10, 3]
    df["C"] = [True, True, True, False, True]

    w = Wrap(df)
    wnew = w.summarize("varianceif(B, C) by G")
    print()
    print(wnew)
    assert ["G1", "G2"] == list(wnew.df["G"])
    np.testing.assert_almost_equal(wnew.df["varianceif_B_C"], [0.5, 0], 3)
    assert 2 == len(wnew.df.columns)

def test_summarize_maxif_noby():
    df = pd.DataFrame()
    df["B"] = [None, 10, 11, 1, 3]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("maxif(B, C)")
    print()
    print(wnew)
    assert list([3]) == list(wnew.df["maxif_B_C"])
    assert 1 == len(wnew.df.columns)

def test_summarize_maxif():
    df = pd.DataFrame()
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    df["B"] = [12, 10, 111, 1, 3]
    df["C"] = [True, True, True, False, False]

    w = Wrap(df)
    wnew = w.summarize("maxif(B, C) by G")
    print()
    print(wnew)
    assert ["G1", "G2"] == list(wnew.df["G"])
    assert [12, 111] == list(wnew.df["maxif_B_C"])
    assert 2 == len(wnew.df.columns)

def test_summarize_minif_noby():
    df = pd.DataFrame()
    df["B"] = [None, 10, -11, 1, 3]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("minif(B, C)")
    print()
    print(wnew)
    assert list([1]) == list(wnew.df["minif_B_C"])
    assert 1 == len(wnew.df.columns)

def test_summarize_minif():
    df = pd.DataFrame()
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    df["B"] = [12, 10, 111, 1, 3]
    df["C"] = [True, True, True, False, False]

    w = Wrap(df)
    wnew = w.summarize("minif(B, C) by G")
    print()
    print(wnew)
    assert ["G1", "G2"] == list(wnew.df["G"])
    assert [10, 111] == list(wnew.df["minif_B_C"])
    assert 2 == len(wnew.df.columns)

def test_summarize_anyif_noby():
    df = pd.DataFrame()
    df["B"] = [None, 10, -11, 1, 3]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("anyif(B, C)")
    print()
    print(wnew)
    assert list([1]) == list(wnew.df["anyif_B_C"])
    assert 1 == len(wnew.df.columns)

def test_summarize_anyif():
    df = pd.DataFrame()
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    df["B"] = [None, 10, 111, 1, 3]
    df["C"] = [True, True, False, False, True]

    w = Wrap(df)
    wnew = w.summarize("anyif(B, C) by G")
    print()
    print(wnew)
    assert ["G1", "G2"] == list(wnew.df["G"])
    assert [10, 3] == list(wnew.df["anyif_B_C"])
    assert 2 == len(wnew.df.columns)

def test_summarize_anyif_noby_allnull():
    df = pd.DataFrame()
    df["B"] = [None, None, None, None, None]
    df["C"] = [True, False, False, True, True]

    w = Wrap(df)
    wnew = w.summarize("anyif(B, C)")
    print()
    print(wnew)
    assert list([None]) == list(wnew.df["anyif_B_C"])
    assert 1 == len(wnew.df.columns)

def test_summarize_composit_argument():
    df = pd.DataFrame()
    df["A"] = [1, 0, 1, 0, 1]
    df["B"] = [1, 1, 1, 0, 0]
    df["G"] = [1, 1, 1, 1, 0]

    w = Wrap(df)
    wnew = w.summarize("count(), avg(A), Cov = avg(A * B) - avg(A) * avg(B) by G")

    print()
    print(wnew)
    assert [1, 4] == list(wnew.df["count_"])
    assert [1, 0.5] == list(wnew.df["avg_A"])
    assert [0, 0.5 - 0.5*3/4] == list(wnew.df["Cov"])
    assert 4 == len(wnew.df.columns)

def test_summarize_composit_argument_default_name():
    df = pd.DataFrame()
    df["A"] = [1, 0, 1, 0, 1]
    df["B"] = [1, 1, 1, 0, 0]
    df["G"] = [1, 1, 1, 1, 0]

    w = Wrap(df)
    wnew = w.summarize("avg(A * B) - avg(A) * avg(B) by G")

    print()
    print(wnew)
    assert [0, 0.5 - 0.5*3/4] == list(wnew.df["Column1"])
    assert 2 == len(wnew.df.columns)

def test_summarize_composit_argument_method_noby():
    df = pd.DataFrame()
    df["A"] = ["HI", "HI", "HI", "HI"]
    df["G"] = [1, 1, 1, 0]

    w = Wrap(df)
    wnew = w.summarize("tolower(any(A))")

    print()
    print(wnew)
    assert ["hi"] == list(wnew.df["Column1"])
    assert 1 == len(wnew.df.columns)

def test_summarize_composit_argument_default_name_default_groupby_name():
    df = pd.DataFrame()
    df["A"] = [1, 1, 1, 1, 1]
    df["B"] = [1, 1, 1, 0, 0]
    df["G"] = [7, 7, 7, 7, 7]

    w = Wrap(df)
    wnew = w.summarize("sum(A * B) - any(A) * sum(B) by G + 1")

    print()
    print(wnew)
    assert list([0]) == list(wnew.df["Column2"])
    assert list([8]) == list(wnew.df["Column1"])
    assert 2 == len(wnew.df.columns)

def test_summarize_two_groupby_default_name():
    df = pd.DataFrame()
    df["A"] = [1, 0, 1, 0, 1]
    df["B"] = [1, 1, 1, 0, 0]
    df["G"] = [1, 1, 1, 1, 1]

    w = Wrap(df)
    wnew = w.summarize("count() by G + 1, B + 1")

    print()
    print(wnew)
    assert list([2, 3]) == list(wnew.df["count_"])
    assert list([2, 2]) == list(wnew.df["Column1"])
    assert list([1, 2]) == list(wnew.df["Column2"])
    assert 3 == len(wnew.df.columns)

def test_summarize_default_name_conflicts():
    df = pd.DataFrame()
    df["A"] = [1, 0, 1, 0, 1]
    df["B"] = [1, 1, 1, 0, 0]
    df["G"] = [1, 1, 1, 1, 1]

    w = Wrap(df)
    wnew = w.summarize("count(), count() + 1, Column2 = count() by G + 1, B + 1")

    print()
    print(wnew)
    assert ["Column1", "Column2_1", "count_", "Column3", "Column2" ] == list(wnew.df.columns)
