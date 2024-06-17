import pytest
from markdown_parser.lifter import lift
from markdown_parser.renderer import render

def test_simple_render(parser):
    text = "text **bold _emp_ bold**"
    i = parser.parse(text)
    l = lift(i)
    r = render(l)
    assert str(r[0]) == '<p>text <b>bold <em>emp</em> bold</b></p>'

def test_quotes(parser):
    text = """
> quote1
>> quote nested1
>> quote nested2
"""
    i = parser.parse(text)
    l = lift(i)
    r = render(l)
    assert str(r[0]) == '<blockquote>quote1<blockquote>quote nested1<br/>quote nested2</blockquote></blockquote>'

@pytest.mark.parametrize(["data", "expected"], [
    ("* list1\n* list2",'<ul><li>list1</li><li>list2</li></ul>'),
    ("1. list1\n1. list2",'<ol><li>list1</li><li>list2</li></ol>'),
    ("1. list1\n2. list2",'<ol><li>list1</li><li>list2</li></ol>'),
    ("2. list1\n1. list2",'<ol start="2"><li>list1</li><li>list2</li></ol>'),
])
def test_list_flat(parser, data, expected):
    i = parser.parse(data)
    l = lift([i])
    r = render(l)
    assert str(r[0]) == expected

@pytest.mark.parametrize(["data", "expected"], [
    ("* list1\n    * list2",'<ul><li>list1<ul><li>list2</li></ul></li></ul>'),
    ("* list1\n    1. list2",'<ul><li>list1<ol><li>list2</li></ol></li></ul>'),
    ("* list1\n    2. list2",'<ul><li>list1<ol start="2"><li>list2</li></ol></li></ul>'),
])
def test_list_nested(parser, data, expected):
    i = parser.parse(data)
    l = lift([i])
    r = render(l)
    assert str(r[0]) == expected

@pytest.mark.parametrize(["data", "expected"], [
    ("{^hint|content}",'<p><span data-tooltip="content">hint</span></p>'),
])
def test_popover(parser, data, expected):
    i = parser.parse(data)
    l = lift([i])
    r = render(l)
    assert str(r[0]) == expected

def test_footnote_1(parser):
    data = "[^ref]\n\n[^ref]: content"
    expected1 = '<sup><a href="#fn-1" id="fnref-1">1</a></sup>'
    expected2 = '<div class="footnotes"><hr/><ol><li id="fn-1"> content<a href="#fnref-1">↩</a></li></ol></div>'
    i = parser.parse(data)
    l = lift(i)
    r = render(l)
    assert len(r) == 3
    assert str(r[0]) == expected1
    assert str(r[2]) == expected2

def test_footnote_2(parser):
    data = "[^ref][^ref2]\n\n[^ref]: content\n[^ref2]: content2"
    expected1 = '<sup><a href="#fn-1" id="fnref-1">1</a></sup>'
    expected2 = '<div class="footnotes"><hr/><ol><li id="fn-1"> content<a href="#fnref-1">↩</a></li><li id="fn-2"> content2<a href="#fnref-2">↩</a></li></ol></div>'
    i = parser.parse(data)
    l = lift(i)
    r = render(l)
    assert len(r) == 4
    assert str(r[0]) == expected1
    assert str(r[2]) == "<br/>"
    assert str(r[3]) == expected2
