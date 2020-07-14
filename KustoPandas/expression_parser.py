import numpy as np

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

class Sub(Opp):
    op = "-"
class Mul(Opp):
    op = "*"
class Div(Opp):
    op = "/"

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

class Num:
    def __init__(self, value):
        self.value = value.strip()
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Num({})".format(self.value)

class Var:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value.strip()
    def __repr__(self):
        return "Var({})".format(self.value)


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
    if isinstance(line, str):
        return list(line)
    output = []
    for val in line:
        if isinstance(val, Partial):
            output += list(val.value)
        else:
            output.append(val)
    return output
        

def parse_math(line):
    if len(line) == 0:
        raise Exception("parsing math but line is length 0")
    leftover = [c for c in line if c != " "]
    if len(leftover) == 1 and isinstance(leftover[0], Expression):
        return leftover[0]
    
    #print("line", line)
    line = explode(line)
    #print("exploded", line)
    i = len(line)
    for c in reversed(line):
        i -= 1
        if c == "+" or c == "-":
            left = parse_math(line[:i])
            right = parse_math(line[i+1:])
            if c == "+":
                return Add(left, right)
            else:
                return Sub(left, right)
    i = len(line)
    for c in reversed(line):
        i -= 1
        if c == "*" or c == "/":
            left = parse_math(line[:i])
            right = parse_math(line[i+1:])
            if c == "*":
                return Mul(left, right)
            else:
                return Div(left, right)

    #if isinstance(line, basestr):
    if not "".join(line).strip():
        return None
    return Pure(line)


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
    if tail.strip():
        output.append(Partial(tail))
    
    #print("output", output)
    return parse_math(output)
