import arpeggio
from arpeggio.peg import ParserPEG


from kusto_pandas.expression_parser.expression_parser_types import *

from kusto_pandas.expression_parser.tabular_operators import *


kusto_peg = r"""

// DEFINE THE TERMINAL rules.

int         <- r'\d\d*';
float       <- r'\d+\.\d*' /  r'\d*\.\d+';
number      <- float / int;
identifier  <- r'[a-zA-Z_][a-zA-Z0-9_]*';
columnNameOrPattern  <- r'[a-zA-Z0-9_*]*';
stringLiteral <- ( r'"[^"]*"' / r'\'[^\']*\'' );
timespanLiteral <- r'[1-9]\d*[dhms]';

// DEFINE THE GRAMAR OF OPERATORS AND ALGEBREIC EXPRESSIONS
// operator precedence is defined by the chaining of the rules together

// todo:  in c an assignment returns a value, so you can have them be part of the chain of operations e.g. x = 1 + (y = 5) 
// this is not the case in Kusto, I should update it to reflect that.

primaryExpr <- ( timespanLiteral / number / identifier / stringLiteral / "(" assignment ")" );

// todo: you cannot have assignments inside a method call
// generally * is not allowed, but any(*) is an exception.  
methodCall  <- identifier "(" ( "*" / assignmentList )? ")";
squareBrackets  <- identifier ("[" assignment "]")+;

posfixExpr  <- methodCall / squareBrackets / primaryExpr;

dot         <- posfixExpr ("." posfixExpr)*;

factor      <- ( "+" / "-" / "not" )?  dot;

prod        <- factor  (("*" / "/") factor )*;
sum         <- prod  (("+" / "-") prod )*;

gt          <- sum (( ">=" / "<=" / ">" / "<" ) sum )?;
eq          <- gt (( "==" / "!=" ) gt )?;
and         <- eq (("and") eq )?;
or          <- and ("or" and )?;

between     <- or ( "between" "(" or ".." or ")" )?;

stringOp    <- between (( "contains_cs" / "!contains_cs" / "contains" / "!contains" /
                     "startswith_cs" / "!startswith_cs" / "startswith" / "!startswith" /
                     "has_cs" / "!has_cs" / "has" / "!has"
                    ) between )?;

list        <- "(" assignmentList ")";
inList      <- stringOp ("in~" / "!in~" / "!in" / "in" ) (list / stringOp) / stringOp;

assignment  <- identifier "=" inList / inList;
assignmentList      <- assignment ("," assignment)*;

// Use this root rule if you just want to parse a simple expression
kustoStatement  <- assignment EOF;

// DEFINE THE KUSTO TABULAR OPERATORS 
asc         <- "asc" / "desc";
sortColumn  <- stringOp asc?;
simpleAssignment <- identifier "=" identifier;

take        <- "take" int;
where       <- "where" inList;
extend      <- "extend" assignmentList;
summarize   <- "summarize" assignmentList ( "by" assignmentList )?;
sort        <- "sort" "by" sortColumn ("," sortColumn)*;
top         <- "top" int "by" sortColumn ("," sortColumn)*;
project     <- "project" assignmentList;
projectAway <- "project-away" columnNameOrPattern ("," columnNameOrPattern)*;
projectKeep <- "project-keep" columnNameOrPattern ("," columnNameOrPattern)*;
projectReorder <- "project-reorder" columnNameOrPattern ("," columnNameOrPattern)*;
projectRename <- "project-rename" simpleAssignment ("," simpleAssignment)*;
distinct    <- "distinct" ("*" / assignmentList);

tabularOperator <- take / where / extend / summarize / sort / top / projectAway / projectKeep / projectReorder / projectRename / project / distinct;

// use this root rule if you want to parse a full Kusto statement
kusto       <- tabularOperator EOF;

"""

class Visitor(arpeggio.PTNodeVisitor):
    def visit_int(self, node, children):
        return Int(node.value)
        
    def visit_float(self, node, children):
        return Float(node.value)

    def visit_identifier(self, node, children):
        return Var(node.value)
    
    def visit_columnNameOrPattern(self, node, children):
        return ColumnNameOrPattern(node.value)

    def visit_stringLiteral(self, node, children):
        # remove the enclosing quotes
        return StringLiteral(node.value[1:-1])

    def visit_timespanLiteral(self, node, children):
        num = node.value[:-1]
        unit = node.value[-1]
        return TimespanLiteral(Int(num), unit)

    def visit_factor(self, node, children):
        if "-" in children:
            return UnaryMinus(children[-1])
        elif "not" in children:
            return UnaryNot(children[-1])
        return children[-1]
    
    def visit_add(self, node, children):
        return node.value
    
    def _visit_binary_op(self, node, children):
        if len(children) == 1:
            return children[0]

        left = children[0]

        for o, right in zip(children[1::2], children[2::2]):
            op = all_operators_dict[o]
            if op == AmbiguousMinus or op == AmbiguousStar:
                op = op.binary
            
            operator = op(left, right)

            left = operator

        return left
    
    def _visit_binary_op_single(self, node, children, op):
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
        if len(children) == 1:
            return children[0]
        
        # todo: refactor. there is no need for DotDot here
        dotdot = DotDot(children[1], children[2])
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
        _PARSER[root] = ParserPEG(kusto_peg, root, debug=debug)

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
        print(parse_tree.tree_str())

    expression_tree = arpeggio.visit_parse_tree(parse_tree, Visitor(debug=debug))
    if debug:
        print(str(expression_tree))

    return expression_tree

def parse_expression_tabular_operator(input, debug=False):
    return parse_expression(input, debug=debug, root="kusto")

