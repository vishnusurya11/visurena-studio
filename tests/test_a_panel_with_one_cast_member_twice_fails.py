"""G-WHO on panels (Jekyll ep06 shot 25, 2026-10-29).  The panel drew Utterson twice and no Poole; the panel
checks counted two figures for two cast and passed it, and the take opened on it and morphed Utterson into
Poole.  G-WHO ran on takes only.  Now the panel content check asks it too, and a twin fails the panel, so the
panel ladder redraws it before any take is rendered."""
from __future__ import annotations

from types import SimpleNamespace

from scripts.episode import panel_content_check as pcc
from studio import figure_who as fw
from studio import panel_content as pc

STAGED = {"poole": {"hair_colour": "fair", "facial_hair": "none", "coat": "dark", "hat": "none"},
          "gabriel_john_utterson": {"hair_colour": "grey", "facial_hair": "none", "coat": "dark", "hat": "hat"}}
SHOT = SimpleNamespace(index=25, faces=["gabriel_john_utterson", "poole"], size="medium")


def seen(people: int) -> pc.Seen:
    return SimpleNamespace(people=people)


def test_a_panel_drawing_one_man_twice_is_a_who_fault(monkeypatch, tmp_path):
    figures = [{"hair": "grey", "facial_hair": "none", "coat": "black", "headwear": "bowler"},
               {"hair": "grey", "facial_hair": "none", "coat": "black", "headwear": "bowler"}]
    monkeypatch.setattr(pcc, "read_who", lambda path, seed=19: figures)
    monkeypatch.setattr(pc, "twin_applies", lambda planned, size, people: True)
    faults = pcc.who_check(SHOT, seen(2), tmp_path / "shot_25.png", STAGED)
    assert faults and faults[0].startswith("who: 2 figures read as 'gabriel_john_utterson'")


def test_a_panel_with_both_men_passes(monkeypatch, tmp_path):
    figures = [{"hair": "blond", "facial_hair": "none", "coat": "black", "headwear": "none"},
               {"hair": "grey", "facial_hair": "none", "coat": "black", "headwear": "bowler"}]
    monkeypatch.setattr(pcc, "read_who", lambda path, seed=19: figures)
    monkeypatch.setattr(pc, "twin_applies", lambda planned, size, people: True)
    assert pcc.who_check(SHOT, seen(2), tmp_path / "shot_25.png", STAGED) == []


def test_a_one_cast_panel_is_never_asked(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise AssertionError("asked")
    monkeypatch.setattr(pcc, "read_who", boom)
    one = SimpleNamespace(index=3, faces=["henry_jekyll"], size="close")
    assert pcc.who_check(one, seen(1), tmp_path / "shot_03.png", STAGED) == []


def test_an_unreadable_who_answer_is_a_fault(monkeypatch, tmp_path):
    def unread(path, seed=19):
        raise pc.Unreadable("no figures list")
    monkeypatch.setattr(pcc, "read_who", unread)
    monkeypatch.setattr(pc, "twin_applies", lambda planned, size, people: True)
    assert pcc.who_check(SHOT, seen(2), tmp_path / "shot_25.png", STAGED)[0].startswith("unread: who")
