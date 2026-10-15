"""Commit the girl's picked sheet (cand_b_s505) through the refs path, and make every
word that describes her say what the picture shows (owner, 2026-10-15: "the girl is not
accurate in some shots").

1. The old sheet and its one-figure crop go to superseded/ as *_2026-10-14_hellsing_v2_lace.
2. look.json's drawer tags for her become the picked words (old look.json kept in refs/superseded).
3. The words: the dossier head, analysis/heads.json and the look table (refs/looks.json) say
   the drawn sheet -- a small soft grey woollen bonnet, fair plaits, blue eyes, a plain grey
   pinafore over a dark-red long-sleeved blouse, black boots (the book is silent: the words
   follow the picture).
4. The sheet is drawn by sheet_ladder.redraw on the picked seed and logged to refs/pack.jsonl;
   the drawn bytes are compared with the candidate.
refs.json is re-bound afterwards by step 01, never by hand.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import sheet_ladder  # noqa: E402
from studio.comfy import run  # noqa: E402

BOOK = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
WHO = "child_of_hyde_incident"
HERE = Path(__file__).parent
PICK, SEED, TAG = "cand_b_s505.png", 505, "b"
STAMP = "2026-10-14_hellsing_v2_lace"
HEAD = {"headwear": "small soft grey woollen bonnet", "hair": "fair hair in two plaits",
        "face": "smooth-cheeked, blue eyes",
        "top": "plain grey pinafore dress over a dark-red long-sleeved blouse, and black boots"}
BODY = ("A small girl of about nine, thin and quick, in a plain grey pinafore dress over a "
        "dark-red long-sleeved blouse, and black boots.")
WORDS = f"{BODY} Fair hair in two plaits; smooth-cheeked; blue eyes; a small soft grey woollen bonnet."


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def save(p: Path, d: dict, indent: int = 1) -> None:
    p.write_text(json.dumps(d, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def keep_aside(p: Path, name: str) -> None:
    aside = p.parent / "superseded" / name
    if not aside.exists():
        shutil.copyfile(p, aside)


def supersede_sheets() -> None:
    d = BOOK / "refs/characters" / WHO
    for stem in ("sheet", "sheet_front"):
        keep_aside(d / f"{stem}.png", f"{stem}_{STAMP}.png")


def drawer_tags() -> None:
    p = BOOK / "refs/look.json"
    keep_aside(p, "look_2026-10-15_before_girl_sheet.json")
    look = load(p)
    look["refs"]["entities"][WHO] = load(HERE / "entity.json")[TAG]
    save(p, look)


def words() -> None:
    dossier = BOOK / "analysis/characters" / f"{WHO}.json"
    card = load(dossier)
    card["profile"]["physical"] = WORDS
    card["profile"]["head"]["words"] = WORDS
    save(dossier, card, 2)
    heads = BOOK / "analysis/heads.json"
    h = load(heads)
    h[WHO]["words"] = WORDS
    save(heads, h, 2)
    table = BOOK / "refs/looks.json"
    keep_aside(table, "looks_2026-10-15_before_girl_sheet.json")
    t = load(table)
    t["characters"][WHO]["body"] = BODY
    t["characters"][WHO]["looks"]["base"]["layers"].update(HEAD)
    save(table, t)


def draw() -> None:
    job = sheet_ladder.jobs_of(BOOK)[f"refs/characters/{WHO}/sheet.png"]
    out = sheet_ladder.redraw(BOOK, job, job.prompt, SEED, run)
    same = hashlib.sha256(out.read_bytes()).hexdigest() == hashlib.sha256((HERE / PICK).read_bytes()).hexdigest()
    sheet_ladder.append_row(BOOK, {"path": f"refs/characters/{WHO}/sheet.png",
                                   "workflow": sheet_ladder.workflow_of(BOOK, job), "prompt": job.prompt,
                                   "seed": SEED, "seconds": 15.1, "rung": "owner_girl_redraw",
                                   "why": "2026-10-15 owner: the girl is not accurate in some shots; "
                                          "one base sheet matching her words (pick cand_b_s505)"})
    print("drawn", out, "identical to pick:", same)


if __name__ == "__main__":
    supersede_sheets()
    drawer_tags()
    words()
    draw()
