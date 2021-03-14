import os, sys
from context import Wrap

# hack to avoid having to add the dependency to the package until it's ready
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../KustoPandas/expression_parser')))

from arpeggio_parser import parse_expression

def parse_and_visit(input, vars=None):
    expression_tree = parse_expression(input, debug=True)
    result = expression_tree.evaluate(vars)
    return result

def test_number():
    assert 10 == parse_and_visit("10")
    assert 1 == parse_and_visit("1.")
    assert .1 == parse_and_visit(".1")
    assert 1.1 == parse_and_visit("1.1")

def test_factor():
    assert -10 == parse_and_visit("-10")
    assert 10 == parse_and_visit("10")
    assert 10 == parse_and_visit("+10")

def test_add():
    assert 2 == parse_and_visit("1 + 1")
    assert 0 == parse_and_visit("1 - 1")
    assert -1 == parse_and_visit("-2 - (-1)")

def test_add2():
    assert 3 == parse_and_visit("1 + 1 + 1")
    assert 1 == parse_and_visit("1 + (1 - 1)")
    assert 1 == parse_and_visit("((1 + 1) - 1)")

def test_prod():
    assert 2 == parse_and_visit("1 * 2")
    assert 2 == parse_and_visit("4/2")

def test_prod2():
    assert 6 == parse_and_visit("1 * 2 * 3")
    assert 8 == parse_and_visit("4 * 8 / 4")
    assert 8 == parse_and_visit("4 * (8 / 4)")
    assert 8 == parse_and_visit("(4 * 8) / 4")

def test_prod_add():
    assert 7 == parse_and_visit("1 + 2 * 3")
    assert 7 == parse_and_visit("1 + (2 * 3)")
    assert 9 == parse_and_visit("(1 + 2) * 3")
    assert 24 == parse_and_visit("(1 + (14 / 2)) * 3")

def test_gt():
    assert True == parse_and_visit("2 > 1")
    assert False == parse_and_visit("2 > 2")
    assert False == parse_and_visit("2 > 3")

def test_ge():
    assert True == parse_and_visit("2 >= 1")
    assert True == parse_and_visit("2 >= 2")
    assert False == parse_and_visit("2 >= 3")

def test_lt():
    assert False == parse_and_visit("2 < 1")
    assert False == parse_and_visit("2 < 2")
    assert True == parse_and_visit("2 < 3")

def test_le():
    assert False == parse_and_visit("2 <= 1")
    assert True == parse_and_visit("2 <= 2")
    assert True == parse_and_visit("2 <= 3")

def test_parse_parentheses_lt():
    parsed = parse_expression("1 < (6 - 4) ")
    assert str(parsed) == "(1 < (6 - 4))"
    assert True == parsed.evaluate(None)

def test_lt_add():
    parsed = parse_expression("1 < 5 - 6 ")
    assert str(parsed) == "(1 < (5 - 6))"
    assert False == parsed.evaluate(None)

def test_eq():
    assert True == parse_and_visit("1 == 1")
    assert False == parse_and_visit("1 == 2")

def test_ne():
    assert False == parse_and_visit("1 != 1")
    assert True == parse_and_visit("1 != 2")

def test_ne_lt():
    parsed = parse_expression("(3>5)!=(1<4)")
    assert str(parsed) == "((3 > 5) != (1 < 4))"
    assert True == parsed.evaluate(None)

def test_and():
    parsed = parse_expression("3>5 and (1<4)")
    assert str(parsed) == "((3 > 5) and (1 < 4))"
    assert False == parsed.evaluate(None)

def test_or():
    parsed = parse_expression("3==5 or (1<4)")
    assert str(parsed) == "((3 == 5) or (1 < 4))"
    assert True == parsed.evaluate(None)

def test_var():
    parsed = parse_expression("x + 1")
    assert str(parsed) == "(x + 1)"
    assert 3 == parsed.evaluate({"x": 2})

def test_var2():
    assert 4 == parse_and_visit("x + y", dict(x=1, y=3))
    assert True == parse_and_visit("andy and ory", dict(andy=True, ory=True))
    assert 4 == parse_and_visit("_x + y_", dict(_x=1, y_=3))
    assert 4 == parse_and_visit("x_y + y", dict(x_y=1, y=3))
    assert 4 == parse_and_visit("X + x", dict(X=1, x=3))

def test_string_literal():
    assert True == parse_and_visit("x == \"hi\"", dict(x="hi"))
    assert False == parse_and_visit("x == \"hig\"", dict(x="hi"))
    assert True == parse_and_visit("x == \"h'i\"", dict(x="h'i"))

def test_string_literal_singlequote():
    assert True == parse_and_visit("x == 'hi'", dict(x="hi"))
    assert False == parse_and_visit("x == 'hig'", dict(x="hi"))
    assert True == parse_and_visit("x == 'h\"i'", dict(x="h\"i"))

def test_assignment():
    assert 2 == parse_and_visit("x = 2", dict())["x"]

def test_assignment2():
    assert 2 == parse_and_visit("x = y", dict(y=2))["x"]
    assert True == parse_and_visit("x = 1 + 2 == y", dict(y=3))["x"]

def test_contains():
    assert True == parse_and_visit("x contains y", dict(x="hight", y="Hi"))
    assert False == parse_and_visit("x !contains y", dict(x="hight", y="hi"))

def test_contains_cs():
    assert False == parse_and_visit("x contains_cs y", dict(x="hight", y="Hi"))
    assert True == parse_and_visit("x contains_cs y", dict(x="hight", y="hi"))
    assert False == parse_and_visit("x !contains_cs y", dict(x="hight", y="hi"))

def test_startswith():
    assert True == parse_and_visit("x startswith y", dict(x="hight", y="Hi"))
    assert False == parse_and_visit("x !startswith y", dict(x="hight", y="hi"))

def test_startswith_cs():
    assert False == parse_and_visit("x startswith_cs y", dict(x="hight", y="Hi"))
    assert True == parse_and_visit("x startswith_cs y", dict(x="hight", y="hi"))
    assert False == parse_and_visit("x !startswith_cs y", dict(x="hight", y="hi"))

def test_has():
    assert True == parse_and_visit("x has y", dict(x="a hi ght", y="Hi"))
    assert False == parse_and_visit("x has y", dict(x="ahi ght", y="Hi"))
    assert False == parse_and_visit("x has y", dict(x="a hight", y="Hi"))
    assert False == parse_and_visit("x !has y", dict(x="a hi ght", y="hi"))

def test_has_cs():
    assert False == parse_and_visit("x has_cs y", dict(x="a hi ght", y="Hi"))
    assert True == parse_and_visit("x has_cs y", dict(x="a hi ght", y="hi"))
    assert False == parse_and_visit("x !has_cs y", dict(x="a hi ght", y="hi"))