import pandas as pd

def are_all_series(*args):
    return all((isinstance(a, pd.Series) for a in args))

def _is_datetime(series):
    if not are_all_series(series):
        # is_datetime64_any_dtype only works on series types
        series = pd.Series(series)
    return pd.api.types.is_datetime64_any_dtype(series)