from functools import reduce
import fnmatch
from collections import OrderedDict

from .expression_parser import parse_expression, Assignment, Var, Method, By, Comma, flatten_comma, Mul, Asc, Desc

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
    
    def is_asc(self):
        return isinstance(self.expression, Asc)

    def is_desc(self):
        return isinstance(self.expression, Desc)
    
    def __str__(self):
        return str(self.parsed)

class Inputs:
    def __init__(self, *args, **kwargs):
        self.parsed_inputs = _parse_input_expression_args_kwargs(args, kwargs)
    
    def parse_as_column_name_or_pattern(self, df):
        column_names = []
        for parsed in self.parsed_inputs:
            column_names += _parse_column_name_or_pattern(parsed, df)
        
        column_names = remove_duplicates_maintain_order(column_names)
        
        return column_names
    
    def parse_as_simple_assigments(self):
        result = []
        for parsed in self.parsed_inputs:
            if parsed.assignment_name is None:
                raise Exception("Expected a simple assignment: " + str(parsed))
            
            if not isinstance(parsed.expression, Var):
                raise Exception("Expected a simple assignment: " + str(parsed))
            
            result.append((parsed.assignment_name, str(parsed.expression)))
        
        return result

def remove_duplicates_maintain_order(list_with_duplicates):
    return list(OrderedDict.fromkeys(list_with_duplicates))

def _flatten_column_name_or_pattern(value):
    # Wildcards are parsed as multiplication because there is no way to distinguish multiplication vs wildcard
    # without knowing the context.  This is a bit hacky, but it seems to work.
    if isinstance(value, Mul):
        return _flatten_column_name_or_pattern(value.left) + "*" + _flatten_column_name_or_pattern(value.right)
    if isinstance(value, Var):
        return str(value)
    return ""

def _parse_column_name_or_pattern(parsed: SimpleExpression, df):
    if parsed.assignment_name is not None:
        # assignments are not allowed if column patterns are allowed
        raise Exception("expected only column name or pattern: " + str(parsed.parsed))

    pattern = _flatten_column_name_or_pattern(parsed.expression)

    matching_columns = [c for c in df.columns if fnmatch.fnmatchcase(c, pattern)]

    if len(matching_columns) == 0:
        raise KeyError("Could not find a collumn which matches: " + pattern)

    return matching_columns
    

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


