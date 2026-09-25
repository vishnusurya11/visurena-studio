"""The bench report is appended to docs/calibration/<judge>.md and the
baseline written to docs/calibration/bench/<judge>.json.

One calibration doc per judge is the repo's convention: the thresholds and
the set they were fitted on, now with a `## Bench <date>` section per run.
The baseline is the ratchet's memory: which owner catches this judge made,
by codex, sha8 and path -- opaque, never the words.
"""
import json
from pathlib import Path

from scripts.calibration import bench
from studio import judge_bench as jb

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def refuses_everything(row):
    return {"refused": True, "classes": ["unknown"], "values": {}}


def test_the_report_and_the_baseline_land_in_the_docs_folder(tmp_path):
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), refuses_everything)
    doc, base = bench.write(tmp_path, "fixture", outcomes, "abcdef01", "git:0000000")
    assert doc == tmp_path / "fixture.md" and base == tmp_path / "bench" / "fixture.json"
    assert "## Bench " in doc.read_text(encoding="utf-8")
    saved = json.loads(base.read_text(encoding="utf-8"))
    assert saved["judge"] == "fixture" and saved["version"] == "abcdef01"
    assert {c["path"] for c in saved["caught"]} == {"episodes/ep01/takes/r2v/T04.mp4",
                                                     "episodes/ep01/takes/r2v/T05.mp4"}


def test_a_second_run_appends_the_doc_and_replaces_the_baseline(tmp_path):
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), refuses_everything)
    (tmp_path / "fixture.md").write_text("# fixture calibration\n\nthe walls.\n", encoding="utf-8")
    bench.write(tmp_path, "fixture", outcomes, "abcdef01", "git:0000000")
    bench.write(tmp_path, "fixture", outcomes, "abcdef02", "git:0000001")
    text = (tmp_path / "fixture.md").read_text(encoding="utf-8")
    assert text.startswith("# fixture calibration") and text.count("## Bench ") == 2
    assert json.loads((tmp_path / "bench" / "fixture.json").read_text(encoding="utf-8"))["version"] == "abcdef02"
