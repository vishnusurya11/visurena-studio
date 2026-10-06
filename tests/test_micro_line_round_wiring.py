"""plan_repair's micro-line round: residual G-HOLE rows and unsplit ONE PER
TAKE pairs route to fill_holes, which splices at most `max_inserts` canned
micro-lines through the contract and writes the plan back.  The `_fill` seam
is the only caller -- zero network, zero spend.  The G-RATE guard refuses an
insertion that would push the measured-rate projection past MAX_SECONDS."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from studio import episode_home
from studio import plan_cures as pc
from studio.episode_spec import MAX_SECONDS, Episode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
spec = importlib.util.spec_from_file_location("pr_micro", ROOT / "scripts" / "episode" / "plan_repair.py")
pr = importlib.util.module_from_spec(spec)
sys.modules["pr_micro"] = pr
spec.loader.exec_module(pr)

from test_hole_gate_measures_like_step05 import episode_with_wordless_run  # noqa: E402

MICRO = "I heard the wind drag its claws along the shutters"


def book_with_plan(tmp_path) -> Path:
    book = tmp_path / "book"
    home = episode_home.home(book, 1)
    home.mkdir(parents=True)
    (home / "plan.json").write_text(
        json.dumps(episode_with_wordless_run().model_dump()), encoding="utf-8")
    return book


def test_fill_holes_splices_a_canned_line_through_the_contract(tmp_path):
    book = book_with_plan(tmp_path)
    before = episode_home.read_json(episode_home.home(book, 1) / "plan.json")
    assert pr.fill_holes(book, 1, _fill=lambda ground: MICRO) is True
    doc = episode_home.read_json(episode_home.home(book, 1) / "plan.json")
    assert len(doc["lines"]) == len(before["lines"]) + 1
    assert [l["index"] for l in doc["lines"]] == list(range(len(doc["lines"])))
    new = next(l for l in doc["lines"] if l["text"] == MICRO)
    assert new["kind"] == "narration" and new["speaker"] == "b"
    Episode.model_validate(doc)


def test_a_declined_fill_leaves_the_plan_alone(tmp_path):
    book = book_with_plan(tmp_path)
    before = (episode_home.home(book, 1) / "plan.json").read_text(encoding="utf-8")
    assert pr.fill_holes(book, 1, _fill=lambda ground: None) is False
    assert (episode_home.home(book, 1) / "plan.json").read_text(encoding="utf-8") == before


def test_the_rate_guard_blocks_an_over_budget_insertion():
    fat = {"shots": [{"index": 0, "beat_s": 0.0, "coda_s": 0.0}],
           "lines": [{"shot": 0, "text": " ".join(["w"] * 600)}]}
    assert pr.rate_blocked(fat, 3.0) is True
    lean = {"shots": [{"index": 0, "beat_s": 0.0, "coda_s": 0.0}],
            "lines": [{"shot": 0, "text": "a few words"}]}
    assert pr.rate_blocked(lean, 3.0) is False
    assert MAX_SECONDS < 600 / 3.0


def test_micro_targets_names_the_hole_shot_then_the_unsplit_pairs_shot():
    doc = {"shots": [{"index": 0, "setup": "a", "beat_s": 0.0, "coda_s": 1.0},
                     {"index": 1, "setup": "a", "beat_s": 0.0, "coda_s": 1.6},
                     {"index": 2, "setup": "a", "beat_s": 0.0, "coda_s": 1.6},
                     {"index": 3, "setup": "b", "beat_s": 0.0, "coda_s": 0.2}],
           "lines": [{"shot": 0, "text": "just four words here"},
                     {"shot": 3, "text": "the button line lands here"}]}
    targets = pr.micro_targets(doc, 2.5)
    assert targets and targets[0][0] == 2          # the hole's most even split
    assert 1 in [t[0] for t in targets]            # the unsplit pair's line-light shot


def test_grounding_reads_the_lines_either_side_of_the_hole(tmp_path):
    book = book_with_plan(tmp_path)
    doc = episode_home.read_json(episode_home.home(book, 1) / "plan.json")
    targets = pr.micro_targets(doc, 3.0)
    shot_index, hole = targets[0]
    ground = pr.grounding(book, 1, doc, shot_index, hole, 3.0)
    assert ground["shot"]["index"] == shot_index
    assert ground["gap_s"] > 5.5
    assert ground["prev_text"] and ground["next_text"]
    assert ground["source_paragraph"] == ""        # no chapters on the test book
