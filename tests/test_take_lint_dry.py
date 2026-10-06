"""G-TAKELINT: episode_ref_official's REAL lint, run on take cards dry-built
from the PROJECTED timeline at plan time -- no boards read, nothing rendered,
$0.  Each fault is remapped from the take-internal [Shot k] to the plan's own
shot index and tagged with the data layer whose text carries the word: a plan
field, a refs.json physical, or an analysis/props card.  Step 06's own check
stays the wall; this gate moves its word families in front of the signature."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio.episode_spec import Line, Setup, Shot  # noqa: E402

spec = importlib.util.spec_from_file_location("takes_r2v", ROOT / "scripts" / "episode" / "takes_r2v.py")
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)

NARR = "Then we walked on together down the lane and the morning opened wide."


def book_of(tmp_path, physical="A lean man of thirty, dark hair.", from_refs=False) -> Path:
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    rows = [{"ref_id": "char-watson", "kind": "character", "entity_id": "watson",
             "name": "John Watson", "display": "Dr. Watson", "gender": "male",
             "physical": physical}]
    (book / "refs" / "refs.json").write_text(json.dumps({"refs": rows}), encoding="utf-8")
    if from_refs:
        (book / "refs" / "characters" / "watson").mkdir(parents=True)
        (book / "refs" / "characters" / "watson" / "sheet.png").write_bytes(b"")
    return book


def episode_of(shots, lines, setup=None):
    setups = {"lane": setup or Setup(described="A hillside lane in grey daylight from the LEFT.",
                                     cast=["watson"])}
    # where/light empty puts the house's own back (house_style.adopt's rule)
    ep = SimpleNamespace(shots=shots, lines=lines, setups=setups, aspect="1:1",
                         where="", light="", look="")
    ep.shot = lambda i: next(s for s in shots if s.index == i)
    return ep


def shot_of(index, **over):
    base = dict(index=index, section="friction", setup="lane", size="wide", faces=[],
                frame="A hillside lane under a grey sky.",
                motion="The camera pushes in toward the gate across the whole shot",
                at_rest="The gate sits at the LEFT of the frame.")
    base.update(over)
    return Shot(**base)


def rows_of(shots) -> list[dict]:
    return [{"index": s.index, "seconds": 6.0, "setup": s.setup, "cuts": []} for s in shots]


def test_an_unpaced_plan_climb_is_a_takelint_row_tagged_plan(tmp_path):
    """The climb rides in at_rest: a MOTION gait is auto-paced by the builder's
    own `guarantee`, while the detail sentences are unwritable by design ('the
    gait is never its business'), so this is the plan-layer L8 that really
    reaches step 06."""
    book = book_of(tmp_path)
    shots = [shot_of(14, at_rest="He climbs the lane toward the gate, his coat dark "
                                 "against the chalk. The gate sits at the LEFT of the frame.")]
    lines = [Line(index=0, kind="narration", speaker="watson", text=NARR, shot=14)]
    ep = episode_of(shots, lines)
    rows = tr.dry_faults(book, ep, 3, rows_of(shots))
    hit = [r for r in rows if "L8 NO PACE" in r]
    assert hit, rows
    assert "G-TAKELINT shot 14" in hit[0] and hit[0].endswith("[plan]")


def test_a_dirty_refs_physical_is_tagged_with_its_row(tmp_path):
    book = book_of(tmp_path, physical="A stout man, a revolver held at his lap.")
    shots = [shot_of(2, size="medium_close", faces=["watson"],
                     frame="Watson at the gate, his coat dark with rain.")]
    lines = [Line(index=0, kind="narration", speaker="watson", text=NARR, shot=2)]
    ep = episode_of(shots, lines)
    rows = tr.dry_faults(book, ep, 3, rows_of(shots))
    hit = [r for r in rows if "L2 STILLNESS" in r and "'held'" in r]
    assert hit, rows
    assert hit[0].endswith("[row watson]")


def test_a_dirty_props_card_is_tagged_with_its_card(tmp_path):
    book = book_of(tmp_path, from_refs=True)
    (book / "analysis" / "props").mkdir(parents=True)
    (book / "analysis" / "props" / "revolver.json").write_text(json.dumps(
        {"name": "service revolver", "aliases": ["revolver"],
         "profile": {"physical": "She holds her fire.", "scale": "a hand-long revolver"}}),
        encoding="utf-8")
    (book / "refs" / "props" / "revolver").mkdir(parents=True)
    (book / "refs" / "props" / "revolver" / "sheet.png").write_bytes(b"")
    shots = [shot_of(5, frame="The service revolver on the table, grey light across it.")]
    lines = [Line(index=0, kind="narration", speaker="watson", text=NARR, shot=5)]
    ep = episode_of(shots, lines, Setup(described="A hillside lane in grey daylight from the LEFT.",
                                        cast=["watson"], props=["revolver"]))
    rows = tr.dry_faults(book, ep, 3, rows_of(shots))
    hit = [r for r in rows if "L2 STILLNESS" in r and "'holds'" in r]
    assert hit, rows
    assert hit[0].endswith("[card revolver]")


def test_parse_faults_round_trips_a_canned_message_with_an_inner_semicolon():
    msg = ("the prompt fails the lint (2 faults): L2 STILLNESS: ['held']; "
           "L8 NO PACE [Shot 1]: a walk; climb or ride with no pace named")
    got = tr.parse_faults(ValueError(msg))
    assert got == ["L2 STILLNESS: ['held']",
                   "L8 NO PACE [Shot 1]: a walk; climb or ride with no pace named"]


def test_parse_faults_prefers_the_structured_list_on_the_exception():
    err = ValueError("the prompt fails the lint (1 faults): L3 SLOW: reworded entirely")
    err.faults = ["L3 SLOW: the structured copy"]
    assert tr.parse_faults(err) == ["L3 SLOW: the structured copy"]


def test_shot_two_of_a_two_shot_take_maps_to_the_plans_second_index():
    index, said = tr.remap_shots("L8 NO PACE [Shot 2]: a walk with no pace named", [4, 5])
    assert index == 5 and "[shot 5]" in said
