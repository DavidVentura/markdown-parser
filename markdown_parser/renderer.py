from dataclasses import dataclass
from markdown_parser.nodes import *
from markdown_parser.parser import make_parser
from markdown_parser.lifter import lift, pop, QuoteBlock, FullQuote, Paragraph, HTMLNode, List, FullListItem, RefBlock
from typing import TypeVar

T = TypeVar('T')
U = TypeVar('U')

@dataclass
class TextHTMLNode(HTMLNode):
    text: str = ""

    def __str__(self):
        return self.text

def interleave_1(items: list[T], to_add: U) -> list[T | U]:
    interleaved = [(to_add, item) for item in items]
    flattened = [i for item in interleaved for i in item][1:]  # remove leading to_add
    return flattened

def render(items: Node | list[Node]) -> list[HTMLNode]:
    return _render(items, {})

def _render(items: Node | list[Node], ref_map: dict[str, int]) -> list[HTMLNode]:
    ret: list[HTMLNode] = []
    if isinstance(items, Node):
        items = [items]

    while item := pop(items):
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
                ret.append(HTMLNode(tag_name, _render(item.content, ref_map)))
            case CodeBlock():
                ret.append(HTMLNode("pre", [HTMLNode("code", [TextHTMLNode(tag="", text='\n'.join(item.lines))])]))
            case Image():
                if item.url is None:
                    continue
                props = [KV("src", item.url)]
                if item.alt:
                    props.append(KV("alt", item.alt))
                ret.append(HTMLNode("img", [], props))
            case Anchor():
                ret.append(HTMLNode("a", _render(item.content, ref_map), [KV("href", item.href)]))
            case InlineCode():
                ret.append(HTMLNode("code", [item.text]))
            case ParBreak():
                ret.append(HTMLNode("br"))
            case Paragraph():
                ret.append(HTMLNode("p", _render(item.children, ref_map)))
            case PlainText():
                ret.append(TextHTMLNode(tag="", text=item.text))
            case Bold():
                ret.append(HTMLNode("b", _render(item.content, ref_map)))
            case Emphasis():
                ret.append(HTMLNode("em", _render(item.content, ref_map)))
            case FullQuote():
                ret.extend(_render(item.content, ref_map))
                if item.children:
                    ret.append(HTMLNode("blockquote", _render(interleave_1(item.children, ParBreak()), ref_map)))
            case QuoteBlock():
                ret.append(HTMLNode("blockquote", _render(item.children, ref_map)))
            case HTMLNode():
                ret.append(HTMLNode(item.tag, _render(item.children, ref_map), item.props))
            case List():
                props = []
                tag = ""
                match item.marker:
                    case UnorderedListIndicator():
                        tag = "ul"
                    case OrderedListIndicator():
                        tag = "ol"
                        if item.marker.num > 1:
                            props = [KV("start", str(item.marker.num))]
                ret.append(HTMLNode(tag, _render(item.children, ref_map), props))
            case FullListItem():
                tag = "li"
                all_li_content = item.content
                if item.children:
                    props = []
                    first = item.children[0]
                    assert isinstance(first, FullListItem)
                    match first.marker:
                        case UnorderedListIndicator():
                            ntag = "ul"
                        case OrderedListIndicator():
                            ntag = "ol"
                            if first.marker.num > 1:
                                props = [KV("start", str(first.marker.num))]
                    all_li_content += [HTMLNode(ntag, item.children, props)]
                ret.append(HTMLNode(tag, _render(all_li_content, ref_map)))
            case Ref():
                idx = max(ref_map.values()) if ref_map else 1
                ref_map[item.text] = idx
                a = HTMLNode("a", [TextHTMLNode("", text=str(idx))], props=[KV("href", f"#fn-{idx}")])
                sup = HTMLNode("sup", [a])
                ret.append(sup)
            case RefBlock():
                ret.append(HTMLNode("ol", _render(item.children, ref_map)))
            case RefItem():
                idx = ref_map[item.ref]
                ret.append(HTMLNode("li", _render(item.text, ref_map), props=[KV("id", f"fn-{idx}")]))
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
