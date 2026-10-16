"""SHEET-ROW on the real reader for every row rewritten to its sheet (owner 2026-10-15: the sheet is
truth): Utterson, Enfield, Hyde, the girl, Lanyon, the constable (new sheet). Writes sheet_row_iter5.jsonl."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import look_back, look_timeline  # noqa: E402
from studio.judges import sheet_row  # noqa: E402

BOOK = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
WHO = ("gabriel_john_utterson", "richard_enfield", "edward_hyde", "child_of_hyde_incident",
       "reginald_lanyon", "carew_policeman")


def main() -> None:
    table, rows = look_timeline.load(BOOK), []
    for who in WHO:
        base = table.characters[who].looks[table.characters[who].base]
        v = sheet_row.judge(BOOK / f"refs/characters/{who}/sheet.png", base.layers, base.markers,
                            look_back.vlm_reader, who)
        rows.append({"case": who, "passed": v.passed, "faults": [f.model_dump() for f in v.faults]})
        print(json.dumps(rows[-1]), flush=True)
    (Path(__file__).parent / "sheet_row_iter5.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n",
                                                                 encoding="utf-8")


if __name__ == "__main__":
    main()
