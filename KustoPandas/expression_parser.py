import numpy as np
import re
import pandas as pd
import inspect 

from .expression_parser_types import *

def find_matching_parentheses(line):
    matches = np.zeros(len(line), dtype=np.int)
    stack = []
    for i, c in enumerate(line):
        #print(c)
        if c == "(":
            stack.append(i)
        elif c == ")":
            if len(stack) == 0:
                raise Exception("found unmatched closing parenthesis at column ", i)
            previous = stack.pop()
            matches[previous] = i - previous
            matches[i] = previous - i
    return matches

match_internal = re.compile("[a-zA-Z_0-9]+")
match_first = re.compile("[a-zA-Z_]")

def assert_var_name(var):
    if not match_first.match(var):
        raise Exception("variable name starts with illegal character " + var)
    if not match_internal.match(var):
        raise Exception("variable name has illegal characters " + var)

def parse_timespan_literal(val):
    if val[-1] in ["d", "h", "m", "s"]:
        unit = val[-1]
        num = parse_num(val[:-1])
        if num is not None:
            return TimespanLiteral(num, unit)
    return None

def parse_var(val):
    timespan = parse_timespan_literal(val)
    if timespan is not None:
        return timespan

    assert_var_name(val)
    return Var(val)

def parse_num(val):
    try:
        int(val)
        return Int(val)
    except:
        pass
    try:
        float(val)
        return Float(val)
    except:
        pass
    
    return None
    
def parse_num_or_var(val):
    if len(val) == 0:
        raise Exception("parsing variable or literal but is emtpy")
    parsed = parse_num(val)
    if parsed is not None:
        return parsed
    return parse_var(val)

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

def get_expression_tree_method_stack():
    return MethodStack([
        last_method,
        get_parse_operators_method([Contains, NotContains, In, NotIn]), # I'm just guessing what priority these should have
        get_parse_operators_method([Mul, Div]),
        get_parse_operators_method([Add, Sub]),
        get_parse_operators_method([Gt, Lt, Ge, Le]),
        get_parse_operators_method([Eq, NEq]),
        get_parse_operators_method([And]),
        get_parse_operators_method([Or]),
        get_parse_operators_method([Assignment], right_to_left=True),
        get_parse_operators_method([Comma], right_to_left=False),
        parse_unary_operators,
        parse_parentheses,
    ])

def build_expression_tree(parts):
    method_stack = get_expression_tree_method_stack()
    parsed = method_stack.evaluate_next_method(parts)
    return parsed

def op_matches_start(line, op):
    for i in range(len(op.op)):
        if i >= len(line):
            return False
        if op.op[i] != line[i]:
            return False
    return True

def is_whole_word_match(word, line, i):
    # we already know it matches.  just verify the match is on whole word
    if not (i == 0 or line[i-1] == " "):
        return False
    end = i + len(word)
    if not (end >= len(line) or line[end] == " "):
        return False
    return True

def get_matching_op(line, i):
    matched_ops = [o for o in all_operators_sorted if op_matches_start(line[i:], o)]
    for op in matched_ops:
        if op_is_not_special_chars(op.op):
            # have to avoid matching op "and" on "rand" or "android"
            # assert that it has to have whitespace before and after
            if is_whole_word_match(op.op, line, i):
                return op
        else:
            return op
    return None

def is_op(c):
    return inspect.isclass(c) and issubclass(c, Opp)

def parse_string_literals_parts(line, method_stack):
    matching = None
    last = 0
    for i, c in enumerate(line):
        if matching is None:
            if c == "\"" or c == "'":
                matching = c
                last = i
        else:
            if c == matching:
                left = method_stack.evaluate_next_method(line[:last])
                val = StringLiteral("".join(line[last+1:i]))
                right = method_stack.rerun_current_method(line[i+1:])
                return left + [val] + right
    
    return method_stack.evaluate_next_method(line)

def is_unary_operator(parts, i):
    if i >= len(parts):
        raise Exception("can't have operator at end of line: " + str(parts))
    if i == 0 or is_op(parts[i-1]) or parts[i-1] == "(":
        return True
    return False

def resolve_ambiguous_operators(parts):
    indices = [i for i, c in enumerate(parts) if c == AmbiguousMinus]

    for i in indices:
        c = parts[i]
        if is_unary_operator(parts, i):
            parts[i] = c.unary
        else:
            parts[i] = c.binary
    return parts

def parse_characters_part(line, chars, keep_character, method_stack):
    if not line:
        return []
    for i, c in enumerate(line):
        if c in chars:
            left = method_stack.evaluate_next_method(line[:i])
            right = method_stack.rerun_current_method(line[i+1:])
            if keep_character:
                return left + [c] + right
            else:
                return left + right
    
    return method_stack.evaluate_next_method(line)

def parse_chars_whitespace(line, method_stack):
    return parse_characters_part(line, [" "], False, method_stack)

def parse_chars_parentheses(line, method_stack):
    return parse_characters_part(line, ["(", ")"], True, method_stack)

def identify_operators(line, method_stack):
    if not line:
        return []

    for i, c in enumerate(line):
        op = get_matching_op(line, i)
        if op is not None:
            left = method_stack.evaluate_next_method(line[:i])
            right = method_stack.rerun_current_method(line[i+len(op.op):])
            # right = identify_operators(line[i+len(op.op):], method_stack)
            return left + [op] + right
    return method_stack.evaluate_next_method(line)

def parse_chars_num_or_var(line, method_stack):
    if method_stack.stack:
        raise Exception("method_stack should be empty")
    return [parse_num_or_var(line)]

class MethodStack:
    def __init__(self, stack, current_method=None):
        self.stack = stack
        self.current_method = current_method

    def copy(self):
        return MethodStack(list(self.stack), current_method=self.current_method)

    def evaluate_next_method(self, parts):
        if len(parts) == 0:
            return []
        if not self.stack:
            raise Exception("method stack empty(?)")
        method = self.stack[-1]
        new_method_stack = MethodStack(list(self.stack[:-1]), current_method=method)
        return method(parts, new_method_stack)
    
    def rerun_current_method(self, parts):
        return self.current_method(parts, self.copy())

def get_method_stack():
    stack = [
        parse_chars_num_or_var,
        identify_operators,
        parse_chars_parentheses,
        parse_chars_whitespace,
        parse_string_literals_parts,
    ]
    return MethodStack(stack)

def parse_parts_of_line(line):
    method_stack = get_method_stack()
    parsed = method_stack.evaluate_next_method(line)
    resolved = resolve_ambiguous_operators(parsed)
    return resolved

def parse_statement(line):
    parts = parse_parts_of_line(line)
    parsed = build_expression_tree(parts)
    return parsed
