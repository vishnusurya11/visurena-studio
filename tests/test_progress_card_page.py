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

from command_center_fixtures import CODEX
from test_progress_card_api import _drive, board  # noqa: F401  (the fixture)

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "studio" / "command_center" / "templates" / "base.html").read_text(encoding="utf-8")
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
    assert re.search(r'data-k="big">1<span class="of">/3', card)
    assert "done around <b>" in card and "09 shoot" in card
    assert card.count('class="lt st-') == 3 and "st-rendering" in card


def test_the_card_sits_above_the_head(board):
    html = _page(board, _drive(time.time() - 3600))
    assert html.index('id="live"') < html.index('id="head"')


def test_the_hero_is_a_progressbar_with_words(board):
    card = _card(_page(board, _drive(time.time() - 3600)))
    assert 'role="progressbar"' in card
    assert re.search(r'aria-valuetext="take 1 of 3, done around \d\d:\d\d"', card)


def test_the_live_region_holds_no_clock(board):
    card = _card(_page(board, _drive(time.time() - 3600)))
    region = re.search(r'<span class="lv-vital" aria-live="polite">(.*?)</span></span>', card, re.S).group(1)
    assert "data-clock" not in region and card.count("aria-live") == 1


def test_a_dead_run_is_one_still_sentence(board):
    card = _card(_page(board, []))
    assert "data-still" in card and "Run stopped" in card
    assert "st-rendering" not in card and "is-moving" not in card and "lv-sheet" not in card


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
    return BASE[BASE.index("/* live card"):BASE.index("/* /live card */")]


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


def test_every_animation_is_gated_behind_no_preference():
    css = _live_css()
    gated = _blocks(css, "@media (prefers-reduced-motion: no-preference)")
    uses = [m.start() for m in re.finditer(r"animation:(?!none)", css)]
    assert uses and gated
    assert all(any(a <= u <= b for a, b in gated) for u in uses)


def test_reduced_motion_stops_everything_in_the_card():
    assert "@media (prefers-reduced-motion: reduce){.live *{animation:none!important;transition-duration:1ms!important}}" in BASE


def test_the_motion_tokens_are_a_second_root_block():
    assert BASE.index(":root{--ease-out") > BASE.index("*{box-sizing:border-box}")
    for token in ("--d4:900ms", "--breathe:2.8s", "--sheen:2.4s", "--stripe:1.6s", "@property --dev"):
        assert token in _live_css()


def _tokens(block: str) -> dict[str, str]:
    return dict(re.findall(r"--([a-z0-9-]+):(#[0-9a-f]{6})", block))


def _lum(hex_: str) -> float:
    def ch(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(hex_[i:i + 2]) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


THEMES = {"light": _tokens(BASE[BASE.index(":root{"):BASE.index("@media (prefers-color-scheme: dark)")]),
          "dark": _tokens(BASE[BASE.index(':root[data-theme="dark"]{'):BASE.index("*{box-sizing")])}
PAIRS = [("ink", "paper"), ("ink-2", "paper"), ("think", "paper"), ("ok", "paper"), ("qc", "paper"),
         ("accent", "paper"), ("ink", "paper-2"), ("ink-2", "paper-2"), ("qc", "qc-bg"), ("paper", "think")]


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("fg,bg", PAIRS)
def test_every_text_pair_the_card_uses_holds_4_5(theme, fg, bg):
    t = THEMES[theme]
    assert _contrast(t[fg], t[bg]) >= 4.5, (theme, fg, bg, _contrast(t[fg], t[bg]))


def test_the_card_never_sets_text_in_ink_3():
    assert "--ink-3" not in _live_css()
