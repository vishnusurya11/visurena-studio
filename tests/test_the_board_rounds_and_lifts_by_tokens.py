"""Corners and elevation come from tokens (ruling PKG-3, row 3.7; P09.7, P09.11).

A radius is `var(--r-*)`, `0` or `50%` -- the 3, 5, 7 px drift is gone.  On Studio
black a drop shadow does nothing, so elevation is a surface plus a ring: a
`box-shadow` outside tokens.css is a ring or an inset bar (no blur), or a token;
the one real shadow (`--shadow-pop`) belongs to floating layers, and each `--e-*`
token means the same thing in both themes."""
from __future__ import annotations

import re

from board_css import block, css, declarations
from board_css_rules import values

RADIUS_PART = re.compile(r"var\(--r-[\w-]+\)|0|50%|inherit")
LENGTH = re.compile(r"-?\d*\.?\d+(px)?$")


def test_every_radius_is_a_token_zero_or_round():
    for name in ("components", "pages"):
        for sel, v in values(css(name), "border-radius"):
            assert all(RADIUS_PART.fullmatch(p) for p in v.split()), (name, sel, v)


def _parts(value: str) -> list[str]:
    """A box-shadow list split on the commas that are not inside a function."""
    out, depth, cur = [], 0, ""
    for ch in value:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return out + [cur.strip()]


def _blurless(part: str) -> bool:
    """A ring or an inset bar: its third length (the blur) is zero, or the part is a token."""
    if part == "none" or re.fullmatch(r"var\(--[\w-]+\)", part):
        return True
    lengths = [w for w in part.removeprefix("inset").split() if LENGTH.fullmatch(w)]
    return len(lengths) >= 3 and float(lengths[2].removesuffix("px") or 0) == 0


def test_the_ring_reader_tells_a_ring_from_a_drop():
    assert _blurless("inset 0 0 0 1px var(--rule)") and _blurless("0 0 0 3px color-mix(in srgb,red 1%,blue)")
    assert not _blurless("0 4px 16px rgba(0,0,0,.12)")


def test_every_shadow_outside_the_tokens_is_a_ring_or_a_token():
    for name in ("components", "pages"):
        for sel, v in values(css(name), "box-shadow"):
            assert all(_blurless(p) for p in _parts(v)), (name, sel, v)


def test_elevation_means_one_thing_in_both_themes():
    layer = block(css("tokens"), "@layer tokens {")
    light = declarations(block(layer, ':root[data-theme="light"]{'))
    assert not {"e-1", "e-2", "e-3"} & set(light)
    dark = declarations(block(layer, ":root{"))
    assert dark["e-3"] == "var(--shadow-pop)"
