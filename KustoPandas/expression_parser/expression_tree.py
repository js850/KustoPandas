
from KustoPandas.expression_parser.expression_parser_types import *

class MethodStack:
    def __init__(self, stack, current_method=None):
        self.stack = stack
        self.current_method = current_method

    def copy(self):
        return MethodStack(list(self.stack), current_method=self.current_method)
    
    def pop(self):
        method = self.stack.pop()
        self.current_method = method
        return method

    def evaluate_next_method(self, parts):
        if len(parts) == 0:
            return []
        if not self.stack:
            raise Exception("method stack empty(?)")
        new_method_stack = self.copy()
        method = new_method_stack.pop()
        return method(parts, new_method_stack)
    
    def rerun_current_method(self, parts):
        return self.current_method(parts, self.copy())

def last_method(line, method_stack):
    if method_stack.stack:
        raise Exception("method stack is not empty")
    if len(line) == 0:
        raise Exception("parsing math but line is length 0")
    if len(line) == 1:
        if not isinstance(line[0], Expression):
            raise Exception("expected Expression: " + str(line[0]))
        return line[0]
    raise Exception("at end of last method, but line is not empty: " + str(line))

def parse_operators_stack(operators, line, method_stack, right_to_left=False):
    indices = range(len(line))
    if right_to_left:
        indices = reversed(indices)

    for i in indices:
        for operator in operators:
            if line[i] == operator:
                if right_to_left:
                    left = method_stack.rerun_current_method(line[:i])
                    right = method_stack.evaluate_next_method(line[i + 1:])
                else:
                    left = method_stack.evaluate_next_method(line[:i])
                    right = method_stack.rerun_current_method(line[i + 1:])
                return operator(left, right)
    return method_stack.evaluate_next_method(line)

def get_parse_operators_method(operators, right_to_left=False):
    def parse_op(line, method_stack):
        return parse_operators_stack(operators, line, method_stack, right_to_left=right_to_left)
    return parse_op

def parse_unary_operators(line, method_stack):
    output = []    
    i = 0

    # matches = [i for i in range(len(line)-1) if is_unary_operator(line, i)]
    while i < len(line) - 1:
        if line[i] in (UnaryMinus, UnaryNot):
            new_op = line[i](line[i+1])
            output.append(new_op)
            i += 2
        else:
            output.append(line[i])
            i += 1
    
    if i < len(line):
        output.append(line[i])

    return method_stack.evaluate_next_method(output)

def split_one_level(matches):
    groups = []
    i = 0
    while i < len(matches):
        offset = matches[i]
        #print(i, offset)
        if offset > 0:
            groups.append((i, i + offset))
            i += offset + 1
        else:
            i += 1
    return groups    

def parentheses_are_method_arguments(line, i):
    if i == 0:
        return False
    return isinstance(line[i-1], Var)

def flatten_comma(value):
    if isinstance(value.right, Comma):
        return [value.left] + flatten_comma(value.right)
    return [value.left, value.right]

def convert_to_method_args(parsed):
    if parsed is None:
        return Args([])
    if isinstance(parsed, Comma):
        args = flatten_comma(parsed)
        return Args(args)

    return Args([parsed])

def find_matching_parentheses(line, left="(", right=")"):
    matches = np.zeros(len(line), dtype=np.int)
    stack = []
    for i, c in enumerate(line):
        #print(c)
        if c == left:
            stack.append(i)
        elif c == right:
            if len(stack) == 0:
                raise Exception("found unmatched closing " + right + " at column " + i)
            previous = stack.pop()
            matches[previous] = i - previous
            matches[i] = previous - i
    return matches

def parse_parentheses(line, method_stack, matches=None):
    if len(line) == 0:
        return None

    if matches is None:
        matches = find_matching_parentheses(line)

    parentheses = split_one_level(matches)
    
    if not parentheses:
        # fix this
        return method_stack.evaluate_next_method(line)

    output = []
    last = 0
    for i, end in parentheses:
        if i > last:
            output += line[last:i]
        parsed = parse_parentheses(line[i+1:end], method_stack, matches=matches[i+1:end])
        if parentheses_are_method_arguments(line, i):
            args = convert_to_method_args(parsed)
            method_name = output.pop()
            method = Method(method_name, args)
            output.append(method)
        elif isinstance(parsed, Comma):
            list_instance = flatten_comma(parsed)
            list_expression = ListExpression(list_instance)
            output.append(list_expression)
        else:
            output.append(parsed)
        last = end + 1
    
    tail = line[last:]
    output += tail
    
    #print("output", output)
    return method_stack.evaluate_next_method(output)

def parse_square_brackets(line, method_stack, matches=None):
    if len(line) == 0:
        return None

    if matches is None:
        matches = find_matching_parentheses(line, left="[", right="]")

    parentheses = split_one_level(matches)
    
    if not parentheses:
        # fix this
        return method_stack.evaluate_next_method(line)

    output = []
    last = 0
    for i, end in parentheses:
        if i > last:
            output += line[last:i]
        parsed = parse_square_brackets(line[i+1:end], method_stack, matches=matches[i+1:end])

        arg_name = output.pop()
        brackets = SquareBrackets(arg_name, parsed)
        output.append(brackets)

        last = end + 1
    
    tail = line[last:]
    output += tail
    
    #print("output", output)
    return method_stack.evaluate_next_method(output)

def get_expression_tree_method_stack():
    return MethodStack([
        last_method,
        get_parse_operators_method([
            Contains, NotContains, ContainsCs, NotContainsCs,
            StartsWith, NotStartsWith, StartsWithCs, NotStartsWithCs,
            In, NotIn, InCis, NotInCis,
            Has, NotHas, HasCs, NotHasCs]), # I'm just guessing what priority these should have
        get_parse_operators_method([Mul, Div]),
        get_parse_operators_method([Add, Sub]),
        get_parse_operators_method([Gt, Lt, Ge, Le]),
        get_parse_operators_method([Eq, NEq]),
        get_parse_operators_method([And]),
        get_parse_operators_method([Or]),
        get_parse_operators_method([Assignment], right_to_left=True),
        get_parse_operators_method([Comma], right_to_left=False),
        get_parse_operators_method([Between]),
        get_parse_operators_method([DotDot]),
        get_parse_operators_method([By]),
        parse_unary_operators,
        parse_square_brackets,
        parse_parentheses,
    ])

def build_expression_tree(parts):
    method_stack = get_expression_tree_method_stack()
    parsed = method_stack.evaluate_next_method(parts)
    return parsed
