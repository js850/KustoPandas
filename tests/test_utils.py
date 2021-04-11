import numpy as np

def replace_nan(array, val):
    """
    comparing lists with nan in them is annoying because nan == nan returns true
    """
    return list(np.where(np.isnan(array), val, array))