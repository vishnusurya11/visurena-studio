"""Every string a model receives names what IS present.

Three failures in this repo were caused by asking for an absence and being
given it: "no vocals" produced humming (`trailer_music`), `NO_TYPE`'s "no
lettering" produced the word CRISTERION on a shop board, and `PLATE_FRAME`'s
"no people" produced a room full of drinkers.  A text encoder embeds tokens;
"drum" contributes the drum direction whether or not "no" precedes it.

So the rule is derived, not stylistic: name the thing that occupies the slot
the unwanted thing would occupy.  This file is the guard that keeps it true.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from studio import (affirm, cast_card, describe, h3_prompt, music_tone,
                    portrait, shot_grammar, trailer_refs, trailer_shot)
from studio.affirm import negations
from studio.portrait import Passage

SCARLET = Path("library/20260822113400_a-study-in-scarlet")


class TestNegations:
    def test_it_catches_every_form_the_audit_found(self):
        caught = negations("no drums, not loud, free of text, rather than a sub, "
                           "reverb gone, nothing else, without a bow, avoid brass")
        assert {"no", "not", "free of", "rather than", "gone", "nothing",
                "without", "avoid"} <= set(w.lower() for w in caught)

    def test_a_leading_minus_is_a_negative_weight(self):
        assert negations("cello, violin, -drums") == ["-d"]

    def test_it_reads_hyphens_as_part_of_the_word(self):
        """`\\b` would split `pump-organ` and flag nothing; the look-arounds
        treat a hyphen as a word character so `-drums` is the only minus."""
        assert negations("a pump-organ, close-miked, a four-note figure") == []

    def test_the_musical_vocabulary_of_absence_passes(self):
        """A named event is not a denial: silence, rest and stop are things
        the players DO.  So are the terms whose spelling contains a negation."""
        assert negations("a nocturne in G minor, unaccompanied, two full bars of "
                         "silence, shadowless light, an unhurried unbroken take, "
                         "notation from Nottingham, an innocent bystander, "
                         "non-diegetic score, no-one on the plain") == []

    def test_a_caller_may_name_its_own_exceptions(self):
        """A closed answer vocabulary handed to a labeller is data, not a
        request to draw: `describe.TRAITS` offers "none" as an ANSWER."""
        assert negations('"headgear": one of ["none", "top hat"]') == ["none"]
        assert negations('"headgear": one of ["none", "top hat"]',
                         allowed=("none",)) == []

    def test_is_affirmative_is_the_same_question(self):
        assert affirm.is_affirmative("a solo violin over a harmonium drone")
        assert not affirm.is_affirmative("a solo violin, no drums")


class TestScan:
    def test_it_reports_file_line_and_phrase(self, tmp_path):
        module = tmp_path / "m.py"
        module.write_text('PLATE = "an empty room, no people"\nMODEL_TEXT = (PLATE,)\n',
                          encoding="utf-8")
        assert affirm.scan([module]) == [f"{module}:1: no :: an empty room, no people"]

    def test_a_module_declaring_nothing_reports_nothing(self, tmp_path):
        module = tmp_path / "m.py"
        module.write_text('MESSAGE = "no codex row with id"\n', encoding="utf-8")
        assert affirm.scan([module]) == []

    def test_it_reads_every_string_in_a_json_tone(self, tmp_path):
        tone = tmp_path / "tone.json"
        tone.write_text('{"genre": "chamber, not orchestral", "bpm": 100}',
                        encoding="utf-8")
        assert affirm.scan([tone]) == [f"{tone}:1: not :: chamber, not orchestral"]

    def test_a_directory_is_walked(self, tmp_path):
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "a.py").write_text('A = "no brass"\nMODEL_TEXT = (A,)\n',
                                               encoding="utf-8")
        assert len(affirm.scan([tmp_path])) == 1

    def test_the_shipped_tone_is_affirmative(self):
        assert affirm.scan([SCARLET / "trailer/music/tone.json"]) == []

    def test_every_module_this_step_owns_is_clean(self):
        owned = ["studio/music_tone.py", "studio/trailer_music.py",
                 "studio/trailer_refs.py", "studio/trailer_shot.py",
                 "studio/shot_grammar.py", "studio/cast_card.py",
                 "studio/h3_prompt.py"]
        assert affirm.scan([Path(p) for p in owned]) == []


def a_tone() -> music_tone.Tone:
    return music_tone.load_tone(SCARLET)


def model_bound() -> list[tuple[str, str, tuple[str, ...]]]:
    """(label, text, allowed) for every string this repo sends to a model.

    Each builder is driven with a fixture rather than trusted, because the
    negations that shipped were in the SENTENCES the builders write, never in
    the data they were given.
    """
    tone = a_tone()
    rows = [("music_tone.caption", music_tone.caption(tone), ()),
            ("h3_prompt.build", h3_prompt.build(
                "A cinematic live-action photograph.", "a tall lean man",
                "a gaslit drawing room", "he turns a ring in the lamplight",
                "A medium shot.", "A close shot.",
                "The camera pushes in with small amplitude at slow speed.",
                4.2, "build"), ()),
            ("h3_prompt.build (empty plate)", h3_prompt.build(
                "A cinematic live-action photograph.", "", "a bare Soho street",
                "rain crosses the cobbles", "A wide shot.", "A medium shot.",
                "The camera is a static shot, the frame perfectly still.",
                4.2, "quiet"), ()),
            ("trailer_shot.shot_prompt", trailer_shot.shot_prompt(
                trailer_refs.STYLE, ["a tall lean man."], "a gaslit room",
                "He lifts the glass.", "build", 4.2), ()),
            ("trailer_shot.shot_prompt (no cast)", trailer_shot.shot_prompt(
                trailer_refs.STYLE, [], "a bare Soho street", "Rain falls.",
                "quiet", 4.2), ()),
            ("trailer_refs.character_prompt", trailer_refs.character_prompt(
                "A tall lean man.", trailer_refs.palette_for("detective")), ()),
            ("trailer_refs.location_prompt", trailer_refs.location_prompt(
                "a gaslit drawing room", trailer_refs.palette_for("detective")), ()),
            ("shot_grammar.motivated_move", shot_grammar.motivated_move(
                "pushes in", "small", "slow", "the letter falls",
                "the folded letter", "a doorframe"), ()),
            ("describe.prompt_for (one frame)", describe.prompt_for(1),
             tuple(v for pool in describe.TRAITS.values() for v in pool)),
            ("describe.prompt_for (contact sheet)", describe.prompt_for(3),
             tuple(v for pool in describe.TRAITS.values() for v in pool)),
            ("describe.prompt_for (one of several)", describe.prompt_for(3, "the tall man"),
             tuple(v for pool in describe.TRAITS.values() for v in pool)),
            ("portrait.prompt_for", portrait.prompt_for(
                "Holmes", [Passage(chapter=2, n=4, text="He was very tall.")],
                violation="a quote was paraphrased"), ())]
    for mode in music_tone.LYRICS_MODES:
        sheet = music_tone.lyrics_plan(a_vocal_tone(mode))
        rows.append((f"music_tone.lyrics_plan[{mode}]", sheet, ()))
    for label, pool in (("cast_card", cast_card.POOLS),
                        ("trailer_refs.PALETTES", trailer_refs.PALETTES),
                        ("shot_grammar.FRAMING", shot_grammar.FRAMING),
                        ("shot_grammar.ANGLE", shot_grammar.ANGLE),
                        ("trailer_shot.FRAMING", trailer_shot.FRAMING)):
        for key, value in pool.items():
            for text in ((value,) if isinstance(value, str) else tuple(value)):
                rows.append((f"{label}[{key}]", text, ()))
    for arc, moves in trailer_shot.CAMERA.items():
        rows += [(f"trailer_shot.CAMERA[{arc}]", move, ()) for move in moves]
    return rows


def a_vocal_tone(mode: str) -> music_tone.Tone:
    """The Scarlet tone with a voice, so every lyric mode is exercised."""
    from dataclasses import replace
    return replace(a_tone(), lyrics_mode=mode,
                   refrain="Follow the scarlet thread" if mode == "refrain" else None,
                   vocalise=("Ra-che", "vindicta", "Lu-ci-a"))


@pytest.mark.parametrize("label,text,allowed", model_bound(),
                         ids=lambda v: v if isinstance(v, str) and len(v) < 40 else "")
def test_every_model_facing_constant_is_affirmative(label, text, allowed):
    assert negations(text, allowed=allowed) == [], f"{label}: {text[:200]}"


def test_the_reauthor_prompt_asks_for_what_should_play():
    """`reauthor` writes the next caption's percussion line, so its own
    instruction is model-facing at one remove: run 10 told the model "not
    double it, not a triple subdivision" and the caption it wrote back was
    a click track."""
    from scripts.trailer import step_03_music as step
    assert negations(step.reauthor_prompt(a_tone(), None)) == []
