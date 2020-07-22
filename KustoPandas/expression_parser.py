import numpy as np
import re
import pandas as pd
import inspect 

def are_all_series(*args):
    return all((isinstance(a, pd.Series) for a in args))

class Expression:
    pass

class UnaryOpp(Expression):
    op = ""
    def __init__(self, right):
        self.right = right
    
    def __str__(self):
        if op_is_not_special_chars(self.op):
            space = " "
        else:
            space = ""
        return "({0}{1}{2})".format(self.op, space, self.right)

    def __repr__(self):
        return str(self)

    def evaluate_internal(self, right):
        raise NotImplementedError()

    def evaluate(self, vals):
        right = self.right.evaluate(vals)
        return self.evaluate_internal(right)


class Opp(Expression):
    op = ""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def __str__(self):
        return "({0} {1} {2})".format(self.left, self.op, self.right)

    def __repr__(self):
        return str(self)

    def evaluate_internal(self, left, right):
        raise NotImplementedError()

    def evaluate(self, vals):
        left = self.left.evaluate(vals)
        right = self.right.evaluate(vals)
        return self.evaluate_internal(left, right)

class Add(Opp):
    op = "+"
    def evaluate_internal(self, left, right, **kwargs):
        return left + right

class Sub(Opp):
    op = "-"
    def evaluate_internal(self, left, right, **kwargs):
        return left - right

class UnaryMinus(UnaryOpp):
    op = "-"
    def evaluate_internal(self, right, **kwargs):
        return -right

class Mul(Opp):
    op = "*"
    def evaluate_internal(self, left, right, **kwargs):
        return left * right

class Div(Opp):
    op = "/"
    def evaluate_internal(self, left, right, **kwargs):
        return left / right

class Eq(Opp):
    op = "=="
    def evaluate_internal(self, left, right, **kwargs):
        return left == right

class NEq(Opp):
    op = "!="
    def evaluate_internal(self, left, right, **kwargs):
        return left != right

class Gt(Opp):
    op = ">"
    def evaluate_internal(self, left, right, **kwargs):
        return left > right

class Lt(Opp):
    op = "<"
    def evaluate_internal(self, left, right, **kwargs):
        return left < right

class Ge(Opp):
    op = ">="
    def evaluate_internal(self, left, right, **kwargs):
        return left >= right

class Le(Opp):
    op = "<="
    def evaluate_internal(self, left, right, **kwargs):
        return left <= right

class UnaryNot(UnaryOpp):
    # this doesn't actually exist in kusto.  but it seems useful, so why not add it?
    op = "not"
    def evaluate_internal(self, right, **kwargs):
        if are_all_series(right):
            return ~right
        return not right

class Assignment(Opp):
    op = "="
    def evaluate(self, vals):
        return {str(self.left): self.right.evaluate(vals)}

class And(Opp):
    op = "and"
    def evaluate_internal(self, left, right, **kwargs):
        if are_all_series(left, right):
            return left & right
        return left and right 

class Or(Opp):
    op = "or"
    def evaluate_internal(self, left, right, **kwargs):
        if are_all_series(left, right):
            return left | right
        return left or right 

class Contains(Opp):
    op = "contains"
    def evaluate_internal(self, left, right, **kwargs):
        if are_all_series(left):
            return left.str.contains(right, case=False)
        return right.lower() in left.lower() 

class NotContains(Opp):
    op = "!contains"
    def evaluate_internal(self, left, right, **kwargs):
        if are_all_series(left):
            return ~left.str.contains(right, case=False)
        return right.lower() not in left.lower()     

class Comma(Opp):
    op = ","
    def evaluate(self, vals):
        raise NotImplementedError("Comma does not have an implementation")

class AmbiguousMinus(Opp):
    # - can be either unary or binary op
    op = "-"
    unary = UnaryMinus
    binary = Sub

all_operators = [Add, AmbiguousMinus, Div, Mul, Eq, NEq, Gt, Lt, Ge, Le,
                 UnaryNot, Assignment,
                 And, Or, Comma, Contains, NotContains]
