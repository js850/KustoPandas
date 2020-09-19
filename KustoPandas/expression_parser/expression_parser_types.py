import numpy as np
import re
import pandas as pd
import inspect 

def are_all_series(*args):
    return all((isinstance(a, pd.Series) for a in args))

match_az = re.compile("[a-zA-Z]")

def op_is_not_special_chars(op):
    # e.g. contains, or, and
    return match_az.search(op) is not None

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
        return _not(right)

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

def _contains(left, right, case_sensitive):
    if are_all_series(left):
        return left.str.contains(right, case=case_sensitive)
    return right.lower() in left.lower() 

class Contains(Opp):
    op = "contains"
    def evaluate_internal(self, left, right, **kwargs):
        return _contains(left, right, False)

class NotContains(Opp):
    op = "!contains"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_contains(left, right, False))   

class ContainsCs(Opp):
    op = "contains_cs"
    def evaluate_internal(self, left, right, **kwargs):
        return _contains(left, right, True)

class NotContainsCs(Opp):
    op = "!contains_cs"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_contains(left, right, True))   

def _starts_with(left, right, case_sensitive):
    # Pandas doesn't support case insensitive startswith.  can we do better than lowercasing everything?
    if are_all_series(left):
        # Pandas doesn't support case insensitive startswith.  can we do better than lowercasing everything?
        if not case_sensitive:
            left = left.str.lower()
            right = right.lower()
        return left.str.startswith(right)
    if not case_sensitive:
        left = left.lower()
        right = right.lower()
    return left.startswith(right) 

class StartsWith(Opp):
    op = "startswith"
    def evaluate_internal(self, left, right, **kwargs):
        return _starts_with(left, right, False)

class NotStartsWith(Opp):
    op = "!startswith"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_starts_with(left, right, False))

class StartsWithCs(Opp):
    op = "startswith_cs"
    def evaluate_internal(self, left, right, **kwargs):
        return _starts_with(left, right, True)

class NotStartsWithCs(Opp):
    op = "!startswith_cs"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_starts_with(left, right, True))

def _in(left, right):
    if are_all_series(left):
        return left.isin(right)
    return left in right 

def _in_cis(left, right):
    right = [r.lower() for r in right]
    if are_all_series(left):
        return left.str.lower().isin(right)
    return left.lower() in right

class In(Opp):
    op = "in"
    def evaluate_internal(self, left, right, **kwargs):
        return _in(left, right)

class NotIn(Opp):
    op = "!in"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_in(left, right))

class InCis(Opp):
    op = "in~"
    def evaluate_internal(self, left, right, **kwargs):
        return _in_cis(left, right)

class NotInCis(Opp):
    op = "!in~"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_in_cis(left, right))

class By(Opp):
    op = "by"
    def evaluate_internal(self, left, right, **kwargs):
        raise NotImplementedError("By does not have an implementation")

class Comma(Opp):
    op = ","
    def evaluate_internal(self, left, right, **kwargs):
        if isinstance(self.right, Comma):
            return [left] + right
        return [left, right]
    def __str__(self):
        return "(" + self._str_internal() + ")"
    def _str_internal(self):
        if isinstance(self.right, Comma):
            return str(self.left) + ", " + self.right._str_internal()
        return str(self.left) + ", " + str(self.right)

class AmbiguousMinus(Opp):
    # - can be either unary or binary op
    op = "-"
    unary = UnaryMinus
    binary = Sub

all_operators = [Add, AmbiguousMinus, Div, Mul, Eq, NEq, Gt, Lt, Ge, Le,
                 UnaryNot, Assignment,
                 And, Or, Comma,
                 Contains, NotContains, ContainsCs, NotContainsCs,
                 StartsWith, NotStartsWith, StartsWithCs, NotStartsWithCs,
                 In, NotIn, InCis, NotInCis, By]
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

def _not(input):
    if are_all_series(input):
        return ~input
    return not input
