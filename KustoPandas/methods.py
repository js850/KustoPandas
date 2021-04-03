import numpy as np
import pandas as pd

from KustoPandas import dynamic_methods
from KustoPandas.expression_parser.expression_parser_types import _not

def _is_datetime(series):
    return pd.api.types.is_datetime64_any_dtype(series)

def iff(condition, a, b):
    return np.where(condition, a, b)

def datetime(val):
    return pd.to_datetime(val)

def todatetime(val):
    return datetime(val)

def toint(val):
    return val.astype(int)

def todouble(val):
    return pd.to_numeric(val)

def toreal(val):
    return todouble(val)

def tobool(series):
    raise NotImplementedError("tobool is not implemented because series.astype(bool) converts all strings to bools.  Doing it properly will take some effort")

def double(val):
    return todouble(val)

def real(val):
    return todouble(val)

def bin(series, round_to):
    if _is_datetime(series):
        return series.dt.floor(round_to)
    else:
        if round_to != 1:
            raise NotImplementedError("bin so far only supports rounding to nearest integer.  round_to = " + str(round_to))
        return pd.Series(np.floor(series))

def floor(series, round_to):
    return bin(series, round_to)

def ceiling(series):
    return pd.Series(np.ceil(series))

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

def isfinite(series):
    return pd.Series(np.isfinite(series))

def isinf(series):
    return pd.Series(np.isinf(series))

def tolower(series):
    return series.str.lower()

def toupper(series):
    return series.str.upper()

def tostring(series):
    return iff(isempty(series), "", series.astype(str))

def log(series):
    return pd.Series(np.log(series))

def log10(series):
    return pd.Series(np.log10(series))

def log2(series):
    return pd.Series(np.log2(series))

def exp(series):
    return pd.Series(np.exp(series))

def exp2(series):
    return pd.Series(np.exp2(series))

def exp10(series):
    return pd.Series(np.power(10, series))

def sqrt(series):
    return pd.Series(np.sqrt(series))

def strlen(series):
    return series.str.len()

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

all_methods = [iff, datetime, todatetime, bin, floor, ceiling, extract, toint, 
               todouble, toreal, double, real, tobool,
               isnull, isnan, isempty,
               isnotnull, isnotnan, isnotempty,
               isfinite, isinf,
               tolower, toupper, tostring,
               log, log10, log2, sqrt,
               exp, exp2, exp10,
               strlen
               ] + dynamic_methods._all_methods

method_map = dict(((m.__name__, m) for m in all_methods))

# not is a reserved keywork in python.  I can't have a method called not
method_map["not"] = _not

def get_methods():
    return method_map