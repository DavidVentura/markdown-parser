from dataclasses import field, dataclass

from markdown_parser.nodes import *
from markdown_parser.parser import make_parser
from markdown_parser.lifter import lift, pop, QuoteBlock, FullQuote, Paragraph
from typing import TypeVar

T = TypeVar('T')

@dataclass
class HTMLNode:
    tag: str
    children: list['HTMLNode | str'] = field(default_factory=list)
    props: list[KV] = field(default_factory=list)

    @property
    def self_closing(self):
        return self.tag in ['hr', 'img', 'link', 'br']

    def __str__(self):
        props = " ".join(f'{prop.key}={prop.val}' for prop in self.props)
        if props:
            props = " " + props
        if self.self_closing:
            return f'<{self.tag}{props} />'
        children = "".join(str(c) for c in self.children)
        return f'<{self.tag}{props}>{children}</{self.tag}>'

def interleave_1(items: list[T], to_add: T) -> list[T]:
    interleaved = [(to_add, item) for item in items]
    flattened = [i for item in interleaved for i in item][1:]  # remove leading to_add
    return flattened

def render(items: Node | list[Node | str]) -> list[HTMLNode | str]:
    ret: list[HTMLNode | str] = []
    if isinstance(items, Node):
        items = [items]

    while item := pop(items):
        # TODO: list, popover
        match item:
            case Metadata():
                pass
            case Hr():
                ret.append(HTMLNode('hr'))
            # TODO: HtmlOpenTag / HtmlCloseTag have to get lifted
            case HtmlOpenTag():
                props = " ".join(f'{prop.key}={prop.val}' for prop in item.props)
                ret.append(f'<{item.elem_type} {props}>')
            case HtmlCloseTag():
                ret.append(f'</{item.elem_type}>')
            case HtmlSelfCloseTag():
                node = HTMLNode(item.elem_type, [], item.props)
                assert node.self_closing
                ret.append(node)
            case Heading():
                tag_name = "h" + str(item.level)
                ret.append(HTMLNode(tag_name, render(item.content)))
            case CodeBlock():
                ret.append(HTMLNode("pre", [HTMLNode("code", ['\n'.join(item.lines)])]))
            case Image():
                ret.append(HTMLNode("img", [], [KV("src", item.url), KV("alt", item.alt)]))
            case Anchor():
                ret.append(HTMLNode("a", render(item.content), [KV("href", item.href)]))
            case InlineCode():
                ret.append(HTMLNode("code", [item.text]))
            case ParBreak():
                ret.append(HTMLNode("br"))
            case Paragraph():
                ret.append(HTMLNode("p", render(item.children)))
            case PlainText():
                ret.append(item.text)
            case Bold():
                ret.append(HTMLNode("b", render(item.content)))
            case Emphasis():
                ret.append(HTMLNode("em", render(item.content)))
            case FullQuote():
                ret.extend(render(item.content))
                if item.children:
                    ret.append(HTMLNode("blockquote", interleave_1(item.children, ParBreak())))
            case QuoteBlock():
                ret.append(HTMLNode("blockquote", render(item.children)))
            case other:
                print('was other', type(other))

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
