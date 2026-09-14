"""A gate that can refuse must leave a way forward.

`bed_gate` listens to the music bed and refuses one that sings -- episode 3's
sang invented English verse under the narration for 64 % of its length and
reached YouTube's queue.  The refusal is right.

But the bed's seed is `90000 + number`, fixed per episode, and the refused file
is renamed to `bed.sings.wav`.  So re-running `assemble` regenerates the SAME
bed from the SAME seed, it sings again, and it is refused again.  Measured on
episode 4, 2026-09-14: the assemble died after four minutes of GPU with no
master, and every retry would have died the same way.  There is no flag to
change the seed.

`refused_name` in the same subsystem already wrote the rule down -- "a model
that sings once tends to sing again ... read the name off what is there, never
off a counter".  The seed follows it: each refused bed already on disk moves the
next attempt along, so a plain re-run re-rolls, and the number is reproducible
from the disk rather than remembered.
"""
from pathlib import Path

from scripts.episode.assemble import bed_seed


def refused(home: Path, *names: str) -> Path:
    (home / "audio").mkdir(parents=True, exist_ok=True)
    for n in names:
        (home / "audio" / n).write_bytes(b"")
    return home


def test_a_first_bed_uses_the_episodes_own_seed(tmp_path):
    assert bed_seed(refused(tmp_path) / "audio" / "bed.wav", 4) == 90004


def test_one_refusal_on_disk_moves_the_seed(tmp_path):
    home = refused(tmp_path, "bed.sings.wav")
    assert bed_seed(home / "audio" / "bed.wav", 4) != 90004


def test_each_further_refusal_moves_it_again(tmp_path):
    home = refused(tmp_path, "bed.sings.wav", "bed.sings2.wav")
    seeds = {bed_seed(home / "audio" / "bed.wav", 4)}
    seeds.add(bed_seed(refused(tmp_path, "bed.sings3.wav") / "audio" / "bed.wav", 4))
    assert len(seeds) == 2


def test_the_seed_is_reproducible_from_the_disk(tmp_path):
    """Read off what is there, never off a counter: the same tree gives the same
    seed twice."""
    home = refused(tmp_path, "bed.sings.wav")
    assert bed_seed(home / "audio" / "bed.wav", 4) == bed_seed(home / "audio" / "bed.wav", 4)


def test_two_episodes_never_share_a_seed(tmp_path):
    home = refused(tmp_path, "bed.sings.wav")
    a = bed_seed(home / "audio" / "bed.wav", 4)
    b = bed_seed(home / "audio" / "bed.wav", 5)
    assert a != b


def test_a_refused_bed_of_another_name_is_not_counted(tmp_path):
    home = refused(tmp_path, "bed.wav", "voice_00.wav")
    assert bed_seed(home / "audio" / "bed.wav", 4) == 90004
