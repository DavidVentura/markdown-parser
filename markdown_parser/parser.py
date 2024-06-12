import lark
from markdown_parser.transformer import NodeTransformer
from markdown_parser.nodes import ParBreak, Node

grammar1 = r"""
TEXT: /[^\n]+/
LF: /\n/
PAR_BREAK: LF LF+

CODELINE: /(.|\n)+?(?=```)/
IDENTIFIER: /[A-Za-z]+/
CODE_BLOCK: "```" [IDENTIFIER] LF CODELINE "```"

start: (CODE_BLOCK | TEXT | LF | PAR_BREAK)+
"""
grammar2 = r"""

# string does not capture any symbols which may start an inline-tag
STRING: /[^`*[_{<>\n\\!]/
# string can't capture valid text which is not actually a tag, examples:
# * some [text] which is not an anchor
#  - still can't have [^text]
#  - stop searching at ... newline? => probably
BR_WORD_NOT_ANCHOR: /\[[^^(]+?](?![(\n])/
ESCAPED_CHAR: "\\" /./
NON_IMAGE_BANG: /!(?!\[)/
# * some {text} which is not a directive
#  - not {^somethng}
#  - no newline
CUR_BR_WORD_NOT_DIRECTIVE: /{[^^\n]+?}/

# NOT working
# * some text with a | which is not a table
PIPE_STRING: /[^|\n]+?(?=[|])/
ARROW_R: "->"
ARROW_L: "<-"

# group of string-til-delim without capture
# eg: "a str") "a str"] "a str"}

PAR_STRING: /[^)]+(?=[)])/
# not starting with ^, that's a ref ([^ref])
# allowed to have ^ ([W^X])
# limitation of not having a newline in the bracket ([text\nasd]),
# as we need some way of finding a stop. otherwise we need to limit to `[`
# which forbids links-to-images: [![]()]()
BR_STRING: /[^!^\]][^\]\n]*(?=])/
CUR_BR_STRING: /[^}]+(?=})/
COLON_STRING: /[^:\n]+?(?=:)/

superscript: "<sup>" (italic | star_bold | non_nestable_inlines)+ "</sup>"
subscript: "<sub>"  (italic | star_bold | non_nestable_inlines)+ "</sub>"
small: "<small>"  (italic | star_bold | non_nestable_inlines)+ "</small>"
smaller: "<smaller>"  (italic | star_bold | non_nestable_inlines)+ "</smaller>"

_LF: /\n/
%import common.ESCAPED_STRING
%import common.WS

%import common.SIGNED_NUMBER    -> NUMBER

?element: (non_nestable_inlines
    | non_nestable_blocks
    | italic
    | star_bold)

?non_nestable_inlines: (inline_pre
    | ref
    | anchor
    | image
    | plain_text
    | custom_directive
    | popover
    | small
    | smaller
    | superscript
    | subscript)

?non_nestable_blocks.1: (code_block
    | refitem
    | quote
    | html
    | heading
    | table
    | list
    | hr)
#    | metadata)

?xstart: anchor | image
?start: non_nestable_blocks? (hr | non_nestable_inlines | italic | star_bold | _LF)*

hr: "---" "-"*
META_PROP: /[^:]+(?=:)/
META_VALUE: /[^\n]+/
meta_line: META_PROP ":" [META_VALUE] _LF+
metadata: hr _LF meta_line+ hr

italic: (star_italic | under_italic)

quote_body: ">" " "? (quote_body | italic | star_bold | non_nestable_inlines)+
quote: (quote_body _LF?)+

# * item
#   * nested
# * item
LEADING_SPACE_LI: /^\s*((\d+[.])|([*+-])) /m
list: (list_item _LF?)+
list_item: LEADING_SPACE_LI (non_nestable_inlines | star_bold | italic)+

# 1. item
#   3. item2
# 1. item3
LEADING_SPACE_NL: /^\s*\d+[.] /m
ordered_list: (ordered_list_item _LF?)+
ordered_list_item: LEADING_SPACE_NL (non_nestable_inlines | star_bold | italic)+

# `some inline code()`
NOT_BACKTICK: /[^`]+(?=`)/
?inline_code: NOT_BACKTICK
inline_pre: "`" [inline_code] "`"

# _italic text_
?under_italic: "_" (non_nestable_inlines | star_bold)+ "_"
# *italic text*
# "* " is to match a longer terminal, such as LEADING_SPACE_BL
# which otherwise takes priority
?star_italic: "*" (non_nestable_inlines | star_bold)+ "*"

# **bold text**
# bold > italic
star_bold.2: "**" (non_nestable_inlines | italic)+ "**"

# some normal text 192874981 xx
# everything > plain_text
plain_text.-2: (STRING | BR_WORD_NOT_ANCHOR | ESCAPED_CHAR | NON_IMAGE_BANG | CUR_BR_WORD_NOT_DIRECTIVE | ARROW_R | ARROW_L)+

# ```bash
# a code block
# ```
# code block > inline_pre (`)
CODELINE: /(.|\n)+?(?=```)/
code: CODELINE
identifier: /[A-Za-z]+/
code_block.2: "```" [identifier] _LF (code) "```"


TAB_DIV: /[:  -]+/
table_cell: (italic | star_bold | non_nestable_inlines)+
table_row: "|" (table_cell "|")+ _LF?
table_divisor: "|" (TAB_DIV "|")+ _LF
table: table_row table_divisor table_row+

# ![alt](url)
image: "![" [BR_STRING] "](" [PAR_STRING] ")"

# [text](url)
anchor: "[" (image | inline_pre | plain_text | italic | star_bold)* "](" [PAR_STRING] ")"

# Extensions

# [^ref]
ref: "[^" /[^\]]+/ "]"

# [^ref]: some text
# where [^ref] is at the start of a line
refitem: "[^" /[^\]]+/ "]:" (non_nestable_inlines | italic | star_bold)+

# {^embed-file: file}
custom_directive: "{^" COLON_STRING ":" CUR_BR_STRING "}"

# {^hint|content w spaces}
popover: "{^" PIPE_STRING "|" CUR_BR_STRING "}"


EQUAL: "="
QUOTE: "\""

HTML_PROP_NAME: /[^=>\s]+/
HTML_VALUE: EQUAL QUOTE /[^"]*/ QUOTE

SPACES: / +/
html: SPACES? html_tag (non_nestable_inlines | code_block | _LF | html_tag)*
?html_tag: html_open_tag | html_close_tag
html_open_tag: "<" /[^\s>]+/ (WS? HTML_PROP_NAME [HTML_VALUE] )* ">"
html_close_tag: "</" /[^>]+?(?=>)/ ">"

HASH: "#"
heading: HASH+ (non_nestable_inlines | star_bold | italic)+

# TODO
# -----*
# &mdash; html entities
"""

