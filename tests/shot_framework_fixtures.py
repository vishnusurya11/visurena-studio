"""Jekyll Kawajiri ep01 as a book-shaped fixture, and its take prompts built by the production writer.

The shot-framework ruling (2026-10-21) lands defect fixes in `studio/episode_ref_official.py`; its red
tests read the prompts the writer builds for ep01's benched takes (T06, T10, T13, T15, T26), not the words
recorded when they rendered.  tests/fixtures/shot_framework/ holds copies of ep01's plan.json, placed.json,
refs/refs.json, refs/looks.json, refs/look.json, two analysis/locations rows, and the delivered cards'
words (shots.json).  `take_prompt` is `takes_r2v.card`'s own `ro.build` call for a from-refs take that
stages its panel (the mode ep01 rendered in), with nothing read from disk but those records."""
from __future__ import annotations

import contextlib
import json
from pathlib import Path

BOOK = Path(__file__).parent / "fixtures" / "shot_framework"


def delivered(index: int) -> str:
    """The words take `index` rendered from (ep01 takes/r2v/shots.json)."""
    rows = json.loads((BOOK / "shots.json").read_text(encoding="utf-8"))
    return next(r["prompt"] for r in rows if r["index"] == index)


def plan() -> dict:
    return json.loads((BOOK / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8"))


@contextlib.contextmanager
def adopted():
    """While open, the book's canon is adopted; every module table it writes is put back after."""
    from scripts.episode import takes_r2v as tr
    from studio import episode_home, house_style as hs, episode_ref_official as ro
    keep = (hs._where, hs._light, hs._look, hs._atmosphere, hs._panel_look, dict(hs._places), ro.DRAWN,
            tr.W, tr.H, tr.FROM_REFS)
    tables = [(t, t.copy()) for t in (ro.DISPLAY, ro.WOMEN, ro.CREATURES, ro.YOUNG, ro.ALIASES)]
    try:
        episode = episode_home.load_plan(BOOK, 1)
        tr.adopt_canon(BOOK, episode)
        yield episode
    finally:
        hs._where, hs._light, hs._look, hs._atmosphere, hs._panel_look, hs._places, ro.DRAWN, \
            tr.W, tr.H, tr.FROM_REFS = keep
        for table, was in tables:
            table.clear()
            table.update(was)


def take_of(episode, index: int) -> tuple[dict, dict]:
    """(the take packed on shot `index`, measured lines) from placed.json, as `takes_r2v.cards` packs it."""
    from studio import episode_takes as tk
    placed = json.loads((BOOK / "episodes" / "ep01" / "placed.json").read_text(encoding="utf-8"))
    shots = [dict(s, setup=episode.shot(s["index"]).setup) for s in placed["shots"]]
    take = next(t for t in tk.takes(shots, tk.budget_for(episode)) if t["shots"][0] == index)
    return {**take, "placed": shots}, {l["index"]: l for l in placed["lines"]}


def take_prompt(index: int) -> str:
    """The prompt the production writer builds today for ep01 take `index` (panel staged, from refs)."""
    from scripts.episode import takes_r2v as tr
    from studio import episode_ref_official as ro
    with adopted() as episode:
        take, measured = take_of(episode, index)
        shots = [episode.shot(i) for i in take["shots"]]
        setup = episode.setups[shots[0].setup]
        faces = tr.people_staged(shots, tr.staging_candidates(episode, shots))
        lines = [l for l in episode.lines if l.shot in take["shots"]]
        at = {l.index: (measured[l.index]["at"], measured[l.index]["seconds"]) for l in lines}
        sizes = [s.size for s in shots] + [c.size for s in shots for c in s.cuts]
        return ro.build(shots, take["placed"], lines, at, take["frames"], faces, tr.physicals(BOOK, setup),
                        setup.described, tr.narrator_of(episode.lines), ends=[], setup=setup,
                        refs=len(faces) + 1, fps=tr.FPS, props=[], panel=True, pin=True,
                        **tr.staged_facts(sizes, True, faces, panel=True))


def detailed(text: str) -> str:
    """The detailed_description section of a prompt."""
    from studio import episode_ref_official as ro
    return ro.sections(text).get("detailed_description") or ""
