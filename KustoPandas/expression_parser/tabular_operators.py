import pandas as pd

from ._simple_expression import SimpleExpression, _evaluate_and_get_name
from .aggregates import create_aggregate

def ensure_column_name_unique(df, col):
    while col in df.columns:
        col = col + "_"
    return col

class Take:
    def __init__(self, n):
        self.n = n
    
    def evaluate_top(self, df, vars):
        n = self.n.evaluate(vars)
        return df.head(n)
    
class Where:
    def __init__(self, predicate):
        self.predicate = predicate
    
    def evaluate_top(self, df, vars):
        mask = self.predicate.evaluate(vars)

        return df[mask].copy()
class Extend:
    def __init__(self, args):
        self.args = args
    
    def evaluate_top(self, df, var_map):
        dfnew = df.copy(deep=False)
        for parsed in self.args:
            se = SimpleExpression(parsed)
            name = se.get_name()
            result = se.evaluate(var_map)
            dfnew[name] = result
        
        return dfnew

class Summarize:
    def __init__(self, aggregates, by):
        self.aggregates = aggregates
        self.by = by
    
    def evaluate_top(self, df, variable_map):
        dftemp = pd.DataFrame(index=df.index.copy())

        group_by_col_names = []
        for parsed in self.by:
            col_name, series = _evaluate_and_get_name(parsed, variable_map)
            if col_name in group_by_col_names:
                raise Exception("Column can only appear once in group by expression " + col_name)

            group_by_col_names.append(col_name)
            dftemp[col_name] = series
        
        all_columns = set(df.columns) - set(group_by_col_names)

        args = [create_aggregate(a, all_columns) for a in self.aggregates]

        for arg in args:
            for col_name, col_value in arg.evaluate_column_inputs(variable_map):
                if col_name not in dftemp.columns:
                    dftemp[col_name] = col_value

        if len(group_by_col_names) > 0:
            grouped = dftemp.groupby(group_by_col_names)
        else:
            # it's allowed to pass nothing as group by.  In which case the aggregate will 
            # operate on the entire series
            grouped = dftemp
        dfnew = pd.DataFrame()

        for arg in args:
            result = arg.apply(grouped, variable_map)
            for col, series in result:
                col = ensure_column_name_unique(dfnew, col)
                dfnew[col] = series
        
        if len(group_by_col_names) > 0:
            dfnew = dfnew.reset_index()
        
        return dfnew