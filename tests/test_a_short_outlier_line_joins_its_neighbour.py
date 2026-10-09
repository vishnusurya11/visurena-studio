"""ep27 (2026-10-09 17:00Z): three revoice rounds could not cure the narrator's
split voice -- every failing pair ran through l01 'Yet I write on.' (2.46 s), and
every render of it sat further from his other lines than the original.  The line
shares shot 1 with l02 'Carver's germs most likely killed them.'  Joined, the
book's words are kept, the outlier is gone and the line is long enough to measure.
The recorder reuses every recording whose text it already has, so only the
joined line is said again."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from studio import plan_cures as pc

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("say_lines_join", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["say_lines_join"] = say
spec.loader.exec_module(say)

N = "unnamed_first_person_narrator"


def _doc():
    lines = [{"index": 0, "shot": 0, "kind": "narration", "speaker": N, "text": "I am ending my story."},
             {"index": 1, "shot": 1, "kind": "narration", "speaker": N, "text": "Yet I write on."},
             {"index": 2, "shot": 1, "kind": "narration", "speaker": N, "text": "Carver's germs killed them."},
             {"index": 3, "shot": 2, "kind": "narration", "speaker": N, "text": "Only bacteria were found."}]
    return {"lines": lines, "answer": "line 3", "shots": [{"index": i} for i in range(3)]}


def test_a_short_line_joins_the_next_line_on_its_shot():
    doc = pc.join_line(_doc(), 1)
    assert [l["text"] for l in doc["lines"]] == ["I am ending my story.",
                                                 "Yet I write on. Carver's germs killed them.",
                                                 "Only bacteria were found."]
    assert [l["index"] for l in doc["lines"]] == [0, 1, 2]
    assert doc["answer"] == "line 2"


def test_a_line_with_no_neighbour_on_its_shot_is_left_alone():
    doc = _doc()
    assert pc.join_line(json.loads(json.dumps(doc)), 3) == doc


def test_step_04_joins_a_lone_short_culprit_after_the_rounds(tmp_path, monkeypatch):
    from scripts.episode import step_04_record as step
    from studio import episode_home
    home = tmp_path / "ep27"
    (home / "audio" / "lines").mkdir(parents=True)
    (home / "review").mkdir()
    (home / "plan.json").write_text(json.dumps(_doc()), encoding="utf-8")
    rows = [{"index": i, "text": l["text"], "seconds": 2.46 if i == 1 else 4.0, "speaker": N}
            for i, l in enumerate(_doc()["lines"])]
    (home / "audio" / "lines" / "lines.json").write_text(json.dumps(rows), encoding="utf-8")
    split = {N: {"ok": False, "under": [["l00", "l01"], ["l01", "l02"], ["l01", "l03"]]}}
    (home / "review" / "speaker_check.json").write_text(json.dumps(split), encoding="utf-8")
    (home / "review" / step.REVOICED).write_text(json.dumps([[1], [1], [1]]), encoding="utf-8")
    monkeypatch.setattr(episode_home, "write_plan", lambda path, doc: path.write_text(json.dumps(doc), encoding="utf-8"))
    calls = []
    ctx = SimpleNamespace(home=home, book_dir=tmp_path, number=27, extra=[],
                          run_script=lambda script, *a, **k: calls.append(script.rsplit("/", 1)[-1]))
    assert step.done(ctx) is False                       # rounds spent, the join not yet tried
    step.revoice(ctx)
    plan = json.loads((home / "plan.json").read_text(encoding="utf-8"))
    assert plan["lines"][1]["text"] == "Yet I write on. Carver's germs killed them."
    assert calls == ["say_lines.py", "speaker_check.py"]
    assert step.done(ctx) is True                        # joined once: the door decides


def test_the_recorder_reuses_a_recording_by_its_text(tmp_path):
    out = tmp_path / "episodes" / "ep27" / "audio" / "lines"
    out.mkdir(parents=True)
    for i, word in enumerate(["a", "b", "c", "d"]):
        (out / f"l{i:02d}.wav").write_bytes(word.encode())
    old = {i: {"index": i, "speaker": N, "text": l["text"], "passed": True, "seconds": 2.0,
               "rel_path": f"episodes/ep27/audio/lines/l{i:02d}.wav"} for i, l in enumerate(_doc()["lines"])}
    new_lines = [SimpleNamespace(index=i, text=l["text"], speaker=N, shot=l["shot"])
                 for i, l in enumerate(pc.join_line(_doc(), 1)["lines"])]
    got = say.rekeyed(old, new_lines, out, tmp_path)
    assert got[0]["text"] == "I am ending my story." and (out / "l00.wav").read_bytes() == b"a"
    assert 1 not in got                                       # the joined line is new: said again
    assert got[2]["text"] == "Only bacteria were found." and (out / "l02.wav").read_bytes() == b"d"
    assert got[2]["rel_path"].endswith("l02.wav") and got[2]["index"] == 2
