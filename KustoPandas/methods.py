import numpy as np
import pandas as pd

def iff(condition, a, b):
    return np.where(condition, a, b)

def datetime(val):
    return pd.to_datetime(val)

def bin(value, round_to):
    # todo implement for other data types
    return value.dt.floor(round_to)

def floor(value, round_to):
    return bin(value, round_to)

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

all_methods = [iff, datetime, bin, floor, extract]

method_map = dict(((m.__name__, m) for m in all_methods))

def get_methods():
    return method_map