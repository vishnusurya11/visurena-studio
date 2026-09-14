"""The black chip has ONE length, and both the cutter and the gate read it.

MEASURED 2026-09-13, on every episode this book has ever produced:

    ep01  expected 3756  master 3714  delta 42
    ep02  expected 3913  master 3871  delta 42
    ep03  expected 4043  master 4001  delta 42

42 = 48 - 6, exactly, three times.  `assemble.END_CHIP_SECONDS` was moved from
2.0 s to 0.25 s ("2 s of silent black before a loop is dead time", title-ends
review 2026-09-11), which renders SIX frames; `edit_gate.tail_check` kept its
`black: int = 48`, and `edit_integrity` never passed the real number.

So `tail["ok"]` has been structurally False since that day, which made
`edit_integrity.ok` False, which made `qc.verdict` False, which made
`qc.passed: false` on EVERY episode ever cut.  Two of the three rows in
`uploads.jsonl` carry a `waived` block as a result.

That is the whole cost of this bug, and it is not the 42 frames: a gate that
can never pass is a gate nobody reads, and routine overriding is how a cut whose
QC report had never seen it reached YouTube on 2026-09-13.
"""
import numpy as np

from studio import edit_gate as gate


def moving(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(n, gate.GREY_H, gate.GREY_W), dtype=np.uint8)


def black(n: int) -> np.ndarray:
    return np.zeros((n, gate.GREY_H, gate.GREY_W), dtype=np.uint8)


def test_the_chip_is_six_frames_not_forty_eight():
    """One quarter-second at 24 fps. The number the cutter actually renders."""
    assert gate.END_CHIP_FRAMES == 6


def test_a_real_tail_passes():
    picture, card = moving(10), moving(6, seed=9)
    good = np.concatenate([picture, card, black(gate.END_CHIP_FRAMES)])
    assert gate.tail_check(good, 10, card)["ok"]


def test_the_forty_eight_frame_tail_this_gate_used_to_demand_now_fails():
    """The mirror of the bug: 48 black frames is 42 too many, and saying so is
    the point -- the old default called the CORRECT tail a fault."""
    picture, card = moving(10), moving(6, seed=9)
    was = np.concatenate([picture, card, black(48)])
    out = gate.tail_check(was, 10, card)
    assert not out["ok"]
    assert out["expected_frames"] == 10 + 6 + gate.END_CHIP_FRAMES


def test_the_expected_count_is_picture_plus_card_plus_the_chip():
    picture, card = moving(10), moving(6, seed=9)
    out = gate.tail_check(np.concatenate([picture, card, black(6)]), 10, card)
    assert out["expected_frames"] == out["master_frames"] == 22


def test_a_caller_may_still_name_a_different_chip():
    """The parameter stays, so a book that wants a longer run-out can say so --
    what is fixed is the DEFAULT agreeing with the cutter."""
    picture, card = moving(10), moving(6, seed=9)
    assert gate.tail_check(np.concatenate([picture, card, black(12)]), 10, card, black=12)["ok"]


def test_the_cutter_derives_its_seconds_from_the_gates_frame_count():
    """One fact, one owner. `studio` holds the contract; `scripts` reads it."""
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("asm", root / "scripts/episode/assemble.py")
    asm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(asm)
    assert round(asm.END_CHIP_SECONDS * asm.FPS) == gate.END_CHIP_FRAMES
