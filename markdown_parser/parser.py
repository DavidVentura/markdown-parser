import lark
from markdown_parser.transformer import NodeTransformer
from markdown_parser.nodes import ParBreak

# this should probably include multi-line blocks like ```
# which shouldn't get split with multiple newlines in between

grammar1 = r"""
TEXT: /[^\n]+/
LF: /\n/
PAR_BREAK: LF LF+

CODELINE: /(.|\n)+?(?=```)/
IDENTIFIER: /[a-z]+/
CODE_BLOCK: "```" [IDENTIFIER] LF CODELINE "```"

start: (CODE_BLOCK | TEXT | LF | PAR_BREAK)+

"""
grammar2 = r"""

# lower than all tags
md_open_sym_inl: "`" | "#" | "*" | "[" | "_" | "{" | ">" | "|"
escaped_sym_inl: "\\" md_open_sym_inl

# string does not capture any symbols which may start a new tag
STRING: /[^`*[_{<>|\n\\!]/
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

superscript: "<sup>" (italic | star_bold | non_nestable_inlines)+ "</sup>"
subscript: "<sub>"  (italic | star_bold | non_nestable_inlines)+ "</sub>"

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
    | superscript
    | subscript)

?non_nestable_blocks.1: (code_block
    | refitem
    | quote
    | html
    | heading
    | table
    | list)

?xstart: table
?start: non_nestable_blocks? (non_nestable_inlines | italic | star_bold | _LF)*

italic: (star_italic | under_italic)

quote_body: ">" " "? (quote_body | italic | star_bold | non_nestable_inlines)+
quote: (quote_body _LF?)+

# * item
#   * nested
# * item
LEADING_SPACE_LI: /^\s*((\d+[.])|([*])) /m
list: (list_item _LF?)+
list_item: LEADING_SPACE_LI (non_nestable_inlines | star_bold | italic)+

# 1. item
#   3. item2
# 1. item3
LEADING_SPACE_NL: /^\s*\d+[.] /m
ordered_list: (ordered_list_item _LF?)+
ordered_list_item: LEADING_SPACE_NL (non_nestable_inlines | star_bold | italic)+

# `some inline code()`
NOT_BACKTICK: /[^`]+/
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
plain_text.-2: (STRING | BR_WORD_NOT_ANCHOR | UNPAIRED_BACKQUOTE | ESCAPED_CHAR | NON_IMAGE_BANG | CUR_BR_WORD_NOT_DIRECTIVE | ARROW_R | ARROW_L)+

# ```bash
# a code block
# ```
# code block > inline_pre (`)
CODELINE: /(.|\n)+?(?=```)/
code: CODELINE
identifier: /[a-z]+/
code_block.2: "```" [identifier] _LF (code) "```"


TAB_DIV: /[:  -]+/
table_cell: (italic | star_bold | non_nestable_inlines)+
table_row: "|" (table_cell "|")+ _LF?
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
html: SPACES? html_tag (plain_text | code_block | _LF | html_tag)*
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

class DoubleParser:
    def __init__(self):
        self.p1 = lark.Lark(grammar1, parser='lalr', debug=True, lexer="contextual")
        self.p2 = lark.Lark(grammar2, parser='lalr', debug=True, lexer="contextual", transformer=NodeTransformer(), maybe_placeholders=True)

    def parse(self, text):
        ret = []
        chunks = self.p1.parse(text).children
        cur_chunk = []
        for chunk in chunks:
            assert isinstance(chunk, lark.Token), chunk
            if chunk.type == "PAR_BREAK":
                if cur_chunk:
                    chunk_text = "\n".join(cur_chunk)
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
            #print(chunk_text)
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

```bash
some code
```

text
"""
    text = "> quote\n"
    text2 = "## *word2* word"
    text = "> quote _italic_ **bold** _**both `code` []()**_"
    text = ">> dquote"
    text = "1. list\n1. item"
    text = "1. list\n    99. item\n1. list2"
    text = """
<div>
text
</div>
"""
    text = """<div> text </div>
"""
    text = """
| Address|Perms|Offset|Path|
|---------------------------------|:----|-------:|:----------:|
|`addr`|**bold**|some text|some **bold** text|
|`addr2`|_italic_|some text|[heap]|
"""
    

    text = '<img src="assets/headers.svg" style="margin: 0px auto; width: 100%; max-width: 30rem" />'

    text = """```bash
    code

    with manylines
    ```
    """
    text = "its #1"
    text = r"shrug ¯\\\_!ツ!\_/¯"
    text = """
> The callback can't be passed directly - we have double box it; once to safely transport the type
> data and once again to have a fixed-size object to reference.
"""

    t = parser.parse(text)
    print(t)
    bp = open('../blog/blog/raw/option-rom/POST.md').read()
    r = parser.parse(bp)
    print('okkk')
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
