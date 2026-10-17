"""The grammar's rows and the free cures (2026-10-17).

Three rows have a deterministic cure, run for $0 before any writer round
(feedback 'a cure is judged by every gate': each is replayed under the whole
battery on Jekyll plan_v3):
- an AMOUNT on a camera head is stripped (H3 governed 0 of 16 amounts);
- a THIRD PUSH is held locked, its actor clauses kept (05: the push softens and
  overruns; a locked frame with the actor's verb carries the beat);
- an over-the-shoulder CLOSE becomes a medium close, its head a third (D4).
Every other grammar row is creative and goes to the writer -- and no row may be
swallowed by an older cure's pattern ('look' -> pin_series, 'of the runtime' ->
holds), which would count it cured while nothing changed.  $0."""
from __future__ import annotations

import copy

from studio import plan_cures as pc
from studio.plan_gates import move_id

ROWS = {
    "G-PUSH shot 3: the camera head names an amount (\"a hand's breadth\") the model ignores; name the "
    "direction only, measured a hand's breadth against no amount": "strip_amounts",
    "G-PUSH shot 9: a push past the episode's two -- hold it locked and let the actor carry the beat, "
    "measured 3 against 2": "hold_extra_pushes",
    "G-OTS shot 4: an over-the-shoulder shot tighter than a medium close (the model opens wider and pushes), "
    "measured close against medium_close": "ots_medium_close",
}
CREATIVE = [
    "G-FACES plan: share of the shots with a face at close or medium_close, measured 0.3 against 0.55",
    "G-WIDE shot 0: a wide's seconds -- cut closer, or split its line, measured 6.1 against 5.0",
    "G-MEDIUM shot 3: a medium's seconds -- split the line across a reverse or an insert, measured 7.4 against 7.0",
    "G-INSERT shot 9: an insert's seconds -- an impact holds one to three; a long line splits across the "
    "insert and a reaction, measured 6.6 against 1.0-3.0",
    "G-LOCKED plan: locked-off share of the shots, measured 0.3 against 0.5",
    "G-TWO shot 7: a two-person reaction is a locked medium two-shot, measured full/follow against medium/locked",
    "G-PAYOFF shot 17: the payoff line is a locked close, measured medium_close/push_slow against close/locked",
    "G-UNSUPPORTED shot 0: asked in words, which the grid and the model ignore; unsupported until a panel "
    "route draws it, measured silhouette against a panel route",
    "G-COLD line 0: the cold open's first line in words -- name the event or its victim, never scenery first, "
    "measured 16 against 10",
    "G-COLD shot 0: the first shot carries a sound at its first frame, measured none against <= 0.25 s",
    "G-ACT plan: act_out shots -- end part A on the spike or its first consequence, held, the bed turning, "
    "measured 0 against 1",
    "G-ACT shot 8: where the act-out starts, as a share of the picture, measured 0.3 against 0.35-0.55",
    "G-CAPTION line 15: share of the narration's content words its shot already shows -- tell what the "
    "picture cannot, measured 0.86 against 0.8",
    "G-REACT shot 3: the exchange on shots 1-2 ends without a silent listener's face, measured a line or no "
    "face against a silent reaction",
    "G-MA plan: holds of 1.2 s or more (beat + coda) -- spend the silence after the reveals, never as crumbs "
    "on every shot, measured 2 against 3",
    "G-INNER line 4: an inner line plays over its speaker's own face, measured ['a'] against b",
    "G-SHOTS plan: shots in the cut -- 6.2 h projected against the owner's 6 h, measured 32 against 30",
]

PUSHED = ("The camera pushes in toward the lawyer's face, travelling a hand's breadth, across the whole "
          "shot; the lawyer lifts his eyes; his hand comes to rest on his chest")


def test_every_grammar_row_goes_to_its_cure_or_the_writer():
    assert {row: pc.cure_for(row) for row in ROWS} == ROWS
    assert [row for row in CREATIVE if pc.cure_for(row)] == []


def _doc():
    shot = {"index": 3, "size": "close", "motion": PUSHED, "frame": "Close on the lawyer",
            "camera": "", "at_rest": "THE FOCUS OF THE PICTURE IS his face, his head half the frame's height."}
    return {"shots": [shot]}


def test_an_amount_is_stripped_from_the_head_and_the_move_kept():
    got = pc.strip_amounts(_doc())["shots"][0]["motion"]
    assert "hand's breadth" not in got and got.startswith("The camera pushes in toward the lawyer's face")
    assert got.endswith("his hand comes to rest on his chest")


def test_an_extra_push_is_held_locked_with_its_actor_clauses():
    got = pc.hold_extra_pushes(_doc(), [3])["shots"][0]["motion"]
    assert move_id(got, "") == "locked" and "the lawyer lifts his eyes" in got


def test_an_over_the_shoulder_close_becomes_a_medium_close_a_third_high():
    doc = _doc()
    doc["shots"][0]["frame"] = "Close over the lawyer's shoulder toward Mr. Enfield's face"
    got = pc.ots_medium_close(copy.deepcopy(doc), [3])["shots"][0]
    assert got["size"] == "medium_close" and "a third of the frame's height" in got["at_rest"]
    assert got["frame"].startswith("Medium close over the lawyer's shoulder")


def test_the_repair_round_runs_the_grammar_cures(tmp_path):
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "scripts" / "episode" / "plan_repair.py"
    spec = importlib.util.spec_from_file_location("plan_repair_grammar", path)
    repair = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(repair)
    doc = _doc()
    doc["shots"][0].update(index=4, frame="Close over the lawyer's shoulder toward Mr. Enfield's face")
    got, uncured, names = repair.apply(doc, list(ROWS)[:1] + list(ROWS)[2:], tmp_path)
    assert names == ["ots_medium_close", "strip_amounts"] and uncured == []
    assert got["shots"][0]["size"] == "medium_close" and "breadth" not in got["shots"][0]["motion"]
