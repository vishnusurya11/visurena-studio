"""The board's stylesheets as rules (PKG-3 lints): every leaf rule as
(selector, body, at-rule context), every @keyframes block by name, and every
declaration of one property -- read from the three files under
studio/command_center/static/css.  Pure text; no browser."""
from __future__ import annotations

import re
from typing import Iterator, NamedTuple

from board_css import css

SHEETS = ("tokens", "components", "pages", "unit", "lists")
GROUPS = ("@layer", "@media", "@supports", "@container")


class Rule(NamedTuple):
    selector: str
    body: str
    context: str


def strip_comments(text: str) -> str:
    """The sheet without /* ... */ comments."""
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _close(text: str, i: int) -> int:
    """The index of the brace that closes the one opened at text[i]."""
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return j
    raise ValueError("unclosed block")


def _blocks(text: str) -> Iterator[tuple[str, str]]:
    """(prelude, body) for each top-level block of a sheet's text."""
    i = 0
    while (k := text.find("{", i)) != -1:
        end = _close(text, k)
        prelude = re.sub(r"@layer [\w, -]+;", "", text[i:k]).strip()
        yield prelude, text[k + 1:end]
        i = end + 1


def rules(text: str, context: str = "") -> Iterator[Rule]:
    """Every leaf style rule, recursing into grouping at-rules; @keyframes,
    @font-face and @property bodies are not style rules and are skipped."""
    for prelude, body in _blocks(strip_comments(text)):
        if prelude.startswith(GROUPS):
            yield from rules(body, f"{context} {prelude}".strip())
        elif not prelude.startswith("@"):
            yield Rule(prelude, body, context)


def keyframes(text: str) -> dict[str, str]:
    """{name: body} for every @keyframes in a sheet, at any depth."""
    out = {}
    for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", strip_comments(text)):
        start = m.end() - 1
        out[m.group(1)] = text_between(strip_comments(text), start)
    return out


def text_between(text: str, i: int) -> str:
    """The body of the block opened at text[i]."""
    return text[i + 1:_close(text, i)]


def values(text: str, prop: str) -> list[tuple[str, str]]:
    """(selector, value) for every `prop:` declaration in a sheet's style rules."""
    out = []
    for r in rules(text):
        for m in re.finditer(rf"(?<![\w-]){re.escape(prop)}\s*:\s*([^;}}]+)", r.body):
            out.append((r.selector, m.group(1).strip()))
    return out


def all_rules(*names: str) -> list[Rule]:
    """The leaf rules of the named sheets (default: all three)."""
    return [r for n in (names or SHEETS) for r in rules(css(n))]
