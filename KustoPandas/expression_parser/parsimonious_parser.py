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

# OPERATORS
LPAR        = "(" WS*
RPAR        = ")" WS*
LBRAK       = "[" WS*
RBRAK       = "]" WS*
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

IN               = "in" WS*
IN_CIS           = "in~" WS*
NOTIN            = "!in" WS*
NOTIN_CIS        = "!in~" WS*

ASSIGNMENT       = "=" WS*

COMMA            = "," WS*

DOT              = "." WS*

# DEFINE THE GRAMAR OF OPERATORS AND ALGEBREIC EXPRESSIONS
# operator precedence is defined by the chaining of the rules together

# todo:  in c an assignment returns a value, so you can have them be part of the chain of operations e.g. x = 1 + (y = 5) 
# this is not the case in Kusto, I should update it to reflect that.

expressionInParens = LPAR assignment RPAR
primaryExpr = ( timespanLiteral / number / identifier / stringLiteral / expressionInParens )

# todo: you cannot have assignments inside a method call
# note: generally * is not allowed, but any(*) is an exception.  
methodCall  = identifier LPAR ( MUL / assignmentList )? RPAR
squareBrackets  = identifier (LBRAK assignment RBRAK)+

posfixExpr  = methodCall / squareBrackets / primaryExpr

dot         = posfixExpr (DOT posfixExpr)*

factor      = ( PLUS / MINUS / NOT )? dot

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

list        = LPAR assignmentList RPAR
inList      = stringOp (( NOTIN_CIS / IN_CIS / NOTIN / IN ) (list / stringOp) )?

internalAssignment = identifier ASSIGNMENT inList
assignment  = internalAssignment / inList
assignmentList      = assignment (COMMA assignment)*

# Use this root rule if you just want to parse a simple expression
kustoStatement = WS* assignment

# DEFINE THE KUSTO TABULAR OPERATORS 

BY          = "by" WS+
ASC         = ("asc" / "desc") WS*

sortColumn  = stringOp ASC?
sortColumnList = sortColumn (COMMA sortColumn)*
simpleAssignment = identifier ASSIGNMENT identifier
simpleAssignmentList = simpleAssignment (COMMA simpleAssignment)*
columnNameOrPatternList = columnNameOrPattern (COMMA columnNameOrPattern)*

take        = "take" WS+ int
where       = "where" WS+ inList
extend      = "extend" WS+ assignmentList
summarize   = "summarize" WS+ assignmentList ( BY assignmentList )?
sort        = "sort" WS+ BY sortColumnList
top         = "top" WS+ int BY sortColumnList
project     = "project" WS+ assignmentList
projectAway = "project-away" WS+ columnNameOrPatternList
projectKeep = "project-keep" WS+ columnNameOrPatternList
projectReorder = "project-reorder" WS+ columnNameOrPatternList
projectRename = "project-rename" WS+ simpleAssignmentList
distinct    = "distinct" WS+ (MUL / assignmentList)

tabularOperator = take / where / extend / summarize / sort / top / projectAway / projectKeep / projectReorder / projectRename / project / distinct

