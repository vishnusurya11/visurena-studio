"""G-TAIL: a dialogue take whose mouth speaks into the silent guide tail fails (C1_verdict #7).

MEASURED (C1_A): H3 continues the line into the digitally silent tail of its voice
guide, and every invented word echoes the line's last word ("...Keep moving.
Moving!"). Masters strip the take's audio, so the sound never ships, but the mouth
does. Audio and mouth are one sample: a loud tail moves the mouth, a quiet tail
keeps it shut. So the take FAILS when its shipped tail is louder than -45 dB AND
(Whisper hears words after the line's last shared word, OR the mouth is open for
>= 6 frames with >= 2 rises). The mouth branch is armed because the replay over all
204 shipped dialogue takes gives it 0 false fails on the static-mouth takes and the
loud closed-mouth tails. A tail whose post-line clause asks for a mouth action is
exempt; a guide whose speech end disagrees with placed.json by more than a second
was overwritten and reads UNMEASURABLE, never invented. Cure: one reseed, then
keep_best flagged. The fixture is derived from the measured rows.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from studio import invented_speech as inv
from studio import take_ladder
from studio.judges.verdict import Fault, Verdict

ROWS = json.loads((Path(__file__).parent / "fixtures" / "tail" / "shipped_tail_rows.json").read_text())["rows"]


def state(r: dict) -> str:
    return inv.tail_state(ship_db=r["ship_tail_db"], words=r["words"],
                          mouth=inv.mouth_speaks(r["open_run_ship"] or 0, r["ups_ship"] or 0),
                          asked=inv.asked_mouth(" ".join(r["after"])),
                          stale=inv.stale(r["guide_end"], r["placed_end"]))


def by_state() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for r in ROWS:
        out.setdefault(state(r), []).append(r["take"])
    return out


def test_the_shipped_replay_fails_exactly_the_two_speaking_tails():
    assert sorted(by_state()["fail"]) == ["wotw/ep10/T21", "wotw/ep26/T25"]


def test_ep26_t25_fails_only_through_the_mouth_branch():
    row = next(r for r in ROWS if r["take"] == "wotw/ep26/T25")
    assert row["words"] == [] and state(row) == "fail"


def test_the_prompt_asked_mouths_are_exempt():
    assert by_state()["exempt"] == ["wotw/ep25/T21"]          # the laugh: loud, worded, asked
    for take in ("wotw/ep25/T21", "wotw/ep22/T12", "wotw/ep04/T02", "scarlet/ep11/T17"):
        row = next(r for r in ROWS if r["take"] == take)
        assert inv.asked_mouth(" ".join(row["after"])), take


def test_the_five_overwritten_scarlet_guides_are_unmeasurable():
    assert sorted(by_state()["unmeasurable"]) == ["scarlet/ep01/T18", "scarlet/ep01/T20", "scarlet/ep01/T22",
                                                 "scarlet/ep02/T20", "scarlet/ep02/T22"]


def test_a_waving_arm_or_a_sway_is_not_a_mouth_action():
    assert not inv.asked_mouth("his arm goes on waving the others down the hill")
    assert not inv.asked_mouth("her head tips toward the right as her body begins to sway")
    assert not inv.asked_mouth("he pulls his trousers up")


def test_open_runs_and_rises_are_read_off_the_aperture():
    ap = np.array([0, 0, .2, .2, 0, .2, .2, .2, .2, .2, .2, 0])
    assert inv.open_run(ap, 0.1) == (6, 2)


def test_a_quiet_tail_is_never_a_fault():
    assert inv.tail_state(ship_db=-60.0, words=["moving"], mouth=True, asked=False, stale=False) == "pass"


def test_the_tail_row_is_hard_and_unmeasurable_passes_nothing_but_refuses_nothing():
    assert inv.tail_row({"state": "fail"}).hard and not inv.tail_row({"state": "fail"}).ok
    assert inv.tail_row({"state": "unmeasurable"}).ok and inv.tail_row({"state": "unmeasurable"}).value is None


def test_a_tail_fault_is_reseeded_once_then_goes_to_the_terminal(tmp_path):
    fresh = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                    faults=[Fault(kind="tail", where="T05", evidence={"repeated": False})])
    again = fresh.model_copy(update={"faults": [Fault(kind="tail", where="T05", evidence={"repeated": True})]})
    assert take_ladder.route(fresh, tmp_path) == {"seed": {5: fresh.faults}}
    assert take_ladder.route(again, tmp_path) == {}
    assert take_ladder.still_for(tmp_path, 5, again.faults) is None


def test_the_post_line_clause_is_read_from_the_prompt():
    prompt = ("He says <d>Keep moving.</d> At 00:03, as the line ends, his arm goes on waving the others "
              "down the hill. At 00:04 the smoke drifts.")
    assert inv.after_line(prompt) == "At 00:03, as the line ends, his arm goes on waving the others down the hill."


def _wav(path, *parts, sr=24000):
    import soundfile as sf
    sig = np.concatenate([a * np.sin(2 * np.pi * 220 * np.arange(int(s * sr)) / sr) for s, a in parts])
    sf.write(str(path), sig.astype(np.float32), sr)
    return path


def test_the_take_gate_hears_a_sounding_tail_and_fails_it(tmp_path, monkeypatch):
    from scripts.episode import take_dq
    guide = _wav(tmp_path / "voice_05.wav", (1.0, 0.3), (2.0, 0.0))
    take = _wav(tmp_path / "T05.wav", (1.0, 0.3), (2.0, 0.3))
    monkeypatch.setattr(take_dq, "voice_qc_hear", lambda p: "keep moving")
    rec = {"lane": "dialogue", "placed_seconds": 3.0, "line_room": 2.0, "prompt": "At 00:01, as the line ends, he waves."}
    got = take_dq.tail_measure(take, guide, rec, [], None, "keep moving moving")["tail"]
    assert got["state"] == "fail" and got["words"] == ["moving"]
    rows = take_dq.judge_rows({"tail": got}, {**rec, "motion": ""})
    assert [r.name for r in rows][-1] == "tail" and not rows[-1].ok


def test_a_quiet_tail_is_never_sent_to_the_ear(tmp_path, monkeypatch):
    from scripts.episode import take_dq
    guide = _wav(tmp_path / "voice_05.wav", (1.0, 0.3), (2.0, 0.0))
    monkeypatch.setattr(take_dq, "voice_qc_hear", lambda p: (_ for _ in ()).throw(AssertionError("heard")))
    rec = {"lane": "dialogue", "placed_seconds": 3.0, "line_room": 2.0, "prompt": ""}
    assert take_dq.tail_measure(guide, guide, rec, [], None, "x")["tail"]["state"] == "pass"
