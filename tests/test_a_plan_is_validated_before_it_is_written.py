"""A plan script refuses a plan the contract refuses, before anything is written.

MEASURED 2026-09-23 on ep09: "the other man nods slowly" broke the owner's
no-slow rule. The plan script wrote plan.json anyway -- all 16 plan scripts
wrote `json.dumps(doc)` with no validation -- and the fault surfaced as a
pydantic traceback inside grids.py, one stage later, with the old plan gone.
"""
import json
from pathlib import Path

import pytest

from studio import episode_home

ROOT = Path(__file__).resolve().parents[1]
WOTW = "20260827135508_the-war-of-the-worlds"


@pytest.fixture(scope="module")
def doc():
    return json.loads(episode_home.plan_path(episode_home.book_dir(WOTW), 9).read_text(encoding="utf-8"))


def test_a_valid_plan_is_written_byte_for_byte(tmp_path, doc):
    out = tmp_path / "plan.json"
    episode_home.write_plan(out, doc)
    assert out.read_text(encoding="utf-8") == json.dumps(doc, indent=1, ensure_ascii=False)


def test_a_refused_plan_leaves_the_old_one_in_place(tmp_path, doc):
    out = tmp_path / "plan.json"
    out.write_text("the previous plan", encoding="utf-8")
    bad = {**doc, "shots": [{**doc["shots"][0], "motion": doc["shots"][0]["motion"] + "; he nods slowly"}]
           + doc["shots"][1:]}
    with pytest.raises(SystemExit, match="slow"):
        episode_home.write_plan(out, bad)
    assert out.read_text(encoding="utf-8") == "the previous plan"


def test_no_plan_script_writes_its_plan_around_the_contract():
    bypass = [p.name for p in (ROOT / "scripts" / "episode" / "plans").glob("*.py")
              if "OUT.write_text(json.dumps(doc" in p.read_text(encoding="utf-8")]
    assert not bypass, f"write plan.json with episode_home.write_plan: {bypass}"
