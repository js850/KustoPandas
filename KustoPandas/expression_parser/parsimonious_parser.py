import parsimonious
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from KustoPandas.expression_parser.expression_parser_types import *

from KustoPandas.expression_parser.tabular_operators import *

kusto_peg = r"""
# DEFINE THE TERMINAL rules.

WS          = " "

int         = ~'\d\d*' WS*
float       = (~'\d+\.\d*' /  ~'\d*\.\d+') WS*
number      = float / int
identifier  = ~'[a-zA-Z_][a-zA-Z0-9_]*' WS*
columnNameOrPattern  = ~'[a-zA-Z0-9_*]*' WS*
stringLiteral = ( ~'"[^"]*"' / ~'\'[^\']*\'' ) WS*
timespanLiteral = ~'[1-9]\d*[dhms]' WS*

LPAR        = "(" WS*
RPAR        = ")" WS*
PLUS        = "+" WS*
MINUS       = "-" WS*
MUL         = "*" WS*
DIV         = "/" WS*
NOT         = "not" WS*

GT         = ">" WS*
LT         = "<" WS*
GE         = ">=" WS*
LE         = "<=" WS*
EQ         = "==" WS*
NEQ        = "!=" WS*
AND        = "and" WS*
OR         = "or" WS*

BETWEEN    = "between" WS*
DOTDOT     = ".." WS*

CONTAINS         = "contains" WS*
CONTAINS_CS      = "contains_cs" WS*
NOTCONTAINS      = "!contains" WS*
NOTCONTAINS_CS   = "!contains_cs" WS*

STARTSWITH       = "startswith" WS*
STARTSWITH_CS    = "startswith_cs" WS*
NOTSTARTSWITH    = "!startswith" WS*
NOTSTARTSWITH_CS = "!startswith_cs" WS*

HAS              = "has" WS*
HAS_CS           = "has_cs" WS*
NOTHAS           = "!has" WS*
NOTHAS_CS        = "!has_cs" WS*


# DEFINE THE GRAMAR OF OPERATORS AND ALGEBREIC EXPRESSIONS
# operator precedence is defined by the chaining of the rules together

# todo:  in c an assignment returns a value, so you can have them be part of the chain of operations e.g. x = 1 + (y = 5) 
# this is not the case in Kusto, I should update it to reflect that.

expressionInParens = LPAR stringOp RPAR
primaryExpr = ( timespanLiteral / number / identifier / stringLiteral / expressionInParens )
factor      = ( PLUS / MINUS / NOT )? primaryExpr

prod        = factor ((MUL / DIV) factor )*
sum         = prod ((PLUS / MINUS) prod)*

gt          = sum (( GE / LE / GT / LT ) sum )?
eq          = gt (( EQ / NEQ ) gt )?
and         = eq (AND eq )?
or          = and (OR and )?

between     = or ( BETWEEN LPAR or DOTDOT or RPAR )?

stringOp    = between (( 
                    NOTCONTAINS_CS / CONTAINS_CS / NOTCONTAINS /  CONTAINS /
                    NOTSTARTSWITH_CS / NOTSTARTSWITH / STARTSWITH_CS / STARTSWITH /
                    NOTHAS_CS / NOTHAS / HAS_CS / HAS
                    ) between )?

kustoStatement = WS* stringOp

"""

