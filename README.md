# Markdown parser

Parses a subset of Markdown.

The subset is defined as to remove ambiguity; the main differences are:

- "Ambiguous block elements" (quote, html, heading, table, lists) **must** have a preceding newline.
    - The only inline HTML elements that are supported are: `sup`, `sub`, `small`, `smaller`.
- Bare symbols (`*`, `_`, `>`, `<`) **in text** must be escaped (as `\_`, `\*`, ...), this includes underscores in words, so `a_word` becomes `a\_word`.
- Multi-line list items are not allowed
```
* an item
this is just text
```

An example on blocks which require newline, this is not valid:

```md
Some text
# A heading
```

A blank line must precede the heading:
```md
Some text

# A heading
```

## Structured format

Input:
```
text > quote _italic_ **bold** _**both `code` []()**_
```

```python
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
                    Bold([PT("both "),
                    InlineCode("code"),
                    PT(" "),
                    Anchor(None, None)]),
                ]
            ),
        ]
    ),
]
```
where `PT` is `PlainText`

## Not yet implemented

* HTML entities (`&mdash;`)

## Unsupported (and no plans)

* Headings with underlines
```
Heading
-------
```
* Code with indentation
```
    this would automatically
    make code blocks
    without triple-backtick
```

## Extensions

* Popover: `{^hint|content}`
* Custom directive: `{^directive-name: arg1 arg2}`
* Footnotes: `[^reference]` and `[^reference]: markup`

