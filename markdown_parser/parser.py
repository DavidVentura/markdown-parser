import lark
from markdown_parser.transformer import NodeTransformer

grammar = r"""

# lower than all tags
md_open_sym_inl: "`" | "#" | "*" | "[" | "_" | "{" | ">" | "|"
escaped_sym_inl: "\\" md_open_sym_inl

# string does not capture any symbols which may start a new tag
STRING: /[^`#*[_{<|\n\\!]/
# string can't capture valid text which is not actually a tag, examples:
# * some [text] which is not an anchor
#  - still can't have [^text]
#  - stop searching at ... newline? => probably
BR_WORD_NOT_ANCHOR: /\[[^^(]+?](?![(\n])/
ESCAPED_UNDERSCORE: "\\" "_"
ESCAPED_STAR: "\\" "*"
NON_IMAGE_BANG: /!(?!\[)/
# * some {text} which is not a directive
#  - not {^somethng}
#  - no newline
CUR_BR_WORD_NOT_DIRECTIVE: /{[^^\n]+?}/

# NOT working
# * some text with a | which is not a table
PIPE_STRING: /[^|\n]+?(?=[|])/
UNPAIRED_BACKQUOTE.2: "`" /[^`\n]+?](?!`)/
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
# because otherwis
BR_STRING: /[^^][^\]\n]*(?=])/
CUR_BR_STRING: /[^}]+(?=})/
COLON_STRING: /[^:\n]+?(?=:)/

_LF: /\n/
PAR_BREAK: _LF _LF+
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
    | popover)

?non_nestable_blocks.1: (code_block
    | refitem
    | quote
    | html_tag
    | heading
    | table
    | unordered_list
    | ordered_list)

?xstart: (code_block | plain_text | PAR_BREAK | _LF)+
?start: (element | delim)+

delim: _DELIM
_DELIM: (PAR_BREAK | _LF)

italic: (star_italic | under_italic)
#italic: under_italic

# splitting into quote_body allows for recursion, only requiring the first
# match to have a leading newline // be its own block
quote_body: ">" " "? (quote_body | italic | star_bold | non_nestable_inlines)+
quote: _DELIM quote_body

# * item
#   * nested
# * item
LEADING_SPACE_BL: _DELIM ("* " | / +/ "* ")
unordered_list: (unordered_list_item)+
unordered_list_item: LEADING_SPACE_BL (non_nestable_inlines | star_bold | italic)+

# 1. item
#   3. item2
# 1. item3
LEADING_SPACE_NL: (/\d+/ "." | / +/ /\d+/ ".") " "
ordered_list: (ordered_list_item)+
ordered_list_item: LEADING_SPACE_NL (non_nestable_inlines | star_bold | italic)+ _DELIM

# `some inline code()`
?inline_code: /[^`\n]+/
inline_pre: "`" [inline_code] "`"

# _italic text_
?under_italic: "_" (non_nestable_inlines | star_bold)+ "_"
# *italic text*
?star_italic: "*" (non_nestable_inlines | star_bold)+ "*"

# **bold text**
# bold > italic
star_bold.2: "**" (non_nestable_inlines | italic)+ "**"

# some normal text 192874981 xx
# everything > plain_text
plain_text.-2: (STRING | BR_WORD_NOT_ANCHOR | UNPAIRED_BACKQUOTE | ESCAPED_UNDERSCORE | ESCAPED_STAR | NON_IMAGE_BANG | CUR_BR_WORD_NOT_DIRECTIVE | ARROW_R | ARROW_L)+

# ```bash
# a code block
# ```
# code block > inline_pre (`)
code: /(.|\n)+?(?=```)/
identifier: /[a-z]+/
code_block.2: "```" [identifier] _LF (code) "```"


TAB_DIV: /[: -]+/
table_cell: (italic | star_bold | non_nestable_inlines)+
table_row: "|" (table_cell "|")+ _LF
table_divisor: "|" (TAB_DIV "|")+ _LF
table: table_row table_divisor table_row+

# ![alt](url)
image: "![" [BR_STRING] "](" [PAR_STRING] ")"

# [text](url)
anchor: "[" [BR_STRING] "](" [PAR_STRING] ")"

# Extensions

# [^ref]
ref: "[^" /[^\]]+/ "]"

# [^ref]: some text
# where [^ref] is at the start of a line
refitem: _DELIM "[^" /[^\]]+/ "]:" (non_nestable_inlines | italic | star_bold)+

# {^embed-file: file}
custom_directive: "{^" COLON_STRING ":" CUR_BR_STRING "}"

# {^hint|content w spaces}
popover: "{^" PIPE_STRING "|" CUR_BR_STRING "}"


EQUAL: "="
QUOTE: "\""

HTML_PROP_NAME: /[^=>\s]+/
HTML_VALUE: EQUAL QUOTE /[^"]+/ QUOTE

?html_tag: html_open_tag | html_close_tag
html_open_tag: "<" /[^\s>]+/ (WS? HTML_PROP_NAME [HTML_VALUE] )* ">"
html_close_tag: "</" /[^>]+?(?=>)/ ">"

HASH: "#"
heading: HASH+ (non_nestable_inlines | star_bold | italic)+

# TODO
# -----*
# escape = \* \_ \`
# &mdash; html entities
"""


def make_parser():
    return lark.Lark(grammar, parser='lalr', debug=True, lexer="contextual", transformer=NodeTransformer(), maybe_placeholders=True)

if __name__ == "__main__":
    parser = make_parser()
    import glob
    text = """With the bindings generated we only need to connect the 3 required signals to our rust code, here's one as an
example[^2]:
"""
    text = """ the [video](https://i.imgur.com/F5IwMvj.mp4). """
    text = """!"""
    text = """
![](https://raw.githubusercontent.com/davidventura/hn/master/screenshots/comments.png?raw=true)

[^1]: Although it is a tad slow on a test device (2013 Nexus 5). I might evaluate later the performance of calling a [rust implementation](https://github.com/kumabook/readability) instead, and whether that's worth it or not.
"""
    text = """
asd

> first _asd_
> second
> > nested

"""
    text = "some text\n\nparagraph"

    t = parser.parse(text)
    print(t)
    exit(0)
    bp = open('../blog/blog/raw/option-rom/POST.md').read()
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
