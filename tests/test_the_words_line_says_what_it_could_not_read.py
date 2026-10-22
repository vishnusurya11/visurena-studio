"""A2's words line says what it could not read (wave 0 review, majors 1-2 and finding 8).

The wave 0 line printed `words: 0 of 28 rendered from older words; 0 fail a current HARD rule` when
step 06 had written no prompts.json and when the plan had no setups: the same false clean report A2
was built to remove.  Now an input it did not have is "not measured", the denominators count only
what was compared, and the HARD count names the rules a recorded prompt cannot feed (a floor, not a
total).  QC also says when a voice line shipped with its similarity floor dropped to 0.0 (ruling T18:
Jekyll ep01 l11 passed at similarity 0.325 against a floor set to 0.0, silently).
Fixtures: tests/fixtures/craft (Jekyll ep01, copied by name).  No render, no network, no spend."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import qc
from studio import take_inputs as ti

BOOK = Path(__file__).parent / "fixtures" / "craft"
TAKES = BOOK / "episodes" / "ep01" / "takes" / "r2v"
LINES = BOOK / "episodes" / "ep01" / "audio" / "lines" / "lines.json"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def records() -> list[dict]:
    return read(TAKES / "shots.json")


def night() -> dict[int, bool]:
    plan = read(BOOK / "episodes" / "ep01" / "plan.json")
    return {int(r["index"]): ti.night_of(plan["setups"][r["setup"]]) for r in records()}


def audited(built: dict | None) -> dict[int, ti.Inputs]:
    return {int(r["index"]): ti.check(BOOK / r["rel_path"], [], None if built is None else built.get(int(r["index"])))
            for r in records()}


def test_no_prompts_json_is_not_measured_never_zero():
    assert ti.built_prompts(BOOK) is None
    block = ti.words(audited(None), records(), BOOK, night())
    assert block["line"].startswith("words: older words not measured (no prompts.json from step 06);")
    assert block["compared"] == 0


def test_a_take_with_no_recorded_prompt_is_not_counted_as_compared(tmp_path):
    bare = ti.check(tmp_path / "T00.mp4", [], built="the girl runs")
    assert bare.compared is False and bare.reworded is False
    assert ti.check(TAKES / "T01.mp4", [], built="other words").compared is True


def test_the_ep01_line_counts_what_it_compared_and_names_the_rules_it_could_not_feed():
    block = ti.words(audited(ti.built_prompts(TAKES)), records(), BOOK, night())
    assert block["line"].startswith("words: 27 of 28 rendered from older words; 9 of 28 fail a current HARD rule")
    assert "at least" in block["line"] and "L16" in block["line"] and "L7" in block["line"]
    assert block["line"].endswith("(advisory under freeze)")


def test_with_no_setups_the_night_rule_is_named_unread():
    block = ti.words(audited(ti.built_prompts(TAKES)), records(), BOOK, {})
    assert "L28 unread on 28 takes" in block["line"]


def test_the_relint_reads_the_records_own_fps_and_refs():
    rec = records()[6]
    facts = ti.record_facts(rec)
    assert facts["fps"] == rec.get("fps", 24) and facts["refs"] == len(rec.get("refs") or [])


def test_a_words_block_that_breaks_says_not_measured_and_never_parks():
    i = SimpleNamespace(take_dir=TAKES, records=[{"index": 0}], book=BOOK, episode=None)
    out = qc.words_rows(i, {"inputs": {"ok": True}}, audited={0: ti.Inputs(current=True)})
    assert out["inputs"]["words"]["line"].startswith("words: not measured (")
    assert qc.inputs_ok(out) is True


# ---- the voice floor dropped to 0.0 (T18's defect part) --------------------------------------------

def test_qc_names_every_line_that_shipped_with_its_similarity_floor_at_zero():
    block = qc.voice_floor(read(LINES))
    assert block["dropped"] == {"l06": 0.651, "l11": 0.325, "l20": 0.783}
    assert block["line"] == ("voice floor: 3 of 22 lines shipped with the similarity floor at 0.0 "
                             "(l06 0.651, l11 0.325, l20 0.783)")


def test_no_lines_json_is_not_measured():
    assert qc.voice_floor(None)["line"] == "voice floor: not measured (no lines.json)"


def test_the_voice_floor_rides_beside_the_inputs_and_never_moves_the_verdict(tmp_path):
    i = SimpleNamespace(book=BOOK, number=1)
    report = qc.voice_floor_rows(i, {"inputs": {"ok": True}})
    assert report["inputs"]["voice_floor"]["line"].startswith("voice floor: 3 of 22")
    assert qc.inputs_ok(report) is True
