import pandas as pd
import re
from functools import reduce

from .expression_parser import parse_expression, Assignment, Var, Method, By, Comma, flatten_comma
from .aggregates import create_aggregate
from .methods import get_methods
from ._render import render
from ._input_parsing import _parse_input_expression_args, _parse_input_expression_kwargs, _parse_input_expression_args_kwargs, _split_if_comma, _split_by_operator, _evaluate_and_get_name, _parse_input_expression_or_list_of_expressions, Inputs


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
        
        raise KeyError(key)

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
        
        w.project(["A", "B"])

        w.project("A", BNew="B")

        w.project("A", "Bnew=B")

        w.project("A", "Bnew = B+A")
        
        w.project("A, Bnew = B+A")
        """
        inputs = Inputs(*cols, **renamed_cols)

        dfnew = pd.DataFrame()
        var_map = self._get_var_map()

        for parsed in inputs.parsed_inputs:
            result = parsed.evaluate(var_map)
            dfnew[parsed.get_name()] = result
        
        return self._copy(dfnew)

    def project_away(self, *cols):
        inputs = Inputs(*cols)
        dfnew = self.df.copy()
        for column in inputs.parse_as_column_name_or_pattern(dfnew):
            del dfnew[column]

        return self._copy(dfnew)

    def project_keep(self, *cols):
        inputs = Inputs(*cols)
        columns_to_keep = set(inputs.parse_as_column_name_or_pattern(self.df))

        # maintain the original orderin of the columns
        columns = [c for c in self.df.columns if c in columns_to_keep]

        dfnew = self.df[columns].copy()
        return self._copy(dfnew)

    def project_rename(self, *args, **kwargs):
        # improve this implementation
        return self.extend(*args, **kwargs)
    
    def summarize(self, aggregates, by=None):
        if isinstance(aggregates, str):
            parsed = parse_expression(aggregates)
            if isinstance(parsed, By):
                aggs, group_by = _split_by_operator(parsed)
                return self._summarize(aggs, group_by)
            aggregates_parsed = _split_if_comma(parsed)
        else:
            aggregates_parsed = [parse_expression(a) for a in aggregates]

        if isinstance(by, str):
            parsed = parse_expression(by)
            by_parsed = _split_if_comma(parsed)
        elif by is None:
            by_parsed = []
        else:
            by_parsed = [parse_expression(c) for c in by]
        
        return self._summarize(aggregates_parsed, by_parsed)

    def _summarize(self, aggregates, by):
        # if by is None:
        #     parsed 

        dftemp = self.df.copy(deep=False)

        group_by_col_names = []
        variable_map = self._get_var_map()
        for c in by:
            cstr = str(c)
            if cstr in dftemp.columns:
                group_by_col_names.append(cstr)
            else:
                parsed = c
                col_name, series = _evaluate_and_get_name(parsed, variable_map)
                group_by_col_names.append(col_name)
                dftemp[col_name] = series
        
        all_columns = set(self.df.columns) - set(group_by_col_names)

        args = [create_aggregate(a, all_columns) for a in aggregates]

        columns_needed = set()
        for arg in args:
            arg.validate(dftemp)
            for col_name, col_value in arg.columns_needed():
                columns_needed.add(col_name)
                if col_name not in dftemp:
                    result = col_value.evaluate(self._get_var_map())
                    dftemp[col_name] = result

        if len(group_by_col_names) > 0:
            grouped = dftemp.groupby(group_by_col_names)
        else:
            # it's allowed to pass nothing as group by.  In which case the aggregate will 
            # operate on the entire series
            grouped = dftemp
        dfnew = pd.DataFrame()

        for arg in args:
            result = arg.apply(grouped)
            for col, series in result:
                col = ensure_column_name_unique(dfnew, col)
                dfnew[col] = series
        
        if len(group_by_col_names) > 0:
            dfnew = dfnew.reset_index()

        return self._copy(dfnew)
    
    def extend(self, *args, **kwargs):
        inputs = Inputs(*args, **kwargs)

        dfnew = self.df.copy(deep=False)
        var_map = self._get_var_map()
        for parsed in inputs.parsed_inputs:
            name = parsed.get_name()
            result = parsed.evaluate(var_map)
            dfnew[name] = result

        return self._copy(dfnew)
    
    def where(self, condition):
        parsed = parse_expression(condition)
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

        by can be a column name, or an expression built from columns e.g. (strlen(country))
            or it can be a list of such expressions
        desc (if true, sort by descending order) can be a bool
            or list of bools.  If it's a list, it must be equal in length to the list of expressions 
        """
        parsed_inputs = _parse_input_expression_or_list_of_expressions(by)
        if isinstance(desc, bool):
            desc = [desc] * len(parsed_inputs)
        elif len(parsed_inputs) != len(desc):
            raise Exception("the length of lists by and desc must be equal")

        dfnew = self.df.copy(deep=False)

        col_names = ["__tempcol_" + str(i) for i in range(len(parsed_inputs))]

        var_map = self._get_var_map()
        for col, expr in zip(col_names, parsed_inputs):
            series = expr.evaluate(var_map)
            dfnew[col] = series
        
        asc = [not b for b in desc]
        dfnew = dfnew.sort_values(col_names, ascending=asc)

        for c in col_names:
            del dfnew[c]

        return self._copy(dfnew)

    def top(self, n, by, desc=True):
        return self.sort(by, desc=desc).take(n)
    
    def join(self, right, on=None, left_on=None, right_on=None, kind="inner"):
        if isinstance(right, Wrap):
            right = right.df

        # fix suffixes to align with what kusto does in case of name conflict
        dfnew = self.df.merge(right=right, how=kind, on=on, left_on=left_on, right_on=right_on, suffixes=("", "_y"))

        return self._copy(dfnew)
    
    def render(self, visualization=None, **kwargs):
        return render(self, visualization=visualization, **kwargs) 

    def to_clipboard(self, name=None):
        # this is not part of Kusto, but I find it very useful
        df = self.df.copy()
        if isinstance(df, pd.DataFrame):
            df.to_clipboard(index_label=df.columns.name)
        else:
            if name is not None:
                df.name = name
            df.to_clipboard(header=True)
                
        return self
        

    
