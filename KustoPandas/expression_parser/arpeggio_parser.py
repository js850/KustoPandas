import arpeggio
from arpeggio.peg import ParserPEG


from KustoPandas.expression_parser.expression_parser_types import *


kusto_peg = r"""

number      <- r'\d*\.\d*|\d+';
identifier  <- r'[a-zA-Z_][a-zA-Z0-9_]*';
stringLiteral <- ( r'"[^"]*"' / r'\'[^\']*\'' );
timespanLiteral <- r'[1-9]\d*[dhms]';

primaryExpr <- ( timespanLiteral / number / identifier / stringLiteral / "(" assignment ")" );

args        <- assignment ("," assignment)*;
methodCall  <- identifier "(" args? ")";
posfixExpr  <- methodCall / primaryExpr;

factor      <- ( "+" / "-" )?  posfixExpr;

prod        <- factor  (("*" / "/") factor )*;
sum         <- prod  (("+" / "-") prod )*;

gt          <- sum (( ">=" / "<=" / ">" / "<" ) sum )*;
eq          <- gt (( "==" / "!=" ) gt )*;
and         <- eq (("and") eq )*;
or          <- and ("or" and )*;

stringOp    <- or (( "contains_cs" / "!contains_cs" / "contains" / "!contains" /
                     "startswith_cs" / "!startswith_cs" / "startswith" / "!startswith" /
                     "has_cs" / "!has_cs" / "has" / "!has"
                    ) or )*;

assignment  <- identifier "=" assignment / stringOp;

kusto       <- assignment EOF;

"""

class Visitor(arpeggio.PTNodeVisitor):
    def visit_number(self, node, children):
        try:
            int(node.value)
            return Int(node.value)
        except:
            return Float(node.value)
    
    def visit_identifier(self, node, children):
        return Var(node.value)

    def visit_stringLiteral(self, node, children):
        # remove the enclosing quotes
        return StringLiteral(node.value[1:-1])

    def visit_timespanLiteral(self, node, children):
        num = node.value[:-1]
        unit = node.value[-1]
        return TimespanLiteral(Int(num), unit)

    def visit_factor(self, node, children):
        if self.debug:
            print("DEBUG VISIT", node.value)
        if "-" in children:
            return UnaryMinus(children[-1])
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

    def visit_stringOp(self, node, children):
        return self._visit_binary_op(node, children)

    def visit_args(self, node, children):
        return Args(list(children))

    def visit_methodCall(self, node, children):
        method = children[0] 
            
        if len(children) < 2:
            args = Args([])
        else:
            args = children[1]
        
        return Method(method, args)

# it's a list so I can modify it
_PARSER = []

def get_parser(debug=False):
    if not _PARSER:
        _PARSER.append(ParserPEG(kusto_peg, "kusto", debug=debug))
    return _PARSER[0]

def parse_expression(input, debug=True):
    parser = get_parser(debug=True)

    parse_tree = parser.parse(input)

    if debug:
        print(str(parse_tree))
        print(parse_tree.__repr__())
        print(parse_tree.tree_str())

    expression_tree = arpeggio.visit_parse_tree(parse_tree, Visitor(debug))
    if debug:
        print(str(expression_tree))
    return expression_tree

