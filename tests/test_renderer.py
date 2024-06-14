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
