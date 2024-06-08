import pytest

from markdown_parser.parser import make_parser
from markdown_parser.nodes import *


@pytest.fixture(scope="session")
def parser():
    p = make_parser()
    yield p


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
        ("_oneword_", Emphasis([PT("oneword")])),
        ("_two words_", Emphasis([PT("two words")])),
        ("_a_", Emphasis([PT("a")])),
        ("**oneword**", Bold([PT("oneword")])),
        ("**two words**", Bold([PT("two words")])),
        ("**a**", Bold([PT("a")])),
        ("`code`", InlineCode("code")),
        ("`code words()`", InlineCode("code words()")),
        ("[anchor text](url)", Anchor("anchor text", "url")),
        ("[anchor text]()", Anchor("anchor text", None)),
        ("[]()", Anchor(None, None)),
        ("![alt text](url)", Image("alt text", "url")),
        ("![alt text]()", Image("alt text", None)),
        ("![]()", Image(None, None)),
        ("```\nsome code\n```", CodeBlock(None, ["some code"])),
        ("```bash\nsome code\n```", CodeBlock("bash", ["some code"])),
        ("```ini\n[header]\nvalue=1\n```", CodeBlock("ini", ["[header]", "value=1"])),
        (">quote", Quote([PT("quote")])),
    ],
)
def test_simple_cases(parser, md, expected):
    got = parser.parse(md)
    assert got == expected


@pytest.mark.parametrize(
    "md,expected",
    [
        (
            "text _italic_ text",
            [
                PT("text "),
                Emphasis([PT("italic")]),
                PT(" text"),
            ],
        ),
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
                Bold(
                    [
                        PT("bold "),
                        Emphasis([PT("italic")]),
                    ]
                ),
                PT(" text"),
            ],
        ),
        ("italic _`code`_", [PT("italic "), Emphasis([InlineCode("code")])]),
        (
            "text > quote _italic_ **bold** _**both `code` []()**_",
            [
                PT("text "),
                Quote(
                    [
                        PT(" quote "),
                        Emphasis([PT("italic")]),
                        PT(" "),
                        Bold([PT("bold")]),
                        PT(" "),
                        Emphasis(
                            [
                                Bold([PT("both "), InlineCode("code"), PT(" "), Anchor(None, None)]),
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ],
)
def test_compound(parser, md, expected):
    got = parser.parse(md)
    assert got.children == expected


@pytest.mark.parametrize(
    "md,expected",
    [
        ("[^1]", Ref("1")),
        ("[^1]: something", RefItem("1", [PT(" something")])),
        ("{^embed-file: my-file.svg}", CustomDirective("embed-file", ["my-file.svg"])),
        ("{^run-script: script.py --arg 1 2 3}", CustomDirective("run-script", ["script.py", "--arg", "1", "2", "3"])),
        ("{^hint|popover}", Popover("hint", "popover")),
    ],
)
def test_extensions(parser, md, expected):
    got = parser.parse(md)
    assert got == expected