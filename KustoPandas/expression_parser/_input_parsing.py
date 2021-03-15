import uuid
from functools import reduce
import fnmatch
from collections import OrderedDict

# from .arpeggio_parser import parse_expression
from .expression_parser_types import Assignment, Var, Method, By, Comma, Mul, Asc, Desc
from .expression_tree import flatten_comma

from ._simple_expression import SimpleExpression, _get_method_default_name, _generate_temp_column_name, replace_temp_column_names, _evaluate_and_get_name

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


def _parse_inputs_with_by(aggregates, by=None):
    if isinstance(aggregates, str):
        parsed = parse_expression(aggregates)
        if isinstance(parsed, By):
            aggs, by_parsed = _split_by_operator(parsed)
            return aggs, by_parsed
        aggregates_parsed = _split_if_comma(parsed)
    elif isinstance(aggregates, int): # to support w.top(2, "A")
        # there is probably a better way then to convert it to string and back again
        aggregates_parsed = [parse_expression(str(aggregates))]
    else:
        aggregates_parsed = [parse_expression(a) for a in aggregates]

    if isinstance(by, str):
        parsed = parse_expression(by)
        by_parsed = _split_if_comma(parsed)
    elif by is None:
        by_parsed = []
    else:
        by_parsed = [parse_expression(c) for c in by]
    
    return aggregates_parsed, by_parsed

def _wrap_with_simple_expression(expressions):
    return [SimpleExpression(e) for e in expressions]

def _parse_inputs_with_by_return_simple_expression(aggregates, by=None):
    aggregates_parsed, by_parsed = _parse_inputs_with_by(aggregates, by=by)
    return _wrap_with_simple_expression(aggregates_parsed), _wrap_with_simple_expression(by_parsed)
