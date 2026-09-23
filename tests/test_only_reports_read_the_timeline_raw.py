"""Anything that acts on the GPU or the cut reads the timeline through
`episode_home.load_placed`, which refuses a stale one.

Guard for audit item 11: the freshness check existed but only plan_check
called it, while takes_r2v, assemble, qc and take_dq read placed.json raw.
The modules below may read it raw because they only REPORT, and a missing or
stale timeline is something they print, not something they act on.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = {"dossier.py", "story.py", "runcards.py", "plan_check.py", "episode_clock.py"}
WRITER = {"timeline.py"}


def test_no_actor_reads_placed_json_raw():
    hits = []
    for folder in (ROOT / "scripts" / "episode", ROOT / "studio"):
        for path in sorted(folder.glob("*.py")):
            if path.name in REPORTS | WRITER or path.name == "episode_home.py":
                continue
            if '"placed.json"' in path.read_text(encoding="utf-8"):
                hits.append(path.name)
    assert not hits, f"read placed.json through episode_home.load_placed: {hits}"
