import os, sys
from context import Wrap

# hack to avoid having to add the dependency to the package until it's ready
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../KustoPandas/expression_parser')))

from arpeggio_parser import parse_and_visit

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