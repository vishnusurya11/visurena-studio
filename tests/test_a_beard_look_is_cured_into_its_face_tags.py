"""G-LOOK-WORDS on the beard is a deterministic cure, then a wall (C1_verdict #6).

MEASURED on ep25 (C1_L §1a): the narrator's ragged_greyed look carries a beard,
and 4 of the 12 head tags the grid reads -- "(face gaunt, grey eyes, battered
brown felt hat)" -- never say so; a bearded look picture would be staged beside
words that do not ask for a beard. A wall alone would send the writer round the
loop (walls follow the chapter: run the deterministic cure first), so a head tag
of a one-face shot whose staged look is `beard` gains the look's beard phrase
before G-LOOK-WORDS checks it. A tag that already says beard is untouched.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from studio import continuity_place as cp
from studio.continuity_spec import CharacterLooks, Layers, LookBook, Look, Markers, Span, StoryTime

ROOT = Path(__file__).resolve().parents[1]
WOTW = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
RAGGED = Look(layers=Layers(face="sixteen days of grey-brown beard; face gaunt, cheekbones sharp."),
              markers=Markers(facial_hair="beard"))
TABLE = LookBook(book="b", characters={"nar": CharacterLooks(
    base="suit", body="Man of 34.", timeline=[Span(look="suit", start=StoryTime(chapter=1)),
                                              Span(look="ragged", start=StoryTime(chapter=22))],
    looks={"suit": Look(made_by="base", markers=Markers(facial_hair="moustache")), "ragged": RAGGED})})


def plan(*frames: str, faces=("nar",)) -> dict:
    return {"setups": {"road": {"looks": []}},
            "shots": [{"index": i, "setup": "road", "faces": list(faces), "frame": f, "at_rest": ""}
                      for i, f in enumerate(frames)]}


def test_a_bare_head_tag_gains_the_looks_beard_phrase():
    doc = cp.cure_beard_tags(plan("Medium of the narrator (face gaunt, grey eyes, battered brown felt hat) at the corner."), TABLE, 25)
    assert "(face gaunt, grey eyes, battered brown felt hat, sixteen days of grey-brown beard)" in doc["shots"][0]["frame"]
    assert cp.look_word_faults(doc, TABLE, 25) == []


def test_the_wall_refuses_a_bare_head_tag_the_cure_has_not_seen():
    assert cp.look_word_faults(plan("Close on him (face gaunt, grey eyes) in the lane."), TABLE, 25) == [
        "G-LOOK-WORDS shot 0: nar's look 'ragged' has a beard; the head tag (face gaunt, grey eyes) says none"]


def test_a_tag_that_says_beard_or_a_body_tag_is_untouched():
    doc = plan("Wide (face gaunt, bearded, grey eyes) in the lane.", "Back (battered brown felt hat, cracked black boots).")
    assert cp.cure_beard_tags(copy.deepcopy(doc), TABLE, 25) == doc


def test_an_earlier_chapter_without_a_beard_is_untouched():
    doc = plan("Medium (face gaunt, grey eyes) at the corner.")
    assert cp.cure_beard_tags(copy.deepcopy(doc), TABLE, 10) == doc


def test_a_two_face_shot_is_not_judged():
    doc = plan("Two-shot (face gaunt, grey eyes) and the curate.", faces=("nar", "curate"))
    assert cp.look_word_faults(doc, TABLE, 25) == []


@pytest.mark.skipif(not (WOTW / "episodes" / "ep25" / "plan.json").exists(), reason="the WotW library is not on disk")
def test_the_ep25_replay_cures_exactly_the_four_bare_tags():
    from scripts.refs.continuity_replay import table_of
    before = json.loads((WOTW / "episodes" / "ep25" / "plan.json").read_text(encoding="utf-8"))
    after = cp.cure_beard_tags(copy.deepcopy(before), table_of(WOTW), 25)
    changed = [(s["index"], k) for s, t in zip(before["shots"], after["shots"]) for k in ("frame", "at_rest") if s[k] != t[k]]
    assert changed == [(0, "frame"), (0, "at_rest"), (9, "frame"), (11, "frame")]
    assert cp.look_word_faults(after, table_of(WOTW), 25) == []
    assert len(cp.look_word_faults(before, table_of(WOTW), 25)) == 4
