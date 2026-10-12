"""Board review 2026-10-12, part 03 list A (the clear wins).  A2, A3, A4, A7, A14,
A17, A19, A22 and A24 are pinned beside the data-truth fixes; these are the rest.
Each test names its item.  $0."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from board_css_rules import all_rules
from command_center_fixtures import CODEX, make_app
from studio import db, episode_home
from studio.command_center import shell, views
from studio.command_center import unit_parse as up

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture()
def board(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch)), tmp_path


def _rule(selector_part: str):
    return [r for r in all_rules() if selector_part in r.selector]


# A1: a finished episode is not LOOPING


def test_a1_a_loop_that_ended_in_done_is_not_looping():
    rows = [{"how": "failed", "ended_on": "11", "reason": "refused"}] * 3 + [
        {"how": "completed", "ended_on": "12", "reason": "done"}]
    assert up.loop_state(rows)["looping"] is False
    assert up.loop_state([{"how": "failed", "ended_on": "11", "reason": "refused"}] * 4)["looping"] is True


# A5, A6: stale is a warning, every meaning in plain words


def test_a5_stale_is_not_drawn_in_done_green():
    assert all("--st-done" not in r.body for r in _rule(".pill.stale"))


def test_a6_no_meaning_speaks_the_desks_jargon():
    for state, text in views.MEANINGS.items():
        assert not {"terminal", "lease", "row"} & set(text.replace(",", " ").split()), state
    assert "crashed" in views.MEANINGS["stale"] and "looked at" in views.MEANINGS["flagged"]


# A8, A9, A21: contrast, focus, no empty boxes


def test_a8_the_sidebar_counts_are_not_dimmed_below_aa():
    assert all("opacity" not in r.body for r in _rule(".sb-item .n"))


def test_a9_the_segmented_filter_shows_keyboard_focus():
    assert any("outline" in r.body for r in _rule(".segmented a:focus-visible"))


def test_a21_an_up_next_card_without_a_picture_collapses():
    assert _rule(".nextstrip .pic:not(:has(img))")


# A10-A13: the unit head


def test_a10_the_step_bar_has_a_column_per_step(board):
    c, _ = board
    html = c.get(f"/d/episode/{CODEX}/ep04").text
    assert 'style="--n:13"' in html and any("var(--n" in r.body for r in _rule(".ubar"))


def test_a11_a_done_unit_drops_the_where_chip(board):
    c, _ = board
    assert 'class="chip2 where"' not in c.get(f"/d/episode/{CODEX}/ep03").text
    assert 'class="chip2 where"' in c.get(f"/d/episode/{CODEX}/ep04").text


def test_a12_redo_is_not_the_brightest_button(board):
    c, _ = board
    assert 'class="btn sm primary" href="#actions"' not in c.get(f"/d/episode/{CODEX}/ep04").text


def test_a13_a_gate_name_has_no_underscore():
    text = (REPO / "studio/command_center/templates/unit.html").read_text(encoding="utf-8")
    assert "| replace('EYE_', '') | replace('_', ' ') | lower | capitalize" in text


# A15, A16, A18


def test_a15_the_department_crumb_is_capitalised():
    assert shell.crumbs("/d/episode", {})[-1][0] == "Episode"
    assert ("Episode", f"/d/episode?book={CODEX}") in shell.crumbs(f"/d/episode/{CODEX}/ep01", {})


def test_a16_the_orders_table_says_ago_and_status(tmp_path):
    text = (REPO / "studio/command_center/templates/_orders.html").read_text(encoding="utf-8")
    assert "<th>ago</th>" in text and "<th>status</th>" in text and "taken by" not in text
    assert views.ago_words("21 h") == "21 h ago" and views.ago_words("now") == "now" and views.ago_words("") == ""


def test_a18_the_queue_says_its_order_in_plain_words(board):
    c, _ = board
    html = c.get("/queue").text
    assert "slate order" not in html and "no scheduler yet" not in html


# A20: unit titles


def test_a20_a_unit_title_comes_from_its_plan(tmp_path):
    home = tmp_path / "book" / "episodes" / "ep15"
    episode_home.write_json(home / "plan.json", {"title": "What Had Happened in Surrey"})
    row = {"home": "episodes/ep15"}
    assert views.unit_title(tmp_path / "book", row) == "What Had Happened in Surrey"
    assert views.unit_title(tmp_path / "book", {"home": "episodes/ep16"}) == ""
    assert views.unit_title(None, row) == ""


def test_a20_the_title_reaches_the_rows_the_wall_and_the_palette(board):
    c, tmp_path = board
    episode_home.write_json(tmp_path / "library" / f"{CODEX}_a-book" / "episodes" / "ep03" / "plan.json",
                            {"title": "The Cylinder Opens"})
    assert "The Cylinder Opens" in c.get("/d/episode").text
    assert "The Cylinder Opens" in c.get(f"/b/{CODEX}").text
    assert any("The Cylinder Opens" in (e.get("s") or "") for e in c.get("/api/palette.json").json())


# A23: the org chart leaves the beige palette


def test_a23_the_architecture_page_is_on_the_studio_palette():
    text = (REPO / "architecture/index.html").read_text(encoding="utf-8")
    assert "#f6f3ec" not in text and "#181613" not in text and "#0f1012" in text
