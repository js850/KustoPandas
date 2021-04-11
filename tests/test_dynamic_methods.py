import unittest
import pandas as pd
import numpy as np
from context import Wrap

from test_utils import replace_nan

def create_df():
    df = pd.DataFrame(index=range(5))
    df["A"] = [0.0, 1.0, 2.0, 3.0, 4.0]
    df["B"] = [0, 1, 2, 3, 4]
    df["C"] = ["foo1", "foo2", "foo3", "foo4", "foo5"]
    df["D"] = pd.to_datetime(["2009-01-01", "2009-01-02", "2009-01-05", "2009-01-06", "2009-01-07"])    
    df["G"] = ["G1", "G1", "G2", "G1", "G2"]
    return df

def test_todynamic():
    df = pd.DataFrame()
    df["A"] = ["[1, 2]", '{ "a" : 7 }', '{ "b" : "val" }']

    w = Wrap(df)
    w = w.extend("d = todynamic(A)")

    assert [1, 2] == list(w.df["d"][0])
    assert 7 == w.df["d"][1]["a"]
    assert "val" == w.df["d"][2]["b"]

def test_parse_json():
    df = pd.DataFrame()
    df["A"] = ["[1, 2]", '{ "a" : 7 }', '{ "b" : "val" }']

    w = Wrap(df)
    w = w.extend("d = todynamic(A), p = parse_json(A)")

    assert list(w.df["d"]) == list(w.df["p"])

def test_dynamic_array_index():
    df = pd.DataFrame()
    df["A"] = ["[1, 2]", "[3, 4]"]

    w = Wrap(df)
    w = w.extend("d = todynamic(A)").extend("f = d[0], f1 = d[1]")

    assert [1, 3] == list(w.df["f"])
    assert [2, 4] == list(w.df["f1"])

def test_dynamic_array_index_negative():
    df = pd.DataFrame()
    df["A"] = ["[1, 2]", "[3, 4]"]

    w = Wrap(df)
    w = w.extend("d = todynamic(A)").extend("f = d[-2], f1 = d[-1]")

    assert [1, 3] == list(w.df["f"])
    assert [2, 4] == list(w.df["f1"])


def test_dynamic_bag_squarebrackets():
    df = pd.DataFrame()
    df["A"] = ['{ "k": "v0", "k2": { "k3": 3 } }', '{ "k": "v", "k2": { "k3": 13 } }']
    w = Wrap(df)
    w = w.extend("d = todynamic(A)").extend("f = d['k'], f1 = d['k2']['k3']")

    assert ["v0", "v"] == list(w.df["f"])
    assert [3, 13] == list(w.df["f1"])

def test_dynamic_squarebrackets_does_not_throw():
    df = pd.DataFrame()
    df["A"] = ['{ "k": "v0", "k2": { "k3": 3 } }', '{ "k": "v", "k2": { "k3": 13 } }', "[1, 2]"]
    w = Wrap(df)
    w = w.extend("d = todynamic(A)").extend("f = d['k'], f1 = d['k2']['k3'], f2=d[0]")

    assert ["v0", "v", None] == list(w.df["f"])
    assert [3, 13, None] == replace_nan(w.df["f1"], None)
    assert [None, None, 1] == replace_nan(w.df["f2"], None)

def test_dynamic_squarebrackets_variable_index():
    df = pd.DataFrame()
    df["A"] = ['{ "k": "v0", "k2": { "k3": 3 } }', '{ "k4": "v", "k2": { "k3": 13 } }', "[1, 2]"]
    df["B"] = ["k", "k4", 0]
    df["C"] = ["0", "0", "1"]
    w = Wrap(df)
    w = w.extend("d = todynamic(A)").extend("f = d[B], f1 = d[toint(C)]")

    assert ["v0", "v", 1] == list(w.df["f"])
    assert [None, None, 2] == replace_nan(w.df["f1"], None)

def test_dynamic_squarebrackets_index_arithmatic():
    df = pd.DataFrame()
    df["A"] = ["[1, 2, 3]", "[4, 5, 6]"]
    df["B"] = [0, 0]
    w = Wrap(df)
    w = w.extend("d = todynamic(A)").extend("f = d[B], f1 = d[B+1], f2 = d[B-1], f3 = d[(B-1)], f4 = d[(-1)]")

    assert [1, 4] == list(w.df["f"])
    assert [2, 5] == list(w.df["f1"])
    assert [3, 6] == list(w.df["f2"])
    assert [3, 6] == list(w.df["f3"])
    assert [3, 6] == list(w.df["f4"])

def test_dynamic_dot():
    df = pd.DataFrame()
    df["A"] = ['{ "k": "v0", "k2": { "k3": 3 } }', '{ "k": "v", "k2": { "k3": 13 } }', "[1, 2]"]
    w = Wrap(df)
    w = w.extend("d = todynamic(A)").extend("f = d.k, f1 = d.k2.k3")

    assert ["v0", "v", None] == list(w.df["f"])
    assert [3, 13, None] == replace_nan(w.df["f1"], None)