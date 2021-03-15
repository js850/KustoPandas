import pandas as pd
import re
from functools import reduce

from .expression_parser import parse_expression, parse_expression_toplevel, Assignment, Var, Method, By, Comma, flatten_comma
from .expression_parser.aggregates import create_aggregate
from .methods import get_methods
from ._render import render
from .expression_parser._input_parsing import (
    _split_if_comma, _split_by_operator, _evaluate_and_get_name, Inputs, remove_duplicates_maintain_order, _parse_inputs_with_by,
    _parse_inputs_with_by_return_simple_expression, replace_temp_column_names)



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
        df = replace_temp_column_names(df)
        w = Wrap(df)
        w.let_statements = list(self.let_statements)
        return w

    def _get_var_map(self):
        return MultiDict([self.df, get_methods()] + self.let_statements)
    
    def __str__(self):
        return str(self.df)

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
        inputs = Inputs(*args, **kwargs)

        col_map = dict()
        for newcol, oldcol in inputs.parse_as_simple_assigments():
            col_map[oldcol] = newcol
            if oldcol not in self.df.columns:
                raise KeyError("Could not find column: " + oldcol)
        
        dfnew = self.df.rename(columns=col_map).copy()

        return self._copy(dfnew)
    
    def project_reorder(self, *cols):
        inputs = Inputs(*cols)

        specified_cols = inputs.parse_as_column_name_or_pattern(self.df)
        # unspecified columns should be put at the back of the list
        new_cols = remove_duplicates_maintain_order(specified_cols + list(self.df.columns))
        dfnew = self.df[new_cols].copy()
        return self._copy(dfnew)

    def summarize(self, aggregates, by=None):
        """
        w.summarize("count(), sum(A) by M, N")

        w.summarize(["count(), sum(A)", by="M, N")

        w.summarize(["count()", "sum(A)"], by=["M", "N"])

        w.summarize("count(), sum(A)")

        w.summarize(["count()", "sum(A)"])


        """
        expr = "summarize"
        if isinstance(aggregates, str):
            expr += " " + str(aggregates)
        else:
            expr += " " + ", ".join(aggregates)
        
        if by is not None:
            if isinstance(by, str):
                expr += " by " + str(by)
            else:
              expr += " by " + ", ".join(by)

        parsed = parse_expression_toplevel(expr)

        dfnew = parsed.evaluate_top(self.df, self._get_var_map())
        return self._copy(dfnew)

    def extend(self, *args, **kwargs):
        expr = "extend "
        if args:
            expr += ", ".join([str(a) for a in args])
        
        if kwargs:
            expr += ", ".join([str(k) + " = " + str(v) for k, v in kwargs.items()])

        parsed = parse_expression_toplevel(expr)
        dfnew = parsed.evaluate_top(self.df, self._get_var_map())

        return self._copy(dfnew)
    
    def where(self, condition):
        expr = "where " + condition

        parsed = parse_expression_toplevel(expr)
        newdf = parsed.evaluate_top(self.df, self._get_var_map())

        return self._copy(newdf)
    
    def take(self, n):
        expr = "take " + str(n)
        parsed = parse_expression_toplevel(expr)
        newdf = parsed.evaluate_top(self.df, None)
        return self._copy(newdf)
    
    def limit(self, n):
        return self.take(n)
    
    def order(self, *args, **kwargs):
        return self.sort(*args, **kwargs)

    def sort(self, by, asc=False):
        """
        sort by strlen(country) asc, price desc

        by can be a column name, or an expression built from columns e.g. (strlen(country))
            or it can be a list of such expressions
        asc (if true, sort by ascending order) can be a bool
            or list of bools.  If it's a list, it must be equal in length to the list of expressions 
        """
        inputs = Inputs(by)
        parsed_inputs = inputs.parsed_inputs
        return self._sort(parsed_inputs, asc=asc)

    def _sort(self, by_parsed, asc=False):
        if isinstance(asc, bool):
            asc = [asc] * len(by_parsed)
        elif len(by_parsed) != len(asc):
            raise Exception("the length of lists by and asc must be equal")

        dfnew = self.df.copy(deep=False)

        col_names = ["__tempcol_" + str(i) for i in range(len(by_parsed))]

        var_map = self._get_var_map()
        for i, expr in enumerate(by_parsed):
            col = col_names[i]
            series = expr.evaluate(var_map)
            dfnew[col] = series
            if expr.is_asc():
                asc[i] = True
            if expr.is_desc():
                asc[i] = False
        
        dfnew = dfnew.sort_values(col_names, ascending=asc)

        for c in col_names:
            del dfnew[c]

        return self._copy(dfnew)

    def top(self, n, by=None, asc=False):
        """

        w.top(5, "A")

        w.top("5 by A")

        w.top(5, "A", asc=True)

        w.top("5 by A asc")
        """
        n_parsed, by_parsed = _parse_inputs_with_by_return_simple_expression(n, by=by)

        if not len(n_parsed) == 1:
            raise Exception("Top expects exactly one n")
        n_value = n_parsed[0].evaluate(self._get_var_map())

        if not isinstance(n_value, int):
            raise Exception("n must be an integer")

        return self._sort(by_parsed, asc=asc).take(n_value)
    
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
    
    def count(self):
        count = self.df.shape[0]

        dfnew = pd.DataFrame()
        dfnew["Count"] = [count]

        return self._copy(dfnew)
    
    def distinct(self, *args):
        if args[0] == "*":
            return self._copy(self.df.drop_duplicates())
        
        # note: the arguments to kusto distinct must be either "*" or a list of column names.
        # Here we support an arbitrary expression.  e.g. distinct("A + B")
        # It would be extra work to limit it to only column names, and supporting arbitrary expressions seems nice, so I will leave it
        inputs = Inputs(*args)

        var_map = self._get_var_map()
        dfnew = pd.DataFrame()
        for parsed in inputs.parsed_inputs:
            name = parsed.get_name()
            series = parsed.evaluate(var_map)
            dfnew[name] = series
        
        return self._copy(dfnew.drop_duplicates())
    
    def getschema(self):

        d2 = pd.DataFrame()
        d2["ColumnName"] = self.df.columns
        d2["ColumnOrdinal"] = range(len(self.df.columns))
        d2["DataType"] = list(self.df.dtypes)
        d2["ColumnType"] = list(self.df.dtypes)

        return self._copy(d2)
            
        

    
