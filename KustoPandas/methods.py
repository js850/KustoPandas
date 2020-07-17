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

all_methods = [iff, datetime, bin, floor]

method_map = dict(((m.__name__, m) for m in all_methods))

def get_methods():
    return method_map