import os, sys
from context import Wrap

# hack to avoid having to add the dependency to the package until it's ready
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../KustoPandas/expression_parser')))

from arpeggio_parser import parse_and_visit, parse_expression

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
    str(parsed) == "(1 < (6 - 4))"
    True == parsed.evaluate(None)

def test_lt_add():
    parsed = parse_expression("1 < 5 - 6 ")
    str(parsed) == "(1 < (5 - 6))"
    False == parsed.evaluate(None)