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
        return "({0}{1})".format(self.op, self.right)

    def __repr__(self):
        return str(self)

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

    def unary_version():
        return UnaryMinus

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

class Assignment(Opp):
    op = "="
    def evaluate(self, vals):
        return {str(self.left): self.right.evaluate(vals)}

class And(Opp):
    op = "&&"
    def evaluate_internal(self, left, right, **kwargs):
        if are_all_series(left, right):
            return left & right
        return left and right 

class Or(Opp):
    op = "||"
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

all_operators = [Add, Sub, Div, Mul, Eq, NEq, Gt, Lt, Ge, Le, Assignment, And, Or, Comma, Contains, NotContains]
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

def parse_var(val):
    assert_var_name(val)
    return Var(val)

def parse_num_or_var(val):
    try:
        n = int(val)
        return Int(val)
    except:
        try:
            n = float(val)
            return Float(val)
        except:
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

def is_unary_operator(line, i):
    if line[i] == Sub:
        cnext = line[i+1]
        if isinstance(cnext, NumOrVar):
            if i == 0 or is_op(line[i-1]):
                return True
    return False


def parse_unary_operators(line):
    output = []    
    i = 0

    # matches = [i for i in range(len(line)-1) if is_unary_operator(line, i)]
    while i < len(line) - 1:
        if is_unary_operator(line, i):
            new_op = UnaryMinus(line[i+1])
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

def parse_method_args(line, matches):
    args = []
    last = 0
    for i, c in enumerate(line):
        if c == Comma:
            if i == last:
                raise Exception("commas are not separated by a value in args: " + line) 
            parsed = parse_parentheses(line[last:i], matches[last:i])
            args.append(parsed)
            last = i+1
    
    if last < len(line):
        parsed = parse_parentheses(line[last:], matches[last:])
        args.append(parsed)

    return Args(args)

def parse_parentheses(line, matches):

    parentheses = split_one_level(matches)
    
    if not parentheses:
        # fix this
        return parse_unary_operators(line)

    output = []
    last = 0
    for i, end in parentheses:
        if i > last:
            output += line[last:i]
        if parentheses_are_method_arguments(line, i):
            args = parse_method_args(line[i+1:end], matches[i+1:end])
            method_name = output.pop()
            method = Method(method_name, args)
            output.append(method)
        else:
            parsed = parse_parentheses(line[i+1:end], matches[i+1:end])
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
    return match_az.search(op.op) is not None

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
        if op_is_not_special_chars(op):
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

def parse_parts_of_line(line):
    # exploded = list(line)
    with_strings = parse_string_literals_parts(line)
    parsed = parse_rest_parts(with_strings)
    return parsed

def parse_statement(line):
    exploded = parse_parts_of_line(line)
    matches = find_matching_parentheses(exploded)
    parsed = parse_parentheses(exploded, matches)
    return parsed