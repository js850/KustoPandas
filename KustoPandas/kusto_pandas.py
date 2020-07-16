import pandas as pd
import re

import expression_parser as ep
from aggregates import Aggregate
    
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
            result = arg.apply(grouped)
            for col, series in result:
                dfnew[col] = series
        
        self.df = dfnew.reset_index()
        return self
    
    def extend(self, text):
        parsed = ep.parse_statement(text)

        if not isinstance(parsed, ep.Assignment):
            raise Exception("extend expects an assignment: " + text)

        result_map = parsed.evaluate(self.df)

        for k, v in result_map.items():
            self.df[str(k)] = v
        
        return self
    
    def where(self, condition):
        parsed = ep.parse_statement(condition)
        if isinstance(parsed, ep.Assignment):
            raise Exception("where cannot have assignment: " + str(parsed))

        result = parsed.evaluate(self.df)

        self.df = self.df[result]

        return self

        

    
