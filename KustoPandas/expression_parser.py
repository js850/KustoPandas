import numpy as np
import re

class Expression:
    pass

class Opp(Expression):
    op = ""
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def __str__(self):
        return "({0} {1} {2})".format(self.left, self.op, self.right)
    def __repr__(self):
        return str(self)

        

class Add(Opp):
    op = "+"
    def evaluate(self, vals):
        return self.left.evaluate(vals) + self.right.evaluate(vals)

class Sub(Opp):
    op = "-"
    def evaluate(self, vals):
        return self.left.evaluate(vals) - self.right.evaluate(vals)

class Mul(Opp):
    op = "*"
    def evaluate(self, vals):
        return self.left.evaluate(vals) * self.right.evaluate(vals)

class Div(Opp):
    op = "/"
    def evaluate(self, vals):
        return self.left.evaluate(vals) / self.right.evaluate(vals)

class Eq(Opp):
    op = "=="
    def evaluate(self, vals):
        return self.left.evaluate(vals) == self.right.evaluate(vals)

class NEq(Opp):
    op = "!="
    def evaluate(self, vals):
        return self.left.evaluate(vals) != self.right.evaluate(vals)

class Gt(Opp):
    op = ">"
    def evaluate(self, vals):
        return self.left.evaluate(vals) > self.right.evaluate(vals)

class Lt(Opp):
    op = "<"
    def evaluate(self, vals):
        return self.left.evaluate(vals) < self.right.evaluate(vals)
class Ge(Opp):
    op = ">="
    def evaluate(self, vals):
        return self.left.evaluate(vals) >= self.right.evaluate(vals)
class Le(Opp):
    op = "<="
    def evaluate(self, vals):
        return self.left.evaluate(vals) <= self.right.evaluate(vals)

class Assignment(Opp):
    op = "="
    def evaluate(self, vals):
        return {str(self.left): self.right.evaluate(vals)}

class And(Opp):
    op = "&&"
    def evaluate(self, vals):
        return self.left.evaluate(vals) and self.right.evaluate(vals)

class Or(Opp):
    op = "||"
    def evaluate(self, vals):
        return self.left.evaluate(vals) or self.right.evaluate(vals)

class Comma(Opp):
    op = ","
    def evaluate(self, vals):
        return self.left.evaluate(vals) or self.right.evaluate(vals)

all_operators = [Add, Sub, Div, Mul, Eq, NEq, Gt, Lt, Ge, Le, Assignment, And, Or, Comma]
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

    raise Exception("could not parse expression: " + str(line))

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
        return parse_math(line)

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
    return parse_math(output)

def op_matches_start(line, op):
    for i in range(len(op.op)):
        if i >= len(line):
            return False
        if op.op[i] != line[i]:
            return False
    return True

def get_matching_op(line):
    matched_ops = [o for o in all_operators_sorted if op_matches_start(line, o)]
    if matched_ops:
        return matched_ops[0]
    return None

def parse_rest(line):
    if not line:
        return []

    for i, c in enumerate(line):
        if c == " ":
            left = parse_rest(line[:i])
            right = parse_rest(line[i+1:])
            return left + right
        
        op = get_matching_op(line[i:])
        if op is not None:
            left = parse_rest(line[:i])
            right = parse_rest(line[i+len(op.op):])
            return left + [op] + right
        
        if c == "(" or c == ")":
            left = parse_rest(line[:i])
            right = parse_rest(line[i+1:])
            return left + [c] + right

    return [parse_num_or_var("".join(line))]

def parse_parts_of_line(line):
    exploded = list(line)
    parsed = parse_rest(exploded)
    return parsed

def parse_statement(line):
    exploded = parse_parts_of_line(line)
    matches = find_matching_parentheses(exploded)
    parsed = parse_parentheses(exploded, matches)
    return parsed