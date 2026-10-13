"""G-SPEAKER reads the BOOK's narrator (Jekyll ep01 review, 2026-10-13).

Five ladder rounds refused `narrator` on a third-person book and printed the
cast as the menu; the writer took `henry_jekyll`.  Now: an unset narrator is a
plan-wide STOP that names no cast member, the dedicated `narrator` row is a
legal speaker, a character narrating in the narrator's place is refused, and
a `tale` is a character's own voice, never the narrator's.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures, plan_gates

CAST = ["gabriel_john_utterson", "henry_jekyll", "richard_enfield"]


def _ep(*rows):
    return SimpleNamespace(lines=[SimpleNamespace(index=i, kind=k, speaker=s, shot=0) for i, (k, s) in enumerate(rows)])


def test_an_unset_narrator_is_one_plan_wide_stop_naming_no_cast_member():
    got = plan_gates.speaker_faults(_ep(("narration", "narrator"), ("dialogue", "richard_enfield")), CAST, "")
    assert len(got) == 1 and got[0].startswith("G-SPEAKER plan:")
    assert not any(who in got[0] for who in CAST)
    assert plan_cures.cure_for(got[0]) is None            # nothing cures it: the plan stops


def test_the_dedicated_narrator_row_is_a_legal_speaker_outside_the_cast():
    ep = _ep(("narration", "narrator"), ("dialogue", "richard_enfield"))
    assert plan_gates.speaker_faults(ep, CAST, "narrator") == []


def test_a_character_narrating_in_the_narrators_place_is_refused():
    ep = _ep(("narration", "henry_jekyll"), ("narration", "henry_jekyll"), ("dialogue", "richard_enfield"))
    got = plan_gates.speaker_faults(ep, CAST, "narrator")
    assert [g.split(":")[0] for g in got] == ["G-SPEAKER line 0", "G-SPEAKER line 1"]
    assert "'narrator'" in got[0] and "tale" in got[0]


def test_a_character_narrating_beside_the_narrator_is_advice_only():
    """WotW ep22 and ep24 shipped the curate's and the artilleryman's lines as narration."""
    ep = _ep(("narration", "narrator"), ("narration", "henry_jekyll"))
    assert plan_gates.speaker_faults(ep, CAST, "narrator") == []
    assert plan_gates.speaker_advisories(ep, "narrator")[0].startswith("G-SPEAKER line 1:")


def test_a_tale_is_told_by_a_cast_member_never_the_narrator():
    assert plan_gates.speaker_faults(_ep(("narration", "narrator"), ("tale", "richard_enfield")), CAST, "narrator") == []
    got = plan_gates.speaker_faults(_ep(("narration", "narrator"), ("tale", "narrator")), CAST, "narrator")
    assert got and got[0].startswith("G-SPEAKER line 1:") and "tale" in got[0]
