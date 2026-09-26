#!/usr/bin/env python
"""Step 04 -- verdict: the LOOK judge signs the pack; nobody parks.

    uv run python scripts/refs/step_04_verdict.py <codex_id>

Done when refs/verdict.json signs the sha8 of refs/pack.jsonl as it stands.
Otherwise `judges.look` reads every sheet -- or, on a verdict for an earlier
pack, only the rows that arrived since -- and `judged_gate.clear` signs a pass
in the judge's name, climbs the sheet ladder (a bumped seed, then the defining
state first) on a hard fault, and at the terminal keeps the best try of each
sheet and signs the pack flagged with its faults listed, a learning and an
audit row (decision 2026-09-24-automate-the-taste-gates, gates.yaml refs/LOOK).
The refs context carries no budget and no learnings file: the ladder climbs on
its own clock and the learnings go to refs/learnings.jsonl.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import judged_gate, learnings, manifest as unit_manifest, refs_verdict, sheet_ladder, step_cli  # noqa: E402
from studio.judges import look  # noqa: E402

STEP_ID = "04"
NAME = "verdict"
GPU = True
GATE = "LOOK"
LEARNINGS = "refs/learnings.jsonl"
TOOLS = ("reader", "embed", "ocr", "keypoints", "style_embed")


def done(ctx) -> bool:
    return refs_verdict.current(ctx.book_dir) is not None


def learner(ctx):
    """A `learn` for a context without one: the row to refs/learnings.jsonl, a WARNING to the log."""
    def learn(learning):
        learnings.record(Path(ctx.book_dir) / LEARNINGS, learning)
        ctx.log(f"{learning.gate}: {learning.action} (attempt {learning.attempt}) {learning.note}"
                + (" (terminal)" if learning.terminal else ""), step_id=STEP_ID,
                level="INFO" if learning.action == "pass" else "WARNING")
    return learn


def equipped(ctx):
    """The refs context, given the budget and the learn a judged gate climbs on."""
    if getattr(ctx, "budget", None) is None:
        ctx.budget = sheet_ladder.budget()
    if getattr(ctx, "learn", None) is None:
        ctx.learn = learner(ctx)
    return ctx


BIBLE = ("refs/characters/", "refs/props/")
"""What the LOOK judge reads: the sheets that bind an identity.  A place picture
is drawn per episode at its own hour and judged there (the line's look-back);
the first real run would have read 178 pack paths, 150 of them places."""


def bound_ids(book_dir: Path) -> set[str]:
    """The entities refs.json binds: the bible the line reads.  A sheet on disk
    for an entity nobody bound (the first real bible held 49 character sheets
    for 19 bound rows) is not the bible's to judge."""
    import json
    path = Path(book_dir) / "refs" / "refs.json"
    if not path.exists():
        return set()
    return {r["entity_id"] for r in json.loads(path.read_text(encoding="utf-8")).get("refs", [])}


def judged_path(book_dir: Path, path: str, bound: set[str] | None = None) -> bool:
    """A BOUND bible sheet whose picture is on disk.  pack.jsonl is a log: a row
    whose file is gone is a superseded view, not a promise."""
    bound = bound_ids(book_dir) if bound is None else bound
    parts = path.split("/")
    entity = parts[2] if len(parts) >= 4 else ""
    return path.startswith(BIBLE) and entity in bound and (Path(book_dir) / path).exists()


PLACES = "refs/locations/"


def context_path(book_dir: Path, path: str, bound: set[str]) -> bool:
    """What a judged sheet is compared against: the bound bible, and every place
    picture on disk -- the style row's reference set, read for its style vector
    only (no VLM ask) by `look.read_bound`."""
    if path.startswith(PLACES):
        return (Path(book_dir) / path).exists()
    return judged_path(book_dir, path, bound)


def grandfathered(ctx) -> bool:
    """No verdict file yet on a bible that episodes already SHIPPED with (a
    master under episodes/): the first verdict signs the bound sheets on their
    calibrated rows alone -- their identity was judged by the episodes that
    used them.  A new book's first bible is read in full."""
    shipped = any(Path(ctx.book_dir).glob("episodes/ep*/cut/master*.mp4"))
    return refs_verdict.read(ctx.book_dir) is None and shipped


def paths_to_judge(ctx) -> list[str]:
    """Every bible path in the pack, or only the new rows' paths when the verdict is stale."""
    rows = sheet_ladder.pack_rows(ctx.book_dir)
    if refs_verdict.read(ctx.book_dir):
        n = refs_verdict.new_rows(ctx.book_dir)
        ctx.log(f"stale: {refs_verdict.VERDICT} signs another pack; {n} new row(s) since are judged",
                step_id=STEP_ID, level="WARNING")
        rows = rows[len(rows) - n:] if n else []
    bound = bound_ids(ctx.book_dir)
    return [p for p in dict.fromkeys(r["path"] for r in rows) if judged_path(ctx.book_dir, p, bound)]


def tools_of(ctx) -> dict:
    """The judge's readers hung on the context (a test's stubs); the defaults otherwise."""
    given = getattr(ctx, "look_tools", None) or {}
    return {k: given[k] for k in TOOLS if k in given}


def judge_of(ctx, paths: list[str]):
    """A judge over the rows as they stand now (a redraw appends a row), the
    rest of the pack bound; every fault is logged with its evidence."""
    def judge():
        rows = sheet_ladder.pack_rows(ctx.book_dir)
        bound = bound_ids(ctx.book_dir)
        light = grandfathered(ctx)
        others = [] if light else [p for p in dict.fromkeys(r["path"] for r in rows)
                                    if p not in paths and context_path(ctx.book_dir, p, bound)]
        if light:
            ctx.log(f"first verdict: {len(paths)} bound sheet(s) grandfathered -- calibrated rows only",
                    step_id=STEP_ID)
        verdict = look.judge(ctx.book_dir, sheet_ladder.latest(rows, paths),
                             bound=sheet_ladder.latest(rows, others), light=light, **tools_of(ctx))
        for f in verdict.faults:
            ctx.log(f"{GATE}: {f.kind} at {f.where} {f.evidence} {f.note}".strip(), step_id=STEP_ID,
                    level="WARNING" if f.kind in look.HARD else "INFO")
        return verdict
    return judge


def sign_of(ctx):
    return lambda v: refs_verdict.sign(ctx.book_dir, v.summary(), signed_by=v.signer,
                                       faults=[f.model_dump() for f in v.faults])


def run(ctx) -> None:
    equipped(ctx)
    paths = paths_to_judge(ctx)
    ladder = sheet_ladder.SheetLadder(Path(ctx.book_dir), run=getattr(ctx, "draw", None))
    judged_gate.clear(ctx, GATE, judge_of(ctx, paths), sign_of(ctx),
                      judged_gate.Rungs(sheet_ladder.LADDER, ladder.take), ladder.keep_best)
    ctx.log(f"{GATE}: signed by judge:{look.NAME}@{look.VERSION} over {len(paths)} row(s)", step_id=STEP_ID)
    write_manifest(ctx)


def write_manifest(ctx) -> Path:
    """The bible's manifest (studio/manifest.UnitManifest) at refs/, after the
    sign: what crosses to every format line that requires refs/04."""
    home = unit_manifest.home_of(ctx.stage, ctx.unit or "main")
    return unit_manifest.write_manifest(ctx.book_dir, home, unit_manifest.manifest_for(ctx, ctx.stage))


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
