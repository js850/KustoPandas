import json
import os

import parsimonious
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from kusto_pandas.expression_parser.expression_parser_types import *

from kusto_pandas.expression_parser.tabular_operators import *


# Define the grammar of the Kusto language using the PEG format.
# Then use a PEG parser compiler to parse the kusto language text
# https://en.wikipedia.org/wiki/Parsing_expression_grammar
# good tutorial https://tomassetti.me/parsing-in-python/
# Guido van Rossum's PEG blog https://medium.com/@gvanrossum_83706/peg-parsing-series-de5d41b2ed60

# NOTE: The official Kusto grammar is defined here:
# https://github.com/microsoft/Kusto-Query-Language/blob/master/src/Kusto.Language/Parser/QueryGrammar.cs
# and the Tokenizer is here: 
# https://github.com/microsoft/Kusto-Query-Language/blob/master/src/Kusto.Language/Parser/TokenParser.cs


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

        # self.visit_dot = self._visit_binary_op_zero_or_more

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
        return Int(node.children[0].text)
        
    def visit_float(self, node, children):
        return Float(node.children[0].text)

    def visit_quotedIdentifierDq(self, node, children):
        return Var(node.children[1].text, is_quoted=True)
    
    def visit_quotedIdentifierSq(self, node, children):
        return Var(node.children[1].text, is_quoted=True)

    def visit_identifierUnquoted(self, node, children):
        return Var(node.text)
    
    def visit_identifier(self, node, children):
        return children[0]

    def visit_explicitLiteral(self, node, children):
        # "datetime" WS? LPAR datetimeIso6801 RPAR
        literal_type, _, _, string_value, _ = children
        literal_class = explicit_literal_map[literal_type]
        return literal_class(string_value, is_explicit=True)
    
    def visit_columnNameOrPattern(self, node, children):
        return ColumnNameOrPattern(node.children[0].text)

    def visit_stringLiteralDoubleQuote(self, node, children):
        stringLiteral = node.children[1].text
        stringLiteral = stringLiteral.replace('\\"', '"')
        return StringLiteral(stringLiteral)
    
    def visit_stringLiteralSingleQuote(self, node, children):
        stringLiteral = node.children[1].text
        stringLiteral = stringLiteral.replace("\\'", "'")
        return StringLiteral(stringLiteral)

    def visit_timespanLiteral(self, node, children):
        text = node.children[0].text
        return TimespanLiteral(text)

    def visit_unaryOp(self, node, children):
        # ( PLUS / MINUS )? dot
        optional, right = children
        if optional is None:
            return right
        unary_op, _ = optional
        if "-" == unary_op:
            return UnaryMinus(right)
        # no need to do anything for unary "+"
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
    
    def visit_betweenOperand(self, node, children):
        # LPAR sum DOTDOT sum RPAR
        _, first, _, second, _ = children
        return DotDot(first, second)

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
    
    def visit_dotOperand(self, node, children):
        # LDOT posfixExpr
        _, expr = children
        return Dot, expr

    def visit_squareBracketsRight(self, node, children):
        # LBRAK expression RBRAK
        _, expr, _ = children
        return SquareBrackets, expr
    
    def visit_dot(self, node, children):
        left, optional = children
        if optional is None:
            return left
        
        for op, right in optional:
            left = op(left, right)
        return left

    def visit_list(self, node, children):
        return ListExpression(children[1])
    
    def visit_blobLiteralRaw(self, node, children):
        return StringLiteral(node.text)

    def visit_blobLiteral(self, node, children):
        # children[0] is a StringLiteral
        string_val = children[0].evaluate(dict())
        return string_val
    
    def visit_dynamicLiteral(self, node, children):
        # "dynamic" WS? LPAR blobLiteral RPAR
        _, _, _, internal, _ = children
        return DynamicLiteral(internal)
        
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
    
    def visit_union(self, node, children):
        #"union" WS joinParameters? table (COMMA table)*
        _, _, params, table1, other_tables = children
        kwargs = dict()
        if params is not None:
            kwargs.update(params)
        
        tables = [table1]
        
        if other_tables is not None:
            for _, t in other_tables:
                tables.append(t)
        
        return Union(tables, kwargs)


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

def _get_grammar():
    kusto_peg_file = os.path.join(os.path.dirname(__file__), 'kusto_grammar.peg')
    with open(kusto_peg_file) as fin:
        kusto_peg = fin.read()
    return kusto_peg

def get_parser(root):
    if not root in _PARSER:
        kusto_peg = _get_grammar()
        g = Grammar(kusto_peg)
        _PARSER[root] = g.default(root)

    return _PARSER[root]

def parse_expression(input, debug=True, root="kustoStatement"):
    parser = get_parser(root)

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
