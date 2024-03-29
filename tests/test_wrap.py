import unittest
import pandas as pd
import numpy as np
from pandas.core.frame import DataFrame
import pytest

from context import Wrap
from context import expression_parser as ep

from test_utils import replace_nan

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
        wnew = w.project("A", **{"Z_col": "B * 2"})
        self.assertListEqual(["A", "Z_col"], list(wnew.df.columns))
        self.assertListEqual([0, 2, 4, 6, 8], list(wnew.df["Z_col"]))
        self.assertGreater(len(w.df.columns), 2)

    def test_extend(self):
        df = create_df()
        w = Wrap(df)
        w = w.extend("z =B*2")

        z = w.df["z"]
        expected = [0, 2, 4, 6, 8]
        self.assertListEqual(expected, list(z))

    def test_extend_noname(self):
        df = create_df()
        df = df[["B"]]
        w = Wrap(df)
        wnew = w.extend("B*2, B+1")

        assert ["B", "Column1", "Column2"] == list(wnew.df.columns)
    
    def test_where(self):
        df = create_df()
        w = Wrap(df)
        w = w.where("B > 2")
        self.assertListEqual([3, 4], list(w.df["B"]))
    
    def test_where_and(self):
        df = create_df()
        w = Wrap(df)
        w = w.where("(B > 1) and (B < 4)")
        self.assertListEqual([2, 3], list(w.df["B"]))
    
    def test_where_or(self):
        df = create_df()
        w = Wrap(df)
        w = w.where("(B >= 3) or (B < 1)")
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

    def test_where_contains_cs(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C contains_cs \"hi\"")
        self.assertListEqual(["hi", "this"], list(w.df["C"]))
    
    def test_where_notcontains_cs(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C !contains_cs \"hi\"")
        self.assertListEqual(["HI there", "today", "what"], list(w.df["C"]))


    def test_where_startswith(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C startswith \"hi\"")
        self.assertListEqual(["hi", "HI there"], list(w.df["C"]))
    
    def test_where_notstartswith(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C !startswith \"hi\"")
        self.assertListEqual(["today", "what", "this"], list(w.df["C"]))

    def test_where_startswith_cs(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C startswith_cs \"hi\"")
        self.assertListEqual(["hi"], list(w.df["C"]))
    
    def test_where_notstartswith_cs(self):
        df = create_df()
        df["C"] = ["hi", "HI there", "today", "what", "this"]
        w = Wrap(df)
        w = w.where("C !startswith_cs \"hi\"")
        self.assertListEqual(["HI there", "today", "what", "this"], list(w.df["C"]))

    def test_take(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.take(2)
        self.assertListEqual([0, 1], list(wnew.df["B"]))
        self.assertEqual(5, len(w.df["B"]))

    def test_take_expression(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.execute("self | take 1+1")
        self.assertListEqual([0, 1], list(wnew.df["B"]))
        self.assertEqual(5, len(w.df["B"]))
    
    def test_limit(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.limit(2)
        self.assertListEqual([0, 1], list(wnew.df["B"]))
        self.assertEqual(5, len(w.df["B"]))
    
    def test_limit_expression(self):
        df = create_df()
        w = Wrap(df)
        wnew = w.execute("self | limit 1+1")
        self.assertListEqual([0, 1], list(wnew.df["B"]))
        self.assertEqual(5, len(w.df["B"]))

    def test_sort(self):
        df = create_df()
        df["U"] = [9, 1, 7, 1, 2]
        expected = [1, 3, 4, 2, 0]
        w = Wrap(df)
        wnew = w.sort(["U + 1 asc", "B asc"])
        self.assertListEqual([1, 1, 2, 7, 9], list(wnew.df["U"]))
        self.assertListEqual(expected, list(wnew.df["B"]))
        self.assertListEqual(list(range(5)), list(w.df["B"]))

        assert 6 == len(wnew.df.columns)

    def test_sort_1(self):
        df = create_df()
        df["U"] = [9, 8, 7, 1, 2]
        w = Wrap(df)
        wnew = w.sort("U + 1")
        self.assertListEqual([0, 1, 2, 4, 3], list(wnew.df["B"]))
        self.assertListEqual(list(range(5)), list(w.df["B"]))
    
    def test_sort_asc_desc(self):
        df = create_df()
        df["U"] = [9, 9, 7, 1, 2]
        df["U2"] = [1, 2, 3, 4, 5]
        w = Wrap(df)
        wnew = w.sort("U asc, U2 desc")
        assert [3, 4, 2, 1, 0] ==  list(wnew.df["B"])
        assert [1, 2, 7, 9, 9] ==  list(wnew.df["U"])
        assert [4, 5, 3, 2, 1] ==  list(wnew.df["U2"])

    def test_order(self):
        df = create_df()
        df["U"] = [9, 1, 7, 1, 2]
        expected = [1, 3, 4, 2, 0]
        w = Wrap(df)
        wnew = w.order(["U + 1 asc", "B asc"])
        self.assertListEqual(expected, list(wnew.df["B"]))
        self.assertListEqual(list(range(5)), list(w.df["B"]))

    def test_order_execute(self):
        df = create_df()
        df["U"] = [9, 1, 7, 1, 2]
        expected = [1, 3, 4, 2, 0]
        w = Wrap(df)
        wnew = w.execute("self | order by U + 1 asc, B asc")
        self.assertListEqual([1, 1, 2, 7, 9], list(wnew.df["U"]))
        self.assertListEqual(expected, list(wnew.df["B"]))
        self.assertListEqual(list(range(5)), list(w.df["B"]))

        assert 6 == len(wnew.df.columns)

    def test_top(self):
        df = create_df()
        df["U"] = [9, 8, 7, 1, 2]
        w = Wrap(df)
        wnew = w.top(4, "U + 1")
        assert [9, 8, 7, 2] == list(wnew.df["U"])
        self.assertListEqual([0, 1, 2, 4], list(wnew.df["B"]))
        self.assertListEqual(["foo1", "foo2", "foo3", "foo5"], list(wnew.df["C"]))
        assert 6 == len(wnew.df.columns)
        
        wexpected = w.sort("U").take(4)
        pd.testing.assert_frame_equal(wnew.df, wexpected.df)


    def test_top_asc(self):
        df = create_df()
        df["U"] = [9, 8, 7, 1, 2]
        w = Wrap(df)
        wnew = w.top(4, "U + 1 asc")

        assert [1, 2, 7, 8] == list(wnew.df["U"])
        assert 6 == len(wnew.df.columns)

        wexpected = w.sort("U asc").take(4)
        pd.testing.assert_frame_equal(wnew.df, wexpected.df)


    def test_top_input_expression(self):
        df = create_df()
        df["U"] = [9, 8, 7, 1, 2]
        w = Wrap(df)

        wexpected = w.top(4, "U + 1")
        wnew = w.top("4 by U + 1")

        pd.testing.assert_frame_equal(wnew.df, wexpected.df)

    def test_top_input_expression_asc(self):
        df = create_df()
        df["U"] = [9, 8, 7, 1, 2]
        w = Wrap(df)

        wexpected = w.top(4, "U + 1 asc")
        wnew = w.top("4 by U + 1 asc")

        assert [1, 2, 7, 8] == list(wnew.df["U"])
        assert [1, 2, 7, 8] == list(wexpected.df["U"])
        assert 6 == len(wnew.df.columns)

        pd.testing.assert_frame_equal(wnew.df, wexpected.df)

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
    
    def test_bin_datetime(self):
        df = create_df()
        df["D"] = pd.to_datetime(["2009-01-01T08:20", "2009-01-02T08:51", "2009-01-05", "2009-01-06", "2009-01-07"])    
        expected = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])    
        w = Wrap(df)
        wnew = w.extend("Z = bin(D, 1d)")
        self.assertListEqual(list(expected), list(wnew.df["Z"]))

    def test_join(self):
        df = create_df()
        df2 = create_df()
        df2["B"] = [1, 0, -1, -1, -1]

        w = Wrap(df)
        w2 = Wrap(df2)

        wnew = w.join(w2.project("B", "C"), on="B")

        print(wnew.df)

        self.assertListEqual([0, 1], list(wnew.df["B"]))
        self.assertListEqual(["foo1", "foo2"], list(wnew.df["C"]))
        self.assertListEqual(["foo2", "foo1"], list(wnew.df["C_y"]))


    def test_project_away(self):
        df = create_df()
        df = df[["A", "B", "C"]]

        w = Wrap(df)
        wnew = w.project_away("B")
        self.assertListEqual(["A", "C"], list(wnew.df.columns))
        self.assertListEqual(["A", "B", "C"], list(w.df.columns))
    
def test_project_away_wildcard():
    df = create_df()
    df = df[["A", "B"]]
    df["AA"] = df["B"]

    w = Wrap(df)
    wnew = w.project_away("A*")
    assert ["B"] == list(wnew.df.columns)

def test_project_away_wildcard2():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["ABC"] = [1, 2]
    df["B"] = [1, 2]
    df["Q"] = [1, 2]
    df["b"] = [1, 2]
    df["hiA"] = [1, 2]
    df["hiZ"] = [1, 2]
    df["hiZ2"] = [1, 2]

    w = Wrap(df)
    wnew = w.project_away("*B*, A*, *Z")
    assert ["Q", "b", "hiA", "hiZ2"] == list(wnew.df.columns)

def test_project_away_wildcard_nomatch():
    df = pd.DataFrame()
    df["A"] = [1, 2]

    w = Wrap(df)
    with pytest.raises(KeyError):
        w.project_away("A, B*")

def test_project_away_badcolumn():
    df = pd.DataFrame()
    df["A"] = [1, 2]

    w = Wrap(df)
    with pytest.raises(KeyError):
        w.project_away("B")

def test_project_keep():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["AA"] = [1, 2]
    df["B"] = [1, 2]
    df["C"] = [1, 2]

    w = Wrap(df)
    wnew = w.project_keep("B, A*")
    assert ["A", "AA", "B"] == list(wnew.df.columns)
    assert ["A", "AA", "B", "C"] == list(w.df.columns)

def test_project_rename():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["B"] = [5, 6]
    df["C"] = [7, 8]

    w = Wrap(df)
    wnew = w.project_rename("BB = B", CC="C")
    assert ["A", "BB", "CC"] == list(wnew.df.columns)
    assert ["A", "B", "C"] == list(w.df.columns)

def test_project_rename_badcolumn():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["B"] = [5, 6]
    df["C"] = [7, 8]

    w = Wrap(df)
    with pytest.raises(KeyError):
        wnew = w.project_rename("BB = Q")

def test_project_rename_math():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["B"] = [5, 6]
    df["C"] = [7, 8]

    w = Wrap(df)
    with pytest.raises(Exception):
        wnew = w.project_rename("BB = A + B")

def test_project_reorder():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["AA"] = [2, 4]
    df["B"] = [5, 6]
    df["C"] = [7, 8]

    w = Wrap(df)
    wnew = w.project_reorder("C", "A*")
    assert ["C", "A", "AA", "B"] == list(wnew.df.columns)
    assert ["A", "AA", "B", "C"] == list(w.df.columns)

def test_count():
    df = create_df()
    w = Wrap(df)
    w2 = w.count()

    assert ["Count"] == list(w2.df.columns)
    assert [5] == list(w2.df["Count"])

def test_distinct():
    df = pd.DataFrame()
    df["A"] = [1, 1, 1, 2, 2, 2, 1]
    df["B"] = [1, 1, 2, 2, 3, 3, 1]
    df["C"] = [1, 2, 3, 4, 5, 6, 7]

    w = Wrap(df)

    wnew = w.distinct("A, B")

    assert ["A", "B"] == list(wnew.df.columns)
    assert [1, 1, 2, 2] == list(wnew.df["A"])
    assert [1, 2, 2, 3] == list(wnew.df["B"])

def test_distinct_one_arg():
    df = pd.DataFrame()
    df["A"] = [1, 1, 1, 2, 2, 2, 1]
    df["B"] = [1, 1, 2, 2, 3, 3, 1]
    df["C"] = [1, 2, 3, 4, 5, 6, 7]

    w = Wrap(df)

    wnew = w.distinct("A")

    assert ["A"] == list(wnew.df.columns)
    assert [1, 2] == list(wnew.df["A"])

def test_distinct_args():
    df = pd.DataFrame()
    df["A"] = [1, 1, 1, 2, 2, 2, 1]
    df["B"] = [1, 1, 2, 2, 3, 3, 1]
    df["C"] = [1, 2, 3, 4, 5, 6, 7]

    w = Wrap(df)

    wnew = w.distinct("A", "B")

    assert ["A", "B"] == list(wnew.df.columns)
    assert [1, 1, 2, 2] == list(wnew.df["A"])
    assert [1, 2, 2, 3] == list(wnew.df["B"])

def test_distinct_star():
    df = pd.DataFrame()
    df["A"] = [1, 1, 1, 2, 2, 2, 1]
    df["B"] = [1, 1, 2, 2, 3, 3, 1]

    w = Wrap(df)

    wnew = w.distinct("*")

    assert ["A", "B"] == list(wnew.df.columns)
    assert [1, 1, 2, 2] == list(wnew.df["A"])
    assert [1, 2, 2, 3] == list(wnew.df["B"])

def test_getschema():
    df = create_df()

    w = Wrap(df)

    wnew = w.getschema()
    print(wnew.df)

    assert ["A", "B", "C", "D", "G"] == list(wnew.df["ColumnName"])
    assert [0, 1, 2, 3, 4] == list(wnew.df["ColumnOrdinal"])
    assert [np.float64, np.int64, object, np.dtype("datetime64[ns]"), object] == list(wnew.df["DataType"])
    assert 4 == len(wnew.df.columns)

def test_execute():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("self | where G == 'G1' | where A >= 1 | project C")

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])

