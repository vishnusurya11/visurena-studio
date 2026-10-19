"""E1 (retro 2026-10-19, P06): the eval set a content detector is scored on.

The pre-fix pixels of ep01's two shape faults (shot 2 fading into fog, shot 27
a floating hand) lived only in a git-ignored `superseded/` folder, so no fault
could be replayed.  The manifest names every copied picture and carries the
label protocol; a name with no file, or a label outside the vocabulary, is a
broken eval.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent / "fixtures" / "dq_eval" / "kawajiri_ep01"
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
SHAPE = {"ok", "fading", "floating", "cannot_tell"}


def test_every_panel_and_take_frame_the_manifest_names_exists():
    named = [p["file"] for p in MANIFEST["panels"]]
    named += [f for t in MANIFEST["takes"] for f in t["frames"]]
    assert named and [n for n in named if not (ROOT / n).is_file()] == []


def test_the_labels_are_agent_labels_under_a_stated_protocol():
    assert MANIFEST["label_source"] == "agent"
    assert "owner may veto" in MANIFEST["label_protocol"]


def test_the_two_shape_faults_and_twenty_clean_panels_are_there():
    panels = MANIFEST["panels"]
    assert {p["shot"] for p in panels if p["body"] == "fading"} == {2}
    assert {p["shot"] for p in panels if p["limb_attached"] == "floating"} == {27}
    assert sum("_clean" in p["file"] for p in panels) == 20


def test_shape_labels_stay_in_the_closed_vocabulary():
    for p in MANIFEST["panels"]:
        assert p["body"] in SHAPE and p["limb_attached"] in SHAPE


def test_the_crowd_takes_name_a_plan_shot_the_manifest_carries():
    shots = {s["index"] for s in MANIFEST["plan"]["shots"]}
    leaks = [t for t in MANIFEST["takes"] if t["crowd_leak"]]
    assert len(leaks) == 14 and all(t["shot"] in shots for t in MANIFEST["takes"])
