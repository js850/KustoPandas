import pandas as pd
import json

from kusto_pandas.expression_parser.utils import are_all_series, any_are_series, get_apply_elementwise_method, is_series
from kusto_pandas.expression_parser.expression_parser_types import _todynamic

def todynamic(s):
    if is_series(s):
        return s.apply(_todynamic)
    return _todynamic(s)

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
