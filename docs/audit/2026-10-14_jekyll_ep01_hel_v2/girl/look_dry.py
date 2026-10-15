"""The LOOK judge over the girl's new sheet, read in full, WITHOUT the ladder: a dry read
before step 04 signs (a ladder redraw would replace the owner's pick)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import sheet_ladder  # noqa: E402
from studio.judges import look  # noqa: E402

BOOK = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
PATH = "refs/characters/child_of_hyde_incident/sheet.png"
rows = sheet_ladder.pack_rows(BOOK)
v = look.judge(BOOK, sheet_ladder.latest(rows, [PATH]))
print(json.dumps({"passed": v.passed, "faults": [f.model_dump() for f in v.faults]}, indent=1))
