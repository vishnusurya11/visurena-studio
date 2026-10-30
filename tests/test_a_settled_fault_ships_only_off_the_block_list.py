"""The narrow ship-block (owner 2026-10-30, Jekyll ep01-06 retro): a take the ladder settled keep_best/high ships
flagged unless its faults are on the block list -- a wrong person (G-PEOPLE), the prompt's own scaffold words read
back from the picture, hair no staged row allows, or a plate leak of 9 frames or more.

Replayed on the latest take eyes of ep02-06 (skeptic.md section 2), the list refuses exactly the five faults an eye
confirmed -- ep04 T05/T10/T12 (plate leak), ep05 T07 (grey hair on black-haired Jekyll), ep06 T19 ("THE FOCUS OF THE
PICTURE" on the envelope) -- and ships warp, gait and the chapter's own lettered letter (ep05 T18/T22).  Blocking
every settled fault parked 4 of 5 episodes, about 30 % of them on correct pictures."""
from studio import dead_footage as dead
from studio import ship_block as sb


def settled(where, kind, note, value=None, frames=None, how="keep_best"):
    ev = {"settled": how}
    if value is not None:
        ev["value"] = value
    if frames is not None:
        ev["frames"] = frames
    return {"where": where, "kind": kind, "note": note, "evidence": ev}


REPLAY = [
    settled("T05", "leak", "12 frames of plate before the panel", 12, 12),            # ep04
    settled("T10", "leak", "12 frames of plate before the panel", 12, 12, "high"),    # ep04
    settled("T12", "leak", "9 frames of plate before the panel", 9, 9),               # ep04
    settled("T07", "content", "gray hair where the row says otherwise", how="high"),  # ep05
    settled("T19", "content", "scaffold: the prompt's words drawn in the picture (focus, picture)", how="high"),
    settled("T23", "warp", "fail: S 2.67 Se 5.92 over 100% tracked", 2.67),            # ep06, probable false
    settled("T05", "gait", "shuffle: 4.0 steps/s HARD: the feet slide", 0.026),         # ep06
    settled("T18", "content", "text or lettering in the picture"),                     # ep05, the chapter's letter
    settled("T22", "content", "text or lettering in the picture", how="high"),        # ep05
    settled("T11", "look", "no floor p5 22 black 0.07 hue 0.54", 22.35),               # ep05
]


def test_the_replay_blocks_exactly_the_five_confirmed_faults():
    blocked = [(f["where"], f["kind"]) for f in REPLAY if sb.blocks(f)]
    assert blocked == [("T05", "leak"), ("T10", "leak"), ("T12", "leak"), ("T07", "content"), ("T19", "content")]


def test_a_short_leak_still_ships_flagged():
    assert not sb.blocks(settled("T03", "leak", "8 frames of plate before the panel", 8, 8))


def test_a_wrong_person_still_blocks():
    assert sb.blocks(settled("T06", "content", "who: two figures resolve to poole"))


def test_scaffold_words_are_read_from_the_ocr_strings():
    assert sb.scaffold_words(["THE FOCUS OF THE PICTURE Bomye.", "Tisso te botsmle"]) == ["focus", "picture"]
    assert sb.scaffold_words(["Tiros te bobmle", "Henry Jekyll"]) == []


def test_admitted_refuses_a_kept_take_on_the_block_list():
    kept = {5: [REPLAY[0]], 7: [REPLAY[3]], 23: [REPLAY[5]], 18: [REPLAY[7]]}
    assert sorted(dead.admitted(kept)) == [18, 23]


def test_the_blocked_takes_are_named_by_index():
    assert sb.takes(REPLAY) == {5, 7, 10, 12, 19}


def test_the_master_terminal_refuses_a_blocked_fault():
    import pytest
    from studio import master_ladder
    from studio.judges.verdict import Fault, Verdict
    v = Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                faults=[Fault(kind="content", where="shot_19", evidence={"faults": [sb.scaffold_line(["focus"])]})])
    with pytest.raises(SystemExit, match="shot_19"):
        master_ladder.flag(v)


def test_g_dead_cuts_a_kept_take_with_a_long_leak(tmp_path, monkeypatch):
    from tests.test_a_wrong_person_never_ships_flagged import _cut
    leak = {"kind": "leak", "where": "T04", "severity": "normal", "note": "12 frames of plate before the panel",
            "evidence": {"settled": "keep_best", "frames": 12}}
    plan = _cut(tmp_path, monkeypatch, [leak])
    assert plan["cut"] == [4] and plan["flagged"] == []


def test_a_take_that_shows_text_is_read_for_scaffold_words(tmp_path):
    from scripts.episode import take_content_check as tcc
    for i in range(tcc.SAMPLES):
        (tmp_path / f"T19_{i}.png").write_bytes(b"png")
    seen = {"T19_1.png": ["THE FOCUS OF THE PICTURE", "Bomye."]}
    reader = lambda path: seen.get(path.name, [])                                    # noqa: E731
    row = tcc.with_scaffold({"passed": True, "faults": [], "text": True}, tmp_path, "T19", reader)
    assert row["passed"] is False and row["faults"] == [sb.scaffold_line(["focus", "picture"])]


def test_a_take_with_no_text_is_never_ocr_read(tmp_path):
    from scripts.episode import take_content_check as tcc

    def reader(path):
        raise AssertionError("OCR ran on a take with no text")
    row = {"passed": True, "faults": [], "text": False}
    assert tcc.with_scaffold(row, tmp_path, "T03", reader) == row
