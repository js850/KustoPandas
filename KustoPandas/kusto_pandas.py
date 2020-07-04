import pandas as pd
import re

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
        if "=" in text:
            name, func = text.split("=")
            self.new_col = name.strip()
        else:
            func = text

        split_func = func.strip().replace("(", ")").split(")")
        if len(split_func) != 3 and split_func[2]:
            raise Exception("Could not parse aggregate function " + func)
        func_name = split_func[0]
        func_arg = split_func[1]

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

        

    
