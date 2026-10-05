"""The board moves by one set of motion tokens (ruling PKG-3, rows 3.1-3.3; P02).

3.1  Durations and easings live only in tokens.css: one `:root` defines `--d0..--d4`,
     `--d-exit`, `--d-wash` and three easings; no other sheet writes a `ms`/`s` literal or
     redefines a `--d*` token (pages.css once redefined them on its own `:root`).
3.2  Still mode is a token flip -- under prefers-reduced-motion AND `[data-motion=still]` --
     that keeps `--d1` (hover feedback is not motion) and turns every loop to one pass.
     There is no blanket `*{transition:none}` any more.
3.3  One loop: `infinite` is written once, as the `--loop` token the still flip turns
     off; at most three selectors may run an animation on `var(--loop)` (the GPU card
     dot, and the running rail step on the running unit's page)."""
from __future__ import annotations

import re

from board_css import block, css, declarations
from board_css_rules import all_rules, rules, strip_comments, values

DURATION = re.compile(r"(?<![\w.#-])\d*\.?\d+m?s(?![\w-])")
LOOPERS = 3


def test_a_duration_literal_is_written_only_in_the_tokens_file():
    for name in ("components", "pages"):
        found = DURATION.findall(strip_comments(css(name)))
        assert found == [], (name, found)


def test_the_duration_pattern_finds_seconds_and_milliseconds():
    assert DURATION.findall("a{transition:color 120ms,b 2.4s;width:12px}") == ["120ms", "2.4s"]


def test_one_root_defines_the_motion_tokens():
    root = declarations(block(block(css("tokens"), "@layer tokens {"), ":root{"))
    for name in ("d0", "d1", "d2", "d3", "d4", "d-exit", "d-wash", "ease-out", "ease-in", "ease-std", "loop"):
        assert name in root, name
    assert root["d2"] == "200ms" and root["loop"] == "infinite"


def test_no_other_sheet_redefines_a_motion_token():
    for name in ("components", "pages"):
        for r in rules(css(name)):
            assert not re.search(r"--(d\d|d-[\w-]+|ease-[\w-]+|loop)\s*:", r.body), (name, r.selector)


def _still_blocks() -> list[str]:
    """The bodies that flip the board still: the reduced-motion media and data-motion=still."""
    return [r.body for r in rules(css("tokens"))
            if "still" in r.selector or "prefers-reduced-motion" in r.context]


def test_still_mode_is_a_token_flip_that_keeps_hover_feedback():
    bodies = _still_blocks()
    assert len(bodies) >= 2, "reduced motion and data-motion=still both flip the tokens"
    for body in bodies:
        flipped = declarations(body)
        assert flipped.get("loop") == "1" and "d1" not in flipped, flipped
        assert all(flipped.get(d) for d in ("d2", "d3", "d4", "d-wash")), flipped


def test_there_is_no_blanket_kill_of_every_transition():
    for r in all_rules("components", "pages"):
        assert not ("transition:none" in r.body.replace(" ", "") and "*" in r.selector), r


def test_infinite_is_written_once_as_the_loop_token():
    assert "infinite" not in strip_comments(css("components") + css("pages"))
    assert strip_comments(css("tokens")).count("infinite") == 1


def test_at_most_three_selectors_loop():
    loopers = {sel for name in ("components", "pages") for sel, v in values(css(name), "animation")
               if "var(--loop)" in v}
    assert 1 <= len(loopers) <= LOOPERS, loopers


def test_the_gpu_dot_loops_and_a_state_glyph_does_not():
    loopers = " ".join(sel for sel, v in values(css("components"), "animation") if "var(--loop)" in v)
    assert ".gc-dot" in loopers
    for sel, v in values(css("components") + css("pages"), "animation"):
        if re.search(r"\.(running|blue)\b", sel):
            assert "var(--loop)" not in v, sel
