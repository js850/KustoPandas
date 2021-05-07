import os, sys
from context import Wrap

import pandas as pd

# hack to avoid having to add the dependency to the package until it's ready
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../KustoPandas/expression_parser')))

from parsimonious_parser import parse_expression, parse_expression_tabular_operator
import KustoPandas.expression_parser.expression_parser_types as ept

def parse_and_visit(input, vars=None):
    expression_tree = parse_expression(input, debug=True)
    result = expression_tree.evaluate(vars)
    return result

def test_int():
    assert 10 == parse_and_visit("10")
    assert isinstance(parse_expression("10"), ept.Int)

def test_int0():
    assert 0 == parse_and_visit("0")

def test_int_ws():
    assert 10 == parse_and_visit("10 ")
    assert 10 == parse_and_visit(" 10")
    assert 10 == parse_and_visit("10   ")

def test_int_ws2():
    assert 10 == parse_and_visit("   10   ")

def test_float():
    assert 1 == parse_and_visit("1.")
    assert .1 == parse_and_visit(".1")
    assert 1.1 == parse_and_visit("1.1")
    assert 111.1111 == parse_and_visit("111.1111")

def test_float_exponent():
    assert 2 == parse_and_visit("2e0")
    assert 20 == parse_and_visit("2e1")
    assert 20 == parse_and_visit("2E1")
    assert 2e10 == parse_and_visit("2E10")
    assert 2e1 == parse_and_visit("2.E+1")
    assert 2.1e1 == parse_and_visit("2.1E+1")
    assert 2.1e-1 == parse_and_visit("   2.1E-1   ")
    assert .21e2 == parse_and_visit(".21e2")

def test_factor():
    assert -10 == parse_and_visit("-10")
    assert 10 == parse_and_visit("10")
    assert 10 == parse_and_visit("+10")

def test_factor2():
    assert 10 == parse_and_visit("+ 10")
    assert -10 == parse_and_visit(" - 10.0 ")

def test_parens():
    assert 2 == parse_and_visit("(2)")
    assert 2 == parse_and_visit(" ( 2 ) ")

def test_add():
    assert 2 == parse_and_visit("1 + 1")
    assert 2 == parse_and_visit("1+1")
    assert 2 == parse_and_visit(" 1 + 1 ")
    assert 0 == parse_and_visit("1 - 1")
    assert 0 == parse_and_visit("1    -    1")

def test_add_parens():
    assert 2 == parse_and_visit("1 + (1)")
    assert -1 == parse_and_visit("-2 - (-1)")

def test_add2():
    assert 5 == parse_and_visit("1 + 1 + 1 + 1 + 1")
    assert 1 == parse_and_visit("1 + (1 - 1)")
    assert 1 == parse_and_visit("((1 + 1) - 1)")

def test_prod():
    assert 2 == parse_and_visit("1 * 2")
    assert 2 == parse_and_visit("4/2")

def test_prod2():
    assert 24 == parse_and_visit("1 * 2 * 3 * 4")
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
    assert 4 == parse_and_visit("x_1 + y0f", dict(x_1=1, y0f=3))

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

def test_method_call():
    assert 3 == parse_and_visit("y = x(2)", dict(x=lambda k: k+1))["y"]

def test_method_call2():
    def x(a, b):
        return a - b
    assert -1 == parse_and_visit("y = x(2, 3)", dict(x=x))["y"]

def test_method_call3():
    def x(a, b, c):
        return a - b + c
    assert 6 == parse_and_visit("y = x (2, 3, 7)", dict(x=x))["y"]

def test_method_call_any_star():
    parsed = parse_expression("a = any(* )")
    assert "(a = any(*))" == str(parsed)

def test_method_call0():
    def x():
        return 7
    assert 7 == parse_and_visit("y = x()", dict(x=x))["y"]

def test_timespaneLiteral():
    assert pd.to_timedelta("1d") == parse_and_visit("1d")

def test_timespaneLiteral2():
    result = parse_and_visit("y = C + 1d", dict(C=pd.to_datetime("2020-01-02")))
    assert pd.to_datetime("2020-01-03") == result["y"]

def test_in():
    assert True == parse_and_visit('"hi" in ("hi", "there")')
    assert False == parse_and_visit('"hi" in ("Hi", "there")')
    assert False == parse_and_visit('"hi" in ("hid", "there")')
    assert True == parse_and_visit('"hi" !in ("hid", "there")')

