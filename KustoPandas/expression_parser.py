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

all_operators = [Add, Sub, Div, Mul, Eq, NEq, Gt, Lt, Ge, Le, Assignment]

class Pure:
    def __init__(self, value):
        self.value = "".join(value).strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Pure({})".format(self.value)

class Partial:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value.strip()
    def __repr__(self):
        return "Partial({})".format(self.value)

class Int:
    def __init__(self, value):
        self.value = value.strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Int({})".format(self.value)
    def evaluate(self, vals):
        return int(self.value)
    
class Float:
    def __init__(self, value):
        self.value = value.strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Float({})".format(self.value)
    def evaluate(self, vals):
        return float(self.value)


class Var:
    def __init__(self, value):
        self.value = value.strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Var({})".format(self.value)
    def evaluate(self, vals):
        return vals[self.value]


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



def explode(line):
    # if isinstance(line, str):
    #     return list(line)
    output = []
    for val in line:
        if isinstance(val, Partial):
            output += list(val.value)
        else:
            output.append(val)
    return output

match_internal = re.compile("[a-zA-Z_0-9]+")
match_first = re.compile("[a-zA-Z_]")

def assert_var_name(var):
    if not match_first.match(var):
        raise Exception("variable name starts with illegal character " + var)
    if not match_internal.match(var):
        raise Exception("variable name has illegal characters " + var)

def parse_num_or_var(val):
    try:
        n = int(val)
        return Int(val)
    except:
        try:
            n = float(val)
            return Float(val)
        except:
            assert_var_name(val)
            return Var(val)

def starts_with(array, prefix):
    for i in range(len(prefix)):
        if i >= len(array):
            return False
        if array[i] != prefix[i]:
            return False
    return True

def parse_operator(operators, line):
    operators = sorted(operators, key=lambda o: len(o.op), reverse=True)
    for i in range(len(line)):
        for operator in operators:
            if line[i] == operator:
                left = parse_math(line[:i])
                right = parse_math(line[i + 1:])
                return operator(left, right)

def parse_math(line):
    if len(line) == 0:
        raise Exception("parsing math but line is length 0")
    leftover = [c for c in line if c != " "]
    if len(leftover) == 1 and isinstance(leftover[0], Expression):
        return leftover[0]
    
    #print("line", line)
    line = explode(line)
    #print("exploded", line)

    # raise Exception("= operator needs to not match on == >= <= !=, etc")
    # p = parse_operator([Assignment], line)
    # if p is not None:
    #     return p

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

    #if isinstance(line, basestr):
    if not "".join(line).strip():
        raise Exception("expected number or variable, got nothing")
    return parse_num_or_var("".join(line).strip())


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

def parse_parentheses(line, matches):

    parentheses = split_one_level(matches)
    
    if not parentheses:
        # fix this
        return parse_math(line)

    output = []
    last = 0
    for i, end in parentheses:
        if i > last:
            output.append(Partial(line[last:i]))
            parsed = parse_parentheses(line[i+1:end], matches[i+1:end])
            output.append(parsed)
            last = end + 1
    
    tail = line[last:]
    if not isempty(tail):
        output.append(Partial(tail))
    
    #print("output", output)
    return parse_math(output)

def explode_line(line):
    ops = sorted(all_operators, key=lambda o: len(o.op), reverse=True)
    output = []
    i = 0
    while i < len(line):
        matched_ops = [o for o in ops if line[i:].startswith(o.op)]
        if matched_ops:
            op = matched_ops[0]
            output.append(op)
            i += len(op.op)
        else:
            output.append(line[i])
            i += 1
    return output

def parse_statement(line):
    exploded = explode_line(line)
    matches = find_matching_parentheses(exploded)
    parsed = parse_parentheses(exploded, matches)
    return parsed

