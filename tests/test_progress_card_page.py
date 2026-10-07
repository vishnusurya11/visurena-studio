"""The live card on the unit page (progress tracker spec §4, §5): rendered
server-side so it reads with JavaScript off, accessible, calm -- one thing
moves and only while the run is live, every animation is gated behind
prefers-reduced-motion: no-preference, and every text colour pair it uses
holds 4.5:1 in both themes."""
from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import board_css
from command_center_fixtures import CODEX
from test_progress_card_api import _drive, board  # noqa: F401  (the fixture)

ROOT = Path(__file__).resolve().parents[1]
PAGES = board_css.css("pages")
PAGE = f"/d/episode/{CODEX}/ep04"


def _page(board, rows) -> str:
    board["app"].state.procs = lambda: rows
    r = TestClient(board["app"]).get(PAGE)
    assert r.status_code == 200
    return r.text


def _card(html: str) -> str:
    start = html.index('<section id="live"')
    return html[start:html.index("</section>", start)]


def test_the_card_renders_without_javascript(board):
    card = _card(_page(board, _drive(time.time() - 3600)))
    big = re.search(r'data-k="big">(.*?)</span></span>', card, re.S).group(1)
    assert re.sub(r"<[^>]+>", "", big) == "1/3"
    assert "done around <b>" in card and "09 shoot" in card
    assert card.count('role="listitem"') == 3 and re.search(r'title="T\d+ · rendering', card)


def test_the_card_sits_above_the_head(board):
    html = _page(board, _drive(time.time() - 3600))
    assert html.index('id="live"') < html.index('id="head"')


def test_the_hero_is_a_progressbar_with_words(board):
    card = _card(_page(board, _drive(time.time() - 3600)))
    assert 'role="progressbar"' in card
    assert re.search(r'aria-valuetext="take 1 of 3, done around \d\d:\d\d"', card)


def test_the_live_region_holds_no_clock(board):
    card = _card(_page(board, _drive(time.time() - 3600)))
    region = re.search(r'aria-live="polite">(.*?)</span></span>', card, re.S).group(1)
    assert "data-clock" not in region and card.count("aria-live") == 1


def test_a_dead_run_is_one_still_sentence(board):
    import os
    import time
    old = time.time() - 3 * 86400                      # no process AND still files: truly dead
    for p in [board["home"]] + [d for d in Path(board["home"]).iterdir() if d.is_dir()]:
        os.utime(p, (old, old))
    card = _card(_page(board, []))
    assert "data-still" in card and "Run stopped" in card
    assert "· rendering" not in card and 'data-k="sheet"' not in card


def test_the_tab_title_is_the_run(board):
    html = _page(board, _drive(time.time() - 3600))
    assert re.search(r"<title>[●○] 09 shoot 1/3 · ~\d\d:\d\d · ep04</title>", html)


def test_the_partial_is_the_card_alone(board):
    board["app"].state.procs = lambda: _drive(time.time() - 3600)
    r = TestClient(board["app"]).get(f"/partials/unit/episode/{CODEX}/ep04/live")
    assert r.status_code == 200 and r.text.lstrip().startswith("<section id=\"live\"")


def test_a_unit_without_a_run_has_no_card(tmp_path, monkeypatch):
    from command_center_fixtures import make_app
    r = TestClient(make_app(tmp_path, monkeypatch)).get(PAGE)
    assert r.status_code == 200 and 'id="live"' not in r.text


# --- the stylesheet ---


def _live_css() -> str:
    """The card's block of pages.css (plan F2 moved it out of base.html)."""
    return PAGES[PAGES.index("/* live card"):PAGES.index("/* /live card */")]


def _blocks(css: str, head: str) -> list[tuple[int, int]]:
    """(start, end) of every block that opens with `head`."""
    out = []
    for m in re.finditer(re.escape(head), css):
        depth, i = 0, css.index("{", m.start())
        for j in range(i, len(css)):
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            if depth == 0:
                out.append((m.start(), j))
                break
    return out


def test_every_animation_in_the_card_runs_on_motion_tokens():
    """Panel ruling 3.1: a duration is a token from tokens.css, never a literal in the card."""
    css = _live_css()
    uses = re.findall(r"animation:([^;}]+)", css)
    assert uses and all(u.strip() == "none" or "var(--" in u for u in uses), uses
    assert not re.search(r"\d+(\.\d+)?m?s\b", re.sub(r"var\([^)]*\)", "", css))


def test_still_mode_is_a_token_flip_that_stops_the_card():
    """Panel ruling 3.2: reduced motion and data-motion=still set the motion tokens to 1 ms."""
    tokens = (Path(__file__).resolve().parents[1] / "studio" / "command_center" / "static" / "css" / "tokens.css").read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion:reduce)" in tokens and ':root[data-motion="still"]' in tokens
    assert "--breathe:1ms" in tokens and "--sheen:1ms" in tokens


def test_the_card_keeps_no_root_block_of_its_own():
    """Panel ruling 3.1: the motion tokens live in tokens.css alone."""
    assert ":root" not in _live_css()
    assert "@property --dev" in PAGES   # registered outside the layer


THEMES = board_css.themes()   # Studio black and Graphite, var() resolved (static/css/tokens.css)
_contrast = board_css.contrast
PAIRS = [("ink", "paper"), ("ink-2", "paper"), ("think", "paper"), ("ok", "paper"), ("qc", "paper"),
         ("accent", "paper"), ("ink", "paper-2"), ("ink-2", "paper-2"), ("qc", "qc-bg"), ("paper", "think")]


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("fg,bg", PAIRS)
def test_every_text_pair_the_card_uses_holds_4_5(theme, fg, bg):
    t = THEMES[theme]
    assert _contrast(t[fg], t[bg]) >= 4.5, (theme, fg, bg, _contrast(t[fg], t[bg]))


def test_the_cards_muted_text_holds_4_5():
    """ink-3 (the demoted last-words line, ruling 3.5) meets 4.5:1 since P0.3 re-toned it."""
    for theme, t in THEMES.items():
        assert _contrast(t["ink-3"], t["paper"]) >= 4.5, theme


def test_the_card_never_reuses_the_health_bands_loop_class():
    rail = (ROOT / "studio" / "command_center" / "templates" / "_live_rail.html").read_text(encoding="utf-8")
    assert " loop{" not in rail and "is-loop" in rail
