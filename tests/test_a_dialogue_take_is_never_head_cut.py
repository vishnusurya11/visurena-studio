"""ep24 (2026-10-09 02:40Z): the free head cut (A81) wrote T02 a 0.333 s trim --
T02 is a DIALOGUE shot, whose wav is anchored in the take's first frames -- and
the cut refused the whole master ('a head trim on a dialogue shot breaks
lip-sync: T02').  The trim was also measured on a render the cure round then
replaced.  The ladder never cuts a dialogue take's head, a re-render clears its
take's old head, and the edit drops (with a note) a dialogue head it is handed
rather than refusing the episode."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from studio import take_ladder

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_assemble_dialogue_heads", ROOT / "scripts" / "episode" / "assemble.py")
assemble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble)

LEAK = {"frames": 8, "seconds": 0.333, "covers": True}


def _home(tmp_path):
    home = tmp_path / "ep24"
    (home / "takes" / "r2v").mkdir(parents=True)
    plan = {"shots": [{"index": 2}, {"index": 3}],
            "lines": [{"shot": 2, "kind": "dialogue", "text": "Who are you?"},
                      {"shot": 3, "kind": "narration", "text": "He came closer."}]}
    (home / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    for i in (2, 3):
        (home / "takes" / "r2v" / f"T{i:02d}.dq.json").write_text(
            json.dumps({"measures": {"leak": LEAK}}), encoding="utf-8")
    return home


def test_the_ladder_cuts_a_narration_head_and_never_a_dialogue_head(tmp_path):
    home = _home(tmp_path)
    take_ladder.head_cuts(SimpleNamespace(home=home), {2: [], 3: []})
    heads = json.loads((home / "heads.json").read_text(encoding="utf-8"))
    assert heads == {"3": 0.333}


def test_a_rerender_clears_its_takes_old_head(tmp_path):
    home = _home(tmp_path)
    (home / "heads.json").write_text(json.dumps({"2": 0.333, "3": 0.333}), encoding="utf-8")
    take_ladder.clear_heads(home, [2])
    assert json.loads((home / "heads.json").read_text(encoding="utf-8")) == {"3": 0.333}


def test_the_edit_drops_a_dialogue_head_instead_of_refusing():
    placed = {"lines": [{"shot": 12, "kind": "dialogue"}, {"shot": 13, "kind": "narration"}]}
    assert assemble.spoken_heads_dropped({12: 0.5, 13: 0.67}, placed) == {13: 0.67}
