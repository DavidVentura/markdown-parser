# Lift a sequence of elements  into a higher level concept
# (ListItem, ListItem, ListItem) -> (List([ListItem, ...]))
# (HtmlOpenTag, HtmlOpenTag, HtmlCloseTag, HtmlCloseTag) -> (<div><p></p></div>)
# (Quote, Quote, Quote) -> (Quote([entries]))
# (Hr, PlainText, Hr) -> Metadata

from dataclasses import dataclass

from markdown_parser.parser import make_parser
from markdown_parser.nodes import (
    KV,
    Metadata,
    Node,
    HtmlOpenTag,
    ListItem,
    OListItem,
    PlainText,
    Quote,
    Hr,
    UnorderedListIndicator,
    OrderedListIndicator,
    ListBlock,
)
from typing import TypeVar

T = TypeVar("T")


@dataclass
class FullListItem(Node):
    marker: UnorderedListIndicator | OrderedListIndicator
    content: list[Node]
    indent_level: int
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
    prev_indent = None
    """
    - a
        - a
    - a
        - a
        - b
    - a
    - b
    """

    rlist: List | None = None
    ret: list[FullListItem] = []
    while item := pop(items):
        indent_level = item.indentation // 4  # hardcoding 4 spaces?
        full = li_to_full(item, indent_level)
        mb_parents = li_at_level(ret, indent_level - 1)
        if prev_indent is not None:
            if mb_parents:
                last = mb_parents[-1]
                last.children.append(full)
            else:
                # there's no parents only if all items are at the same level
                ret.append(full)
            prev_indent = indent_level
        else:
            prev_indent = indent_level
            rlist = List(full.marker, [])
            ret.append(full)

    assert rlist is not None
    rlist.children = ret
    return rlist


def lift(items: list[Node]) -> list[Node]:
    # [X] N listItems
    # [X] 3 items (hr, plaintext, hr)
    # [ ] N html tags
    # [ ] N quotes
    ret: list[Node] = []
    matched_meta = False
    while node := pop(items):
        match node:
            case Hr():
                # Metadata may only happen once per file
                if matched_meta:
                    continue
                num_match = match_until_delim(items, PlainText, Hr)
                if num_match is None:
                    continue
                meta_kv = items[: num_match - 1]
                ret.append(make_meta_from_lines(meta_kv))
                matched_meta = True
                items = items[num_match:]
            case ListBlock():
                ret.append(make_list(node.children))
            case _:
                ret.append(node)
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
