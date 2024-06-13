from markdown_parser.lifter import FullQuote, List, lift, FullListItem, QuoteBlock
from markdown_parser.nodes import Metadata, OrderedListIndicator, PlainText, UnorderedListIndicator

def test_unordered_list(parser):
    text = """
    + item1
        + item2
            + item3
        + item4
    + item5"""
    i = parser.parse(text)
    got = lift([i])
    assert len(got) == 1
    l = got[0]
    assert isinstance(l, List)
    assert len(l.children) == 2

    item1 = l.children[0]
    assert item1.content == [PlainText('item1')]
    assert len(item1.children) == 2

    # item1 -> item2
    item2 = item1.children[0]
    assert item2.content == [PlainText('item2')]
    assert len(item2.children) == 1

    # item2 -> item3
    item3 = item2.children[0]
    assert item3.content == [PlainText('item3')]
    assert len(item3.children) == 0

    # item1 -> item4
    item4 = item1.children[1]
    assert item4.content == [PlainText('item4')]
    assert len(item4.children) == 0

    item5 = l.children[1]
    assert item5.content == [PlainText('item5')]
    assert len(item5.children) == 0

def test_ordered_list(parser):
    text = """
    5. item1
        1. item2
            4. item3
        4. item4
    4. item5"""
    i = parser.parse(text)
    got = lift([i])
    assert len(got) == 1
    l = got[0]
    assert isinstance(l, List)
    assert len(l.children) == 2

    item1 = l.children[0]
    assert isinstance(item1.marker, OrderedListIndicator)
    assert item1.marker.num == 5
    assert item1.content == [PlainText('item1')]
    assert len(item1.children) == 2

    # item1 -> item2
    item2 = item1.children[0]
    assert isinstance(item2.marker, OrderedListIndicator)
    assert item2.marker.num == 1
    assert item2.content == [PlainText('item2')]
    assert len(item2.children) == 1

    # item2 -> item3
    item3 = item2.children[0]
    assert isinstance(item3.marker, OrderedListIndicator)
    assert item3.marker.num == 4
    assert item3.content == [PlainText('item3')]
    assert len(item3.children) == 0

    # item1 -> item4
    item4 = item1.children[1]
    assert isinstance(item4.marker, OrderedListIndicator)
    assert item4.marker.num == 4
    assert item4.content == [PlainText('item4')]
    assert len(item4.children) == 0

    item5 = l.children[1]
    assert isinstance(item5.marker, OrderedListIndicator)
    assert item5.marker.num == 4
    assert item5.content == [PlainText('item5')]
    assert len(item5.children) == 0


def test_metadata(parser):
    text = """
---
title: the title
date: 2022-11-30
tags: tag1, tag2
description: some description
---
"""

    i = parser.parse(text)
    got = lift(i)
    assert len(got) == 1
    l = got[0]
    assert isinstance(l, Metadata)
    for e in l.entries:
        match e.key:
            case "title":
                assert e.val == "the title"

            case "date":
                assert e.val == "2022-11-30"
            case "tags":
                assert e.val == "tag1, tag2"
            case "description":
                assert e.val == "some description"
            case other:
                assert False, f'Unexpected key {other}'


def test_quote_1(parser):
    text = """
> quote1
>> quote nested1
>> quote nested2
"""

    i = parser.parse(text)
    got = lift(i)
    assert len(got) == 1
    q = got[0]
    assert isinstance(q, QuoteBlock)
    assert len(q.children) == 1
    root = q.children[0]
    assert root.content == [PlainText("quote1")]
    assert len(root.children) == 2
    c1, c2 = root.children

    assert c1.content == [PlainText("quote nested1")]
    assert c2.content == [PlainText("quote nested2")]


def test_quote_2(parser):
    text = """
> quote1
>> quote2
> quote3
>> quote4
"""

    i = parser.parse(text)
    got = lift(i)
    assert len(got) == 1
    q = got[0]
    assert isinstance(q, QuoteBlock)
    assert len(q.children) == 2
    root1, root2 = q.children

    assert root1.content == [PlainText("quote1")]
    assert len(root1.children) == 1
    c1 = root1.children[0]
    assert c1.content == [PlainText("quote2")]

    assert root2.content == [PlainText("quote3")]
    assert len(root2.children) == 1
    c2 = root2.children[0]
    assert c2.content == [PlainText("quote4")]
