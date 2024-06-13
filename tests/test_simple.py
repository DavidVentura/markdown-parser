import pytest

from textwrap import dedent

from lark import Tree, Token

from markdown_parser.nodes import *


def test_base_case(parser):
    tree = parser.parse("some text")
    assert isinstance(tree, PlainText)
    assert tree.text == "some text"


text1 = """

    some text with [sqb]() asd
    some text with [_sqb_]() asd
"""

PT = PlainText


@pytest.mark.parametrize(
    "md,expected",
    [
        ("some text", PT("some text")),
        ("some text with ' ap", PT("some text with ' ap")),
        ("some text with [brackets x] on it", PT("some text with [brackets x] on it")),
        ("some text\n\nparagraph", [PT("some text"), ParBreak(), PlainText(text="paragraph")]),
        ("_oneword_", Emphasis([PT("oneword")])),
        ("_two words_", Emphasis([PT("two words")])),
        ("_a_", Emphasis([PT("a")])),
        ("**oneword**", Bold([PT("oneword")])),
        ("**two words**", Bold([PT("two words")])),
        ("**a**", Bold([PT("a")])),
        ("`code`", InlineCode("code")),
        ("`code words()`", InlineCode("code words()")),
        ("`x]x`", InlineCode("x]x")),
        ("`[sqcode]`", InlineCode("[sqcode]")),
        ("`[sqcode] word`", InlineCode("[sqcode] word")),
        ("two `code` blocks `here`", [PT("two "), InlineCode("code"), PT(" blocks "), InlineCode("here")]),
        ("[anchor text](url)", Anchor([PT("anchor text")], "url")),
        ("[anchor text]()", Anchor([PT("anchor text")], None)),
        ("[]()", Anchor([], None)),
        ("![alt text](url)", Image("alt text", "url")),
        ("![alt text]()", Image("alt text", None)),
        ("![]()", Image(None, None)),
        ("```\nsome code\n```", CodeBlock(None, ["some code"])),
        ("```bash\nsome code\n```", CodeBlock("bash", ["some code"])),
        ("```bash\nsome code\nwith `backticks`\n```", CodeBlock("bash", ["some code", "with `backticks`"])),
        ("```ini\n[header]\nvalue=1\n```", CodeBlock("ini", ["[header]", "value=1"])),
        ("```\nsome code\n\n2 blank lines```", CodeBlock(None, ["some code", "", "2 blank lines"])),
        (">quote", Quote(0, [PT("quote")])),
        (">quote\n>quote2", [Quote(0, [PT("quote")]), Quote(0, [PT("quote2")])]),
        (">quote\n>>nested", [Quote(0, [PT("quote")]), Quote(1, [PT("nested")])]),
        ("hash not #title", PT("hash not #title")),
        ("#h1", Heading(1, [PT("h1")])),
        ("##h2", Heading(2, [PT("h2")])),
        (
            "* list\n* item",
            [ListItem("*", [PT("list")], 0), ListItem("*", [PT("item")], 0)],
        ),
        (
            "1. list\n1. item",
            [OListItem(1, [PT("list")], 0), OListItem(1, [PT("item")], 0)],
        ),
        (
            "1. list\n    99. item\n1. list2",
                [
                    OListItem(1, [PT("list")], 0),
                    OListItem(99, [PT("item")], 4),
                    OListItem(1, [PT("list2")], 0),
                ]
        ),
        ("## *word* word2", Heading(2, [PT(" "), Emphasis([PT("word")]), PT(" word2")])),
    ],
)
def test_simple_cases(parser, md, expected):
    got = parser.parse(md)
    if isinstance(got, Tree):
        assert got.children == expected
    else:
        assert got == expected


@pytest.mark.parametrize(
    "md,expected",
    [
        ("text _italic_ text", [PT("text "), Emphasis([PT("italic")]), PT(" text")]),
        (
            "text **bold** text",
            [
                PT("text "),
                Bold([PT("bold")]),
                PT(" text"),
            ],
        ),
        (
            "text **bold _italic_** text",
            [
                PT("text "),
                Bold([PT("bold "), Emphasis([PT("italic")])]),
                PT(" text"),
            ],
        ),
        ("italic _`code`_", [PT("italic "), Emphasis([InlineCode("code")])]),
        (
            "> quote _italic_ **bold** _**both `code` []()**_",
            Quote(0,
                [
                    PT("quote "),
                    Emphasis([PT("italic")]),
                    PT(" "),
                    Bold([PT("bold")]),
                    PT(" "),
                    Emphasis(
                        [Bold([PT("both "), InlineCode("code"), PT(" "), Anchor([], None)])]
                    ),
                ]
            ),
        ),
        # ("## Title _italic_", []),
        ("<div>[](url)</div>", [HtmlOpenTag("div", []), Anchor([], "url"), HtmlCloseTag("div")]),
        ("[`code`](bbb)", Anchor([InlineCode("code")], "bbb")),
        ("[![](aaa)](bbb)", Anchor([Image(None, "aaa")], "bbb")),
        ("[![x](aaa)](bbb)", Anchor([Image("x", "aaa")], "bbb")),
    ],
)
def test_compound(parser, md, expected):
    got = parser.parse(md)
    if isinstance(got, Tree):
        assert got.children == expected
    else:
        assert got == expected


