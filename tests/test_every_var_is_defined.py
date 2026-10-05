"""Every `var(--x)` the board uses is declared somewhere it can reach (plan F4):
in the stylesheets, on an element's inline style in a template, or by the page's
own scripts -- a misspelt token is a silent transparent, so it is a failure.  A
`var(--x, fallback)` carries its own answer and is exempt."""
from __future__ import annotations

import re

from board_css import CSS, STATIC, TEMPLATES

SOURCES = [*CSS.glob("*.css"), *TEMPLATES.glob("*.html"), *STATIC.glob("*.js")]


def _text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in SOURCES if p.name != "htmx.min.js")


def used(text: str) -> set[str]:
    """Names read with `var(--x)` and no fallback."""
    return set(re.findall(r"var\(--([\w-]+)\)", text))


def declared(text: str) -> set[str]:
    """Names declared as `--x:` (CSS, inline style), registered with @property, or set by a script."""
    names = set(re.findall(r"--([\w-]+)\s*:", text))
    names |= set(re.findall(r"@property\s+--([\w-]+)", text))
    names |= set(re.findall(r"""setProperty\(\s*['"]--([\w-]+)""", text))
    return names


def test_the_reader_finds_uses_and_declarations():
    assert used("a{color:var(--ink);b:var(--x, 1)}") == {"ink"}
    assert declared(":root{--ink:#000} @property --p{} el.style.setProperty('--dev', 1)") == {"ink", "p", "dev"}


def test_every_var_is_defined():
    text = _text()
    missing = sorted(used(text) - declared(text))
    assert not missing, missing
