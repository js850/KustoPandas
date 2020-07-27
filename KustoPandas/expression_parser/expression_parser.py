import numpy as np
import re
import pandas as pd
import inspect 

from KustoPandas.expression_parser.expression_parser_types import *
from KustoPandas.expression_parser.expression_tree import build_expression_tree, MethodStack

match_internal = re.compile("[a-zA-Z_0-9]+")
match_first = re.compile("[a-zA-Z_]")

def assert_var_name(var):
    if not match_first.match(var):
        raise Exception("variable name starts with illegal character " + var)
    if not match_internal.match(var):
        raise Exception("variable name has illegal characters " + var)

def try_tokenize_num(val):
    parsed = try_tokenize_int(val)
    if parsed is not None:
        return parsed
    parsed = try_tokenize_float(val)
    if parsed is not None:
        return parsed

    return None

def try_tokenize_timespan_literal(val):
    if val[-1] in ["d", "h", "m", "s"]:
        unit = val[-1]
        num = try_tokenize_num(val[:-1])
        if num is not None:
            return TimespanLiteral(num, unit)
    return None

def parse_var(val):
    timespan = try_tokenize_timespan_literal(val)
    if timespan is not None:
        return timespan

    assert_var_name(val)
    return Var(val)

def tokenize_and_assert_variable(val):
    # throw on failure here because it is the last in the stack
    assert_var_name(val)
    return Var(val)

def try_tokenize_int(val):
    try:
        int(val)
        return Int(val)
    except:
        return None

def try_tokenize_float(val):
    try:
        float(val)
        return Float(val)
    except:
        return None
    
def get_word_tokenizer(try_parse):
    def parse_whole_word(line, method_stack):
        parsed = try_parse(line)
        if parsed is not None:
            return [parsed]
        else:
            return method_stack.evaluate_next_method(line)
    return parse_whole_word

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

def is_unary_operator(tokens, i):
    if i >= len(tokens):
        raise Exception("can't have operator at end of line: " + str(tokens))
    if i == 0 or is_op(tokens[i-1]) or tokens[i-1] == "(":
        return True
    return False

def resolve_ambiguous_operators(tokens):
    indices = [i for i, c in enumerate(tokens) if c == AmbiguousMinus]

    for i in indices:
        c = tokens[i]
        if is_unary_operator(tokens, i):
            tokens[i] = c.unary
        else:
            tokens[i] = c.binary
    return tokens

def tokenize_line_recursively(line, parser, method_stack):
    if not line:
        return []
    for i in range(len(line)):
        tokens, skip = parser(line, i)
        if tokens is not None:
            left = method_stack.evaluate_next_method(line[:i])
            right = method_stack.rerun_current_method(line[i+skip:])
            return left + tokens + right
    
    return method_stack.evaluate_next_method(line)

def string_literal_tokenizer(line, i):
    c = line[i]
    if c == "\"" or c == "'":
        j = line.find(c, i+1)
        if j >= 0:
            val = StringLiteral(line[i+1:j])
            return [val], j + 1 - i
        else:
            raise Exception("could not find end of string literal: " + str(line))
    return None, 0

def whitespace_tokenizer(line, i):
    if line[i] == " ":
        return [], 1
    return None, 0

def parentheses_tokenizer(line, i):
    if line[i] in ("(", ")"):
        return [line[i]], 1
    return None, 0

def operator_tokenizer(line, i):
    op = get_matching_op(line, i)
    if op is not None:
        return [op], len(op.op)
    return None, 0

def get_line_tokenizer(parser):
    def line_tokenizer(line, method_stack):
        return tokenize_line_recursively(line, parser, method_stack)
    return line_tokenizer

def get_tokenization_method_stack():
    stack = [
        get_word_tokenizer(tokenize_and_assert_variable),
        get_word_tokenizer(try_tokenize_timespan_literal),
        get_word_tokenizer(try_tokenize_float),
        get_word_tokenizer(try_tokenize_int),
        get_line_tokenizer(operator_tokenizer),
        get_line_tokenizer(parentheses_tokenizer),
        get_line_tokenizer(whitespace_tokenizer),
        get_line_tokenizer(string_literal_tokenizer),
    ]
    return MethodStack(stack)

def tokenize_line(line):
    method_stack = get_tokenization_method_stack()
    parsed = method_stack.evaluate_next_method(line)
    resolved = resolve_ambiguous_operators(parsed)
    return resolved

def parse_expression(line):
    tokens = tokenize_line(line)
    parsed = build_expression_tree(tokens)
    return parsed
