import numpy as np
import pandas as pd

from KustoPandas import dynamic_methods

def iff(condition, a, b):
    return np.where(condition, a, b)

def datetime(val):
    return pd.to_datetime(val)

def toint(val):
    return val.astype(int)

def todouble(val):
    return pd.to_numeric(val)

def toreal(val):
    return todouble(val)

def double(val):
    return todouble(val)

def real(val):
    return todouble(val)

def bin(value, round_to):
    # todo implement for other data types
    return value.dt.floor(round_to)

def floor(value, round_to):
    return bin(value, round_to)

def isnull(series):
    return series.isnull()

def isnotnull(series):
    return ~isnull(series)

def isnan(series):
    return isnull(series)

def isnotnan(series):
    return ~isnan(series)

def isempty(series):
    return isnull(series) | (series == "")

def isnotempty(series):
    return ~isempty(series)

def tolower(series):
    return series.str.lower()

def toupper(series):
    return series.str.upper()

def tostring(series):
    return iff(isempty(series), "", series.astype(str))

def extract(regex, capture_group, text):
    if capture_group == 0:
        raise Exception("capture_group 0 not implemented yet because I can't figure out how to do it in Pandas.  Try using capture_group 1 but enclosing the whole regex in parentheses")
    elif capture_group > 0:
        # the output of pandas extract is a dataframe: one column for each capture group, aka set of parentheses
        result_df = text.str.extract(regex)
        # capture_group 1 is at position 0, etc
        series_col_name = result_df.columns[capture_group - 1]
        return result_df[series_col_name]
    else:
        raise Exception("capture_group must be a non-negative integer: " + str(capture_group))

all_methods = [iff, datetime, bin, floor, extract, toint, 
               todouble, toreal, double, real,
               isnull, isnan, isempty,
               isnotnull, isnotnan, isnotempty,
               tolower, toupper, tostring
               ] + dynamic_methods._all_methods

method_map = dict(((m.__name__, m) for m in all_methods))

def get_methods():
    return method_map