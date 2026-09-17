"""A line cloned from an ALTERNATE reference must still be the man in the room.

MEASURED on episode 10 (analyst F).  John Ferrier speaks three lines in one
scene; l14 and l22 were cloned from his design clip and l27, on its fourth try,
from ep08/l25 by the book-wide best-reference rule.  Against the design clip l27
"passed" at 0.701 -- by 0.001.  Against his OTHER lines in the same room it
measured 0.585 / 0.589 / 0.588, while l14-vs-l22 sits at 0.839 and his lines
across two episodes at 0.79-0.90.  The rule bought a pass at the price of the
one thing a listener actually compares: this line against the last one.

So an alternate-reference render is accepted only if its line-vs-line
similarity against the speaker's other PASSED lines in the SAME episode is at
or over EPISODE_VOICE.  Otherwise the design-clip render stays, even at 0.69.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_say2", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["ep_say2"] = say
spec.loader.exec_module(say)


def wav(path: Path, seconds: float = 4.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.zeros(int(24000 * seconds), dtype="float32"), 24000)
    return path


def ferrier_room(tmp_path):
    for n in (14, 22, 27):
        wav(tmp_path / f"episodes/ep10/audio/lines/l{n:02d}.wav")
    return {14: {"index": 14, "speaker": "john_ferrier", "passed": True, "similarity": 0.712,
                 "reference": "design.wav", "rel_path": "episodes/ep10/audio/lines/l14.wav", "text": "Give us time."},
            22: {"index": 22, "speaker": "john_ferrier", "passed": True, "similarity": 0.736,
                 "reference": "design.wav", "rel_path": "episodes/ep10/audio/lines/l22.wav", "text": "We'll fix it."},
            27: {"index": 27, "speaker": "john_ferrier", "similarity": 0.701, "reference": "l25.wav",
                 "rel_path": "episodes/ep10/audio/lines/l27.wav", "text": "I am a free-born American."}}


def test_the_measured_l27_is_a_different_man_from_his_other_two_lines(tmp_path):
    records = ferrier_room(tmp_path)
    scored = {("l27.wav", "l14.wav"): 0.585, ("l27.wav", "l22.wav"): 0.589}
    got = say.episode_voice(tmp_path, records, records[27],
                            similarity=lambda a, b: scored[(a.name, b.name)])
    assert abs(got - 0.587) < 0.001
    assert not say.alternate_ok(got)


def test_a_line_that_matches_the_room_is_accepted(tmp_path):
    records = ferrier_room(tmp_path)
    got = say.episode_voice(tmp_path, records, records[27], similarity=lambda a, b: 0.84)
    assert say.alternate_ok(got)


def test_a_design_clip_render_is_never_judged_this_way(tmp_path):
    records = ferrier_room(tmp_path)
    assert say.episode_voice(tmp_path, records, records[14], similarity=lambda a, b: 0.1) is None
    assert say.alternate_ok(None)


def test_with_no_other_passed_line_in_the_episode_there_is_nothing_to_compare(tmp_path):
    records = ferrier_room(tmp_path)
    records[14]["passed"] = records[22]["passed"] = False
    assert say.episode_voice(tmp_path, records, records[27], similarity=lambda a, b: 0.1) is None


def test_the_floor_is_the_documented_one():
    assert say.EPISODE_VOICE == 0.75
    assert say.alternate_ok(0.75) and not say.alternate_ok(0.749)


def test_listen_all_fails_an_alternate_render_that_is_not_the_room_voice(tmp_path, monkeypatch):
    records = ferrier_room(tmp_path)
    design = wav(tmp_path / "cast/john_ferrier/voice/design.wav")
    monkeypatch.setattr(say, "reference_for", lambda book, who: design)

    def fake_similarity(a, b):
        return 0.59 if "design" not in a.name and "design" not in b.name else 0.71

    monkeypatch.setattr(say.voice_ear, "similarity", fake_similarity)
    failed = say.listen_all([records[27]], tmp_path, lambda clip: records[27]["text"], among=records)
    assert failed == [27]
    assert records[27]["episode_voice"] == 0.59 and not records[27]["passed"]


def test_keep_best_prefers_the_design_render_over_a_rejected_alternate(tmp_path):
    """l27: the alternate scored 0.701 against design, the design render 0.69.
    The alternate is not the man in the room, so 0.69 stays."""
    out = tmp_path / "l27.wav"; out.write_bytes(b"alt")
    prev = tmp_path / "l27.prev.wav"; prev.write_bytes(b"design")
    previous = {"index": 27, "similarity": 0.69, "passed": False, "reference": "design.wav"}
    new = {"index": 27, "similarity": 0.701, "passed": False, "reference": "l25.wav", "episode_voice": 0.59}
    kept = say.keep_best(new, previous, out)
    assert kept["similarity"] == 0.69 and out.read_bytes() == b"design" and not prev.exists()