@pytest.mark.parametrize(
    "md,expected",
    [
        ("[^1]", Ref("1")),
        ("\n[^1]: something", RefItem("1", [PT(" something")])),
        ("{^embed-file: my-file.svg}", CustomDirective("embed-file", ["my-file.svg"])),
        ("{^run-script: script.py --arg 1 2 3}", CustomDirective("run-script", ["script.py", "--arg", "1", "2", "3"])),
        ("{^hint|popover}", Popover("hint", "popover")),
    ],
)
def test_extensions(parser, md, expected):
    got = parser.parse(md)
    assert got == expected


def test_html_oneline(parser):
    html = """<center><video controls><source  src="assets/no-dma.mp4"></source></video></center>"""
    got = parser.parse(html)
    assert got == [
        HtmlOpenTag(elem_type="center", props=[]),
        HtmlOpenTag(elem_type="video", props=[KV(key="controls", val="")]),
        HtmlOpenTag(elem_type="source", props=[KV(key="src", val='"assets/no-dma.mp4"')]),
        HtmlCloseTag(elem_type="source"),
        HtmlCloseTag(elem_type="video"),
        HtmlCloseTag(elem_type="center"),
    ]


def test_html(parser):
    htmlstr = dedent(
        """
    <video controls>
        <source src="/file1" />
        <source src="/file2"></source>
    </video>
    """
    ).strip()

    got = parser.parse(htmlstr)
    assert got == [
        HtmlOpenTag(
            elem_type="video",
            props=[KV(key="controls", val="")],
        ),
        PT(text="    "),
        HtmlSelfCloseTag(
            elem_type="source",
            props=[
                KV(
                    key="src",
                    val='"/file1"',
                ),
                KV(
                    key="src",
                    val='"/file1"',
                ),
            ],
        ),
        PT(text="    "),
        HtmlOpenTag(
            elem_type="source",
            props=[KV(key="src", val='"/file2"')],
        ),
        HtmlCloseTag(elem_type="source"),
        HtmlCloseTag(elem_type="video"),
    ]


def test_code_in_html(parser):
    s = """
    <div>
    ```bash
    hint
    ```
    </div>
    text
    """
    got = parser.parse(s)
    assert got == [
        Token("SPACES", "    "),
        HtmlOpenTag(elem_type="div", props=[]),
        PlainText(text="    "),
        CodeBlock(identifier="bash",
            lines=[
                "    hint",
                "    ",
            ]),
        PlainText(text="    "),
        HtmlCloseTag(elem_type="div"),
        PlainText(text="    text"),
        PlainText(text="    "),
    ]


def test_table(parser):
    table = dedent(
        """
| Address|Perms|Offset|Path|
|---------------------------------|:----|-------:|:----------:|
|`addr`|**bold**|some text|some **bold** text|
|`addr2`|_italic_|some text|[heap]|
    """
    )

    got = parser.parse(table)
    assert got.header == TableRow(
        cells=[
            TableCell(content=[PT(text=" Address")]),
            TableCell(content=[PT(text="Perms")]),
            TableCell(content=[PT(text="Offset")]),
            TableCell(content=[PT(text="Path")]),
        ],
    )
    assert got.divisors == [
        TableDivisor(alignment=Alignment.CENTER),
        TableDivisor(alignment=Alignment.LEFT),
        TableDivisor(alignment=Alignment.RIGHT),
        TableDivisor(alignment=Alignment.CENTER),
    ]
    assert got.rows == [
        TableRow(
            cells=[
                TableCell(content=[InlineCode(text="addr")]),
                TableCell(content=[Bold(content=[PT(text="bold")])]),
                TableCell(content=[PT(text="some text")]),
                TableCell(
                    content=[
                        PT(text="some "),
                        Bold(content=[PT(text="bold")]),
                        PT(text=" text"),
                    ],
                ),
            ],
        ),
        TableRow(
            cells=[
                TableCell(content=[InlineCode(text="addr2")]),
                TableCell(content=[Emphasis(content=[PT(text="italic")])]),
                TableCell(content=[PT(text="some text")]),
                TableCell(content=[PT(text="[heap]")]),
            ],
        ),
    ]


@pytest.mark.parametrize(
    "md,expected",
    [
        ("a word with\\_underscore", PT("a word with_underscore")),
        ("some void\\* data", PT("some void* data")),
        (r"shrug ¯\\\_(ツ)\_/¯", PT(r"shrug ¯\_(ツ)_/¯")),
    ],
)
def test_escapes(parser, md, expected):
    got = parser.parse(md)
    if isinstance(got, Tree):
        assert got.children == expected
    else:
        assert got == expected


@pytest.mark.parametrize(
    "md,expected",
    [
        ("[word in brackets]", PT("[word in brackets]")),
        ("{word in cbrackets}", PT("{word in cbrackets}")),
        # FIXME ("unpaired ` bquote\n", PT("unpaired ` bquote")),
        # FIXME ("word with a | in it", PT("word with a | in it")),
        ("an arrow -> right", PT("an arrow -> right")),
        ('<div key="">', HtmlOpenTag("div", [KV("key", '""')])),
    ],
)
def test_edge_cases(parser, md, expected):
    got = parser.parse(md)
    if isinstance(got, Tree):
        assert got.children == expected
    else:
        assert got == expected



@pytest.mark.parametrize(
    "md,expected",
    [
        ("text 1<sup>D</sup>", [PT("text 1"), Superscript([PT("D")])]),
        ("text 2<sub>**D**</sub>", [PT("text 2"), Subscript([Bold([PT("D")])])]),
    ],
)
def test_inline_html(parser, md, expected):
    got = parser.parse(md)
    if isinstance(got, Tree):
        assert got.children == expected
    else:
        assert got == expected
