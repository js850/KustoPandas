import pandas as pd
import re

import expression_parser as ep
from aggregates import Aggregate
from methods import get_methods

class MultiDict:
    def __init__(self, dicts):
        self.dicts = dicts
    
    def __getitem__(self, key):
        for d in self.dicts:
            try:
                return d[key]
            except KeyError:
                pass
        
        raise KeyError("key")

class Wrap:
    def __init__(self, df):
        self.df = df
        self.let_statements = []
    
    def create_new(self, df):
        w = Wrap(df)
        w.let_statements = list(self.let_statements)
        return w

    def get_var_map(self):
        return MultiDict([self.df, get_methods()] + self.let_statements)

    def let(self, **kwargs):
        w = self.create_new(self.df)
        w.let_statements.append(kwargs)
        return w

    def project(self, *cols, **renamed_cols):
        dfnew = pd.DataFrame()

        for c in cols:
            dfnew[c] = self.df[c]
        
        var_map = self.get_var_map()
        for name, expr in renamed_cols.items():
            parsed = ep.parse_statement(expr)
            result = parsed.evaluate(var_map)
            dfnew[name] = result

        return self.create_new(dfnew)
    
    def summarize(self, resulting_cols, group_by):
        if isinstance(resulting_cols, str):
            resulting_cols = [resulting_cols]

        if isinstance(group_by, str):
            group_by = [group_by]

        dftemp = self.df.copy(deep=False)

        group_by_col_names = []
        temp_col_names = []
        for c in group_by:
            if c in dftemp.columns:
                group_by_col_names.append(c)
            else:
                parsed = ep.parse_statement(c)
                series = parsed.evaluate(self.get_var_map())
                temp_name = "__tempcolname_" + str(len(temp_col_names))
                temp_col_names.append(temp_name)
                group_by_col_names.append(temp_name)
                dftemp[temp_name] = series
        
        args = [Aggregate(a) for a in resulting_cols]
        for arg in args:
            arg.validate(dftemp)

        grouped = dftemp.groupby(group_by_col_names)
        dfnew = pd.DataFrame()

        for arg in args:
            result = arg.apply(grouped)
            for col, series in result:
                dfnew[col] = series
        
        dfnew = dfnew.reset_index()

        return self.create_new(dfnew)
    
    def extend(self, text):
        parsed = ep.parse_statement(text)

        if not isinstance(parsed, ep.Assignment):
            raise Exception("extend expects an assignment: " + text)

        result_map = parsed.evaluate(self.get_var_map())

        newdf = self.df.copy(deep=False)
        for k, v in result_map.items():
            newdf[str(k)] = v
        
        return self.create_new(newdf)
    
    def where(self, condition):
        parsed = ep.parse_statement(condition)
        if isinstance(parsed, ep.Assignment):
            raise Exception("where cannot have assignment: " + str(parsed))

        result = parsed.evaluate(self.get_var_map())

        newdf = self.df[result]
        return self.create_new(newdf)
    
    def take(self, n):
        newdf = self.df.head(n)
        return self.create_new(newdf)#
    
    def sort(self, by, desc=True):
        """
        sort by strlen(country) asc, price desc

        this syntax is a bit awkward.

        by can be a column name, or an expression built from columns e.g. (strlen(country))
            or it can be a list of such expressions
        desc (if true, sort by descending order) can be a bool
            or list of bools.  If it's a list, it must be equal in length to the list of expressions 
        """
        if isinstance(by, str):
            by = [by]
            if not isinstance(desc, bool):
                raise Exception("desc must be of type bool if by is not a list")
            desc = [desc]
        else:
            if isinstance(desc, bool):
                desc = [bool] * len(by)
            if not len(desc) == len(by):
                raise Exception("the length of lists by and desc must be equal")

        df = self.df.copy(deep=False)

        col_names = ["__tempcol_" + str(i) for i in range(len(by))]

        var_map = self.get_var_map()
        for col, expr in zip(col_names, by):
            parsed = ep.parse_statement(expr)
            series = parsed.evaluate(var_map)
            df[col] = series
        
        asc = [not b for b in desc]
        df = df.sort_values(col_names, ascending=asc)

        for c in col_names:
            del df[c]

        return self.create_new(df)

    def top(self, n, by, desc=True):
        return self.sort(by, desc=desc).take(n)
    
    def join(self, right, on=None, left_on=None, right_on=None, kind="inner"):
        if isinstance(right, Wrap):
            right = right.df

        # fix suffixes to align with what kusto does in case of name conflict
        dfnew = self.df.merge(right=right, how=kind, on=on, left_on=left_on, right_on=right_on, suffixes=("", "_y"))

        return self.create_new(dfnew)

        

    
