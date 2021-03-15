import pandas as pd

from ._simple_expression import SimpleExpression

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