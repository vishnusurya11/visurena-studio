"""Candidates for the girl's base sheet (child_of_hyde_incident) on the book's own drawer.

The recipe is refs/look.json's, with the girl's entity tags/negative taken from
`entity.json` beside this file (the words under test); every other entity and the
lead, negative and framing are the book's.  Usage: draw_candidates.py <tag> <seed>...
writes cand_<tag>_s<seed>.png and appends the exact words to cands.jsonl.
"""
import copy
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from studio import book_look  # noqa: E402
from studio.comfy import run  # noqa: E402

BOOK = Path("library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde")
WHO = "child_of_hyde_incident"
HERE = Path(__file__).parent


def recipe(entity: dict) -> dict:
    out = copy.deepcopy(book_look.refs_recipe(BOOK))
    out["entities"][WHO] = entity
    return out


def main(tag: str, seeds: list[int]) -> None:
    entity = json.loads((HERE / "entity.json").read_text(encoding="utf-8"))[tag]
    rec = recipe(entity)
    for seed in seeds:
        wf, values = book_look.drawn_t2i(rec, "", width=1536, height=1024, seed=seed,
                                         prefix="girl/cand", kind="characters", entity=WHO)
        made = run(wf, values)[0]
        name = f"cand_{tag}_s{seed}.png"
        shutil.copyfile(made, HERE / name)
        with (HERE / "cands.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"file": name, "seed": seed, "workflow": wf, "prompt": values["prompt"],
                                 "negative_prompt": values["negative_prompt"]}, ensure_ascii=False) + "\n")
        print(name, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], [int(s) for s in sys.argv[2:]])
