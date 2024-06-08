from lark import Transformer, Token

from markdown_parser.nodes import *

class NodeTransformer(Transformer):
    def plain_text(self, items):
        assert len(items) == 1
        item = items[0]
        assert len(item.children) == 1
        string_tok = item.children[0]
        return PlainText(text=string_tok.value)

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

        rest = rest[1:] # the first element is the newline between ``` and code
        assert len(rest) == 1
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