kusto_peg2 = r"""

# DEFINE THE TERMINAL rules.

int         = ~'\d\d*'
float       = ~'\d+\.\d*' /  ~'\d*\.\d+'
number      = float / int
identifier  = ~'[a-zA-Z_][a-zA-Z0-9_]*'
columnNameOrPattern  = ~'[a-zA-Z0-9_*]*'
stringLiteral = ( ~'"[^"]*"' / ~'\'[^\']*\'' )
timespanLiteral = ~'[1-9]\d*[dhms]'

# DEFINE THE GRAMAR OF OPERATORS AND ALGEBREIC EXPRESSIONS
# operator precedence is defined by the chaining of the rules together

# todo:  in c an assignment returns a value, so you can have them be part of the chain of operations e.g. x = 1 + (y = 5) 
# this is not the case in Kusto, I should update it to reflect that.

primaryExpr = ( timespanLiteral / number / identifier / stringLiteral / ("(" assignment ")") )

# todo: you cannot have assignments inside a method call
# generally * is not allowed, but any(*) is an exception.  
methodCall  = identifier "(" ( "*" / assignmentList )? ")"
squareBrackets  = identifier ("[" assignment "]")+

posfixExpr  = methodCall / squareBrackets / primaryExpr

dot         = posfixExpr ("." posfixExpr)*

factor      = ( "+" / "-" / "not" )?  dot

prod        = factor  (("*" / "/") factor )*
sum         = prod  (("+" / "-") prod )*

gt          = sum (( ">=" / "<=" / ">" / "<" ) sum )?
eq          = gt (( "==" / "!=" ) gt )?
and         = eq (("and") eq )?
or          = and ("or" and )?

between     = or ( "between" "(" or ".." or ")" )?

stringOp    = between (( "contains_cs" / "!contains_cs" / "contains" / "!contains" /
                     "startswith_cs" / "!startswith_cs" / "startswith" / "!startswith" /
                     "has_cs" / "!has_cs" / "has" / "!has"
                    ) between )?

list        = "(" assignmentList ")"
inList      = stringOp ("in~" / "!in~" / "!in" / "in" ) (list / stringOp) / stringOp

assignment  = identifier "=" inList / inList
assignmentList      = assignment ("," assignment)*

# Use this root rule if you just want to parse a simple expression
kustoStatement  = assignment

# DEFINE THE KUSTO TABULAR OPERATORS 
asc         = "asc" / "desc"
sortColumn  = stringOp asc?
simpleAssignment = identifier "=" identifier

take        = "take" int
where       = "where" inList
extend      = "extend" assignmentList
summarize   = "summarize" assignmentList ( "by" assignmentList )?
sort        = "sort" "by" sortColumn ("," sortColumn)*
top         = "top" int "by" sortColumn ("," sortColumn)*
project     = "project" assignmentList
projectAway = "project-away" columnNameOrPattern ("," columnNameOrPattern)*
projectKeep = "project-keep" columnNameOrPattern ("," columnNameOrPattern)*
projectReorder = "project-reorder" columnNameOrPattern ("," columnNameOrPattern)*
projectRename = "project-rename" simpleAssignment ("," simpleAssignment)*
distinct    = "distinct" ("*" / assignmentList)

tabularOperator = take / where / extend / summarize / sort / top / projectAway / projectKeep / projectReorder / projectRename / project / distinct

# use this root rule if you want to parse a full Kusto statement
kusto       = tabularOperator EOF

"""

class PartialNode(list):
    def __init__(self, children):
         for c in children:
            if isinstance(c, PartialNode):
                self += c
            else:
                self.append(c)

