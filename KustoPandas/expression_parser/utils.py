import pandas as pd

def are_all_series(*args):
    return all((isinstance(a, pd.Series) for a in args))

def _is_datetime(series):
    if not are_all_series(series):
        # is_datetime64_any_dtype only works on series types
        series = pd.Series(series)
    return pd.api.types.is_datetime64_any_dtype(series)

def get_apply_elementwise_method(method):
    def apply_elementwise(*args):
        if len(args) == 0:
            # we could just return method() here, but that is identical to let
            # I think this should be called separately for every element.  It would allow someone to
            # return a new value for every row.  
            # TODO
            raise NotImplementedError()
        elif len(args) == 1:
            return args[0].apply(method)
        else:
            dftemp = pd.DataFrame()
            for i, x in enumerate(args):
                dftemp[str(i)] = x
            
            def wrap(x):
                return method(*x)
            result = dftemp.apply(wrap, axis=1)
            return result
    
    return apply_elementwise