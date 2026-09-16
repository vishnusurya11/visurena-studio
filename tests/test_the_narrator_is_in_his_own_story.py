r"""Watson has to DO something in the episode he is narrating.

MEASURED over the seven delivered plans -- narration lines only, dialogue
excluded -- counting the lines in which the narrator is the acting subject of a
verb ("I carried", "I expected", "Holmes and I read"):

    ep01  4     ep02  5     ep03  2
    ep04  1     ep05  1     ep06  3
    ep07  0

Episode 7 is the only episode of the seven in which Watson never acts. His
entire first person in 270 words of narration is one `me` and one `our`, inside
a single line -- "He asked me to fetch up the old terrier our landlady had
wanted put out of its pain" -- where he is the object of somebody else's
request. The chapter he is reporting is the one where a doctor hands an animal
over to settle a question, and the doctor never touches it.

The density tells the same story and ranks the same way:

    ep01 6.3%   ep02 5.7%   ep03 4.4%
    ep04 3.0%   ep05 6.0%   ep06 2.5%   ep07 0.7%

and the two episodes a prior writing review rated highest are ep02 and ep03.

THE FLOOR IS ONE, and that is why this is a gate rather than a taste. It is not
a threshold fitted to seven points: it is the difference between a witness and a
summary. Every episode that has shipped clears it except the one that reads like
a police report. An episode of Watson's memoirs in which Watson never appears is
not narrated by him, whatever the voice on the track.

The density is reported beside it as an ADVISORY, with the delivered band, so
whoever writes the next episode can see the number they are writing against
instead of discovering it afterwards.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_home, episode_spec as es

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"


def line(text, kind="narration", index=0):
    return {"index": index, "kind": kind, "text": text}


def test_the_narrator_acting_is_found():
    said = [line("I carried the landlady's dying terrier up the stairs myself.")]
    assert es.narrator_acts(said) == [0]


def test_the_narrator_as_an_object_is_not_acting():
    """Episode 7's only first person, verbatim."""
    said = [line("He asked me to fetch up the old terrier our landlady had wanted put out of its pain.")]
    assert es.narrator_acts(said) == []


def test_a_narrator_acting_mid_sentence_counts():
    said = [line("The door was bolted from within, and I put my shoulder to it.")]
    assert es.narrator_acts(said) == [0]


def test_a_shared_subject_counts():
    """ep06's line, verbatim: the narrator is still one of the actors."""
    said = [line("Holmes and I read the notices over together at breakfast, and he said nothing.")]
    assert es.narrator_acts(said) == [0]


def test_dialogue_is_not_narration():
    """Every speaker says "I". Only the NARRATOR's own lines are the question."""
    said = [line("I have found it! I have found it!", kind="dialogue"),
            line("He stood over it with his watch open in his hand.")]
    assert es.narrator_acts(said) == []


def test_a_capital_i_inside_a_word_is_not_a_pronoun():
    said = [line("The INSPECTOR said nothing, and Iron gates stood open on the lane.")]
    assert es.narrator_acts(said) == []


def test_an_episode_where_the_narrator_never_acts_is_a_fault():
    said = [line("The window stood wide open.", index=0),
            line("Cold, and some hours dead.", index=1)]
    assert es.silent_narrator(said)


def test_one_line_is_enough():
    said = [line("The window stood wide open.", index=0),
            line("I watched Holmes's face, and nothing moved in it.", index=1)]
    assert es.silent_narrator(said) == []


def test_the_delivered_episodes_measure_as_recorded():
    """The census this gate is built on. ep07 is the only zero."""
    if not (BOOK / "episodes/ep01/plan.json").exists():
        pytest.skip("the book is not on this disk")
    got = {}
    for n in range(1, 8):
        episode = episode_home.load_plan(BOOK, n)
        got[n] = len(es.narrator_acts([l.model_dump() for l in episode.lines]))
    assert got == {1: 4, 2: 5, 3: 2, 4: 1, 5: 1, 6: 3, 7: 0}, got


def test_only_episode_7_fails_the_floor():
    if not (BOOK / "episodes/ep01/plan.json").exists():
        pytest.skip("the book is not on this disk")
    failed = [n for n in range(1, 8)
              if es.silent_narrator([l.model_dump()
                                     for l in episode_home.load_plan(BOOK, n).lines])]
    assert failed == [7], failed


# ---- Part Two has no Watson -------------------------------------------------
#
# Chapters 8 to 13 of A Study in Scarlet leave London entirely: the alkali
# plain, 1847, John Ferrier and Lucy and Brigham Young's caravan. Watson is not
# in them and Doyle tells them in the third person. A rule that says "the
# narrator must act" would refuse every one of those six episodes BY
# CONSTRUCTION -- a gate calibrated on episodes 1 to 7 and applied to a world
# that changes at episode 8.
#
# The discriminator is measured, not assumed: in all seven delivered plans the
# narration's speaker is `john_watson` AND `john_watson` is in the setups' cast.
# A narrator who stands in his own scenes is a witness and must act in them. A
# narrator who appears in none of them is telling somebody else's story, and
# asking him to act is asking for a different story.


def test_a_narrator_who_is_in_the_cast_must_act():
    said = [line("The window stood wide open.")]
    assert es.silent_narrator(said, cast={"john_watson"}, narrator="john_watson")


def test_a_narrator_who_is_in_none_of_the_scenes_need_not():
    """Episode 8's shape: the plain, Ferrier, Lucy, and nobody telling it from
    inside."""
    said = [line("The great salt plain stretched before his eyes, and there was no gleam of hope.")]
    assert es.silent_narrator(said, cast={"john_ferrier", "lucy_ferrier"},
                              narrator="chronicler") == []


def test_the_default_is_still_the_strict_one():
    """A caller that names no cast cannot know whether the narrator is in it, and
    gets the rule that refuses. Nothing loosens by omission."""
    assert es.silent_narrator([line("The window stood wide open.")])


def test_part_one_still_measures_as_recorded():
    if not (BOOK / "episodes/ep07/plan.json").exists():
        pytest.skip("the book is not on this disk")
    failed = []
    for n in range(1, 8):
        episode = episode_home.load_plan(BOOK, n)
        cast = {who for s in episode.setups.values() for who in s.cast}
        narrator = next((l.speaker for l in episode.lines if l.kind == "narration"), "")
        if es.silent_narrator([l.model_dump() for l in episode.lines],
                              cast=cast, narrator=narrator):
            failed.append(n)
    assert failed == [7], failed
