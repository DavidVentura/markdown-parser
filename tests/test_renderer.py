from markdown_parser.lifter import lift
from markdown_parser.renderer import render

def test_simple_render(parser):
    text = "text **bold _emp_ bold**"
    i = parser.parse(text)
    l = lift(i)
    r = render(l)
    assert r == ['text ', '<b>', 'bold ', '<em>', 'emp', '</em>', ' bold', '</b>']

def test_quotes(parser):
    text = """
> quote1
>> quote nested1
>> quote nested2
"""
    i = parser.parse(text)
    l = lift(i)
    r = render(l)
    assert r == ['<blockquote>', 'quote1', '<blockquote>', 'quote nested1', '<br/>', 'quote nested2', '</blockquote>', '</blockquote>']
