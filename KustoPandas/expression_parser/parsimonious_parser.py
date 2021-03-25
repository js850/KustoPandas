import parsimonious
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from KustoPandas.expression_parser.expression_parser_types import *

from KustoPandas.expression_parser.tabular_operators import *

# Define the grammar of the Kusto language using the PEG format.
# Then use a PEG parser compiler to parse the kusto language text
# https://en.wikipedia.org/wiki/Parsing_expression_grammar
# good tutorial https://tomassetti.me/parsing-in-python/
# Guido van Rossum's PEG blog https://medium.com/@gvanrossum_83706/peg-parsing-series-de5d41b2ed60

kusto_peg = r"""
# DEFINE THE TERMINAL rules.

# white space
WS          = ~'[ \n\r\t]+'

# The core terminal rules
int         = ~'\d\d*' WS?
exponent    =  ~'[eE][+\-]?[0-9]+'
fraction    = (~'\d+\.\d*' /  ~'\d*\.\d+')
float       = ((fraction exponent?) / (~'[0-9]+' exponent) ) WS?
number      = float / int
identifier  = ~'[a-zA-Z_][a-zA-Z0-9_]*' WS?
columnNameOrPattern  = ~'[a-zA-Z0-9_*]*' WS?
stringLiteral = ( ~'"[^"]*"' / ~'\'[^\']*\'' ) WS?
timespanLiteral = ~'[1-9]\d*[dhms]' WS?

# OPERATORS
LPAR        = "(" WS?
RPAR        = ")" WS?
LBRAK       = "[" WS?
RBRAK       = "]" WS?
PLUS        = "+" WS?
MINUS       = "-" WS?
MUL         = "*" WS?
DIV         = "/" WS?
NOT         = "not" WS?

GT         = ">" WS?
LT         = "<" WS?
GE         = ">=" WS?
LE         = "<=" WS?
EQ         = "==" WS?
NEQ        = "!=" WS?
AND        = "and" WS?
OR         = "or" WS?

BETWEEN    = "between" WS?
DOTDOT     = ".." WS?

CONTAINS         = "contains" WS?
CONTAINS_CS      = "contains_cs" WS?
NOTCONTAINS      = "!contains" WS?
NOTCONTAINS_CS   = "!contains_cs" WS?

STARTSWITH       = "startswith" WS?
STARTSWITH_CS    = "startswith_cs" WS?
NOTSTARTSWITH    = "!startswith" WS?
NOTSTARTSWITH_CS = "!startswith_cs" WS?

HAS              = "has" WS?
HAS_CS           = "has_cs" WS?
NOTHAS           = "!has" WS?
NOTHAS_CS        = "!has_cs" WS?

IN               = "in" WS?
IN_CIS           = "in~" WS?
NOTIN            = "!in" WS?
NOTIN_CIS        = "!in~" WS?

ASSIGNMENT       = "=" WS?

COMMA            = "," WS?

DOT              = "." WS?

# DEFINE THE GRAMAR OF OPERATORS AND ALGEBREIC EXPRESSIONS
# operator precedence is defined by the chaining of the rules together

expressionInParens = LPAR expression RPAR
primaryExpr = ( timespanLiteral / number / identifier / stringLiteral / expressionInParens )

# note: generally * is not allowed, but any(*) is an exception.  
# I use a new named rule STAR rather than re-using MUL because I need the visitor to do something different (drop the WS)
STAR        = "*" WS?
methodCall  = identifier LPAR ( STAR / expressionList )? RPAR
squareBrackets  = identifier (LBRAK expression RBRAK)+

posfixExpr  = methodCall / squareBrackets / primaryExpr

dot         = posfixExpr (DOT posfixExpr)*

factor      = ( PLUS / MINUS / NOT )? dot

prod        = factor ((MUL / DIV) factor )*
sum         = prod ((PLUS / MINUS) prod)*

gt          = sum (( GE / LE / GT / LT ) sum )?
eq          = gt (( EQ / NEQ ) gt )?
and         = eq ( AND eq )?
or          = and ( OR and )?

between     = or ( BETWEEN LPAR or DOTDOT or RPAR )?

stringOp     = between (( 
                    NOTCONTAINS_CS / CONTAINS_CS / NOTCONTAINS /  CONTAINS /
                    NOTSTARTSWITH_CS / NOTSTARTSWITH / STARTSWITH_CS / STARTSWITH /
                    NOTHAS_CS / NOTHAS / HAS_CS / HAS
                    ) between )?

list        = LPAR expressionList RPAR
inList      = stringOp (( NOTIN_CIS / IN_CIS / NOTIN / IN ) (list / stringOp) )?

expression          = inList
expressionList      = expression (COMMA expression)*

internalAssignment  = identifier ASSIGNMENT expression
assignment          = internalAssignment / expression
assignmentList      = assignment (COMMA assignment)*

# Use this root rule if you just want to parse a simple expression
kustoStatement      = WS? assignment

# DEFINE THE KUSTO TABULAR OPERATORS 

BY          = "by" WS
ASC         = ("asc" / "desc") WS?

# todo: top supports nulls first / nulls last
sortColumn  = expression ASC?
sortColumnList = sortColumn (COMMA sortColumn)*
simpleAssignment = identifier ASSIGNMENT identifier
simpleAssignmentList = simpleAssignment (COMMA simpleAssignment)*
columnNameOrPatternList = columnNameOrPattern (COMMA columnNameOrPattern)*

table       = pipe / identifier
joinParameters = "kind" WS? ASSIGNMENT identifier
LEFT        = "$left."
RIGHT       = "$right."
joinAttribute  = (LEFT identifier EQ RIGHT identifier) / (RIGHT identifier EQ LEFT identifier)  / identifier
joinAttributes = joinAttribute (COMMA joinAttribute)*

# tabular operators
take        = "take" WS int
where       = "where" WS expression
extend      = "extend" WS assignmentList
summarize   = "summarize" WS assignmentList ( BY assignmentList )?
sort        = "sort" WS BY sortColumnList
top         = "top" WS int BY sortColumnList
project     = "project" WS assignmentList
projectAway = "project-away" WS columnNameOrPatternList
projectKeep = "project-keep" WS columnNameOrPatternList
projectReorder = "project-reorder" WS columnNameOrPatternList
projectRename = "project-rename" WS simpleAssignmentList
distinct    = "distinct" WS (STAR / assignmentList)
count       = "count" WS?
getschema   = "getschema" WS?
as          = "as" WS identifier
join        = "join" WS joinParameters? LPAR table RPAR "on" WS joinAttributes


tabularOperator = take / where / extend / summarize / sort / top / projectAway / projectKeep / projectReorder / projectRename / project / distinct / count / getschema / as / join

# use this root rule if you want to parse a full Kusto statement
kustoTabularOperator  = WS? tabularOperator

# DEFINE KUSTO FULL QUERIES

PIPE        = "|" WS?
SEMICOLON   = ";" WS?
LET         = "let" WS

pipe        = identifier (PIPE tabularOperator)+
let         = LET identifier ASSIGNMENT expression
letTable    = LET identifier ASSIGNMENT table


queryStatement = letTable / let / pipe
queryStatements = queryStatement (SEMICOLON queryStatement)* 

kustoQuery  = WS? queryStatements SEMICOLON?

"""

