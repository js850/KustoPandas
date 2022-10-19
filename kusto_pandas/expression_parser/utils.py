import pandas as pd

def is_series(s):
    return isinstance(s, pd.Series)

def are_all_series(*args):
    return all((is_series(a) for a in args))

def any_are_series(*args):
    return any((is_series(a) for a in args))

def first_series_or_none(args):
    for a in args:
        if is_series(a):
            return a

    return None

def _is_datetime(series):
    if not are_all_series(series):
        # is_datetime64_any_dtype only works on series types
        series = pd.Series(series)
    return pd.api.types.is_datetime64_any_dtype(series)

def get_apply_elementwise_method(method):
    def apply_elementwise(*args):
        if len(args) == 0:
            return method(*args)
        elif len(args) == 1:
            return args[0].apply(method)
        else:
            # If the first argument is not a series, then we have to manually specify the number of expected elements
            first_series = first_series_or_none(args)

            if first_series is None:
                return method(*args)

            index_len = len(first_series)

            dftemp = pd.DataFrame(index=range(index_len))
            for i, x in enumerate(args):
                dftemp[str(i)] = x
            
            def wrap(x):
                return method(*x)
            result = dftemp.apply(wrap, axis=1)
            return result
    
    return apply_elementwise