"""What the board's CSS does when the studio changes (ruling PKG-3, rows 3.4, 3.5,
3.8 targets, 3.9; contract C3).

3.4  A row pulse.js marks `.chg` washes once over `--d-wash` -- `--think`, `--accent` on
     a failure, `--qc` on a flag; a row htmx adds fades in (opacity only); a done check
     draws once; `<html data-stale>` desaturates and turns the "as of" line accent; a
     `.tile:target` is a still outline plus one wash, never a 3x pulse.
3.5  The live card's rail fills and sweeps on `transform:scaleX` (no `width` keyframes);
     the live card rule is `section.live`, so the GPU card's `.gc-dot` (flex:none) is
     never drawn as a bordered box.
3.8  Targets: 24 px floor, 44 px on a coarse pointer; anchors land below the sticky bar.
3.9  Reserved boxes: a chart has its aspect ratio and `contain`; no shimmer anywhere; a
     placeholder is static and shows only after `--d-late`."""
from __future__ import annotations

import re

from board_css import css
from board_css_rules import all_rules, keyframes, rules, values


def _bodies(pred) -> str:
    return " ".join(r.body for r in all_rules("components", "pages") if pred(r))


def test_a_changed_row_washes_once_in_the_state_colour():
    chg = _bodies(lambda r: ".chg" in r.selector)
    assert "var(--d-wash)" in chg and "var(--loop)" not in chg
    for colour in ("--think", "--accent", "--qc"):
        assert f"var({colour})" in chg, colour


def test_a_row_htmx_adds_fades_in_and_never_slides():
    added = _bodies(lambda r: "htmx-added" in r.selector)
    assert "opacity:0" in added.replace(" ", "") and "transform" not in added and "height" not in added


def test_a_done_check_draws_once():
    assert "stroke-dashoffset" in " ".join(keyframes(css("components")).values())
    assert "draw" in _bodies(lambda r: ".chg" in r.selector and "done" in r.selector)


def test_stale_data_desaturates_and_its_as_of_turns_accent():
    stale = [r for r in all_rules("components") if "[data-stale]" in r.selector]
    assert any("saturate(.4)" in r.body for r in stale)
    assert any(".asof" in r.selector and "var(--accent)" in r.body for r in stale)


def test_a_target_tile_is_a_still_outline_and_one_wash():
    target = [r for r in all_rules("pages") if ".tile:target" in r.selector]
    assert target and all("var(--loop)" not in r.body and " 3" not in r.body for r in target)
    assert any("outline" in r.body for r in target)


def test_no_keyframes_animate_width():
    for name in ("components", "pages"):
        for kf, body in keyframes(css(name)).items():
            assert not re.search(r"(?<![\w-])width\s*:", body), (name, kf)


def test_the_rail_fills_on_scale_not_width():
    rail = _bodies(lambda r: ".lv-rail" in r.selector and "i::before" in r.selector)
    assert "scaleX" in rail and "transition:width" not in rail.replace(" ", "")


def test_the_live_card_rule_is_scoped_to_its_section():
    for r in all_rules("pages"):
        for sel in r.selector.split(","):
            assert not re.match(r"\s*\.live\b", sel), sel


def test_the_gpu_dot_never_shrinks():
    assert "flex:none" in _bodies(lambda r: ".gc-dot" in r.selector).replace(" ", "")


def test_targets_have_a_floor_and_grow_on_a_coarse_pointer():
    floors = [r for r in all_rules("components") if "min-block-size:24px" in r.body.replace(" ", "")]
    assert floors and any(".btn" in r.selector for r in floors)
    coarse = [r for r in all_rules("components") if "pointer:coarse" in r.context.replace(" ", "")]
    assert any("44px" in r.body for r in coarse)


def test_anchors_land_below_the_sticky_header():
    margins = _bodies(lambda r: "[id^=" in r.selector)
    assert "scroll-margin-top" in margins
    assert "scroll-padding-top" in _bodies(lambda r: r.selector.strip() == "html")


def test_no_sheet_shimmers():
    for name in ("tokens", "components", "pages"):
        for kf, body in keyframes(css(name)).items():
            assert "background-position" not in body or kf in ("lv-sheen",), (name, kf)


def test_a_chart_reserves_its_box():
    chart = _bodies(lambda r: r.selector.strip() == ".chart")
    assert "aspect-ratio" in chart and "contain:layout paint" in chart


def test_a_placeholder_is_static_and_shows_late():
    slot = [r for r in all_rules("components") if ".waitbox" in r.selector]
    body = " ".join(r.body for r in slot)
    assert "var(--d-late)" in body and "var(--loop)" not in body


def test_frames_and_tiles_keep_their_box():
    for sel in (".frame", ".pic", ".chart"):
        found = [v for s, v in values(css("components"), "contain") if s.strip() == sel]
        assert found, sel
