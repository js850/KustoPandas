import unittest
import pandas as pd
import numpy as np
from context import Wrap
import base64

def create_df():
    df = pd.DataFrame(index=range(5))
    df["A"] = [0.0, 1.0, 2.0, 3.0, 4.0]
    df["B"] = [0, 1, 2, 3, 4]
    df["C"] = ["foo1", "foo2", "foo3", "foo4", "foo5"]
    df["D"] = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])    
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    return df

class TestMethods(unittest.TestCase):
    def test_datetime_column(self):
        df = create_df()
        df["D"] = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])    
        df["D1"] = ["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"]   

        self.assertGreater(len(df.columns), 2)
        print(df.columns)
        w = Wrap(df)
        wnew = w.project("D", "DT1=datetime(D1)")
        self.assertListEqual(["D", "DT1"], list(wnew.df.columns))
        self.assertListEqual(list(wnew.df["D"]), list(wnew.df["DT1"]))

    def test_todatetime_column(self):
        df = create_df()
        df["D"] = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])    
        df["D1"] = ["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"]   

        self.assertGreater(len(df.columns), 2)
        print(df.columns)
        w = Wrap(df)
        wnew = w.project("D", "DT1= todatetime(D1)")
        self.assertListEqual(["D", "DT1"], list(wnew.df.columns))
        self.assertListEqual(list(wnew.df["D"]), list(wnew.df["DT1"]))

    def test_extract(self):
        df = pd.DataFrame()
        df["A"] = ["Duration = 1;A, Duration=2;B", "Duration=3;C"]

        w = Wrap(df)
        wnew = w.project("D=extract('uration *= *([0-9]+);([^,]*)', 1, A)")
        self.assertListEqual(["D"], list(wnew.df.columns))
        self.assertListEqual(list(wnew.df["D"]), ["1", "3"])

    def test_extract2(self):
        df = pd.DataFrame()
        df["A"] = ["Duration = 1;A, Duration=2;B", "Duration=3;C"]

        w = Wrap(df)
        wnew = w.project("D=extract('uration *= *([0-9]+);([^,]*)', 2, A)")
        self.assertListEqual(["D"], list(wnew.df.columns))
        self.assertListEqual(list(wnew.df["D"]), ["A", "C"])

    def test_todynamic(self):
        df = pd.DataFrame()
        df["A"] = ['{"k1":"v1"}', '{"k1" : "v2"}']

        w = Wrap(df)
        w = w.extend("D = todynamic(A)")

        self.assertEqual("v1", w.df["D"][0]["k1"])

    def test_toint(self):
        df = create_df()
        df["A"] = [1.2, "1", 2.0, 4, 5]

        w = Wrap(df)
        w = w.extend("D = toint(A)")

        self.assertListEqual([1, 1, 2, 4, 5], list(w.df["D"]))

    def test_todouble(self):
        df = create_df()
        df["A"] = [1.2, "1", "2.7", 4, 5]

        w = Wrap(df)
        w = w.extend("D = todouble(A), D1 = toreal(A), D2 = double(A), D3 = real(A)")

        expected = [float(x) for x in df["A"]]
        self.assertListEqual(expected, list(w.df["D"]))
        self.assertListEqual(expected, list(w.df["D1"]))
        self.assertListEqual(expected, list(w.df["D2"]))
        self.assertListEqual(expected, list(w.df["D3"]))

    def test_isnull(self):
        df = create_df()
        df["A"] = [1, "hi", None, np.nan, ""]

        w = Wrap(df)
        w = w.extend("D = isnull(A)")

        self.assertListEqual([False, False, True, True, False], list(w.df["D"]))

    def test_isnotnull(self):
        df = create_df()
        df["A"] = [1, "hi", None, np.nan, ""]

        w = Wrap(df)
        w = w.extend("D = isnotnull(A)")

        self.assertListEqual([True, True, False, False, True], list(w.df["D"]))

    def test_isnan(self):
        df = create_df()
        df["A"] = [1, "hi", None, np.nan, ""]

        w = Wrap(df)
        w = w.extend("D = isnan(A)")

        self.assertListEqual([False, False, True, True, False], list(w.df["D"]))

    def test_isnotnan(self):
        df = create_df()
        df["A"] = [1, "hi", None, np.nan, ""]

        w = Wrap(df)
        w = w.extend("D = isnotnan(A)")

        self.assertListEqual([True, True, False, False, True], list(w.df["D"]))

    def test_isempty(self):
        df = create_df()
        df["A"] = [1, "hi", None, np.nan, ""]

        w = Wrap(df)
        w = w.extend("D = isempty(A)")

        self.assertListEqual([False, False, True, True, True], list(w.df["D"]))

    def test_isnotempty(self):
        df = create_df()
        df["A"] = [1, "hi", None, np.nan, ""]

        w = Wrap(df)
        w = w.extend("D = isnotempty(A)")

        self.assertListEqual([True, True, False, False, False], list(w.df["D"]))
    
    def test_tolower(self):
        df = create_df()
        df["A"] = ["hi", "HI", " Hi", "", None]

        w = Wrap(df)
        w = w.extend("D = tolower(A)")

        self.assertListEqual(["hi", "hi", " hi", "", None], list(w.df["D"]))
    
    def test_toupper(self):
        df = create_df()
        df["A"] = ["hi", "HI", " Hi", "", None]

        w = Wrap(df)
        w = w.extend("D = toupper(A)")

        self.assertListEqual(["HI", "HI", " HI", "", None], list(w.df["D"]))
    
    def test_tostring(self):
        df = create_df()
        df["A"] = [1, "HI", np.nan, "", None]

        w = Wrap(df)
        w = w.extend("D = tostring(A)")

        assert ["1", "HI", "", "", ""] == list(w.df["D"])


