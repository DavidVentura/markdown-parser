from functools import partial
from dataclasses import dataclass
from markdown_parser.nodes import *
from markdown_parser.parser import make_parser
from markdown_parser.lifter import lift, pop, QuoteBlock, FullQuote, Paragraph, HTMLNode, List, FullListItem, RefBlock
from typing import TypeVar

from markdown_parser.processor import Processor

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

def render(items: Node | list[Node], ext: list[Processor] | None = None) -> list[HTMLNode]:
    return _render(items, {}, ext or [])

def _render(items: Node | list[Node], ref_map: dict[str, int], ext: list[Processor]) -> list[HTMLNode]:
    __render = partial(_render, ref_map=ref_map, ext=ext)

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
                ret.append(HTMLNode(tag_name, __render(item.content)))
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
                ret.append(HTMLNode("a", __render(item.content), [KV("href", item.href)]))
            case InlineCode():
                ret.append(HTMLNode("code", [item.text]))
            case ParBreak():
                ret.append(HTMLNode("br"))
            case Paragraph():
                ret.append(HTMLNode("p", __render(item.children)))
            case PlainText():
                ret.append(TextHTMLNode(tag="", text=item.text))
            case Bold():
                ret.append(HTMLNode("b", __render(item.content)))
            case Emphasis():
                ret.append(HTMLNode("em", __render(item.content)))
            case FullQuote():
                ret.extend(__render(item.content))
                if item.children:
                    ret.append(HTMLNode("blockquote", __render(interleave_1(item.children, ParBreak()))))
            case QuoteBlock():
                ret.append(HTMLNode("blockquote", __render(item.children)))
            case HTMLNode():
                ret.append(HTMLNode(item.tag, __render(item.children), item.props))
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
                ret.append(HTMLNode(tag, __render(item.children), props))
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
                ret.append(HTMLNode(tag, __render(all_li_content)))
            case Popover():  # Extension, should it be "pluggable" ?
                h = HTMLNode("span", [TextHTMLNode(tag='', text=item.hint)], [KV("data-tooltip", item.content)])
                ret.append(h)
            case Ref():
                idx = max(ref_map.values()) + 1 if ref_map else 1
                ref_map[item.text] = idx
                a = HTMLNode("a", [TextHTMLNode("", text=str(idx))],
                        props=[KV("href", f"#fn-{idx}"), KV("id", f"fnref-{idx}")])
                sup = HTMLNode("sup", [a])
                ret.append(sup)
            case RefBlock():
                hr = HTMLNode("hr")
                ol = HTMLNode("ol", __render(item.children))
                div = HTMLNode("div", [hr, ol], [KV("class", "footnotes")])
                ret.append(div)
            case RefItem():
                idx = ref_map[item.ref]
                ref_content = item.text
                ref_content += [Anchor([PlainText("↩")], f"#fnref-{idx}")]
                ret.append(HTMLNode("li", __render(ref_content), props=[KV("id", f"fn-{idx}")]))
            case TableCell():
                ret.append(HTMLNode("td", __render(item.content)))
            case TableRow():
                tr = HTMLNode("tr", __render(item.cells))
                ret.append(tr)
            case TableHeaderCell():
                ret.append(HTMLNode("th", __render(item.content)))
            case Table():
                head_tr = HTMLNode("tr", __render(item.header.cells))
                head = HTMLNode("thead", [head_tr])
                rows = []
                for r in item.rows:
                    rows.extend(__render(r))
                ret.append(HTMLNode("table", [head] + rows))
            # Should probably gather sup/sub/small/smaller/bold/em in "style"
            case Superscript():
                ret.append(HTMLNode("sup", __render(item.content)))
            case Subscript():
                ret.append(HTMLNode("sub", __render(item.content)))
            case Smaller():
                ret.append(HTMLNode("smaller", __render(item.content)))
            case Small():
                ret.append(HTMLNode("small", __render(item.content)))
            case other:
                found = False
                for e in ext:
                    if not isinstance(other, e.render_type):
                        continue
                    found = True
                    ret.extend(e.render(other))
                assert found, f"Item type {other} not handled by any extensions"


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
