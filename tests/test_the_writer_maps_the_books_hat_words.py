"""The look-table writer maps the book's own hat words to the closed marker
(C2_verdict #5).

`first_of` takes the first HEADWEAR pattern that matches.  Replayed over the 61
WotW looks it set 8 wrong: "Black silk top hat" and "billycock hat" fell to
`other_hat`, "Brown felt pork-pie hat" missed the adjacent "felt hat", and a
"straw hat" with a veil read `boater`.  The reader parses its own words through
the same table (`panel_content`), so a change here moves both sides."""
from __future__ import annotations

import json

import pytest

from studio import episode_home, look_table as lt, look_timeline as ltl

WOTW = "20260827135508_the-war-of-the-worlds"
OLD = (("none", r"hatless|bare-?headed"), ("boater", r"boater|straw hat"), ("bowler", r"bowler|derby"),
       ("top_hat", r"top-?hat|silk hat"), ("felt_hat", r"felt hat"), ("cap", r"\bcap\b"),
       ("bonnet", r"bonnet"), ("helmet", r"helmet"), ("hood", r"\bhood\b"), ("other_hat", r"\bhats?\b"))
"""FROZEN: the table before C2_verdict #5."""
CHANGED = {("stent", "pit_frock_coat"): "top_hat", ("stent", "deputation_frock_coat"): "top_hat",
           ("unnamed_cabmen", "summer_rank"): "bowler", ("unnamed_cabmen", "box_coat_london"): "bowler",
           ("unnamed_milkman", "morning_round"): "felt_hat", ("narrators_wife", "mourning_reunion"): "other_hat",
           ("mrs_elphinstone", "white_summer"): "other_hat", ("mrs_elphinstone", "white_grimed"): "other_hat"}


def wotw_headwear() -> dict[tuple[str, str], str]:
    """Every bound WotW row's looks, re-derived from its dossier: (who, look) -> headwear."""
    book = episode_home.book_dir(WOTW)
    rows = json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8")).get("refs") or []
    out = {}
    for who in [r["entity_id"] for r in rows if r.get("kind", "character") == "character" and r.get("entity_id")]:
        path = book / "analysis" / "characters" / f"{who}.json"
        looks = ltl.looks_from_dossier(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else None
        out |= {(who, k): v.markers.headwear for k, v in (looks.looks.items() if looks else [])}
    return out


@pytest.mark.parametrize("words, marker", [
    ("Black silk top hat", "top_hat"), ("a grey top-hat", "top_hat"), ("a stovepipe", "top_hat"),
    ("Low-crowned black billycock hat", "bowler"), ("a derby", "bowler"),
    ("Brown felt pork-pie hat", "felt_hat"), ("Battered black felt hat", "felt_hat"),
    ("a slouch hat", "felt_hat"), ("a wide-awake", "felt_hat"),
    ("Straw boater with a black band", "boater"), ("Wide white straw hat", "other_hat")])
def test_the_books_hat_words_map_to_their_marker(words, marker):
    assert lt.first_of(lt.HEADWEAR, words) == marker


def test_a_verb_is_not_a_felt_hat():
    assert lt.first_of(lt.HEADWEAR, "he felt for his hat") != "felt_hat"


def test_re_deriving_the_wotw_looks_changes_exactly_the_eight_rows(monkeypatch):
    if not episode_home.book_dir(WOTW).exists():
        pytest.skip("no WotW library on this machine")
    now = wotw_headwear()
    monkeypatch.setattr(lt, "HEADWEAR", OLD)
    before = wotw_headwear()
    assert len(now) == 61
    assert {k: now[k] for k in now if now[k] != before[k]} == CHANGED


def test_the_reader_still_says_boater_for_a_straw_hat():
    """The reader side is unmeasured for straw: a panel the VL lists as "straw hat"
    keeps reading `boater`, so G-LOOK-PANEL still advises a straw hat on a felt-hat
    look (the shipped ep25 fault).  Only the writer's straw hat is `other_hat`."""
    from studio import panel_content as pc
    assert pc.seen_marker("headwear", "man in suit, straw hat") == "boater"
    assert pc.seen_marker("headwear", "black billycock hat") == "bowler"
    assert lt.first_of(lt.HEADWEAR, "Wide white straw hat") == "other_hat"
