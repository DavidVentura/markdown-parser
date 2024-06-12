import enum
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
    alt: str | None
    url: str | None

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

class Alignment(enum.Enum):
    LEFT = enum.auto()
    CENTER = enum.auto()
    RIGHT = enum.auto()

@dataclass
class TableDivisor(Node):
    alignment: Alignment

@dataclass
class TableCell(Node):
    content: list[Node]

@dataclass
class TableRow(Node):
    cells: list[TableCell]

@dataclass
class Table(Node):
    header: TableRow
    divisors: list[TableDivisor]
    rows: list[TableRow]

@dataclass
class ListItem(Node):
    content: list[Node]
    indentation: int

@dataclass
class OListItem(ListItem):
    index: int

@dataclass
class UnorderedList(Node):
    items: list[ListItem]

@dataclass
class OrderedList(Node):
    items: list[OListItem]

# Extensions
@dataclass
class Ref(Node):
    text: str

@dataclass
class RefItem(Node):
    ref: str
    text: list[Node]

@dataclass
class CustomDirective(Node):
    name: str
    arguments: list[str]

@dataclass
class Popover(Node):
    hint: str
    content: str

@dataclass
class KV:
    key: str
    val: str
@dataclass
class HtmlOpenTag(Node):
    elem_type: str
    props: list[KV]

@dataclass
class HtmlCloseTag(Node):
    elem_type: str

@dataclass
class HtmlSelfCloseTag(Node):
    elem_type: str
    props: list[KV]

@dataclass
class Heading(Node):
    level: int
    content: list[Node]

@dataclass
class Newline(Node):
    pass

@dataclass
class ParBreak(Node):
    pass

@dataclass
class Superscript(Node):
    content: list[Node]

@dataclass
class Subscript(Node):
    content: list[Node]
