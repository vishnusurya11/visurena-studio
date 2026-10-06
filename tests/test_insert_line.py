"""insert_line splices a narration micro-line with the EXACT reindex: the new
line lands after every existing line of its shot (G-SYNC: a dialogue line
stays first), indices come back 0..n-1 in playback order, the button stays the
last element, and a 'line N' answer is remapped iff N >= the insertion point.
Refused outright on the button shot or later, and on a shot already carrying
MAX_LINES_PER_SHOT lines."""
from __future__ import annotations

import pytest

from studio import plan_cures as pc
from studio.episode_spec import Episode, Line, Setup, Shot

NARR = ("Then we walked on together down the long corridor and neither of us "
        "spoke a word.")  # 17 words
MICRO = "I heard the wind drag its claws along the shutters"  # 10 words


def doc_of(answer="line 2") -> dict:
    return {"answer": answer,
            "shots": [{"index": 0}, {"index": 1}, {"index": 2}, {"index": 3}],
            "lines": [
                {"index": 0, "kind": "dialogue", "speaker": "a", "text": "t0", "shot": 0},
                {"index": 1, "kind": "narration", "speaker": "b", "text": "t1", "shot": 0},
                {"index": 2, "kind": "narration", "speaker": "b", "text": "t2", "shot": 2},
                {"index": 3, "kind": "dialogue", "speaker": "c", "text": "t3", "shot": 3},
            ]}


def test_the_reindex_lands_after_the_shots_own_lines_and_keeps_the_button_last():
    doc = pc.insert_line(doc_of(), 1, MICRO, "b")
    texts = [l["text"] for l in doc["lines"]]
    assert texts == ["t0", "t1", MICRO, "t2", "t3"]              # after shot 0's pair, before shot 2
    assert [l["index"] for l in doc["lines"]] == [0, 1, 2, 3, 4]
    assert doc["lines"][2] == {"index": 2, "kind": "narration", "speaker": "b",
                               "text": MICRO, "shot": 1, "delivery": ""}
    assert doc["lines"][-1]["text"] == "t3"                      # the button is still last


def test_a_line_answer_at_or_past_the_insertion_point_moves_by_one():
    assert pc.insert_line(doc_of("line 2"), 1, MICRO, "b")["answer"] == "line 3"
    assert pc.insert_line(doc_of("line 1"), 1, MICRO, "b")["answer"] == "line 1"
    assert pc.insert_line(doc_of("shot 2"), 1, MICRO, "b")["answer"] == "shot 2"
    assert pc.insert_line(doc_of("the dark"), 1, MICRO, "b")["answer"] == "the dark"


def test_the_button_shot_and_a_full_shot_refuse_the_insertion():
    with pytest.raises(ValueError, match="button"):
        pc.insert_line(doc_of(), 3, MICRO, "b")                  # the button shot itself
    with pytest.raises(ValueError, match="button"):
        pc.insert_line(doc_of(), 4, MICRO, "b")                  # past it
    with pytest.raises(ValueError, match="carries"):
        pc.insert_line(doc_of(), 0, MICRO, "b")                  # already at 2 lines


def test_the_speaker_comes_from_the_first_narration_line():
    assert pc.narration_speaker(doc_of()) == "b"
    assert pc.narration_speaker({"lines": [
        {"kind": "dialogue", "speaker": "a", "text": "t", "shot": 0}]}) is None


def contract_doc() -> dict:
    """A contract-valid episode with a wordless mid-plan shot to insert into."""
    setups = {"lab": Setup(described="a lab", cast=["a", "b"])}
    shots = [Shot(index=0, section="hook", setup="lab", size="medium_close",
                  faces=["a"], frame="f", motion="m")]
    lines = [Line(index=0, kind="dialogue", speaker="a", shot=0,
                  text="You must not blame me if you do not get on with him at all.")]
    for k in range(24):
        section = "turn" if k == 15 else "friction"
        shots.append(Shot(index=len(shots), section=section, setup="lab", size="wide",
                          frame="f", motion="m",
                          coda_s=2.5 if k == 10 else 0.0))
        if k != 10:                                              # shot after k==10 stays wordless
            lines.append(Line(index=len(lines), kind="narration", speaker="b",
                              text=NARR, shot=shots[-1].index))
    shots[-1] = Shot(index=shots[-1].index, section="friction", setup="lab", size="wide",
                     frame="f", motion="m", beat_s=1.5)
    shots.append(Shot(index=len(shots), section="button", setup="lab", size="close",
                      faces=["c"], frame="f", motion="m"))
    lines.append(Line(index=len(lines), kind="dialogue", speaker="c",
                      text="The question now is about blood.", shot=shots[-1].index))
    shots.append(Shot(index=len(shots), section="answer", setup="lab", size="wide",
                      frame="f", motion="m", coda_s=3.0))
    return Episode(number=1, title="t", protagonist="b", setups=setups,
                   shots=shots, lines=lines).model_dump()


def test_the_contract_accepts_the_spliced_plan():
    doc = contract_doc()
    wordless = next(s["index"] for s in doc["shots"]
                    if not any(l["shot"] == s["index"] for l in doc["lines"]))
    got = pc.insert_line(doc, wordless, MICRO, "b")
    Episode.model_validate(got)