all_operators_sorted = sorted(all_operators, key=lambda o: len(o.op), reverse=True)

class NumOrVar(Expression):
    pass

class Int(NumOrVar):
    def __init__(self, value):
        self.value = value.strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Int({})".format(self.value)
    def evaluate(self, vals):
        return int(self.value)
    
class Float(NumOrVar):
    def __init__(self, value):
        self.value = value.strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Float({})".format(self.value)
    def evaluate(self, vals):
        return float(self.value)

class Var(NumOrVar):
    def __init__(self, value):
        self.value = value.strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Var({})".format(self.value)
    def evaluate(self, vals):
        return vals[self.value]

class StringLiteral(NumOrVar):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "\"" + self.value + "\""
    def __repr__(self):
        return "StringLiteral({})".format(self.value)
    def evaluate(self, vals):
        return self.value

class Args:
    def __init__(self, args):
        self.args = args
    def __str__(self):
        return "(" + ", ".join((str(a) for a in self.args)) + ")"
    def __repr__(self):
        return str(self)
    def evaluate(self, vals):
        return [a.evaluate(vals) for a in self.args]


class Method(Expression):
    def __init__(self, name, args):
        self.name = name
        self.args = args
    def __str__(self):
        return str(self.name) + str(self.args)
    def __repr__(self):
        return str(self)
    def evaluate(self, vals):
        method = self.name.evaluate(vals)
        args = self.args.evaluate(vals)
        return method(*args)

class TimespanLiteral(Expression):
    # e.g. 4d resolves to timespan 4 days
    def __init__(self, count, unit):
        self.count = count
        self.unit = unit
    def __str__(self):
        return "{0}{1}".format(str(self.count), self.unit)
    def __repr__(self):
        return str(self) #"DaysLiteral({0})".format(self.value)
    def evaluate(self, vals):
        return pd.Timedelta(self.count.evaluate(None), unit=self.unit)

class ListExpression(Expression):
    def __init__(self, items):
        self.items = items
    def __str__(self):
        return "(" + ", ".join((str(a) for a in self.items)) + ")"
    def __repr__(self):
        return str(self)
    def evaluate(self, vals):
        return [a.evaluate(vals) for a in self.items]

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
match_az = re.compile("[a-zA-Z]")

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
    parsed = parse_num(val)
    if parsed is not None:
        return parsed
    return parse_var(val)

def starts_with(array, prefix):
    for i in range(len(prefix)):
        if i >= len(array):
            return False
        if array[i] != prefix[i]:
            return False
    return True

def parse_operator(operators, line, right_to_left=False):
    indices = range(len(line))
    if right_to_left:
        indices = reversed(indices)

    for i in indices:
        for operator in operators:
            if line[i] == operator:
                # if i == 0:
                #     right = parse_math(line[i + 1:])
                #     unary = operator.get_unary_version()
                #     return unary(right)
                # else:
                left = parse_math(line[:i])
                right = parse_math(line[i + 1:])
                return operator(left, right)

def parse_method(line):
    if len(line) != 2:
        raise Exception("Trying to parse method but got too many items: " + str(line))

    if not isinstance(line[0], Var):
        raise Exception("parse_method: first element is not Var: " + str(line))
    if not isinstance(line[1], Args):
        raise Exception("parse_method: second element is not Args: " + str(line))

    return Method(line[0], line[1])

def parse_math(line):
    if len(line) == 0:
        raise Exception("parsing math but line is length 0")
    if len(line) == 1:
        if not isinstance(line[0], Expression):
            raise Exception("expected Expression: " + str(line[0]))
        return line[0]
    
    p = parse_operator([Comma], line, right_to_left=False)
    if p is not None:
        return p

    p = parse_operator([Assignment], line, right_to_left=True)
    if p is not None:
        return p

    p = parse_operator([Or], line)
    if p is not None:
        return p

    p = parse_operator([And], line)
    if p is not None:
        return p

    p = parse_operator([Eq, NEq], line)
    if p is not None:
        return p

    p = parse_operator([Gt, Lt, Ge, Le], line)
    if p is not None:
        return p

    p = parse_operator([Add, Sub], line)
    if p is not None:
        return p

    p = parse_operator([Mul, Div], line)
    if p is not None:
        return p

    # I'm just guessing what priority these should have
    p = parse_operator([Contains, NotContains], line)
    if p is not None:
        return p

    raise Exception("could not parse expression: " + str(line))