def test_bin():
    df = create_df()
    df["D"] = pd.to_datetime(["2009-01-01T10", "2009-01-02", "2009-01-05T01", "2009-01-06", "2009-01-07T03"])

    w = Wrap(df)
    c = w.extend("F = bin(D, 1d)")

    expected = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])

    assert list(expected) == list(c.df["F"])

def test_floor():
    df = create_df()
    df["D"] = pd.to_datetime(["2009-01-01T10", "2009-01-02", "2009-01-05T01", "2009-01-06", "2009-01-07T03"])

    w = Wrap(df)
    c = w.extend("F = floor(D, 1d)")

    expected = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])

    assert list(expected) == list(c.df["F"])

def test_floor_number():
    df = create_df()
    df["D"] = [1.0, 1.1, 2.2, 3.0, 4.4]

    w = Wrap(df)
    c = w.extend("F = floor(D, 1)")

    expected = [1.0, 1.0, 2.0, 3.0, 4.0]

    assert list(expected) == list(c.df["F"])

def test_ceiling():
    df = create_df()
    df["D"] = [1.0, 1.1, 2.2, 3.0, 4.4]

    w = Wrap(df)
    c = w.extend("F = ceiling(D)")

    expected = [1, 2, 3, 3, 5]
    assert list(expected) == list(c.df["F"])

def test_isfinite():
    df = create_df()
    df["D"] = [1.0, -np.inf, np.inf, None, np.nan]

    w = Wrap(df)
    c = w.extend("F = isfinite(D)")

    assert list([True, False, False, False, False]) == list(c.df["F"])

def test_isinf():
    df = create_df()
    df["D"] = [1.0, -np.inf, np.inf, None, np.nan]

    w = Wrap(df)
    c = w.extend("F = isinf(D)")

    assert list([False, True, True, False, False]) == list(c.df["F"])

def test_log():
    df = create_df()

    w = Wrap(df)
    c = w.extend("F = log(A)")

    assert list(np.log([0, 1, 2, 3, 4])) == list(c.df["F"])

def test_log10():
    df = create_df()

    w = Wrap(df)
    c = w.extend("F = log10(A)")
    
    assert list(np.log10([0, 1, 2, 3, 4])) == list(c.df["F"])

def test_log2():
    df = create_df()

    w = Wrap(df)
    c = w.extend("F = log2(A)")
    
    assert list(np.log2([0, 1, 2, 3, 4])) == list(c.df["F"])

def test_sqrt():
    df = create_df()

    w = Wrap(df)
    c = w.extend("F = sqrt(A)")
    
    assert list(np.sqrt([0, 1, 2, 3, 4])) == list(c.df["F"])

def test_strlen():
    df = create_df()
    df["A"] = ["hi", "", None, " ", "hi "]

    w = Wrap(df)
    c = w.extend("F = strlen(A)")
    
    # comparing is annoying because np.nan == np.nan evaluates to false
    result = np.where(np.isnan(c.df["F"]), -1, c.df["F"])

    assert list([2.0, 0.0, -1, 1.0, 3.0]) == list(result)


def test_exp():
    df = create_df()

    w = Wrap(df)
    c = w.extend("F = exp(A)")

    assert list(np.exp([0, 1, 2, 3, 4])) == list(c.df["F"])

def test_exp2():
    df = create_df()

    w = Wrap(df)
    c = w.extend("F = exp2(A)")

    assert list(np.exp2([0, 1, 2, 3, 4])) == list(c.df["F"])

def test_exp10():
    df = create_df()

    w = Wrap(df)
    c = w.extend("F = exp10(A)")

    assert list(np.power(10, [0, 1, 2, 3, 4])) == list(c.df["F"])

def test_not():
    df = pd.DataFrame()
    df["A"] = [True, False, False]
    w = Wrap(df)
    wnew = w.extend("B = not(A)")
    assert ["A", "B"] == list(wnew.df.columns)
    assert [False, True, True] == list(wnew.df["B"])

def _encode_base64(s):
    str_bytes = bytes(s, "utf-8")
    encoded_bytes = base64.b64encode(str_bytes)
    return encoded_bytes.decode("utf-8")

def _decode_base64(s):
    message_bytes = base64.b64decode(s)
    message = message_bytes.decode('utf-8')
    return message

def test_base64_decode_tostring_series():
    df = pd.DataFrame()
    df["A"] = [_encode_base64("hello"), _encode_base64("There ")]

    w = Wrap(df)
    
    w = w.extend("B = base64_decode_tostring(A)")
    assert ["hello", "There "] == list(w.df["B"])

def test_base64_decode_tostring():
    df = pd.DataFrame()
    df["A"] = ["hello", "There "]
    h = _encode_base64("hello")
    w = Wrap(df)
    
    w = w.let(h=h).extend("B = A == base64_decode_tostring(h)")
    assert [True, False] == list(w.df["B"])

def test_base64_encode_tostring_series():
    df = pd.DataFrame()
    df["A"] = ["hello", "There "]

    w = Wrap(df)
    
    w = w.extend("B = base64_encode_tostring(A)")
    assert [_encode_base64("hello"), _encode_base64("There ")] == list(w.df["B"])

def test_base64_encode_tostring():
    df = pd.DataFrame()
    df["A"] = [_encode_base64("hello"), _encode_base64("There ")]
    h = "hello"
    w = Wrap(df)
    
    w = w.let(h=h).extend("B = A == base64_encode_tostring(h)")
    assert [True, False] == list(w.df["B"])
