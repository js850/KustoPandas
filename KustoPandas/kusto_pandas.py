import pandas as pd
import re

import expression_parser as ep

class AggMethod:
    name = None
    def __init__(self, arg):
        self.arg = arg.strip()
    
    def default_name(self):
        return self.name + "_" + self.arg

class Count(AggMethod):
    name = "count"
    
    def validate(self, df):
        if self.arg:
            raise Exception("count can't take an arg: ", self.arg)
    
    def apply(self, grouped):
        return grouped.size()

class Sum(AggMethod):
    name = "sum"

    def validate(self, df):
        if self.arg not in df.columns:
            raise Exception("sum argument is not a column: ", self.arg)
    
    def apply(self, grouped):
        return grouped[self.arg].sum()

aggregate_map = {
    "count" : Count,
    "sum" : Sum,
}

class Aggregate:
    def __init__(self, text):
        self.new_col = None

        parsed = ep.parse_statement(text)

        if isinstance(parsed, ep.Assignment):
            self.new_col = str(parsed.left)
            method = parsed.right
        else:
            method = parsed

        if not isinstance(method, ep.Method):
            raise Exception("expected method but got: " + str(method))

        func_name = str(method.name)
        if len(method.args.args) == 0:
            func_arg = ""
        else:
            func_arg = str(method.args.args[0])

        self.aggregate_func = aggregate_map[func_name](func_arg)
        if self.new_col is None:
            self.new_col = self.aggregate_func.default_name()


    def validate(self, df):
        self.aggregate_func.validate(df)
    
class Wrap:
    def __init__(self, df):
        self.df = df
    
    def project(self, cols):
        self.df = self.df[cols]
        return self

    def summarize(self, resulting_cols, group_by_cols):
        if isinstance(resulting_cols, str):
            resulting_cols = [resulting_cols]

        if isinstance(group_by_cols, str):
            group_by_cols = [group_by_cols]

        for g in group_by_cols:
            if g not in self.df.columns:
                raise Exception("unknown column name: " + g)
        
        args = [Aggregate(a) for a in resulting_cols]
        for arg in args:
            arg.validate(self.df)

        grouped = self.df.groupby(group_by_cols)
        dfnew = pd.DataFrame()

        for arg in args:
            series = arg.aggregate_func.apply(grouped)
            dfnew[arg.new_col] = series
        
        self.df = dfnew.reset_index()
        return self
    
    def extend(self, text):
        parsed = ep.parse_statement(text)

        if not isinstance(parsed, ep.Assignment):
            raise Exception("exted expects an assignment: " + text)

        result_map = parsed.evaluate(self.df)

        for k, v in result_map.items():
            self.df[str(k)] = v
        
        return self

        

    
