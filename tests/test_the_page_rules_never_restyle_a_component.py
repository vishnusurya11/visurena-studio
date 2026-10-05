"""pages.css is the last cascade layer, so any rule there beats every component
whatever its specificity.  The pre-redesign page rules used that to restyle the
new components: a global `th`/`td` over `.dgrid th`, `button.btn` over `.btn`, a
second `.sbar`, `.muted`, `.small`, `.spacer`, a bare `.gate` over `.gates .gate`,
`.cols` over the key sheet's columns, and `.live` over the GPU card's dot.  The page
layer now only adds: no selector it writes is a component's own selector, and none
is a bare element (element defaults live in the base layer)."""
from __future__ import annotations

import re

from board_css_rules import all_rules

ELEMENT = re.compile(r"^[a-z][a-z0-9]*$")


def _selectors(*names: str) -> set[str]:
    return {s.strip() for r in all_rules(*names) if "keyframes" not in r.selector
            for s in r.selector.split(",")}


def _subjects(*names: str) -> set[str]:
    """The compound each selector styles (its last one): `.gates .gate` -> `.gate`."""
    return {re.split(r"\s*[ >+~]\s*", s)[-1] for s in _selectors(*names)}


def test_no_page_selector_is_a_component_selector():
    assert _selectors("pages") & _selectors("components") == set()


def test_no_page_rule_restyles_a_bare_element():
    for sel in _selectors("pages"):
        assert not ELEMENT.match(sel), sel


def test_no_bare_page_class_is_what_a_component_styles():
    """A one-compound page rule (`.gate`, `.cols`, `.live`) hits every element a component
    styles under that name; `.pill.green` (an old colour word) may stay until its page is ported."""
    taken = _subjects("components")
    for sel in _selectors("pages"):
        if not re.search(r"[ >+~]", sel):
            assert sel not in taken, sel


def test_the_subject_reader_takes_the_last_compound():
    assert re.split(r"\s*[ >+~]\s*", ".gates > .gate.ok")[-1] == ".gate.ok"


def test_the_page_layer_has_no_root_block():
    assert not any(r.selector.startswith(":root") for r in all_rules("pages"))
