# Lift a sequence of elements  into a higher level concept
# (ListItem, ListItem, ListItem) -> (List([ListItem, ...]))
# (HtmlOpenTag, HtmlOpenTag, HtmlCloseTag, HtmlCloseTag) -> (<div><p></p></div>)
# (Quote, Quote, Quote) -> (Quote([entries]))
# (Hr, PlainText, Hr) -> Metadata

from dataclasses import dataclass

from markdown_parser.parser import make_parser
from markdown_parser.nodes import *
from typing import Type, TypeVar

T = TypeVar("T")


@dataclass
class Paragraph(Node):
    children: list[Node]


@dataclass
class QuoteBlock(Node):
    children: list["FullQuote"]

@dataclass
class FullQuote(Node):
    content: list[Node]
    indent_level: int  # meta only
    children: list["FullQuote"]


@dataclass
class FullListItem(Node):
    marker: UnorderedListIndicator | OrderedListIndicator
    content: list[Node]
    indent_level: int  # meta only
    children: list["FullListItem"]

@dataclass
class List(Node):
    marker: UnorderedListIndicator | OrderedListIndicator
    children: list["FullListItem"]


def pop(l: list[T]) -> T | None:
    if len(l):
        return l.pop(0)
    return None


def match_until_delim(items: list[Node], must_match, delim) -> int | None:
    """
    Check whether `items` is composed of [must_match, must_match, must_match, .., delim].
    Return the number of matches, including `delim`.

    Returns None if the sequence does not match
    """
    matching = 0
    for item in items:
        if isinstance(item, delim):
            return matching + 1
        elif isinstance(item, must_match):
            matching += 1
        else:
            return None
    return None


def match_while(items: list[Node], must_match) -> int | None:
    matching = 0
    for item in items:
        if isinstance(item, must_match):
            matching += 1
        else:
            return matching
    return matching


def make_meta_from_lines(lines: list[PlainText]) -> Metadata:
    entries = []
    for line in lines:
        k, _, v = line.text.partition(":")
        k = k.strip()
        v = v.strip()
        entries.append(KV(k, v))
    return Metadata(entries)

def li_to_full(item: ListItem | OListItem, indent_level) -> FullListItem:
    if isinstance(item, OListItem):
        ind = OrderedListIndicator(item.index)
    elif isinstance(item, ListItem):
        ind = UnorderedListIndicator(item.marker)
    else:
        assert False, item
    return FullListItem(ind, item.content, indent_level, [])

def li_at_level(items: list[FullListItem], level: int) -> list[FullListItem]:
    ret = []
    for i in items:
        if i.indent_level == level:
            ret.append(i)
        if i.indent_level < level:
            ret.extend(li_at_level(i.children, level))
    return ret

def make_list(items: list[ListItem | OListItem]) -> List:
    """
    Convert a flat list of ListItem | OListItem, such as
    [ListItem(indentation=n), ListItem(indentation=n+1), ListItem(indentation=n)]
    into a tree shape
    List(content=[
        FullListItem(children=[FullListItem]),
        FullListItem(children=[]),
        ])
    """
    rlist: List | None = None
    ret: list[FullListItem] = []
    while item := pop(items):
        indent_level = item.indentation // 4  # hardcoding 4 spaces?
        full = li_to_full(item, indent_level)
        if rlist is None:
            rlist = List(full.marker, [])
            ret.append(full)
            continue

        mb_parents = li_at_level(ret, indent_level - 1)
        if mb_parents:
            last = mb_parents[-1]
            last.children.append(full)
        else:
            # there's no parents only if all items are at the same level
            ret.append(full)

    assert rlist is not None
    rlist.children = ret
    return rlist


def find_q_parent(items: list[FullQuote], to_add: FullQuote) -> FullQuote | None:
    candidates = [i for i in items if i.indent_level < to_add.indent_level]
    if not candidates:
        return None
    last = candidates[-1]
    if not last.children:
        return last
    mb_child_parent = find_q_parent(last.children, to_add)
    if mb_child_parent:
        return mb_child_parent
    return last

def make_quote(items: list[Quote]) -> QuoteBlock:
    """
    Convert a flat list of Quote, such as:
    Quote(level=0, content=[Text1])
    Quote(level=1, content=[Text2])
    Quote(level=0, content=[Text3])
    into
    FullQuote(content=[
        Text1,
        FullQuote(content=[Text2])
        Text3,
    ])
    """
    flattened: list[FullQuote] = []
    while item := pop(items):
        fq = FullQuote(item.content, indent_level=item.level, children=[])
        if not flattened:
            flattened.append(fq)
            continue
        mb_parent = find_q_parent(flattened, fq)
        if mb_parent:
            mb_parent.children.append(fq)
        else:
            assert len(flattened) == 1, flattened # ehh idk
            flattened.append(fq)

    return QuoteBlock(flattened)

def idx_of_last_block(items: list[Node]) -> int | None:
    ends_paragraph = (Heading, CodeBlock, List, QuoteBlock, RefItem, Table, Hr, Metadata, Paragraph)
    ret = None
    for idx, item in list(enumerate(items))[::-1]:
        if isinstance(item, ends_paragraph):
            return ret
        ret = idx
    return ret

def lift(items: list[Node]) -> list[Node]:
    # [X] N listItems
    # [X] 3 items (hr, plaintext, hr)
    # [X] N quotes
    # [ ] N html tags
    ret: list[Node] = []
    while node := pop(items):
        match node:
            case ParBreak():
                idx = idx_of_last_block(ret)
                if idx is not None:
                    p = Paragraph(ret[idx:])
                    ret = ret[:idx]
                    ret.append(p)
                else:
                    ret.append(ParBreak())
            case Hr():
                # Metadata must be at the start of the file
                if ret:
                    # normal rule
                    ret.append(node)
                    continue

                num_match = match_until_delim(items, PlainText, Hr)
                if num_match is None:
                    # found something other than PlainText + Hr so this is not a meta block
                    ret.append(node)
                    continue

                meta_kv = items[: num_match - 1]
                ret.append(make_meta_from_lines(meta_kv))
                matched_meta = True
                items = items[num_match:]
            case ListBlock():
                ret.append(make_list(node.children))
            case Quote():
                num_match = match_while(items, Quote)
                if num_match is None:
                    continue
                quotes = [node] + items[:num_match]
                items = items[num_match:]
                ret.append(make_quote(quotes))
            case _:
                ret.append(node)

    # final paragraph
    idx = idx_of_last_block(ret)
    if idx is not None:
        p = Paragraph(ret[idx:])
        ret = ret[:idx]
        ret.append(p)
    return ret


if __name__ == "__main__":
    parser = make_parser()
    text = """
---
title: Cursing a process' vDSO for time hacking
date: 2022-11-30
tags: cursed, rust
description: Replacing time-related vDSO entries at runtime
---
"""

    i = parser.parse(text)
    from pprint import pprint
    pprint(lift(i))
    #pprint(lift(i)[0].children, width=200)
