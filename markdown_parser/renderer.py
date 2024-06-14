from markdown_parser.nodes import *
from markdown_parser.parser import make_parser
from markdown_parser.lifter import lift, pop, QuoteBlock, FullQuote, Paragraph
from typing import TypeVar

T = TypeVar('T')

def tag(tag: str, content: list[Node] | Node):
    s = [f'<{tag}>']
    e = [f'</{tag}>']
    if isinstance(content, Node):
        return s + render([content]) + e
    return s + render(content) + e

def interleave_1(items: list[T], to_add: T) -> list[T]:
    interleaved = [(to_add, item) for item in items]
    flattened = [i for item in interleaved for i in item][1:]  # remove leading to_add
    return flattened

def render(items: list[Node]) -> list[str]:
    ret: list[str] = []

    while item := pop(items):
        to_add = []
        match item:
            case ParBreak():
                to_add = ['<br/>']
            case Paragraph():
                to_add = tag("p", item.children)
            case PlainText():
                to_add = [item.text]
            case Bold():
                to_add = tag("b", item.content)
            case Emphasis():
                to_add = tag("em", item.content)
            case FullQuote():
                to_add = render(item.content)
                if item.children:
                    # children should be br-separated?
                    to_add += tag("blockquote", interleave_1(item.children, ParBreak()))
                pass
            case QuoteBlock():
                to_add = tag("blockquote", item.children)
            case other:
                print('was other', type(other))
        ret.extend(to_add)

    return ret

if __name__ == "__main__":
    parser = make_parser()
    text = """
> quote1
>> quote nested1
>> quote nested2
"""
    # text = "text **bold _emp_ bold**"
    i = parser.parse(text)
    l = lift(i)
    r = render(l)
    print(r)
    print('\n'.join(r))
