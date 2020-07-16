import numpy as np
import pandas as pd

def iff(condition, a, b):
    return np.where(condition, a, b)


method_map = {
    "iff": iff
}

def get_methods():
    return method_map