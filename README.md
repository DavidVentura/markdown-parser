# Markdown parser

Parses a subset of Markdown.

The subset is defined as to remove ambiguity; the main difference is that "block elements" (code, quote, html, heading, table, lists)
**must** have a preceding newline.

The other intentional difference is that unpaired symbols (`*`, `_`) **in text** must be escaped (as `\_` `\*`), this includes underscores in words, so `a_word` becomes `a\_word`.

This is valid:
```md
Some text

# A heading
```

and this is not (no newline):
```md
Some text
# A heading
```

This is valid:
```md
Some text

<div>...</div>
```

This is not (no newline):
```md
Some text
<div>...</div>
```

The only inline HTML elements that are supported are: `sup`, `sub`, `small`, `smaller`.

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

