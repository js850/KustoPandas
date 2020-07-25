import pandas as pd
import re
from functools import reduce

from .expression_parser import parse_expression, Assignment, Var, Method, By, Comma, flatten_comma
from .aggregates import create_aggregate
from .methods import get_methods
from ._render import render

class SimpleExpression:
    def __init__(self, parsed):
        """ parsed can be an assignment or a simple expression
        A = B
        A = method(B)
        A = B + C
        method(B) => default name method_B
        B + C => default name 
        """
        self.parsed = parsed

        self.assignment_name = None
        if isinstance(parsed, Assignment):
            self.assignment_name = str(parsed.left)
            self.expression = parsed.right
        else:
            self.expression = parsed
    
    def get_name(self):
        if self.assignment_name is not None:
            return self.assignment_name
        return _get_default_name(self.parsed)

    def evaluate(self, variable_map):
        return self.expression.evaluate(variable_map)
    
    def set_name(self, name):
        self.assignment_name = name

def ensure_column_name_unique(df, col):
    while col in df.columns:
        col = col + "_"
    return col

def _get_method_default_name(method):
    name = str(method.name)
    suffix = ""
    if len(method.args.args) > 0:
        arg1 = method.args.args[0]
        if isinstance(arg1, Var):
            suffix = str(arg1)
    return "{0}_{1}".format(name, suffix)

def _get_default_name(parsed):
    if isinstance(parsed, Var):
        return str(parsed)
    if isinstance(parsed, Method):
        return _get_method_default_name(parsed)
    return "__tempcolumnname_"

def _evaluate_and_get_name(parsed, variable_map):
    result = parsed.evaluate(variable_map)
    if isinstance(parsed, Assignment):
        for name, value in result.items():
            return name, value
    if isinstance(parsed, Var):
        return str(parsed), result
    if isinstance(parsed, Method):
        return _get_method_default_name(parsed), result
    return "__tempcolumnname_", result

def _split_if_comma(parsed):
    if isinstance(parsed, Comma):
        return flatten_comma(parsed)
    else:
        return [parsed]

def _split_by_operator(parsed):
    left = _split_if_comma(parsed.left)
    right = _split_if_comma(parsed.right)
    return left, right

def _parse_input_expression_or_list_of_expressions(input):
    if isinstance(input, str):
        parsed = parse_expression(input)
        return [SimpleExpression(e) for e in _split_if_comma(parsed)]
    return [SimpleExpression(parse_expression(i)) for i in input]

def _parse_input_expression_args(args):
    lists = [_parse_input_expression_or_list_of_expressions(a) for a in args]
    return reduce(lambda a, b: a + b, lists) 

def _parse_input_expression_kwargs(kwargs):
    output = []
    for name, text in kwargs.items():
        parsed = parse_expression(text)
        expression = SimpleExpression(parsed)
        expression.set_name(name)
        output.append(expression)
    return output

def _parse_input_expression_args_kwargs(args, kwargs):
    return _parse_input_expression_args(args) + _parse_input_expression_kwargs(kwargs)

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
        parsed_inputs = _parse_input_expression_args_kwargs(cols, renamed_cols)

        dfnew = pd.DataFrame()
        var_map = self._get_var_map()

        for parsed in parsed_inputs:
            result = parsed.evaluate(var_map)
            dfnew[parsed.get_name()] = result
        
        return self._copy(dfnew)

    def project_away(self, *cols):
        parsed_inputs = _parse_input_expression_args(cols)
        dfnew = self.df.copy()
        for parsed in parsed_inputs:
            del dfnew[parsed.get_name()]

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
        
        args = [create_aggregate(a) for a in aggregates]
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
    
    def extend(self, *args, **kwargs):
        parsed_inputs = _parse_input_expression_args_kwargs(args, kwargs)

        dfnew = self.df.copy(deep=False)
        var_map = self._get_var_map()
        for parsed in parsed_inputs:
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
        

    