class Visitor(NodeVisitor):
    def __init__(self):
        # WS is the second child, we should ignore it
        self.visit_LPAR = self.lift_first_child_of_two
        self.visit_RPAR = self.lift_first_child_of_two
        self.visit_PLUS = self.lift_first_child_of_two
        self.visit_MINUS = self.lift_first_child_of_two
        self.visit_MUL = self.lift_first_child_of_two
        self.visit_DIV = self.lift_first_child_of_two
        self.visit_NOT = self.lift_first_child_of_two

        self.visit_GT = self.lift_first_child_of_two
        self.visit_LT = self.lift_first_child_of_two
        self.visit_GE = self.lift_first_child_of_two
        self.visit_LE = self.lift_first_child_of_two
        self.visit_EQ = self.lift_first_child_of_two
        self.visit_NEQ = self.lift_first_child_of_two
        self.visit_AND = self.lift_first_child_of_two
        self.visit_OR = self.lift_first_child_of_two

        self.visit_BETWEEN = self.lift_first_child_of_two
        self.visit_DOTDOT = self.lift_first_child_of_two

        self.visit_CONTAINS = self.lift_first_child_of_two
        self.visit_CONTAINS_CS = self.lift_first_child_of_two
        self.visit_NOTCONTAINS = self.lift_first_child_of_two
        self.visit_NOTCONTAINS_CS = self.lift_first_child_of_two

        self.visit_STARTSWITH = self.lift_first_child_of_two
        self.visit_STARTSWITH_CS = self.lift_first_child_of_two
        self.visit_NOTSTARTSWITH = self.lift_first_child_of_two
        self.visit_NOTSTARTSWITH_CS = self.lift_first_child_of_two

        self.visit_HAS = self.lift_first_child_of_two
        self.visit_HAS_CS = self.lift_first_child_of_two
        self.visit_NOTHAS = self.lift_first_child_of_two
        self.visit_NOTHAS_CS = self.lift_first_child_of_two

    def lift_first_child_of_two(self, node, children):
        if len(children) == 2:
            return children[0]
        raise Exception("Expected two children, got " + len(children))

    def visit_kustoStatement(self, node, children):
        return children[1]

    def generic_visit(self, node, children):
        if len(children) == 0:
            return node.text
        if len(children) == 1:
            return children[0]
        
        return PartialNode(children)

    def visit_int(self, node, children):
        return Int(node.text)
        
    def visit_float(self, node, children):
        return Float(node.text)

    def visit_identifier(self, node, children):
        return Var(node.text)
    
    def visit_columnNameOrPattern(self, node, children):
        return ColumnNameOrPattern(node.text)

    def visit_stringLiteral(self, node, children):
        # remove the enclosing quotes
        return StringLiteral(node.text[1:-1])

    def visit_timespanLiteral(self, node, children):
        num = node.text[:-1]
        unit = node.text[-1]
        return TimespanLiteral(Int(num), unit)

    def visit_factor(self, node, children):
        if len(children) == 1: # TODO: not possible
            return children[0]
        if "-" == children[0]:
            return UnaryMinus(children[-1])
        if "not" == children[0]:
            return UnaryNot(children[-1])
        # can be "+"
        return children[-1]
    
    def visit_expressionInParens(self, node, children):
        # ignore parentheses at index 0 and 2
        return children[1]
    
    def _visit_binary_op(self, node, children):
        if children[1] == "":
            return children[0]

        if len(children) != 2: raise Exception()

        left = children[0]

        flattened = children[1]
        for i in range(0, len(flattened), 2):
            opstr = flattened[i]
            right = flattened[i+1]
            op = all_operators_dict[opstr]
            if op == AmbiguousMinus or op == AmbiguousStar:
                op = op.binary
            
            operator = op(left, right)

            left = operator

        return left
    
    def _visit_binary_op_single(self, node, children, op):
        return self._visit_binary_op(node, children)
        # if there is only one operator, then the op is not in the children list
        if len(children) == 1:
            return children[0]
        
        left = children[0]

        for right in children[1:]:
            operator = op(left, right)
            left = operator

        return left
        

    def visit_sum(self, node, children):
        return self._visit_binary_op(node, children)
    
    def visit_prod(self, node, children):
        return self._visit_binary_op(node, children)
    
    def visit_gt(self, node, children):
        return self._visit_binary_op(node, children)

    def visit_eq(self, node, children):
        return self._visit_binary_op(node, children)

    def visit_and(self, node, children):
        return self._visit_binary_op_single(node, children, And)

    def visit_or(self, node, children):
        return self._visit_binary_op_single(node, children, Or)
        
    def visit_assignment(self, node, children):
        return self._visit_binary_op_single(node, children, Assignment)
    
    def visit_between(self, node, children):
        if children[1] == "":
            return children[0]
        
        # todo: refactor. there is no need for DotDot here
        partial = children[1] # this has ["(", left, "..", right, ")"]
        dotdot = DotDot(partial[2], partial[4])
        return Between(children[0], dotdot)

    def visit_stringOp(self, node, children):
        return self._visit_binary_op(node, children)

    def visit_assignmentList(self, node, children):
        return list(children)

    def visit_methodCall(self, node, children):
        method = children[0] 
            
        if len(children) < 2:
            args = Args([])
        elif children[1] == "*":
            args = Args([Star()])
        else:
            args = Args(children[1])
        
        return Method(method, args)
    
    def visit_squareBrackets(self, node, children):
        left = children[0]
        for child in children[1:]:
            left = SquareBrackets(left, child)
        return left

    def visit_dot(self, node, children):
        left = children[0]
        for child in children[1:]:
            left = Dot(left, child)
        return left
    
    def visit_list(self, node, children):
        return ListExpression(children[0])

    def visit_inList(self, node, children):
        return self._visit_binary_op(node, children)
        
    def visit_take(self, node, children):
        return Take(children[0])
    
    def visit_where(self, node, children):
        return Where(children[0])

    def visit_extend(self, node, children):
        return Extend(children[0])
    
    def visit_summarize(self, node, children):
        aggregates = children[0]
        if len(children) > 1:
            by = children[1]
        else:
            by = []
        return Summarize(aggregates, by)
    
    def visit_sortColumn(self, node, children):
        var = children[0]
        if len(children) == 1:
            return SortColumn(var)
        
        asc = children[1] == "asc"
        return SortColumn(var, asc=asc)
        
    def visit_sort(self, node, children):
        return Sort(list(children))
    
    def visit_top(self, node, children):
        n = children[0]
        sort_columns = children[1:]
        return Top(n, sort_columns)
    
    def visit_project(self, node, children):
        return Project(children[0])
    
    def visit_projectAway(self, node, children):
        return ProjectAway(list(children))

    def visit_projectKeep(self, node, children):
        return ProjectKeep(list(children))
    
    def visit_simpleAssignment(self, node, children):
        return self.visit_assignment(node, children)
    
    def visit_projectRename(self, node, children):
        return ProjectRename(list(children))

    def visit_projectReorder(self, node, children):
        return ProjectReorder(list(children))

    def visit_distinct(self, node, children):
        return Distinct(children[0])

_PARSER = dict()

def get_parser(root, debug=False):
    if not root in _PARSER:
        g = Grammar(kusto_peg)
        _PARSER[root] = g.default(root)

    return _PARSER[root]

def parse_expression(input, debug=True, root="kustoStatement"):
    parser = get_parser(root, debug=False)

    if debug:
        print ("---------------------- INPUT -----------------------------")
        print(input)

    parse_tree = parser.parse(input)

    if debug:
        print(str(parse_tree))
        print(parse_tree.__repr__())
        # print(parse_tree.tree_str())

    visitor = Visitor()
    expression_tree = visitor.visit(parse_tree)
    if debug:
        print(str(expression_tree))

    return expression_tree

def parse_expression_toplevel(input, debug=False):
    return parse_expression(input, debug=debug, root="kusto")