def test_execute_let():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("let a = 'G2'")

    assert "G2" == wnew._get_var_map()["a"]

def test_execute_let_semicolon():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("let a = 'G2';")

    assert "G2" == wnew._get_var_map()["a"]

def test_execute_let2_pipe():
    df = create_df()

    w = Wrap(df)
    wnew = w.let(a='G1').execute("self | where G == a | where A >= 1 | project C")

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])

def test_execute_let_pipe():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("let a = 'G1'; self | where G == a | where A >= 1 | project C")

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])

def test_execute_let_dataframe():
    df = create_df()
    df2 = pd.DataFrame()

    w = Wrap(df2).let(D=df)
    wnew = w.execute("let a = 'G1'; D | where G == a | where A >= 1 | project C")

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])

def test_execute_let_dataframe2():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("let a = self | where G == 'G1' | where A >= 1; a | project C")

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])

def test_execute_as():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("self | where G == 'G1' | as table | take 1; table | where A >= 1 | project C")

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])

def test_execute_join():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("self | where G == 'G1' | project G | as T1; self | join kind=inner (T1) on G | project A, G")
    
    assert ["A", "G"] == list(wnew.df.columns)
    assert ["G1"] * 9 == list(wnew.df["G"])
    
def test_execute_join_right_in_parens():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("""
    self 
    | join kind=inner ( 
        self 
        | where G == 'G1' 
        | project G ) 
        on G 
    | project A, G
    """)
    
    assert ["A", "G"] == list(wnew.df.columns)
    assert ["G1"] * 9 == list(wnew.df["G"])

