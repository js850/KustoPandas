import pandas as pd

from .expression_parser import parse_expression_toplevel
from .methods import get_methods
from ._render import render
from .expression_parser._simple_expression import replace_temp_column_names

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

def _serialize_named_expressions(kwargs):
    if kwargs is None:
        return ""

    return ", ".join([str(k) + " = " + str(v) for k, v in kwargs.items()])

def _serialize_expressions(args, kwargs = None):
    expr = " "

    if isinstance(args, str):
        args_expr = args
    else:
        args_expr = ", ".join([str(a) for a in args])

    kwargs_expr = _serialize_named_expressions(kwargs)

    expr += args_expr

    if args_expr and kwargs_expr:
        expr += ", "
    
    expr += kwargs_expr
    return expr


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
    
    def _execute_tabular_operator(self, expression):
        parsed = parse_expression_toplevel(expression)
        return parsed.evaluate_pipe(self)

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
        expr = "project " + _serialize_expressions(cols, renamed_cols)

        return self._execute_tabular_operator(expr)

    def project_away(self, *cols):
        expr = "project-away " + _serialize_expressions(cols)
        return self._execute_tabular_operator(expr)

    def project_keep(self, *cols):
        expr = "project-keep " + _serialize_expressions(cols)
        return self._execute_tabular_operator(expr)

    def project_rename(self, *args, **kwargs):
        expr = "project-rename " + _serialize_expressions(args, kwargs)
        return self._execute_tabular_operator(expr)

    def project_reorder(self, *cols):
        expr = "project-reorder " + _serialize_expressions(cols)
        return self._execute_tabular_operator(expr)

    def summarize(self, aggregates, by=None):
        """
        w.summarize("count(), sum(A) by M, N")

        w.summarize(["count(), sum(A)", by="M, N")

        w.summarize(["count()", "sum(A)"], by=["M", "N"])

        w.summarize("count(), sum(A)")

        w.summarize(["count()", "sum(A)"])


        """
        expr = "summarize " + _serialize_expressions(aggregates)

        if by is not None:
            expr += " by " + _serialize_expressions(by)

        return self._execute_tabular_operator(expr)

    def extend(self, *args, **kwargs):
        expr = "extend " + _serialize_expressions(args, kwargs)
        return self._execute_tabular_operator(expr)
    
    def where(self, condition):
        expr = "where " + condition
        return self._execute_tabular_operator(expr)
    
    def take(self, n):
        expr = "take " + str(n)
        return self._execute_tabular_operator(expr)
    
    def limit(self, n):
        return self.take(n)
    
    def order(self, by):
        return self.sort(by)

    def sort(self, by):
        """
        sort by strlen(country) asc, price desc

        by can be a column name, or an expression built from columns e.g. (strlen(country))
            or it can be a list of such expressions
        """
        expr = "sort by " + _serialize_expressions(by)
        return self._execute_tabular_operator(expr)

    def top(self, n, by=None):
        """

        w.top(5, "A")

        w.top("5 by A")

        w.top(5, "A", asc=True)

        w.top("5 by A asc")
        """
        expr = "top " + str(n)
        if by is not None:
            expr += " by " + _serialize_expressions(by)
        return self._execute_tabular_operator(expr)
        
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
        expr = "count"
        return self._execute_tabular_operator(expr)

    def distinct(self, *args):
        expr = "distinct " + _serialize_expressions(args)
        return self._execute_tabular_operator(expr)

    def getschema(self):
        expr = "getschema"
        return self._execute_tabular_operator(expr)
