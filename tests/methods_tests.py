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



