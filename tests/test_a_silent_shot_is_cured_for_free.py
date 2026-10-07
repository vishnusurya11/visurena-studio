"""ep22 (2026-10-07): the landed luna plan climbed four rungs on ONE fault --
'G-STORY plan: shots carrying no line (silent shots), measured 0 against 1' --
and the writer, told to keep every other word, never gave a shot up.  The cure
is one move: the shortest single narration line, not the hook, the turn or the
button, joins the line before it, and its shot falls silent.  $0."""
from __future__ import annotations

from studio import plan_cures


def _doc():
    shots = [{"index": i, "section": "setup", "beat_s": 0.0} for i in range(6)]
    shots[0]["section"] = "hook"; shots[3]["section"] = "turn"; shots[5]["section"] = "payoff"
    lines = [{"index": 0, "kind": "narration", "speaker": "n", "shot": 0, "text": "one two three four five six seven"},
             {"index": 1, "kind": "narration", "speaker": "n", "shot": 1, "text": "eight nine ten eleven twelve thirteen"},
             {"index": 2, "kind": "narration", "speaker": "n", "shot": 2, "text": "fourteen fifteen"},
             {"index": 3, "kind": "narration", "speaker": "n", "shot": 3, "text": "sixteen seventeen eighteen nineteen"},
             {"index": 4, "kind": "dialogue", "speaker": "c", "shot": 4, "text": "Twenty."},
             {"index": 5, "kind": "narration", "speaker": "n", "shot": 5, "text": "the button line here now"}]
    return {"shots": shots, "lines": lines}


def test_the_shortest_narration_line_joins_the_line_before_and_its_shot_falls_silent():
    out = plan_cures.silent_shot(_doc())
    shots_with_lines = {l["shot"] for l in out["lines"]}
    assert 2 not in shots_with_lines and len(out["lines"]) == 5
    assert out["lines"][1]["text"] == "eight nine ten eleven twelve thirteen fourteen fifteen"
    assert [l["index"] for l in out["lines"]] == [0, 1, 2, 3, 4]


def test_the_hook_the_turn_the_button_and_dialogue_are_never_the_one_silenced():
    doc = _doc()
    doc["lines"] = [l for l in doc["lines"] if l["shot"] in (0, 3, 4, 5)]
    for s in doc["shots"]:
        pass
    out = plan_cures.silent_shot(doc)
    assert len(out["lines"]) == 4                      # nothing eligible: unchanged


def test_the_cure_is_in_the_table():
    assert plan_cures.cure_for("G-STORY plan: shots carrying no line (silent shots), measured 0 against 1") == "silent_shot"
