from lark import Transformer, Token

from markdown_parser.nodes import *

class NodeTransformer(Transformer):
    def plain_text(self, items):
        text = "".join(items)
        return PlainText(text=text)

    def under_italic(self, items):
        return self.italic(items)

    def italic(self, items):
        return Emphasis(content=items)

    def star_bold(self, items):
        return Bold(content=items)

    def quote(self, items):
        return Quote(content=items)

    def inline_pre(self, items):
        assert len(items) == 1
        string_tok = items[0]
        return InlineCode(text=string_tok.value)

    def image(self, items):
        alt, url = items
        if alt is not None:
            alt = alt.value
        if url is not None:
            url = url.value
        return Image(alt, url)

    def anchor(self, items):
        text, url = items
        if text is not None:
            text = text.value
        if url is not None:
            url = url.value
        return Anchor(text, url)

    def custom_directive(self, items):
        name, args = items
        name = name.value
        if args is not None:
            args = args.value
        else:
            args = ""

        return CustomDirective(name, args.split())

    def ref(self, items):
        return Ref(items[0].value)

    def refitem(self, items):
        return RefItem(items[0].value, items[1:])

    def code_block(self, items):
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

    def popover(self, items):
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

    def html_close_tag(self, items):
        assert len(items) == 1
        return HtmlCloseTag(items[0].value)

    def heading(self, items):
        count = len([1 for i in items if isinstance(i, Token) and i.type == "HASH"])
        return Heading(count, items[count:])

    def unordered_list_item(self, items):
        if isinstance(items[0], ParBreak):
            items = items[1:]
        leading_space, *content = items
        indentation = 0
        if leading_space is not None:
            assert leading_space.type == "LEADING_SPACE_BL"
            indentation = len(leading_space.value.lstrip('\n')) - 2 # trailing "* "
        return ListItem(content, indentation)

    def unordered_list(self, items):
        # filter out delimiting newlines
        return UnorderedList([i for i in items if not isinstance(i, Token)])

    def ordered_list_item(self, items):
        leading_space, *content = items
        indentation = 0
        assert leading_space is not None
        assert leading_space.type == "LEADING_SPACE_NL"
        # spaces digit(s) dot spaces
        num = int(leading_space.partition(".")[0].strip())
        indentation = len(leading_space.value) - len(leading_space.lstrip())
        return OListItem(content, indentation, num)

    def ordered_list(self, items):
        # filter out delimiting newlines
        return OrderedList([i for i in items if not isinstance(i, Token)])

    def PAR_BREAK(self, _items):
        return ParBreak()

    def table(self, items):
        header, divisors, *rows = items
        return Table(header, divisors, rows)

    def table_cell(self, items):
        return TableCell(items)

    def table_row(self, items):
        return TableRow(items)

    def table_divisor(self, items):
        ret = []
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