def test_execute_join_special_characters():
    df = create_df()
    df["b:G"] = df["G"]

    w = Wrap(df)
    wnew = w.execute("""
    self 
    | join kind=inner ( 
        self 
        | where ["b:G"] == 'G1' 
        | project ["b:G"] ) 
        on ["b:G"] 
    | project A, ["b:G"]
    """)
    
    assert ["A", "b:G"] == list(wnew.df.columns)
    assert ["G1"] * 9 == list(wnew.df["b:G"])

def test_execute_join_nokind():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("""
    self 
    | join ( 
        self 
        | where G == 'G1' 
        | project G ) 
        on G 
    | project A, G
    """)
    
    assert ["A", "G"] == list(wnew.df.columns)
    assert ["G1"] * 9 == list(wnew.df["G"])

def test_execute_join_left_on_right_on():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("""
    self 
    | join ( 
        self 
        | where G == 'G1' 
        | project GG=G ) 
        on $left.G == $right.GG 
    | project A, G
    """)
    
    assert ["A", "G"] == list(wnew.df.columns)
    assert ["G1"] * 9 == list(wnew.df["G"])

def test_execute_join_right_on_left_on():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("""
    self 
    | join ( 
        self 
        | where G == 'G1' 
        | project GG=G ) 
        on $right.GG ==  $left.G
    | project A, G
    """)
    
    assert ["A", "G"] == list(wnew.df.columns)
    assert ["G1"] * 9 == list(wnew.df["G"])

