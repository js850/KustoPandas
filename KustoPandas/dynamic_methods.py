import pandas as pd
import json


def todynamic(s):
    return s.apply(json.loads)

def parse_json(s):
    return todynamic(s)

_all_methods = [todynamic, parse_json]