"""split_setup never leaves a one-shot setup (Jekyll Kawajiri ep01: walk_on_day_2 held shot 26
alone, a whole second place master and anchor for 2.7 s of picture).  A lone tail shot cannot merge
back (it spilled because it did not fit the cap), so the neighbour hands it a shot: every part of a split has two shots or more."""
import copy
import json
from collections import Counter
from pathlib import Path

from studio import plan_cures as pc

PLAN = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02" / "plan.json"
RATE = 2.45


def walk_on(part_secs: float) -> dict:
    """ep01 with shot 26 back in walk_on_day and the day-walk codas raised until the first
    eight shots hold `part_secs` of picture (the draft that spilled shot 26 alone)."""
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    doc["setups"].pop("walk_on_day_2")
    for s in doc["shots"]:
        s["setup"] = "walk_on_day" if s["setup"] == "walk_on_day_2" else s["setup"]
    own = [s for s in doc["shots"] if s["setup"] == "walk_on_day" and s["index"] != 26]
    for s in own * 4:
        if sum(pc._shot_secs(doc, RATE)[o["index"]] for o in own) >= part_secs:
            break
        s["coda_s"] = min(4.0, round(s["coda_s"] + 0.5, 2))
    return doc


def sizes(doc: dict) -> Counter:
    return Counter(s["setup"] for s in doc["shots"])


def test_the_draft_would_have_split_a_lone_shot_without_the_rule():
    doc = walk_on(48.4)
    shots = sum(pc._shot_secs(doc, RATE)[s["index"]] for s in doc["shots"] if s["setup"] == "walk_on_day")
    assert shots > pc.SETUP_CAP_S


def test_a_split_leaves_no_one_shot_part():
    out = pc.split_setup(walk_on(48.4), RATE)
    parts = {k: n for k, n in sizes(out).items() if k.startswith("walk_on_day")}
    assert len(parts) == 2 and min(parts.values()) >= 2


def test_every_part_stays_inside_the_cap():
    out = pc.split_setup(walk_on(48.4), RATE)
    secs = pc._shot_secs(out, RATE)
    per = Counter()
    for s in out["shots"]:
        per[s["setup"]] += secs[s["index"]]
    assert all(v <= pc.SETUP_CAP_S + 1e-6 for k, v in per.items() if k.startswith("walk_on_day"))


def test_shots_keep_their_story_order_across_the_parts():
    out = pc.split_setup(walk_on(48.4), RATE)
    names = [s["setup"] for s in out["shots"] if s["setup"].startswith("walk_on_day")]
    assert names == sorted(names)                       # walk_on_day.. then walk_on_day_2..


def test_a_setup_inside_its_cap_is_not_split_at_all():
    doc = walk_on(30.0)
    out = pc.split_setup(copy.deepcopy(doc), RATE)
    assert "walk_on_day_2" not in out["setups"] and out == doc


def test_a_setup_of_one_shot_the_writer_made_is_left_alone():
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    out = pc.split_setup(copy.deepcopy(doc), RATE)
    assert sizes(out) == sizes(doc)                      # walk_on_day_2 was never split by the cap
