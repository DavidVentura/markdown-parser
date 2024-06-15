
from markdown_parser.nodes import *
from markdown_parser.parser import make_parser
from markdown_parser.lifter import lift, pop, QuoteBlock, FullQuote, Paragraph, HTMLNode
from typing import TypeVar

T = TypeVar('T')

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
                props = [KV("src", item.url)]
                if item.alt:
                    props.append(KV("alt", item.alt))
                ret.append(HTMLNode("img", [], props))
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
            case HTMLNode():
                ret.append(HTMLNode(item.tag, render(item.children), item.props))
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
