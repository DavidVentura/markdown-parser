import lark
from markdown_parser.transformer import NodeTransformer

grammar = r"""

# lower than all tags
md_open_sym_inl: "`" | "#" | "*" | "[" | "_" | "{" | ">" | "|"
escaped_sym_inl: "\\" md_open_sym_inl

# string does not capture any symbols which may start a new tag
string: /[^`#*[_{>|\n]+/
PAR_STRING: /[^)]+/
BR_STRING: /[^]]+/
CUR_BR_STRING: /[^}]+/
COLON_STRING: /[^:\n]+?(?=:)/
PIPE_STRING: /[^|\n]+?(?=[|])/
identifier: /[a-z]+/

code: /[^`]+/
?inline_code: /[^`]+/
%import common.NEWLINE

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

?non_nestable_blocks: (code_block
    | quote
    | table_row)

notworking: (
    | unordered_list
    | table_row)

?start: (element | NEWLINE)+

italic: (star_italic | under_italic)

quote: ">" (italic | star_bold | non_nestable_inlines)+

# * item
# * item
unordered_list: "*" element+ NEWLINE

# `some inline code()`
inline_pre: "`" inline_code "`"

# _italic text_
?under_italic: "_" (non_nestable_inlines | star_bold)+ "_"
# *italic text*
?star_italic: "*" (non_nestable_inlines | star_bold)+ "*"

# **bold text**
# bold > italic
star_bold.2: "**" (non_nestable_inlines | italic)+ "**"

# some normal text 192874981 _ 81
# everything > plaintext
plain_text.-2: string+

# ```bash
# a code block
# ```
# code block > inline_pre (`)
code_block.2: "```" [identifier NEWLINE] (code)+ "```"

table_cell: (italic | star_bold | non_nestable_inlines)+
table_row: "|" (table_cell "|")+ NEWLINE

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

# TODO
# -----*
# heading # ## ### ...
# <html>
# numbered list 1. 2. 3.
# unordered list (-)
# unordered list (*, -) subitem
# escape = \* \_ \`
# &mdash; html entities
"""


def make_parser():
    return lark.Lark(grammar, parser='lalr', debug=True, lexer="contextual", transformer=NodeTransformer())

if __name__ == "__main__":
    parser = make_parser()
    text1 = """`some inline pre`

    xx _some italic text_

    /usr/bin/cat
    **some bold**

    ```
    without
    ```

    ```bash
    some code
    more code _with under_

    ![a link](href)

    [qwe](rty)

    ```

    code is done

    ![a link](href)

    [qwe](rty)
    """

    table = """
    | Address                         |Perms|Offset  |Path|
    |---------------------------------|-----|--------|------------|
    |`5604dff9a000-5604dff9c000`|`r--p`|000000|`/usr/bin/cat`|


    | Address                         |Perms|Offset  |Path|
    |---------------------------------|-----|--------|------------|
    |`5604dff9a000-5604dff9c000` | `r--p` |000000|/usr/bin/cat|
    |`5604e121d000-5604e123e000` | `rw-p` |000000|[heap]|
    |`7f38a9bd8000-7f38a9c02000` | `r-xp` |002000|ld-linux-x86-64.so.2|
    |`7fff378cb000-7fff378ec000` | `rw-p` |000000|[stack]|
    |`7fff3794f000-7fff37953000` | `r--p` |000000|[vvar]|
    |`7fff37953000-7fff37955000` | `r-xp` |000000|[vdso]|

    qwe
    """

    #text1 = "**a_s_d**"
    text2 = """
    xx _asd_
    `qwe`
    **bold**
    ```bash
    asd
    ```

    ![asd](qwe)

    """

    bp = open('../blog/blog/raw/option-rom/POST.md').read()

    text2 = """
    In this series, we've been implementing a PCI-e GPU and so far we were able to put some pixels on the (emulated) screen via purpose-built userspace programs. Now it's time to make the GPU available to the system, and we'll start by making it **available** to {^UEFI|Unified Extensible Firmware Interface} [Option ROM](https://en.wikipedia.org/wiki/Option_ROM).


    **asd**
    """
    text1 = """some text **boldy**
    some text2 [qqqqqqqqq](asd)
    some text3 _undery_"""
    text1 = bp
    text1 = """_aaa aaa_
    _asdqwe_
    _a_
    _aa_

    normal text _with italics_ and more 
    normal text **with bold** and more 

    normal **bold _italic_ more** normal
    _italic **bold** something_

    `asd`

    _ital asd end_

    _ital `code` **also bold `code`**_

    a ref: [^1]

    _**[anchor text](anchor url)**_

    ![alt text](url)

    {^embed-file: my-file.py}
    {^run-script: my-file.py --args 1 2 3}

    ```
       without
    ```
    ```bash
    some code _with under_
    xcaqwe
       xcaqwe
    ```
    ```ini
    [Defines]
      INF_VERSION    = 0x00010005
      BASE_NAME      = OptionRom
      FILE_GUID      = f1f6026b-aa59-4e68-9fbe-6be92e37a225
      MODULE_TYPE    = UEFI_DRIVER
      VERSION_STRING = 1.0
    ```

    and after code also

    > some quote _with italic_ and **bold** and _**both `code!` [link]()**_

    also text'with apostrophes
    blah {^UEFI|Unified Extensible Firmware Interface} qq

    some text with [sqb]() asd
    some text with [_sqb_]() asd
    """
    text1 = """
    something w fn [^1]

    [^1]: the footnote _with it_
    """
    r = parser.parse(text1)
    print(r.pretty())
