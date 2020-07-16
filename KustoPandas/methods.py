import numpy as np
import pandas as pd

def iff(condition, a, b):
    return np.where(condition, a, b)

def datetime(val):
    return pd.to_datetime(val)

all_methods = [iff, datetime]

method_map = dict(((m.__name__, m) for m in all_methods))

def get_methods():
    return method_map