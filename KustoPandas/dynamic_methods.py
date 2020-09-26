import pandas as pd
import json


def todynamic(s):
    return s.apply(json.loads)

_all_methods = [todynamic]