"""Best-of-N compared one file, and two copies of the same function disagreed
about where the losers live.

`take_dq --attempts` is supposed to judge every roll of a take and keep the best.
It found them with `take_dir.glob("T<NN>_*.mp4")`, and `migrate_layout` moved the
displaced rolls into `take_dir/attempts/`. So on any migrated episode the glob
returned nothing, `attempts_of` handed back the kept file alone, and the report
said `kept T07.mp4 of 1` while four rolls sat one folder down.

MEASURED 2026-09-14: episode 3 holds T07_fail1, _fail3, _fail4 and _fail5 in
`takes/r2v/attempts/`; episode 4's sit flat in `takes/r2v/`, because the renderer
wrote them after the move and nothing told it where they go. Two locations, and
a reader of either report concludes a best-of-5 was adjudicated.

`next_fail` has the same blindness and a worse consequence: it names the next
free `_failN` off a glob of the flat folder, so with the losers elsewhere it
returns `_fail1` while `attempts/T07_fail1.mp4` already exists. Its own docstring
promises "no displaced attempt is ever overwritten", and that held only by the
accident of the collision being in a different directory.

There were TWO copies of it -- `take_dq.next_fail` and `takes_r2v.next_fail` --
whose own docstring says "the renderer had its own, worse, copy of the idea".
One copy now, in `episode_home`, beside the `attempts_dir` helper that has been
sitting there with zero callers.
"""
from pathlib import Path

from studio import episode_home


def roll(where: Path, name: str) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    (where / name).write_bytes(b"x")
    return where / name


# ---- finding every roll -----------------------------------------------------

def test_a_roll_in_the_attempts_room_is_found(tmp_path):
    roll(tmp_path, "T07.mp4")
    roll(tmp_path / "attempts", "T07_fail1.mp4")
    got = [p.name for p in episode_home.attempts_of(tmp_path, 7)]
    assert got == ["T07.mp4", "T07_fail1.mp4"]


def test_a_roll_left_flat_is_still_found(tmp_path):
    """Episode 4's rolls were written after the move and sit in the take dir."""
    roll(tmp_path, "T12.mp4")
    roll(tmp_path, "T12_fail1.mp4")
    got = [p.name for p in episode_home.attempts_of(tmp_path, 12)]
    assert got == ["T12.mp4", "T12_fail1.mp4"]


def test_both_rooms_are_read_together(tmp_path):
    roll(tmp_path, "T07.mp4")
    roll(tmp_path, "T07_fail1.mp4")
    roll(tmp_path / "attempts", "T07_fail2.mp4")
    got = [p.name for p in episode_home.attempts_of(tmp_path, 7)]
    assert got == ["T07.mp4", "T07_fail1.mp4", "T07_fail2.mp4"]


def test_the_kept_file_comes_first(tmp_path):
    roll(tmp_path / "attempts", "T07_fail1.mp4")
    roll(tmp_path, "T07.mp4")
    assert episode_home.attempts_of(tmp_path, 7)[0].name == "T07.mp4"


def test_another_takes_rolls_are_not_collected(tmp_path):
    roll(tmp_path, "T07.mp4")
    roll(tmp_path / "attempts", "T08_fail1.mp4")
    assert [p.name for p in episode_home.attempts_of(tmp_path, 7)] == ["T07.mp4"]


def test_no_rolls_at_all_is_an_empty_list(tmp_path):
    assert episode_home.attempts_of(tmp_path, 7) == []


# ---- and never overwriting one ----------------------------------------------

def test_the_next_name_counts_rolls_in_both_rooms(tmp_path):
    roll(tmp_path / "attempts", "T07_fail1.mp4")
    roll(tmp_path, "T07_fail2.mp4")
    assert episode_home.next_fail(tmp_path, 7).name == "T07_fail3.mp4"


def test_the_next_name_lands_in_the_attempts_room(tmp_path):
    assert episode_home.next_fail(tmp_path, 7).parent.name == "attempts"


def test_a_first_roll_is_fail_one(tmp_path):
    assert episode_home.next_fail(tmp_path, 7).name == "T07_fail1.mp4"


def test_a_gap_is_never_filled(tmp_path):
    """Read off what is there, never off a counter: `_fail1` and `_fail3` on disk
    means the next is `_fail4`, so nothing is ever written over."""
    roll(tmp_path / "attempts", "T07_fail1.mp4")
    roll(tmp_path / "attempts", "T07_fail3.mp4")
    assert episode_home.next_fail(tmp_path, 7).name == "T07_fail4.mp4"


def test_the_renderer_and_the_judge_share_one_copy():
    import inspect
    from scripts.episode import take_dq, takes_r2v
    for mod in (take_dq, takes_r2v):
        src = inspect.getsource(mod)
        assert "def next_fail" not in src, f"{mod.__name__} keeps its own copy"