def test_execute_join_multiple_join_conditions():
    df = pd.DataFrame()
    df["A"] = [1, 1]
    df["B"] = [1, 2]
    df["C"] = [10, 20]
    df["D"] = [100, 200]

    df2 = pd.DataFrame()
    df2["A"] = [1, 1]
    df2["B2"] = [1, 0]
    df2["C2"] = [10, 0]

    w = Wrap(df)
    w = w.let(df2=df2)

    wnew = w.execute("""
    self 
    | join ( df2 ) 
        on A, $right.B2 ==  $left.B, $left.C == $right.C2
    """)
    
    assert ["A", "B", "C", "D", "B2", "C2"] == list(wnew.df.columns)
    assert [100] == list(wnew.df["D"])

def test_execute_wrap_object():
    df = create_df()

    w = Wrap(df)
    w2 = Wrap(pd.DataFrame()).let(w=w)
    wnew = w2.execute("w | where G == 'G1' | where A >= 1 | project C")

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])

def test_let_elementwise():
    df = pd.DataFrame()
    df["A"] = ["hello", "alice", "bob"]

    w = Wrap(df)
    
    def first(s):
        return s[0]
    
    w = w.let_elementwise(first1=first)
    wnew = w.extend("B = first1(A)")

    assert ["A", "B"] == list(wnew.df.columns)
    assert ["h", "a", "b"] == list(wnew.df["B"])