class DoubleParser:
    def __init__(self) -> None:
        self.p1 = lark.Lark(grammar1, parser='lalr', debug=True, lexer="contextual")
        self.p2 = lark.Lark(grammar2, parser='lalr', debug=True, lexer="contextual", transformer=NodeTransformer(), maybe_placeholders=True)

    def parse(self, text: str) -> Node | list[Node]:
        ret: list[Node] = []
        chunks = self.p1.parse(text).children
        cur_chunk: list[str] = []
        for chunk in chunks:
            assert isinstance(chunk, lark.Token), chunk
            if chunk.type == "PAR_BREAK":
                if cur_chunk:
                    chunk_text = "\n".join(cur_chunk)
                    # print("#" * 50, "\n", chunk_text)
                    res = self.p2.parse(chunk_text)
                    if isinstance(res, lark.Tree):
                        ret.extend(res.children)
                    elif isinstance(res, list):
                        ret.extend(res)
                    else:
                        # single-item parsing
                        ret.append(res)
                    cur_chunk = []
                ret.append(ParBreak())
                continue
            if chunk.type == "LF":
                continue
            cur_chunk.append(chunk.value)

        if cur_chunk:
            chunk_text = "\n".join(cur_chunk)
            # print(chunk_text)
            res = self.p2.parse(chunk_text)
            if isinstance(res, lark.Tree):
                ret.extend(res.children)
            elif isinstance(res, list):
                ret.extend(res)
            else:
                # single-item parsing
                ret.append(res)
            cur_chunk = []

        # ugh, compat with parse()
        if len(ret) == 1:
            return ret[0]
        return ret

def make_parser():
    return DoubleParser()

if __name__ == "__main__":
    parser = make_parser()
    import glob
    for f in sorted(glob.glob('../blog/blog/raw/*/POST.md')):
        with open(f) as fd:
            bp = fd.read()
        try:
            r = parser.parse(bp)
            print("OK", f)
        except:
            print("NOK", f)
            raise
        #print(r.pretty())
