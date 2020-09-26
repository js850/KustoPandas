import pandas as pd
import json


def dynamic(s):
    return s.apply(json.loads)

_all_methods = [dynamic]