def parse_unary_operators(line):
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

    return parse_math(output)


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

def isempty(line):
    for c in line:
        if c != " ":
            return False
    return True

def parentheses_are_method_arguments(line, i):
    if i == 0:
        return False
    return isinstance(line[i-1], Var)

def unroll_comma(value):
    if isinstance(value.right, Comma):
        return [value.left] + unroll_comma(value.right)
    return [value.left, value.right]

def convert_to_method_args(parsed):
    if parsed is None:
        return Args([])
    if isinstance(parsed, Comma):
        args = unroll_comma(parsed)
        return Args(args)

    return Args([parsed])

def parse_parentheses(line, matches):
    if len(line) == 0:
        return None

    parentheses = split_one_level(matches)
    
    if not parentheses:
        # fix this
        return parse_unary_operators(line)

    output = []
    last = 0
    for i, end in parentheses:
        if i > last:
            output += line[last:i]
        parsed = parse_parentheses(line[i+1:end], matches[i+1:end])
        if parentheses_are_method_arguments(line, i):
            args = convert_to_method_args(parsed)
            method_name = output.pop()
            method = Method(method_name, args)
            output.append(method)
        elif isinstance(parsed, Comma):
            list_instance = unroll_comma(parsed)
            list_expression = ListExpression(list_instance)
            output.append(list_expression)
        else:
            output.append(parsed)
        last = end + 1
    
    tail = line[last:]
    if not isempty(tail):
        output += tail
    
    #print("output", output)
    return parse_unary_operators(output)

def op_matches_start(line, op):
    for i in range(len(op.op)):
        if i >= len(line):
            return False
        if op.op[i] != line[i]:
            return False
    return True

def op_is_not_special_chars(op):
    # e.g. contains, or, and
    return match_az.search(op) is not None

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

# class OpenParens:
#     pass

# class CloseParens:
#     pass

def parse_line_part(line):
    if not line:
        return []
    for i, c in enumerate(line):
        if c in [" "]:
            left = parse_line_part(line[:i])
            right = parse_line_part(line[i+1:])
            return left + right

        if c == "(" or c == ")":
            left = parse_line_part(line[:i])
            right = parse_line_part(line[i+1:])
            return left + [c] + right

    for i, c in enumerate(line):
        op = get_matching_op(line, i)
        if op is not None:
            left = parse_line_part(line[:i])
            right = parse_line_part(line[i+len(op.op):])
            return left + [op] + right
        
    return [parse_num_or_var(line)]


def parse_rest_parts(parts):
    if not parts:
        return []

    for i, line in enumerate(parts):
        if isinstance(line, str):
            left = parts[:i]
            center = parse_line_part(line)
            right = parse_rest_parts(parts[i+1:])
            return left + center + right 
    return parts

def parse_string_literals_parts(line):
    matching = None
    last = 0
    for i, c in enumerate(line):
        if matching is None:
            if c == "\"" or c == "'":
                matching = c
                last = i
        else:
            if c == matching:
                left = line[:last]
                val = StringLiteral("".join(line[last+1:i]))
                right = parse_string_literals_parts(line[i+1:])
                return [left] + [val] + right
    
    return [line]

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

def parse_parts_of_line(line):
    # exploded = list(line)
    with_strings = parse_string_literals_parts(line)
    parsed = parse_rest_parts(with_strings)
    resolved = resolve_ambiguous_operators(parsed)
    return resolved

def parse_statement(line):
    exploded = parse_parts_of_line(line)
    matches = find_matching_parentheses(exploded)
    parsed = parse_parentheses(exploded, matches)
    return parsed