import numpy as np
import re
import pandas as pd
import inspect 

from .expression_parser_types import *
from .expression_tree import build_expression_tree, MethodStack

match_internal = re.compile("[a-zA-Z_0-9]+")
match_first = re.compile("[a-zA-Z_]")

def assert_var_name(var):
    if not match_first.match(var):
        raise Exception("variable name starts with illegal character " + var)
    if not match_internal.match(var):
        raise Exception("variable name has illegal characters " + var)

def try_parse_num(val):
    parsed = try_parse_int(val)
    if parsed is not None:
        return parsed
    parsed = try_parse_float(val)
    if parsed is not None:
        return parsed

    return None

def try_parse_timespan_literal(val):
    if val[-1] in ["d", "h", "m", "s"]:
        unit = val[-1]
        num = try_parse_num(val[:-1])
        if num is not None:
            return TimespanLiteral(num, unit)
    return None

def parse_var(val):
    timespan = try_parse_timespan_literal(val)
    if timespan is not None:
        return timespan

    assert_var_name(val)
    return Var(val)

def parse_and_assert_variable(val):
    assert_var_name(val)
    return Var(val)

def try_parse_int(val):
    try:
        int(val)
        return Int(val)
    except:
        return None

def try_parse_float(val):
    try:
        float(val)
        return Float(val)
    except:
        return None
    
def get_parse_unary_expression_method(try_parse):
    def parse_unary_expression(line, method_stack):
        parsed = try_parse(line)
        if parsed is not None:
            return [parsed]
        else:
            return method_stack.evaluate_next_method(line)
    return parse_unary_expression

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

def get_method_stack():
    stack = [
        get_parse_unary_expression_method(parse_and_assert_variable),
        get_parse_unary_expression_method(try_parse_timespan_literal),
        get_parse_unary_expression_method(try_parse_float),
        get_parse_unary_expression_method(try_parse_int),
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
