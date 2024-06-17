from lark import Transformer, Token, Tree

from markdown_parser.nodes import *

class NodeTransformer(Transformer):
    def plain_text(self, items) -> PlainText:
        text = "".join(items)
        return PlainText(text=text)

    def under_italic(self, items: list[Node]) -> Emphasis:
        return self.italic(items)

    def italic(self, items: list[Node]) -> Emphasis:
        return Emphasis(content=items)

    def star_bold(self, items: list[Node]) -> Bold:
        return Bold(content=items)

    def delim(self, items: list[Node]) -> Node:
        assert len(items) == 1, items
        return items[0]

    def quote_body(self, items: list[Token | Node]) -> Quote:
        lead, *items = items
        assert isinstance(lead, Token)
        level = lead.value.count(">")
        return Quote(level - 1, items)

    def quote(self, items: list[Node]) -> list[Node]:
        return items

    def inline_pre(self, items: list[Token]) -> InlineCode:
        assert len(items) == 1
        string_tok = items[0]
        if string_tok is not None: # ``
            return InlineCode(text=string_tok.value)
        return InlineCode(text="")

    def image(self, items: list[Node]) -> Image:
        alt, url = items
        if alt is not None:
            assert isinstance(alt, Token)
            alt = alt.value
        if url is not None:
            assert isinstance(url, Token)
            url = url.value
        return Image(alt, url)

    def anchor(self, items: list[Node | Token]) -> Anchor:
        *text, url = items
        if url is not None:
            url = url.value
        return Anchor(text, url)

    def custom_directive(self, items: list[Token]) -> CustomDirective:
        name, args = items
        name = name.value
        if args is not None:
            args = args.value
        else:
            args = ""

        return CustomDirective(name, args.split())

    def ref(self, items: list[Token]) -> Ref:
        return Ref(items[0].value)

    def refblock(self, items: list[Token | Node]) -> RefBlock:
        return RefBlock(items)

    def refitem(self, items: list[Token | Node]) -> RefItem:
        return RefItem(items[0].value, items[1:])

    def code_block(self, items: list[Token | Tree]) -> CodeBlock:
        identifier_t, *rest = items
        identifier = None
        if identifier_t is not None:
            assert len(identifier_t.children) == 1
            identifier = identifier_t.children[0]

            if identifier is not None:
                identifier = identifier.value

        assert len(rest) == 1
        #rest = rest[1:] # the first element is the newline between ``` and code
        code_tree = rest[0]
        assert len(code_tree.children) == 1
        lines = code_tree.children[0].splitlines()
        if lines[0].strip() == '':
            lines = lines[1:]

        return CodeBlock(identifier, lines)

    def popover(self, items: list[Token]) -> Popover:
        hint, content = items
        return Popover(hint.value, content.value)

    def html_open_tag(self, items):
        tag, *pprops = items

        nodeprops = []
        propname = ""
        propval = ""
        self_closing = False
        for parsed in pprops:
            if parsed is None:
                continue
            if parsed.type == "WS":
                continue
            if parsed.type == "HTML_PROP_NAME":
                if propname:
                    nodeprops.append(KV(propname, propval))
                if parsed.value == "/":
                    self_closing = True
                    continue
                propval = ""
                propname = parsed.value
            if parsed.type == "HTML_VALUE":
                assert parsed.value[0] == "="
                propval = parsed.value[1:] # starts with '='

        if propname:
            nodeprops.append(KV(propname, propval))

        if self_closing:
            return HtmlSelfCloseTag(tag.value, nodeprops)

        return HtmlOpenTag(tag.value, nodeprops)

    def html_close_tag(self, items) -> HtmlCloseTag:
        assert len(items) == 1
        return HtmlCloseTag(items[0].value)

    def heading(self, items) -> Heading:
        count = len([1 for i in items if isinstance(i, Token) and i.type == "HASH"])
        return Heading(count, items[count:])

    def LEADING_SPACE_LI(self, items):
        assert isinstance(items, Token)
        stripped = items.lstrip()
        leading_space = len(items) - len(stripped)
        if stripped[0] in ['*', '-', '+']:
            marker = UnorderedListIndicator(stripped[0])
        else:
            # number - support 9) 8) ?
            assert '.' in stripped
            num, _, _ = stripped.partition('.')
            num = int(num)
            marker = OrderedListIndicator(num)
        return ListItemIndicator(leading_space, marker)

    def list_block(self, items):
        return ListBlock(items)

    def list_item(self, items) -> OListItem | ListItem:
        li = items[0]
        content = items[1:]
        match li.marker:
            case OrderedListIndicator(idx):
                return OListItem(idx, content, li.indentation)
            case UnorderedListIndicator():
                return ListItem(li.marker.marker, content, li.indentation)

        assert False

    def PAR_BREAK(self, _items) -> ParBreak:
        return ParBreak()

    def table(self, items) -> Table:
        header, divisors, *rows = items
        return Table(header, divisors, rows)

    def table_cell(self, items) -> TableCell:
        return TableCell(items)

    def table_row(self, items) -> TableRow:
        return TableRow(items)

    def ESCAPED_CHAR(self, items) -> str:
        assert isinstance(items, Token)
        s = items.value
        assert len(s) == 2
        assert s.startswith('\\')
        return s[1]

    def superscript(self, items) -> Superscript:
        return Superscript(items)

    def subscript(self, items) -> Subscript:
        return Subscript(items)

    def table_divisor(self, items) -> list[TableDivisor]:
        ret: list[TableDivisor] = []
        for item in items:
            text = item.value.strip()
            alignment = Alignment.CENTER
            if text.startswith(":") and text.endswith(":"):
                alignment = Alignment.CENTER
            elif text.startswith(":"):
                alignment = Alignment.LEFT
            elif text.endswith(":"):
                alignment = Alignment.RIGHT

            td = TableDivisor(alignment)
            ret.append(td)
        return ret

    def hr(self, items) -> Hr:
        return Hr()

    def meta_line(self, items) -> KV:
        assert len(items) == 2
        k, v = items
        return KV(k.strip(), v.strip())

    def metadata(self, items) -> Metadata:
        _, *entries, _ = items
        return Metadata(entries)

