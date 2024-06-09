# Markdown parser

Parses a subset of Markdown. Generates a tree:

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

* Escaping literal symbols (`\*` generates `*` in a text item)
* HTML entities (`&mdash;`)

## Unsupported (and no plans)

* Italics with single star `*text*`
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

