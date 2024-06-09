import lark
from markdown_parser.transformer import NodeTransformer

grammar = r"""

# lower than all tags
md_open_sym_inl: "`" | "#" | "*" | "[" | "_" | "{" | ">" | "|"
escaped_sym_inl: "\\" md_open_sym_inl

# string does not capture any symbols which may start a new tag
STRING: /[^`#*[_{<>|\n]+/
# string can't capture valid text which is not actually a tag, examples:
# * some [text] which is not an anchor
#  - still can't have [^text]
#  - stop searching at ... newline? => probably
BR_WORD_NOT_ANCHOR: /\[[^^(]+?](?![(\n])/
# * some {text} which is not a directive TODO
# * some text with a | which is not a table

PIPE_STRING: /[^|\n]+?(?=[|])/

# string-til-delim without capture eg: "a str") "a str"] "a str"}
PAR_STRING: /[^)]+(?=[)])/
BR_STRING: /[^]]+(?=])/
CUR_BR_STRING: /[^}]+(?=})/
COLON_STRING: /[^:\n]+?(?=:)/

_LF: /\n/
PAR_BREAK: _LF _LF+
?inline_code: /[^`]+/
%import common.ESCAPED_STRING
%import common.WS

%import common.SIGNED_NUMBER    -> NUMBER

?element: (non_nestable_inlines
    | non_nestable_blocks
    | italic
    | star_bold)

?non_nestable_inlines: (inline_pre
    | ref
    | refitem
    | anchor
    | image
    | plain_text
    | custom_directive
    | popover)

?non_nestable_blocks.1: (code_block
    | quote
    | html_tag
    | heading
    | table
    | unordered_list
    | ordered_list)

?xstart: (unordered_list | plain_text| _LF )+
?start: (element | PAR_BREAK | _LF)+

#italic: (star_italic | under_italic)
italic: under_italic

quote: ">" (italic | star_bold | non_nestable_inlines)+

# * item
#   * nested
# * item
LEADING_SPACE_BL: ("* " | / +/ "* ")
unordered_list: (unordered_list_item)+
unordered_list_item: LEADING_SPACE_BL (non_nestable_inlines | star_bold | italic)+ (_LF| PAR_BREAK)

# 1. item
#   3. item2
# 1. item3
LEADING_SPACE_NL: (/\d+/ "." | / +/ /\d+/ ".") " "
ordered_list: (ordered_list_item)+
ordered_list_item: LEADING_SPACE_NL (non_nestable_inlines | star_bold | italic)+ (_LF| PAR_BREAK)

# `some inline code()`
inline_pre: "`" inline_code "`"

# _italic text_
?under_italic: "_" (non_nestable_inlines | star_bold)+ "_"
# *italic text*
?star_italic: "*" (non_nestable_inlines | star_bold)+ "*"

# **bold text**
# bold > italic
star_bold.2: "**" (non_nestable_inlines | italic)+ "**"

# some normal text 192874981 xx
# everything > plain_text
plain_text.-2: (STRING | BR_WORD_NOT_ANCHOR)+

# ```bash
# a code block
# ```
# code block > inline_pre (`)
code: /(.|\n)+?(?=```)/
identifier: /[a-z]+/
code_block.2: "```" [identifier] _LF (code) "```"


TAB_DIV: /[:-]+/
table_cell: (italic | star_bold | non_nestable_inlines)+
table_row: "|" (table_cell "|")+ _LF
table_divisor: "|" (TAB_DIV "|")+ _LF
table: table_row table_divisor table_row+

# ![alt](url)
image: "!" "[" [BR_STRING] "]" "(" [PAR_STRING] ")"

# [text](url)
anchor: "[" [BR_STRING] "]" "(" [PAR_STRING] ")"

# Extensions

# [^ref]
ref: "[^" /[^\]]/ "]"

# [^ref]: some text
# prio over ref
refitem.2: "[^" /[^\]]/ "]:" (non_nestable_inlines | italic | star_bold)+

# {^embed-file: file}
custom_directive: "{" "^" COLON_STRING ":" CUR_BR_STRING "}"

# {^hint|content w spaces}
popover: "{" "^" PIPE_STRING "|" CUR_BR_STRING "}"


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
    bp = open('../blog/blog/raw/option-rom/POST.md').read()
    r = parser.parse(bp)
    #print(r)
    print(r.pretty())
