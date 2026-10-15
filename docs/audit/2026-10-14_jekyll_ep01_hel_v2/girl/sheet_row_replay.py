"""SHEET-ROW on the real reader: the superseded lace sheet against its old row (must refuse),
the redrawn sheet against its aligned row (must pass), and every other bound Jekyll base
sheet against its own row (the false-refusal count).  Writes sheet_row_replay.jsonl."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import look_back, look_timeline  # noqa: E402
from studio.continuity_spec import Layers  # noqa: E402
from studio.judges import sheet_row  # noqa: E402

BOOK = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
WHO = "child_of_hyde_incident"
OLD = Layers(headwear="small knitted woollen bonnet", hair="fair hair in two plaits", face="smooth-cheeked",
             top="plain grey pinafore dress and black boots")
HERE = Path(__file__).parent


def one(name: str, picture: Path, layers, markers) -> dict:
    v = sheet_row.judge(picture, layers, markers, look_back.vlm_reader, name)
    row = {"case": name, "passed": v.passed, "faults": [f.model_dump() for f in v.faults]}
    print(json.dumps(row), flush=True)
    return row


def main() -> None:
    table = look_timeline.load(BOOK)
    rows = [one("girl_old_lace_vs_old_row", BOOK / f"refs/characters/{WHO}/superseded/sheet_2026-10-14_hellsing_v2_lace.png",
                OLD, table.characters[WHO].looks["base"].markers)]
    bound = {r["entity_id"] for r in json.loads((BOOK / "refs/refs.json").read_text(encoding="utf-8"))["refs"]}
    for who, card in table.characters.items():
        sheet = BOOK / f"refs/characters/{who}/sheet.png"
        if sheet.exists() and who in bound:
            base = card.looks[card.base]
            rows.append(one(who, sheet, base.layers, base.markers))
    (HERE / "sheet_row_replay.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
