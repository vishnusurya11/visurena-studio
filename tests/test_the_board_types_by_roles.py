"""The board sets type by role (ruling PKG-3, row 3.6; P09.2).

Ten roles, `--t-micro` (11 px) to `--t-hero` (60 px), live in tokens.css; nothing
on the board is smaller than 11 px.  components.css and pages.css write every
font size through a role -- never a raw px, em or rem -- so the census cannot drift
back to the 22 sizes (9.5, 10.5, 12.5 ...) the old page rules carried.  Form
controls inherit the page's font (the stray 13.33 px Arial)."""
from __future__ import annotations

import re

from board_css import block, css, declarations
from board_css_rules import rules, values

ROLES = ("micro", "label", "body", "lead", "title", "h3", "sub", "h2", "h1", "hero")
ROLE = re.compile(r"var\(--t-(%s)\)" % "|".join(ROLES))
FLOOR = 11


def _tokens() -> dict[str, str]:
    return declarations(block(block(css("tokens"), "@layer tokens {"), ":root{"))


def test_the_ten_roles_run_from_eleven_to_sixty_px():
    t = _tokens()
    sizes = [int(t[f"t-{r}"].removesuffix("px")) for r in ROLES]
    assert sizes == sorted(sizes) and sizes[0] == FLOOR and sizes[-1] == 60


def _shorthand_size(value: str) -> str:
    """The size part of a `font:` shorthand (the token before `/` or the family)."""
    m = re.search(r"(var\(--t-[\w-]+\)|\d*\.?\d+(px|em|rem|%)|inherit)", value)
    return m.group(1) if m else value


def test_the_shorthand_reader_finds_the_size():
    assert _shorthand_size("500 var(--t-label)/16px var(--f-mono)") == "var(--t-label)"
    assert _shorthand_size("600 12.5px/1 var(--f-mono)") == "12.5px"


def _sizes() -> list[tuple[str, str, str]]:
    out = []
    for name in ("components", "pages"):
        out += [(name, s, v) for s, v in values(css(name), "font-size")]
        out += [(name, s, _shorthand_size(v)) for s, v in values(css(name), "font") if v != "inherit"]
    return out


def test_every_font_size_is_a_role():
    for name, sel, size in _sizes():
        assert ROLE.fullmatch(size) or size == "inherit", (name, sel, size)


def test_form_controls_inherit_the_font():
    found = [r for r in rules(css("components")) if "button" in r.selector and "textarea" in r.selector]
    assert any("font:inherit" in r.body.replace(" ", "") for r in found)


def test_no_role_is_arial_or_a_bare_ui_font():
    t = _tokens()
    for fam in ("f-display", "f-text", "f-mono"):
        assert not t[fam].startswith(("Arial", "system-ui")), t[fam]
