import pandas as pd
import re


class Count:
    name = "count"
    def __init__(self, arg):
        self.arg = arg
    
    def validate(self, df):
        if self.arg.strip():
            raise Exception("count can't take an arg: ", self.arg)

aggregate_map = {
    "count" : Count
}

class Aggregate:
    def __init__(self, text):
        if "=" in text:
            name, func = text.split("=")
            self.new_col = name.strip()

            split_func = func.strip().replace("(", ")").split(")")
            if len(split_func) != 3 and split_func[2]:
                raise Exception("Could not parse aggregate function " + func)
            func_name = split_func[0]
            func_arg = split_func[1]

            self.aggregate_func = aggregate_map[func_name](func_arg)

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

        

    
