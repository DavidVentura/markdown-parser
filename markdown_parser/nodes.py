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
    content: list[Node]
    href: str

@dataclass
class Image(Node):
    alt: str | None
    url: str | None

@dataclass
class Quote(Node):
    level: int
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
class TableHeaderCell(Node):
    content: list[Node]

@dataclass
class TableHeaderRow(Node):
    cells: list[TableHeaderCell]

@dataclass
class Table(Node):
    header: TableHeaderRow
    divisors: list[TableDivisor]
    rows: list[TableRow]

@dataclass
class UnorderedListIndicator(Node):
    marker: str

@dataclass
class OrderedListIndicator(Node):
    num: int

@dataclass
class ListItemIndicator(Node):
    indentation: int
    marker: UnorderedListIndicator | OrderedListIndicator

@dataclass
class ListItem(Node):
    marker: str
    content: list[Node]
    indentation: int

@dataclass
class OListItem(Node):
    index: int
    content: list[Node]
    indentation: int

@dataclass
class ListBlock(Node):
    children: list[ListItem | OListItem]

# Extensions
@dataclass
class Ref(Node):
    text: str

@dataclass
class RefItem(Node):
    ref: str
    text: list[Node]

@dataclass
class RefBlock(Node):
    children: list[RefItem]

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

@dataclass
class Hr(Node):
    pass

@dataclass
class Metadata(Node):
    entries: list[KV]
