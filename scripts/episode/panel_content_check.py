#!/usr/bin/env python
"""The content gate on panels: a vision model LISTS what is in each panel, and
code judges the list against the plan. Local, $0.

    uv run python scripts/episode/panel_content_check.py <book_id> <episode>

Writes episodes/epNN/storyboard/panel_content.json, which takes_r2v refuses to
render without. Exits 1 on any failed panel, any panel the reader could not
read, any planned panel missing, or nothing to judge.

Promoted from a session driver (audit 2026-09-22, items 2, 4, 7). On the way in:
- An UNREAD panel is a failure. The driver printed it and then counted
  `seen - bad` as clean, so an unread panel passed.
- Who may be in a panel is the plan's: the setup's crowd and the shot's
  `extras`, not people-words found in the prose.
- Which places are flat is on each location row (`landform`); the banned
  subjects are the book's (analysis/dq_rules.json). The two runners each kept
  their own lists and had drifted apart.
- The hour is the setup's (`panel_dq.at_night`).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_refs, comfy, episode_home, panel_content as pc, panel_dq
from studio.episode_home import episode_arg

WORKFLOW = "image_qwen3vl_caption"
TOKENS = 1024
"""A crowded panel names a dozen subjects; the default budget cut the answer
off mid-JSON, which `parse` rightly refused to read."""


def read(path: Path, seed: int = 11) -> pc.Seen:
    """One panel through the vision model, into the closed vocabulary. Raises
    `Unreadable` rather than ever returning a guessed answer."""
    said = comfy.cached_text(WORKFLOW, {"image_1": comfy.stage_image(path), "prompt": pc.ASK,
                                     "seed": seed, "max_new_tokens": TOKENS}, readable=pc.readable)
    return pc.parse(said if isinstance(said, str) else str(said))


TWIN_TOKENS = 256
"""The twin read is three short keys; a tight budget keeps the ask cheap."""


def read_twins(path: Path, seed: int = 17) -> pc.Twins:
    """The G-TWIN ask on one panel -- same face AND same dress -- judged in
    code by `pc.twin_fault`; the fixed seed keeps the vlm cache warm."""
    said = comfy.cached_text(WORKFLOW, {"image_1": comfy.stage_image(path), "prompt": pc.TWIN_ASK,
                                     "seed": seed, "max_new_tokens": TWIN_TOKENS},
                             readable=pc.twin_readable)
    return pc.parse_twins(said if isinstance(said, str) else str(said))


def twin_check(shot, seen: pc.Seen, path: Path) -> tuple[list[str], dict]:
    """The twin ask when it applies: (fault lines, the row's twin fields).
    An Unreadable ask on these sizes is a fault of its own -- the face is the
    picture, and a silent skip is a gate that passes everything."""
    if not pc.twin_applies(len(shot.faces or []), shot.size, seen.people):
        return [], {}
    try:
        t = read_twins(path)
    except pc.Unreadable as why:
        return [f"unread: twin {str(why)[:100]}"], {}
    bad = pc.twin_fault(t)
    return ([bad] if bad else []), {"figures": t.figures, "distinct": t.distinct, "twins": t.twins}


def physical_of(book: Path, who: list[str]) -> list[str]:
    """The bound rows of everyone the shot casts, ONE PER FACE (the hair check
    reads each row alone since 2026-09-30). A missing row raises: CAST BOUND
    refuses the plan before this can run, and a silent skip here would drop
    the facial-hair check without a word."""
    return [cast_refs.row(book, name).get("physical", "") for name in who]


def judge(book: Path, shot, setup, seen: pc.Seen) -> list[str]:
    return pc.faults(seen, frame=f"{shot.frame} {shot.at_rest}", planned=len(shot.faces or []),
                     crowd=bool((setup.crowd or "").strip()),
                     flat=pc.flat_place(book, setup.location),
                     night=panel_dq.at_night(setup.described), banned=pc.banned_subjects(book),
                     physical=physical_of(book, list(shot.faces or [])),
                     size=shot.size, extras=getattr(shot, "extras", 0))


def row_for(book: Path, shot, setup, path: Path) -> dict:
    """One panel's verdict row; an unreadable answer is a failed row."""
    try:
        seen = read(path)
    except pc.Unreadable as why:
        return {"shot": shot.index, "passed": False, "faults": [f"unread: {str(why)[:120]}"]}
    twins, fields = twin_check(shot, seen, path)                 # G-TWIN (2026-10-05)
    got = judge(book, shot, setup, seen) + twins
    return {"shot": shot.index, "passed": not got, "faults": got, "people": seen.people,
            "lookalikes": seen.lookalikes, "hour": seen.hour, "landform": seen.landform,
            "text": seen.text, "subjects": seen.subjects, **fields}


def main(book_id: str, number: int, only: list[int] | None = None) -> int:
    """All panels, or -- after a redraw -- ONLY the redrawn shots, their fresh
    rows merged into panel_content.json beside the untouched ones (five-hour
    plan fix 2c, 2026-09-30: a rung re-read the whole board at ~15 min a pass;
    ep13 paid 28 passes)."""
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    from studio import cast_refs, panel_ladder
    if why := cast_refs.chapter_refusal(book, number):   # this chapter's clothes (audit item 9)
        raise SystemExit(why)
    home = episode_home.home(book, number) / "storyboard"
    wanted = [s for s in ep.shots if not only or s.index in only]
    rows, missing = [], []
    with comfy.model_kept():        # the VL model loaded once for the batch (speed plan #6)
        for shot in wanted:
            path = home / f"shot_{shot.index:02d}.png"
            if not path.exists():
                missing.append(shot.index)
                continue
            row = row_for(book, shot, ep.setups[shot.setup], path)
            rows.append(row)
            print(f"  {'ok  ' if row['passed'] else 'FAIL'} shot {shot.index:02d}  "
                  f"{'; '.join(row['faults'])}", flush=True)
    out = home / "panel_content.json"
    if only:
        rows = panel_ladder.merge_content_rows(episode_home.read_json(out) if out.exists() else [], rows)
    episode_home.write_json(out, rows)
    failed = [r["shot"] for r in rows if not r["passed"]]
    print(f"\n{len(rows) - len(failed)}/{len(ep.shots)} panels clean on content; "
          f"failing {failed}; missing {missing}")
    return 1 if (failed or missing or not rows) else 0


if __name__ == "__main__":
    plain = [a for a in sys.argv[1:] if not a.startswith("--")]
    raise SystemExit(main(plain[0], episode_arg(sys.argv), [int(a) for a in plain[2:] if a.isdigit()]))