def test_in_notcs():
    assert True == parse_and_visit('"hi" in~ ("Hi", "there")')
    assert False == parse_and_visit('"hi" in~ ("hid", "there")')
    assert False == parse_and_visit('"hi" !in~ ("Hi", "there")')

def test_project_away():
    parsed = parse_expression_tabular_operator("project-away B")
    assert parsed is not None

def test_square_brackets():
    assert 7 == parse_and_visit("d['k2']", dict(d={"k2": 7}))

def test_square_brackets_twolevel():
    d = dict(k1=dict(k2=dict(k3="val")))
    assert "val" == parse_and_visit("d[ 'k1'] ['k2' ]['k3']", dict(d=d))

def test_square_brackets_extend_twolevel():
    parsed = parse_expression_tabular_operator("extend D = d['k2']['k3']")
    assert parsed is not None

def test_square_brackets_extend():
    parsed = parse_expression_tabular_operator("extend D = d['k2']")
    assert parsed is not None

def test_between():
    assert True == parse_and_visit('1 between (0 .. 2)')
    assert True == parse_and_visit('1 between ( 1 .. 2 )')
    assert True == parse_and_visit('2 between ( 1 .. 2 )')
    assert False == parse_and_visit('-1 between ( 1 .. 2 )')

def test_datetime_literal():
    assert pd.to_datetime("2014-11-08") == parse_and_visit('datetime(2014-11-08)')
    assert pd.to_datetime("2014-05-25T08:20:03.123456Z") == parse_and_visit('datetime(2014-05-25T08:20:03.123456Z)')
    assert pd.to_datetime("2014-11-08 15:55") == parse_and_visit('datetime(2014-11-08 15:55)')

def test_datetime_literal_in_method():
    assert "2014-11-08 00:00:00" == parse_and_visit('str(datetime(2014-11-08))', vars={"str": str})

def test_mod():
    assert 1 == parse_and_visit("7 % 3")

def test_mod_series():
    a = pd.Series([7, 7, 11])
    b = pd.Series([3, 6, 4])
    s = parse_and_visit("a % b", vars=dict(a=a, b=b))
    assert [1, 1, 3] == list(s)

# def test_mod_series_dt():
#     a = pd.to_datetime(pd.Series(["2021-04-04T09:43:37.2284308Z", "2021-04-04T09:44:37.2284308Z"]))
#     s = parse_and_visit("a % 1h", vars=dict(a=a))
#     assert [pd.Timedelta("00:43:37.228430800"), pd.Timedelta("00:44:37.228430800")] == list(s)

# def test_mod_dt():
#     a = pd.to_datetime("2021-04-04T09:43:37.2284308Z")
#     assert pd.Timedelta("00:43:37.228430800") == parse_and_visit("a % 1h", vars=dict(a=a))

# def test_mod_dt2():
#     assert pd.Timedelta("00:43:37") == parse_and_visit("datetime(2021-04-04T09:43:37) % 1h")

def test_mod_timedelta():
    a = pd.to_timedelta("00:43:37.228430800")
    assert pd.Timedelta("00:03:37.228430800") == parse_and_visit("a % 10m", vars=dict(a=a))

def test_contains_or():
    # TODO; this fails to parse, I think because contains and or do not have the right priority
    assert True == parse_and_visit("'cppt' contains 'ppt' or 'asdf' contains 'docx'")

def test_dynamic_literal_list():
    assert [1, 2] == parse_and_visit("dynamic([1, 2])")

def test_dynamic_literal_bag():
    assert dict(k=1, k2=2, k3="hello", k4=[1, 2]) == parse_and_visit("""dynamic({"k": 1, "k2":2, "k3": "hello", "k4": [1, 2]})""")

def test_comment_int():
    assert 1 == parse_and_visit("1 # comment ")

def test_comment_multiline():
    assert 2 == parse_and_visit("""
    1 
    # comment
    + # c2 
    1 #c3
    # endc 
    """)

def test_comment_float():
    assert 1.1 == parse_and_visit("1.1# comment # se")

def test_comment_identifier():
    assert True == parse_and_visit("1 == x# comment", dict(x=1))

def test_comment_stringLiteral():
    assert True == parse_and_visit("x == 'hi'# comment", dict(x='hi'))

def test_comment_timespaneLiteral():
    assert pd.to_timedelta("1d") == parse_and_visit("1d# comment")
