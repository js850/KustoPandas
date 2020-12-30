from functools import reduce

from .expression_parser import parse_expression, Assignment, Var, Method, By, Comma, flatten_comma

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
