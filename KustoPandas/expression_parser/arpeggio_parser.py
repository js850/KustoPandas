import arpeggio
from arpeggio.peg import ParserPEG


from KustoPandas.expression_parser.expression_parser_types import *


kusto_peg = r"""
number      <- r'\d*\.\d*|\d+';
factor      <- ( "+" / "-" )?  ( number / "(" eq ")" );
prod        <- factor  (("*" / "/") factor )*;
sum         <- prod  (("+" / "-") prod )*;

gt          <- sum (( ">=" / "<=" / ">" / "<" ) sum )*;
eq          <- gt (( "==" / "!=" ) gt )*;

kusto       <- eq EOF;


"""

class Visitor(arpeggio.PTNodeVisitor):
    def visit_number(self, node, children):
        if self.debug:
            print("DEBUG", node.value)
        return Float(node.value)
    
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

    def visit_sum(self, node, children):
        return self._visit_binary_op(node, children)
    
    def visit_prod(self, node, children):
        return self._visit_binary_op(node, children)
    
    def visit_gt(self, node, children):
        return self._visit_binary_op(node, children)

    def visit_eq(self, node, children):
        return self._visit_binary_op(node, children)

def parse_expression(input, debug=True):
    parser = ParserPEG(kusto_peg, "kusto", debug=debug)

    parse_tree = parser.parse(input)

    if debug:
        print(str(parse_tree))
        print(parse_tree.__repr__())
        print(parse_tree.tree_str())

    expression_tree = arpeggio.visit_parse_tree(parse_tree, Visitor(debug))
    return expression_tree

def parse_and_visit(input, debug=True):
    expression_tree = parse_expression(input, debug=debug)

    if debug:
        print(str(expression_tree))

    return expression_tree.evaluate(None)