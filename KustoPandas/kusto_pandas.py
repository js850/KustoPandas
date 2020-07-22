import pandas as pd
import re

from .expression_parser import parse_statement, Assignment
from .aggregates import create_aggregate
from .methods import get_methods

def ensure_column_name_unique(df, col):
    while col in df.columns:
        col = col + "_"
    return col


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
    
    def _repr_html_(self):
        return self.df._repr_html_()

    def _copy(self, df):
        w = Wrap(df)
        w.let_statements = list(self.let_statements)
        return w

    def _get_var_map(self):
        return MultiDict([self.df, get_methods()] + self.let_statements)

    def let(self, **kwargs):
        w = self._copy(self.df)
        w.let_statements.append(kwargs)
        return w

    def project(self, *cols, **renamed_cols):
        """
        all of the following are acceptable

        w.project("A", "B")

        w.project("A", BNew = "B")

        w.project("A", "Bnew=B")

        w.project("A", "Bnew = B+A")
        """
        dfnew = pd.DataFrame()
        var_map = self._get_var_map()

        for c in cols:
            parsed = parse_statement(c)
            result = parsed.evaluate(var_map)
            if isinstance(parsed, Assignment):
                for k, v in result.items():
                    dfnew[k] = v
            else:
                dfnew[c] = result
        
        for name, expr in renamed_cols.items():
            parsed = parse_statement(expr)
            result = parsed.evaluate(var_map)
            dfnew[name] = result

        return self._copy(dfnew)
    
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
                parsed = parse_statement(c)
                series = parsed.evaluate(self._get_var_map())
                temp_name = "__tempcolname_" + str(len(temp_col_names))
                temp_col_names.append(temp_name)
                group_by_col_names.append(temp_name)
                dftemp[temp_name] = series
        
        args = [create_aggregate(a) for a in resulting_cols]
        columns_needed = set()
        for arg in args:
            arg.validate(dftemp)
            for col_name, col_value in arg.columns_needed():
                columns_needed.add(col_name)
                if col_name not in dftemp:
                    result = col_value.evaluate(self._get_var_map())
                    dftemp[col_name] = result

        grouped = dftemp.groupby(group_by_col_names)
        dfnew = pd.DataFrame()

        for arg in args:
            result = arg.apply(grouped)
            for col, series in result:
                col = ensure_column_name_unique(dfnew, col)
                dfnew[col] = series
        
        dfnew = dfnew.reset_index()

        return self._copy(dfnew)
    
    def extend(self, text):
        parsed = parse_statement(text)

        if not isinstance(parsed, Assignment):
            raise Exception("extend expects an assignment: " + text)

        result_map = parsed.evaluate(self._get_var_map())

        newdf = self.df.copy(deep=False)
        for k, v in result_map.items():
            newdf[str(k)] = v
        
        return self._copy(newdf)
    
    def where(self, condition):
        parsed = parse_statement(condition)
        if isinstance(parsed, Assignment):
            raise Exception("where cannot have assignment: " + str(parsed))

        result = parsed.evaluate(self._get_var_map())

        newdf = self.df[result]
        return self._copy(newdf)
    
    def take(self, n):
        newdf = self.df.head(n)
        return self._copy(newdf)#
    
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

        var_map = self._get_var_map()
        for col, expr in zip(col_names, by):
            parsed = parse_statement(expr)
            series = parsed.evaluate(var_map)
            df[col] = series
        
        asc = [not b for b in desc]
        df = df.sort_values(col_names, ascending=asc)

        for c in col_names:
            del df[c]

        return self._copy(df)

    def top(self, n, by, desc=True):
        return self.sort(by, desc=desc).take(n)
    
    def join(self, right, on=None, left_on=None, right_on=None, kind="inner"):
        if isinstance(right, Wrap):
            right = right.df

        # fix suffixes to align with what kusto does in case of name conflict
        dfnew = self.df.merge(right=right, how=kind, on=on, left_on=left_on, right_on=right_on, suffixes=("", "_y"))

        return self._copy(dfnew)

        

    
