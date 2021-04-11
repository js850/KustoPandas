import pandas as pd
import json

from KustoPandas.expression_parser.utils import are_all_series, any_are_series, get_apply_elementwise_method, is_series

def todynamic(s):
    return s.apply(json.loads)

def parse_json(s):
    return todynamic(s)

def _pack_strings(*args):
    d = dict()
    for k, v in zip(args, args[1:]):
        d[k] = v
    return d

def pack(*args):
    wrapped = get_apply_elementwise_method(_pack_strings)
    return wrapped(*args)

_all_methods = [todynamic, parse_json, pack]

_method_map = dict(((m.__name__, m) for m in _all_methods))

# aliases
_method_map["pack_dictionary"] = pack
