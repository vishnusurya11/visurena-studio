"""The writer cannot opt out of the shot grammar (anime-TV, owner 2026-10-17).

`grammar` is set by code from the brief's band, never by the draft (as the
spoken rate is): the framing and screenplay gates are hard on a plan that
declares it, so a writer free to leave it empty would leave it empty.  The
book's motif rides the band too, so episode N repeats episode 1's ritual.  $0."""
from __future__ import annotations

from agents import episode_writer as ew
from studio import episode_spec, plan_brief
from tests.test_episode_writer import canned_draft


def test_grammar_is_a_code_set_field():
    assert "grammar" in ew.CODE_SET_FIELDS and "grammar" not in ew.Draft.model_fields


def test_the_band_names_the_studio_grammar():
    assert plan_brief.band()["grammar"] == episode_spec.STUDIO_GRAMMAR == "anime_tv"


def test_to_episode_writes_the_bands_grammar_and_motif():
    brief = {"band": {"grammar": "anime_tv", "motif": "the blind door in the by-street"}}
    ep = ew.to_episode(ew.Draft.model_validate(canned_draft()), brief)
    assert ep.grammar == "anime_tv" and ep.motif == "the blind door in the by-street"


def test_a_written_motif_is_kept():
    draft = {**canned_draft(), "motif": "the lamp at the gate"}
    ep = ew.to_episode(ew.Draft.model_validate(draft), {"band": {"motif": "the blind door"}})
    assert ep.motif == "the lamp at the gate"


def test_no_brief_is_the_legacy_grammar():
    assert ew.to_episode(ew.Draft.model_validate(canned_draft())).grammar == ""


def test_the_writer_skill_names_every_grammar_gate_and_bans_amounts():
    text = ew.load_skill()
    section = text.split("## The anime-TV grammar", 1)[1].split("\n## ", 1)[0]
    for gate in ("G-FACES", "G-WIDE", "G-MEDIUM", "G-INSERT", "G-LOCKED", "G-PUSH", "G-TWO", "G-PAYOFF",
                 "G-OTS", "G-UNSUPPORTED", "G-SHOTS", "G-COLD", "G-ACT", "G-CAPTION", "G-REACT", "G-MA"):
        assert gate in section, gate
    assert "`inner`" in text and "act_out" in text and "tease" in text
    assert "with its amount" not in text and "a hand's breadth) or the gait" not in text
