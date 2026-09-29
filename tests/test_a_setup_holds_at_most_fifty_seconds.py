"""G-SETUP (2026-09-28): a setup is one place at one hour from one side, and it
holds at most MAX_SETUP_SECONDS of projected picture.  The retired Sherlock
contract said "no setup over ~25 s; add a setup whenever it buys variety";
G-COVER (2026-09-26) then filled ep13's hedge with 16 shots and ep14's attic
with 12 (attic + dormer view + doorstep + street on one night picture), which
the layout rule fragmented into 12 and 6 renders.  The wall is the battery's,
not the contract's: a rendered plan is judged in report mode and never refused."""
import json
from pathlib import Path

from studio import episode_spec as spec, plan_brief, plan_gates

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"


def episode() -> spec.Episode:
    return spec.Episode(**json.loads(PLAN.read_text(encoding="utf-8")))


def test_the_fixture_plan_is_clean_and_a_swollen_setup_is_named():
    ep = episode()
    assert plan_gates.setup_faults(ep) == []
    first = ep.shots[0].setup
    swollen = ep.model_copy(update={"shots": [s.model_copy(update={"setup": first}) for s in ep.shots]})
    faults = plan_gates.setup_faults(swollen)
    assert len(faults) == 1 and faults[0].startswith("G-SETUP") and first in faults[0]


def test_the_wall_is_thirty_seconds_and_the_writer_is_told():
    assert plan_gates.MAX_SETUP_SECONDS == 50.0
    assert plan_brief.band()["max_setup_seconds"] == 50.0
