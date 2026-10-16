"""Owner decision 2026-10-15: the SHEET IS TRUTH. Rewrite the Jekyll rows to the drawn sheets.

Edits, in the book's own sources (never the sheets): the look table (refs/looks.json body
and base layers), the head words (analysis/heads.json), the dossier physical
(analysis/characters/<who>.json profile.physical) and, for Utterson and Enfield, the
drawer tags in refs/look.json. Then `looks_table.py --remark` and `cast_rows.py` rebind.

Run once:  uv run python docs/audit/2026-10-15_jekyll_ep01_ref_audit/iter5/rows_to_sheets.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BOOK = ROOT / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"

NEW = {
    "gabriel_john_utterson": {
        "body": "A lean, long, bony, dry man of about forty, narrow-chested, with a long, gaunt, rugged, unsmiling face.",
        "look": "base",
        "layers": {"headwear": "black bowler hat with a pale grey band",
                   "hair": "lank grey hair, white at the sides, falling to his collar",
                   "face": "clean-shaven, long, gaunt, rugged, unsmiling face",
                   "top": "long black double-breasted overcoat with six white buttons, white shirt, black tie"},
        "head": "A lean, long, bony, dry man of about forty, narrow-chested, with a long, gaunt, rugged face that "
                "is never lighted by a smile. Lank grey hair, white at the sides, falling to his collar; clean-shaven; "
                "a black bowler hat with a pale grey band; a long black double-breasted overcoat with six white buttons.",
        "physical": "A lean, long, bony, dry man of about forty, narrow-chested, with a long, gaunt, rugged face that is "
                    "unsmiling. Lank grey hair, white at the sides, falling to his collar; clean-shaven; a black bowler "
                    "hat with a pale grey band; a long black double-breasted overcoat with six white buttons, a white "
                    "shirt and a black tie.",
        "apart_from": {"henry_jekyll": "owner ruling 2026-10-15 (the sheet is truth: grey hair): both grey and "
                       "clean-shaven, but Utterson is lean and gaunt under a black bowler in a long black "
                       "double-breasted overcoat with white buttons; Jekyll large, broad and smooth-faced under a "
                       "tall black silk top hat"},
    },
    "richard_enfield": {
        "body": "A compact, upright, broad-shouldered gentleman of about forty, a well-dressed man about town with a "
                "heavy jaw and a lined face, who carries a black walking cane.",
        "look": "frock_coat_topper",
        "layers": {"headwear": "light-brown top hat with a brown band",
                   "hair": "receding brown hair",
                   "face": "clean-shaven",
                   "top": "mid-grey long frock coat with black lapels, cream waistcoat, navy bow tie, black gloves, "
                          "black walking cane"},
        "head": "A compact, upright, broad-shouldered gentleman of about forty, a well-dressed man about town with a "
                "heavy jaw and a lined face. Receding brown hair; clean-shaven; a light-brown top hat with a brown "
                "band; a mid-grey long frock coat over a cream waistcoat, black gloves and a black walking cane.",
        "physical": "A compact, upright, broad-shouldered gentleman of about forty, a well-dressed man about town with "
                    "a heavy jaw and a lined face. Receding brown hair; clean-shaven; a light-brown top hat with a "
                    "brown band; a mid-grey long frock coat with black lapels, a cream waistcoat, a navy bow tie, "
                    "black gloves and a black walking cane.",
    },
    "edward_hyde": {
        "body": "A small, slight, sinister young man of about twenty-five, adult in build but a head shorter than "
                "other men, narrow-shouldered and pale, his thin lips curled in a wide, cold grin, with lean, "
                "corded, knuckly pale hands.",
        "look": "base",
        "layers": {"top": "knee-length black double-breasted coat, white shirt"},
        "head": "A small, slight, sinister young man of about twenty-five, adult in build but a head shorter than "
                "other men, narrow-shouldered and pale, his thin lips curled in a wide, cold grin, with lean, corded, "
                "knuckly pale hands. Coarse, unkempt short black hair; clean-shaven, pale smooth cheeks; a soft black "
                "felt wideawake hat with a low flat crown and a wide floppy brim.",
        "physical": "A small, slight, sinister young man of about twenty-five, adult in build but a head shorter than "
                    "other men, narrow-shouldered and pale, his thin lips curled in a wide, cold grin, and lean, "
                    "corded, knuckly pale hands. Coarse, unkempt short black hair; clean-shaven, pale smooth cheeks; "
                    "a soft black felt wideawake hat with a low flat crown and a wide floppy brim; a knee-length "
                    "black double-breasted coat over a white shirt.",
    },
    "reginald_lanyon": {
        "look": "rosy_dapper",
        "layers": {"headwear": "black silk top hat with a white band",
                   "top": "dapper navy-blue frock coat, white waistcoat, black cravat"},
        "head_replace": ("a grey silk top hat", "a black silk top hat with a white band"),
    },
    "carew_policeman": {
        "look": "base_uniform",
        "layers": {"face": "thick sandy-red moustache; lined face, bushy eyebrows"},
        "head_replace": ("a short red beard", "a thick sandy-red moustache"),
    },
}

TAGS = {
    "gabriel_john_utterson": (("(dusty sandy-grey hair:1.3)", "(grey hair:1.3), white at the sides"),
                              ("black frock coat, dark waistcoat, white shirt, black cravat, (plain black frock coat:1.3)",
                               "(long black double-breasted overcoat:1.3), six white buttons, white shirt, black tie")),
    "richard_enfield": (("fashionable dark frock coat, waistcoat, cravat", "(mid-grey long frock coat:1.3), black lapels, "
                         "(cream waistcoat:1.2), navy bow tie, (black gloves:1.2), black walking cane"),
                        ("(dark grey frock coat:1.3), brown waistcoat", "")),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")


def looks_table() -> None:
    path = BOOK / "refs" / "looks.json"
    doc = load(path)
    for who, new in NEW.items():
        entry = doc["characters"][who]
        if "body" in new:
            entry["body"] = new["body"]
        entry["looks"][new["look"]]["layers"].update(new["layers"])
    save(path, doc)


def heads() -> None:
    path = BOOK / "analysis" / "heads.json"
    doc = load(path)
    for who, new in NEW.items():
        if "head" in new:
            doc[who]["words"] = new["head"]
        if "head_replace" in new:
            old, now = new["head_replace"]
            doc[who]["words"] = doc[who]["words"].replace(old, now)
        if "apart_from" in new:
            doc[who].setdefault("apart_from", {}).update(new["apart_from"])
    save(path, doc)


def dossiers() -> None:
    for who, new in NEW.items():
        if "physical" not in new:
            continue
        path = BOOK / "analysis" / "characters" / f"{who}.json"
        doc = load(path)
        doc["profile"]["physical"] = new["physical"]
        save(path, doc)


def drawer_tags() -> None:
    path = BOOK / "refs" / "look.json"
    doc = load(path)
    for who, swaps in TAGS.items():
        entity = doc["refs"]["entities"][who]
        for old, now in swaps:
            assert old in entity["tags"], (who, old)
            entity["tags"] = entity["tags"].replace(old, now).replace(", ,", ",")
    save(path, doc)


if __name__ == "__main__":
    looks_table()
    heads()
    dossiers()
    drawer_tags()
    print("rows rewritten to the sheets; now: looks_table.py --remark, then cast_rows.py")