class Visitor(NodeVisitor):
    def __init__(self):
        # WS is the second child, we should ignore it
        # self.visit_LPAR = self.lift_first_of_two_children
        # self.visit_RPAR = self.lift_first_of_two_children
        # self.visit_PLUS = self.lift_first_of_two_children
        # self.visit_MINUS = self.lift_first_of_two_children
        # self.visit_MUL = self.lift_first_of_two_children
        # self.visit_DIV = self.lift_first_of_two_children
        # self.visit_NOT = self.lift_first_of_two_children

        # self.visit_GT = self.lift_first_child_of_two
        # self.visit_LT = self.lift_first_child_of_two
        # self.visit_GE = self.lift_first_child_of_two
        # self.visit_LE = self.lift_first_child_of_two
        # self.visit_EQ = self.lift_first_child_of_two
        # self.visit_NEQ = self.lift_first_child_of_two
        # self.visit_AND = self.lift_first_child_of_two
        # self.visit_OR = self.lift_first_child_of_two

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
        self.visit_expressionList = self._visit_list_with_at_least_one
        self.visit_assignmentList = self._visit_list_with_at_least_one

        self.visit_sum = self._visit_binary_op_zero_or_more
        self.visit_prod = self._visit_binary_op_zero_or_more
        self.visit_gt = self._visit_binary_op_optional
        self.visit_eq = self._visit_binary_op_optional
        self.visit_and = self._visit_binary_op_optional
        self.visit_or = self._visit_binary_op_optional
        self.visit_stringOp = self._visit_binary_op_optional
        self.visit_inList = self._visit_binary_op_optional

        self.visit_dot = self._visit_binary_op_zero_or_more

        self.visit_kustoQuery = self.lift_second_of_three_children
        self.visit_kustoTabularOperator = self.lift_second_of_two_children
        self.visit_kustoStatement = self.lift_second_of_two_children

        self.visit_ASC = self.lift_first_of_two_children
        self.visit_STAR = self.lift_first_of_two_children

    def visit_WS(self, node, children):
        return None

    def generic_visit(self, node, children):
        if node.text == "":
            # non-matched optional node
            return None
        if len(children) == 0:
            # raw match, e.g. "+" from  ("+" / "-")
            return node.text
        if len(children) == 1:
            if isinstance(node.expr, parsimonious.expressions.ZeroOrMore) or isinstance(node.expr, parsimonious.expressions.OneOrMore):
                # for consistency this should always return a list even if there was only one match
                return children
            # pass through node
            return children[0]
        
        return children

    def lift_second_of_three_children(self, node, children):
        _, child, _ = children
        return child

    def lift_second_of_two_children(self, node, children):
        _, child = children
        return child
    
    def lift_first_of_two_children(self, node, children):
        child, _ = children
        return child

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
        (unary_op, _), right = children
        if "-" == unary_op:
            return UnaryMinus(right)
        if "not" == unary_op:
            return UnaryNot(right)
        # can be "+"
        return right
    
    def visit_expressionInParens(self, node, children):
        # ignore parentheses at index 0 and 2
        return children[1]
    
    def _visit_binary_op_generic(self, node, children, zero_or_more):
        left, optional_part = children
        if optional_part is None:
            return left

        if not zero_or_more:
            optional_part = [optional_part]

        for match in optional_part:
            (opstr, _), right = match
            op = all_operators_dict[opstr]
            # todo: refactor this.  ambiguous operators were only necessary with the custom parser
            if op == AmbiguousMinus or op == AmbiguousStar:
                op = op.binary
            
            operator = op(left, right)

            left = operator

        return left

    def _visit_binary_op_optional(self, node, children):
        # gt (( EQ / NEQ ) gt )?
        return self._visit_binary_op_generic(node, children, False)

    def _visit_binary_op_zero_or_more(self, node, children):
        # prod ((PLUS / MINUS) prod)*
        return self._visit_binary_op_generic(node, children, True)
    
    def visit_internalAssignment(self, node, children):
        return Assignment(children[0], children[2])
    
    def visit_between(self, node, children):
        left, optional = children
        if optional is None:
            return left

        # optional:   BETWEEN LPAR or DOTDOT or RPAR
        _, _, first, _, second, _ = optional
        
        # todo: refactor. there is no need for DotDot here
        dotdot = DotDot(first, second)
        return Between(left, dotdot)

    def _visit_list_with_at_least_one(self, node, children):
        first, rest = children
        result = [first]
        if rest is not None:
            # take only the values and drop the commas
            result += [value for (_, value) in rest]
        return result

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
        left, in_brackets = children
        for match in in_brackets:
            _, right, _ = match
            left = SquareBrackets(left, right)
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
        var, optional_asc = children
        
        asc = optional_asc == "asc"
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
    
    def visit_count(self, node, children):
        return Count()
    
    def visit_getschema(self, node, children):
        return GetSchema()
    
    def visit_pipe(self, node, children):
        start, right_expression = children

        tabular_operators = [TableIdentifier(start)]
        tabular_operators += [op for _, op in right_expression]

        return Pipe(tabular_operators)
    
    def visit_as(self, node, children):
        # "as" WS identifier
        _, _, identifier = children
        return As(identifier)
    
    def visit_joinParameters(self, node, children):
        #= "kind" WS ASSIGNMENT identifier
        _, _, _, joinKind = children
        return dict(kind=str(joinKind))

    def visit_joinAttribute(self, node, children):
        # (LEFT identifier EQ RIGHT identifier) / (RIGHT identifier EQ LEFT identifier)  / identifier
        val, = children
        attributes = dict()
        if isinstance(val, Var):
            # I could also use just the "on" parameter, but this is more convenient for merging multiple join conditions because of
            # pandas.errors.MergeError: Can only pass argument "on" OR "left_on" and "right_on", not a combination of both 
            attributes["left_on"] = [str(val)]
            attributes["right_on"] = [str(val)]
        else:
            lr1, var1, _, lr2, var2 = val
            if "left" in str(lr1):
                attributes["left_on"] = [str(var1)]
                attributes["right_on"] = [str(var2)]
            else:
                attributes["left_on"] = [str(var2)]
                attributes["right_on"] = [str(var1)]
        return attributes

    def _merge_join_on_dicts(self, a1, a2):
        for k, v in a2.items():
            # the key should always be there
            a1[k] += v
        return a1

    def visit_joinAttributes(self, node, children):
        # joinAttribute (COMMA joinAttribute)*
        a1, rest = children
        attributes = a1.copy()
        if rest is not None:
            for _, more in rest:
                attributes = self._merge_join_on_dicts(attributes, more)
        return attributes
    
    def visit_table(self, node, children):
        table, = children
        if isinstance(table, Var):
            return TableIdentifier(str(table))
        return table

    def visit_join(self, node, children):
        # "join" WS joinParameters? LPAR table RPAR "on" WS joinAttributes
        _, _, params, _, right, _, _, _, attributes = children
        kwargs = attributes.copy()
        if params is not None:
            kwargs.update(params)
        return Join(right, kwargs)

    def visit_let(self, node, children):
        # LET identifier ASSIGNMENT expression
        _, left, _, right = children
        return Let(left, right)

    def visit_letTable(self, node, children):
        # LET identifier ASSIGNMENT table
        _, left, _, right = children
        return LetTable(left, right)
    
    def visit_queryStatements(self, node, children):
        first, rest = children
        statements = [first]
        if rest is not None:
            for _, right in rest:
                statements.append(right)
        
        return Query(statements)


_PARSER = dict()

def get_parser(root, debug=False):
    if not root in _PARSER:
        g = Grammar(kusto_peg)
        _PARSER[root] = g.default(root)

    return _PARSER[root]

def parse_expression(input, debug=True, root="kustoStatement"):
    parser = get_parser(root, debug=False)

    if debug:
        print("input string: ", input)

    parse_tree = parser.parse(input)

    if debug:
        print()
        print("Printing the parse tree")
        print(str(parse_tree))

    visitor = Visitor()
    expression_tree = visitor.visit(parse_tree)
    if debug:
        print()
        print("The parsed expression")
        print(str(expression_tree))

    return expression_tree

def parse_expression_tabular_operator(input, debug=False):
    return parse_expression(input, debug=debug, root="kustoTabularOperator")

def parse_expression_query(input, debug=False):
    return parse_expression(input, debug=debug, root="kustoQuery")
