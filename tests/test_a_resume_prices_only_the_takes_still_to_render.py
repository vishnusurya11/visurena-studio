"""ep14 (2026-09-28): a resume with all 30 takes on disk was refused -- "the
takes want 7727 s and the episode ceiling leaves 7500 s" -- because the
affordability check priced a FULL render of the step, not the work left.
The render is priced by the shots that still have no take; the ladder prices
its own rungs."""
from pathlib import Path

from scripts.episode import step_09_shoot as step


def test_the_share_left_is_the_shots_without_a_take(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    shots = [{"index": i} for i in range(4)]
    assert step.share_missing(room, shots) == 1.0
    for i in (0, 1, 2):
        (room / f"T{i:02d}.mp4").write_bytes(b"take")
    assert step.share_missing(room, shots) == 0.25
    (room / "T03.mp4").write_bytes(b"take")
    assert step.share_missing(room, shots) == 0.0


def test_no_shots_is_a_full_render():
    assert step.share_missing(Path("nowhere"), []) == 1.0