def test_let_elementwise_multiple_params():
    df = pd.DataFrame()
    df["A"] = [1, 2]

    w = Wrap(df)

    def x(a, b):
        # add assertion to ensure the function is called elementwise
        assert a == 1 or a == 2
        return a + b
    w = w.let_elementwise(x=x)
    
    wnew = w.extend("B = x(A, A + 1)")

    assert [3, 5] == list(wnew.df["B"])

def test_let_no_params():
    df = pd.DataFrame()
    df["A"] = [1, 1]

    w = Wrap(df)

    def x():
        return 3
    w = w.let(x=x)
    
    wnew = w.extend("B = A + x()")

    assert [4, 4] == list(wnew.df["B"])



def test_let_new_method_overrides_old_one():
    df = pd.DataFrame()
    df["A"] = [1, 2]

    w = Wrap(df)
    w = w.let(b=1)
    w = w.let(b=2)

    wnew = w.extend("B = A + b")
    assert ["A", "B"] == list(wnew.df.columns)
    assert [3, 4] == list(wnew.df["B"])

def test_union():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["B"] = [10, 20]

    df2 = pd.DataFrame()
    df2["A"] = [3, 4]
    df2["C"] = 30, 40

    w = Wrap(df)
    wnew = w.union([df2])

    assert ["A", "B", "C"] == list(wnew.df.columns)
    assert [1, 2, 3, 4] == list(wnew.df["A"])
    assert [10, 20, -1, -1] == replace_nan(wnew.df["B"], -1)
    assert [-1, -1, 30, 40] == replace_nan(wnew.df["C"], -1)

def test_union_inner():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["B"] = [10, 20]

    df2 = pd.DataFrame()
    df2["A"] = [3, 4]
    df2["C"] = 30, 40

    w = Wrap(df)
    wnew = w.union([df2], kind="inner")

    assert ["A"] == list(wnew.df.columns)
    assert [1, 2, 3, 4] == list(wnew.df["A"])

def test_union_execute():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["B"] = [10, 20]

    df2 = pd.DataFrame()
    df2["A"] = [3, 4]
    df2["C"] = [30, 40]

    w = Wrap(df)
    w = w.let(df2=df2)
    wnew = w.execute("""
    self 
    | union kind=outer df2
    """)

    assert ["A", "B", "C"] == list(wnew.df.columns)
    assert [1, 2, 3, 4] == list(wnew.df["A"])
    assert [10, 20, -1, -1] == replace_nan(wnew.df["B"], -1)
    assert [-1, -1, 30, 40] == replace_nan(wnew.df["C"], -1)

def test_union_execute_multiple_tables():
    df = pd.DataFrame()
    df["A"] = [1, 2]
    df["B"] = [10, 20]

    df2 = pd.DataFrame()
    df2["A"] = [3, 4]
    df2["C"] = [30, 40]

    df3 = pd.DataFrame()
    df3["A"] = [5, 6]
    df3["D"] = [50, 60]

    w = Wrap(df)
    w = w.let(df2=df2, df3=df3)
    wnew = w.execute("""
    self 
    | union kind=outer df2, df3
    """)

    assert ["A", "B", "C", "D"] == list(wnew.df.columns)
    assert [1, 2, 3, 4, 5, 6] == list(wnew.df["A"])
    assert [10, 20, -1, -1, -1, -1] == replace_nan(wnew.df["B"], -1)
    assert [-1, -1, 30, 40, -1, -1] == replace_nan(wnew.df["C"], -1)
    assert [-1, -1, -1, -1, 50, 60] == replace_nan(wnew.df["D"], -1)

def test_execute_comment():
    df = create_df()

    w = Wrap(df)
    wnew = w.execute("""
    self #c0
    | where G == 'G1' # c1
    # comment
    | where A >= 1 #c3
    | project C # another comment
    """)

    assert ["C"] == list(wnew.df.columns)
    assert ["foo2", "foo4"] == list(wnew.df["C"])