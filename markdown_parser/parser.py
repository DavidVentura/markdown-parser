import lark

grammar = r"""

url: /.+/
STRING: /[^[*_{}`\n]+/
PAR_STRING: /[^)]+/
BR_STRING: /[^]]+/
identifier: /[a-z]+/

code: /[^`]+/
?inline_code: /[^`]+/
newline: /\n/

%import common.SIGNED_NUMBER    -> NUMBER

?element: (
    | code_block
    | inline_pre
    | ref
    | quote
    | italic
    | unordered_list
    | star_bold
    | anchor
    | image
    | table_row
    | newline
    | custom_directive
    | plain_text)

?start: (element | newline)+

italic: star_italic
    | under_italic

quote: "> " (italic | star_bold | plain_text)+

unordered_list: "*" element+ newline
inline_pre: "`" inline_code "`"
?under_italic: "_" (star_bold | plain_text)+ "_"
star_bold: "**" (italic | plain_text)+ "**"
?star_italic: "*" (star_bold | plain_text)+ "*"
plain_text.-2: (STRING | NUMBER)+
code_block.2: "```" [identifier newline] (code)+ "```"

table_cell: (inline_pre | italic | star_bold | plain_text)+
table_row: "|" (table_cell ["|"])+ "|" [/ +/] newline

image: "!" "[" plain_text "]" "(" url ")"
anchor: "[" BR_STRING "]" "(" PAR_STRING ")"
ref: "[^" /[^\]]/ "]"

custom_directive: "{" "^" plain_text "}"

# >
# ``
# **
# _ _
# ** **

# ``` ```
# []()
# ![]()
# -----*
# # ## ### ...
# <html>
# bullet list *
# numbered list 1. 2. 3.
# escape = \* \_ \`
# &mdash; html entities
# tables ???


# extensions
# [^note] + [^note]:
# {custom-directive args}
"""


parser = lark.Lark(grammar, parser='lalr', debug=True)
text1 = """`some inline pre`

xx _some italic text_

/usr/bin/cat
**some bold**

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
|`5604dff9a000-5604dff9c000` | `r--p` |000000|/usr/bin/cat|
|`5604e121d000-5604e123e000` | `rw-p` |000000|heap|
|`7f38a9bd8000-7f38a9c02000` | `r-xp` |002000|ld-linux-x86-64.so.2|
|`7fff378cb000-7fff378ec000` | `rw-p` |000000|stack|
|`7fff3794f000-7fff37953000` | `r--p` |000000|vvar|
|`7fff37953000-7fff37955000` | `r-xp` |000000|vdso|

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
text1 = """asd"""
r = parser.parse(text1)
print(r.pretty())