# use this root rule if you want to parse a full Kusto statement
kusto       = WS* tabularOperator
"""

class PartialNode(list):
    def __init__(self, children):
        # keep a single flat list
         for c in children:
            if isinstance(c, PartialNode):
                self += c
            else:
                self.append(c)

class Visitor(NodeVisitor):
    def __init__(self):
        pass
        # WS is the second child, we should ignore it
        # self.visit_LPAR = self.lift_first_child_of_two
        # self.visit_RPAR = self.lift_first_child_of_two
        # self.visit_PLUS = self.lift_first_child_of_two
        # self.visit_MINUS = self.lift_first_child_of_two
        # self.visit_MUL = self.lift_first_child_of_two
        # self.visit_DIV = self.lift_first_child_of_two
        # self.visit_NOT = self.lift_first_child_of_two

        # self.visit_GT = self.lift_first_child_of_two
        # self.visit_LT = self.lift_first_child_of_two
        # self.visit_GE = self.lift_first_child_of_two
        # self.visit_LE = self.lift_first_child_of_two
        # self.visit_EQ = self.lift_first_child_of_two
        # self.visit_NEQ = self.lift_first_child_of_two
        # self.visit_AND = self.lift_first_child_of_two
        # self.visit_OR = self.lift_first_child_of_two

        # self.visit_BETWEEN = self.lift_first_child_of_two
        # self.visit_DOTDOT = self.lift_first_child_of_two

        # self.visit_CONTAINS = self.lift_first_child_of_two
        # self.visit_CONTAINS_CS = self.lift_first_child_of_two
        # self.visit_NOTCONTAINS = self.lift_first_child_of_two
        # self.visit_NOTCONTAINS_CS = self.lift_first_child_of_two

        # self.visit_STARTSWITH = self.lift_first_child_of_two
        # self.visit_STARTSWITH_CS = self.lift_first_child_of_two
        # self.visit_NOTSTARTSWITH = self.lift_first_child_of_two
        # self.visit_NOTSTARTSWITH_CS = self.lift_first_child_of_two

        # self.visit_HAS = self.lift_first_child_of_two
        # self.visit_HAS_CS = self.lift_first_child_of_two
        # self.visit_NOTHAS = self.lift_first_child_of_two
        # self.visit_NOTHAS_CS = self.lift_first_child_of_two
    
        # self.visit_IN = self.lift_first_child_of_two
        # self.visit_IN_CIS = self.lift_first_child_of_two
        # self.visit_NOTIN = self.lift_first_child_of_two
        # self.visit_NOTIN_CIS = self.lift_first_child_of_two

        # self.visit_ASSIGNMENT = self.lift_first_child_of_two
        # self.visit_COMMA = self.lift_first_child_of_two

        self.visit_columnNameOrPatternList = self._visit_list_with_at_least_one
        self.visit_simpleAssignmentList = self._visit_list_with_at_least_one

        self.visit_sum = self._visit_binary_op
        self.visit_prod = self._visit_binary_op
        self.visit_gt = self._visit_binary_op
        self.visit_eq = self._visit_binary_op
        self.visit_and = self._visit_binary_op
        self.visit_or = self._visit_binary_op
        self.visit_stringOp = self._visit_binary_op
        self.visit_inList = self._visit_binary_op

        self.visit_dot = self._visit_binary_op


    def lift_first_child_of_two(self, node, children):
        if len(children) == 2:
            return children[0]
        raise Exception("Expected two children, got " + len(children))

    def visit_WS(self, node, children):
        return None

    def visit_kustoStatement(self, node, children):
        return children[1]

    def generic_visit(self, node, children):
        if node.text == "":
            # non-matched optional node
            return None
        if len(children) == 0:
            # raw match, e.g. "+" from  ("+" / "-")
            return node.text
        if len(children) == 1:
            # pass through node
            return children[0]
        
        # In parsimonius, there is a node in the parse tree for every single node, even non-named nodes.
        #   e.g. the rule `sum = expr (PLUS expr)*` has two children, `expr` and `(PLUS expr)*` where the second is an un-named node
        #   The way I have it set up here
        #   if `(plus expr)*` does not match it will be None
        #   if it does match then it will be PartialNode(["+", expr])
        #   PartialNode will keep the list flat, so if there are multiple matches it will be PartialNode(["+", expr, "+", expr2])

        # here I want to do a few things.
        # First, ignore whitespace in the terminal rules.  
        #   example rule:   `PLUS = "+" WS*`
        #   The children of PLUS is "+" and the non-named rule `WS*` 
        #   I want the output of visit_PLUS to return "+" and completely ignore the WS.
        #   The first option I tried was to make an explicit visitor for all terminal rules with WS.  That quickly got annoying since there were dozens of them.
        #   Instead I try to handle the logic here by having visit_WS return None and remove all None values from children here
        #   I also have to handle the case where `WS*` does not match -- which is why I have non-matching optional nodes also return None

        # remove whitespace and not matched optional nodes
        if None in children:
            return self.generic_visit(node, [c for c in children if c is not None])

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
        # remove whitespace outside the quotes and the enclosing quotes
        return StringLiteral(node.text.strip()[1:-1])

    def visit_timespanLiteral(self, node, children):
        num = node.text[:-1]
        unit = node.text[-1]
        return TimespanLiteral(Int(num), unit)

    def visit_factor(self, node, children):
        if children[0] is None:
            return children[-1]
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
        if children[1] is None:
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
    
    def visit_internalAssignment(self, node, children):
        return Assignment(children[0], children[2])
    
    def visit_between(self, node, children):
        if children[1] is None:
            return children[0]
        
        # todo: refactor. there is no need for DotDot here
        partial = children[1] # this has ["(", left, "..", right, ")"]
        dotdot = DotDot(partial[2], partial[4])
        return Between(children[0], dotdot)

    def _visit_list_with_at_least_one(self, node, children):
        result = [children[0]]
        if children[1] is None:
            return result
        # children[1] is a list like [",", val1, ",", val2]
        # take only the values and drop the commas
        rest = children[1][1::2]
        return result + rest

    def visit_assignmentList(self, node, children):
        return self._visit_list_with_at_least_one(node, children)

    def visit_methodCall(self, node, children):
        method = children[0] 
        
        in_parens = children[2]

        if in_parens is None:
            args = Args([])
        elif in_parens == "*":
            args = Args([Star()])
        else:
            args = Args(in_parens)
        
        return Method(method, args)
    
    def visit_squareBrackets(self, node, children):
        left = children[0]
        # this has the form ["[", value, "]", "[", value2, "]" ]
        in_brackets = children[1] 
        for child in in_brackets[1::3]:
            left = SquareBrackets(left, child)
        return left

    def visit_list(self, node, children):
        return ListExpression(children[1])
        
    def visit_take(self, node, children):
        return Take(children[2])
    
    def visit_where(self, node, children):
        return Where(children[2])

    def visit_extend(self, node, children):
        return Extend(children[2])
    
    def visit_summarize(self, node, children):
        aggregates = children[2]

        if children[3] is None:
            by = []
        else:
            by = children[3][1]
        return Summarize(aggregates, by)
    
    def visit_sortColumn(self, node, children):
        var = children[0]
        
        asc = children[1] == "asc"
        return SortColumn(var, asc=asc)
    
    def visit_sortColumnList(self, node, children):
        return self._visit_list_with_at_least_one(node, children)

    def visit_sort(self, node, children):
        return Sort(children[3])
    
    def visit_top(self, node, children):
        n = children[2]
        sort_columns = children[4]
        return Top(n, sort_columns)
    
    def visit_project(self, node, children):
        return Project(children[2])
    
    def visit_projectAway(self, node, children):
        return ProjectAway(children[2])

    def visit_projectKeep(self, node, children):
        return ProjectKeep(children[2])
    
    def visit_simpleAssignment(self, node, children):
        return Assignment(children[0], children[2])
    
    def visit_projectRename(self, node, children):
        return ProjectRename(children[2])

    def visit_projectReorder(self, node, children):
        return ProjectReorder(children[2])

    def visit_distinct(self, node, children):
        return Distinct(children[2])

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

