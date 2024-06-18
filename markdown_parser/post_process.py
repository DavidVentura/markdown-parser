from dataclasses import dataclass
from typing import TypeVar
from markdown_parser.lifter import pop, lift, HTMLNode
from markdown_parser.nodes import Node, Heading, KV
from markdown_parser.renderer import render
from markdown_parser.parser import make_parser
from markdown_parser.processor import Processor

# HTML level can add attributes such as `id` for anchors/headings
# but HTML level loses certain abstractions -- the RefBlock is just hr div ol li li ..
# and what about codeblocks, getting per-line metadata

# -> wrap on the AST (node) level with specialized nodes (CodeLine, HeadingAnchor)
# -> then renderer can 'special-case' them
# -> could be part of 'extensions'
# -> can parser (syntax) extensions be implemented?

# what about global hooks? eg: asciinema. it could be a directive, but still needs "global" level?
# - the <script> tag could be inserted after the body
T = TypeVar("T", bound=Node)
U = TypeVar("U", bound=Node)

@dataclass
class HeadingAnchor(Node):
    heading: Heading

class InsertHeadingAnchors(Processor[Heading, HeadingAnchor]):
    def __init__(self):
        self.process_type = Heading
        self.render_type = HeadingAnchor

    @staticmethod
    def transform(node: Heading) -> list[HeadingAnchor]:
        return [HeadingAnchor(node)]

    @staticmethod
    def render(node: HeadingAnchor) -> list[HTMLNode]:
        # TODO: need to recursively walk a Node and get its PlainText
        pt = ["todo-id"]
        props = [KV("id", "-".join(pt))]
        return [HTMLNode("a", render([node.heading]), props)]


def postprocess(items: list[Node], rules: list[Processor]) -> list[HTMLNode]:
    ret = []
    while item := pop(items):
        matched = False
        for r in rules:
            if not isinstance(item, r.process_type):
                continue
            ret.extend(r.transform(item))
            matched = True
        if not matched:
            pass
            # ret.append(item)
    return ret


if __name__ == "__main__":
    parser = make_parser()
    text = open('../blog/blog/raw/cursed-vdso/POST.md').read()
    i = parser.parse(text)
    l = lift(i)
    a=InsertHeadingAnchors()
    p = postprocess(l, [a])
    print(p)
    r = render(p, [a])
    print('rend', r)
