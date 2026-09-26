"""The board is the org chart's sibling (decision 2026-09-25, "the org-chart
page"): the design language flows from `architecture/index.html` to the board,
never back.  Its `:root{...}` token block and both dark-mode blocks are copied
byte for byte into the base template, and the fonts come from the same link."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = ROOT / "architecture" / "index.html"
BASE = ROOT / "studio" / "command_center" / "templates" / "base.html"


def _tokens(html: str) -> str:
    """From `:root{` to the line before `*{box-sizing`: the three token blocks."""
    start = html.index(":root{")
    end = html.index("*{box-sizing:border-box}")
    return html[start:end]


def test_the_token_block_is_byte_equal():
    tokens = _tokens(ORG.read_text(encoding="utf-8"))
    assert tokens.startswith(":root{") and '@media (prefers-color-scheme: dark)' in tokens
    assert ':root[data-theme="dark"]{' in tokens
    assert tokens in BASE.read_text(encoding="utf-8")


def test_the_fonts_are_the_org_charts():
    link = re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]+">',
                     ORG.read_text(encoding="utf-8")).group(0)
    assert link in BASE.read_text(encoding="utf-8")


def test_the_board_never_meta_refreshes():
    for page in (ROOT / "studio" / "command_center" / "templates").glob("*.html"):
        assert "http-equiv" not in page.read_text(encoding="utf-8"), page.name
