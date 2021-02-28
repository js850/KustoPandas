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
        self.descendents = [right]
    
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

class UnaryOppLeft(Expression):
    op = ""
    def __init__(self, left):
        self.left = left
        self.descendents = [left]
    
    def __str__(self):
        if op_is_not_special_chars(self.op):
            space = " "
        else:
            space = ""
        return "({0}{1}{2})".format(self.left, space, self.op)

    def __repr__(self):
        return str(self)

    def evaluate_internal(self, left):
        raise NotImplementedError()

    def evaluate(self, vals):
        left = self.left.evaluate(vals)
        return self.evaluate_internal(left)

class Opp(Expression):
    op = ""
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.descendents = [left, right]
    
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
        return left.str.contains(right, case=case_sensitive, na=False)
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

def _has(left, right, case_sensitive):
    pattern = "\\b" + right + "\\b"
    if are_all_series(left):
        return left.str.contains(pattern, case=case_sensitive)
    flags = 0
    if not case_sensitive:
        flags = re.IGNORECASE
    return re.search(pattern, left, flags=flags) is not None

class Has(Opp):
    op = "has"
    def evaluate_internal(self, left, right, **kwargs):
        return _has(left, right, False)

class NotHas(Opp):
    op = "!has"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_has(left, right, False))

class HasCs(Opp):
    op = "has_cs"
    def evaluate_internal(self, left, right, **kwargs):
        return _has(left, right, True)

class NotHasCs(Opp):
    op = "!has_cs"
    def evaluate_internal(self, left, right, **kwargs):
        return _not(_has(left, right, True))

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

class DotDot(Opp):
    op = ".."
    def evaluate_internal(self, left, right, **kwargs):
        raise NotImplementedError("DotDot does not have an implementation")

class Between(Opp):
    op = "between"
    def evaluate(self, vals):
        if not isinstance(self.right, DotDot):
            raise Exception("Between operator must act on DotDot")
        left = self.left.evaluate(vals)
        lower = self.right.left.evaluate(vals)
        upper = self.right.right.evaluate(vals)

        if are_all_series(left):
            return (lower <= left) & (left <= upper)
        return lower <= left and left <= upper

class Star(Expression):
    op = "*"
    def __str__(self):
        return self.op

    def __repr__(self):
        return str(self)

class Asc(UnaryOppLeft):
    op = "asc"
    def evaluate_internal(self, left):
        return left

class Desc(UnaryOppLeft):
    op = "desc"
    def evaluate_internal(self, left):
        return left

class AmbiguousMinus(Opp):
    # - can be either unary or binary op
    op = "-"
    unary = UnaryMinus
    binary = Sub

class AmbiguousStar(Expression):
    op = "*"
    binary = Mul
    nullary = Star

class Dot(Opp):
    op = "."
    def __str__(self):
        return "({0}{1}{2})".format(self.left, self.op, self.right)
    def evaluate(self, vals):
        # D.k is equivalent to D["k"]
        left = self.left.evaluate(vals)
        # The right value should not be evaluated
        right = str(self.right)
        return _square_brackets_evaluate(left, right)

generic_expression_operators = [
    Add, AmbiguousMinus, AmbiguousStar, Div, Eq, NEq, Gt, Lt, Ge, Le,
    UnaryNot, And, Or,
    Contains, NotContains, ContainsCs, NotContainsCs,
    StartsWith, NotStartsWith, StartsWithCs, NotStartsWithCs,
    In, NotIn, InCis, NotInCis, 
    Has, NotHas, HasCs, NotHasCs,
    Between, DotDot,
    Comma, Dot,
    ]

assignment = [Assignment]

all_generic_operators = generic_expression_operators + assignment

# These specialty operators only make sense in the context of certain functions like summarize and sort
# TODO: do a better job of recognizing operators within the context of where they occur.
# For example, A*B can be multiplication or wildcard depending on the context.  
# one option is to pass the context to the parser.  e.g. for the sort operatoror 
specialty_operators = [By, Asc, Desc] # Star

all_operators = all_generic_operators + specialty_operators

def get_symbol_operators():
    return [o for o in all_operators if not op_is_not_special_chars(o.op)]

def get_non_symbol_operators():
    return [o for o in all_operators if op_is_not_special_chars(o.op)]

class NumOrVar(Expression):
    pass

class Int(NumOrVar):
    def __init__(self, value):
        self.value = value.strip()
        self.descendents = []
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Int({})".format(self.value)
    def evaluate(self, vals):
        return int(self.value)
    
class Float(NumOrVar):
    def __init__(self, value):
        self.value = value.strip()
        self.descendents = []
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Float({})".format(self.value)
    def evaluate(self, vals):
        return float(self.value)

class Var(NumOrVar):
    def __init__(self, value):
        self.value = value.strip()
        self.descendents = []
    def __str__(self):
        return self.value
    def __repr__(self):
        return "Var({})".format(self.value)
    def evaluate(self, vals):
        return vals[self.value]

class StringLiteral(NumOrVar):
    def __init__(self, value):
        self.value = value
        self.descendents = []
    def __str__(self):
        return "\"" + self.value + "\""
    def __repr__(self):
        return "StringLiteral({})".format(self.value)
    def evaluate(self, vals):
        return self.value

class Args(Expression):
    def __init__(self, args):
        self.args = args
        self.descendents = list(args)

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
        self.descendents = [name, args]
        self.aggregate_instance = None

    def __str__(self):
        return str(self.name) + str(self.args)
    def __repr__(self):
        return str(self)
    def evaluate(self, vals):
        if self.has_aggregate_instance():
            return self.aggregate_instance.evaluate(vals)

        method = self.name.evaluate(vals)
        args = self.args.evaluate(vals)
        return method(*args)
    
    def set_aggregate_instance(self, agg):
        self.aggregate_instance = agg
    
    def has_aggregate_instance(self):
        return self.aggregate_instance is not None

def _square_brackets_apply(v, k):
    try:
        return v[k]
    except:
        # dynamic objects just return null for failure
        return None

def _square_brackets_two_series(variables, keys):
    def eval_row(row):
        # this operates on the dataframe one row at a time
        return _square_brackets_apply(row["v"], row["k"])
    
    df = pd.DataFrame({"k" : keys, "v" : variables})
    return df.apply(eval_row, axis=1)

def _square_brackets_evaluate(variable, value):
    if are_all_series(variable):
        if are_all_series(value):
            return _square_brackets_two_series(variable, value)
        return variable.apply(lambda v: _square_brackets_apply(v, value))
    return _square_brackets_apply(variable, value)

class SquareBrackets(Expression):
    def __init__(self, variable, value):
        self.variable = variable
        self.value = value
        self.descendents = [variable, value]

    def __str__(self):
        return str(self.variable)  + "[" + str(self.value) + "]"
    def __repr__(self):
        return str(self)
    def evaluate(self, vals):
        variable = self.variable.evaluate(vals)
        value = self.value.evaluate(vals)
        return _square_brackets_evaluate(variable, value)

class TimespanLiteral(Expression):
    # e.g. 4d resolves to timespan 4 days
    def __init__(self, count, unit):
        self.count = count
        self.unit = unit
        self.descendents = []
    def __str__(self):
        return "{0}{1}".format(str(self.count), self.unit)
    def __repr__(self):
        return str(self) #"DaysLiteral({0})".format(self.value)
    def evaluate(self, vals):
        return pd.Timedelta(self.count.evaluate(None), unit=self.unit)

class ListExpression(Expression):
    def __init__(self, items):
        self.items = items
        self.descendents = list(items)

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
