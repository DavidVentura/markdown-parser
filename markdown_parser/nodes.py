from dataclasses import dataclass

@dataclass
class Node:
    pass

@dataclass
class PlainText(Node):
    text: str

@dataclass
class Bold(Node):
    content: list[Node]

@dataclass
class Emphasis(Node):
    content: list[Node]

@dataclass
class Anchor(Node):
    text: str | None
    href: str | None

@dataclass
class Image(Node):
    alt: list[Node]
    url: str

@dataclass
class Quote(Node):
    content: list[Node]

@dataclass
class CodeBlock(Node):
    identifier: str | None
    lines: list[str]

@dataclass
class InlineCode(Node):
    text: str

@dataclass
class Table(Node):
    cells: list[Node]

@dataclass
class ListItem(Node):
    content: list[Node]
    indentation: int

@dataclass
class UnorderedList(Node):
    items: list[ListItem]

# Extensions
@dataclass
class Ref(Node):
    text: str

@dataclass
class RefItem(Node):
    ref: str
    text: str

@dataclass
class CustomDirective(Node):
    name: str
    arguments: list[str]

@dataclass
class Popover(Node):
    hint: str
    content: str
