#!/usr/bin/env python
"""Step 09_08 -- the tiny-face rung (face-blur round 2, 2026-10-19; BENCH_R2 lead 5, arm A3c).

The face refine (09_07) refuses a crop it cannot paste cleanly: on ep01 T01 the H3 crop repainted
the background round Utterson (36 px) and Enfield (30 px) and the seam read 19.1 against its wall of
18.  Under about 40 px nothing else gives such a face an eye.  The bench's 1024x1024 draw of the
same take (the Spark take graph, nothing else changed) was the only arm that drew both faces with
clean ink lines and a readable eye (cel eye 44 -> 55 and 57 -> 80, identity up).  So:

A take earns ONE re-render on that graph (takes_r2v `--tiny-face`, TINY_FACE_BASE) when
  - its refine decision on its CURRENT bytes refused (seam or drift) a face whose smallest tracked
    height is 20-40 px (`min_px`, else the row's `face_px`; under 20 px a 4/3 draw still gives no
    face: T06's 11 px Hyde drew none at 1024),
  - that person is planned on the take (a face of its shots, or a speaker of a line in them),
  - the take renders on the Spark graph (a wide or full shot: the 1024 graph IS that graph; an
    insert or a close size renders on Wuli),
  - the episode is square (1024x1024 is the only canvas the bench measured), and no still holds it.
The draw is a normal retake (its next seed, the same staged sheets, panel and audio), scaled back to
the episode's canvas on landing; then take_dq (G-WARP, flicker and every row), take_content (crowd,
extras) and the take eye judge it.  It is kept only when the eye passes it, then refined again (the
draw buys the take one more refine); else the old take, its graph, verdicts and record come back
(keep_best) and the draw is archived.  One draw per take per episode (the cap table's face_refine
row, 1 per take, counted as attempts.json `tiny_face.T<nn>`), its seconds booked to the `retakes`
wall, priced 1.75x a take and cut before the clock's reserve like the refine.  Never a loop: one
pass after step 09's refine.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, face_refine as fr, step_attempts, step_caps, take_ladder  # noqa: E402
from studio.face_paste import sha8  # noqa: E402

TINY_PX = 40.0
"""The soft paste's line (face_paste.SOFT_PX): a refused face under it is the T01 case."""
FLOOR_PX = 20.0
"""Under this a 1024 draw (x 4/3) still gives no face (T06 Hyde 10-11 px, eye 0 -> 0 at A3c)."""
REFUSALS = ("seam", "drift")
"""The walls a cleaner draw can answer; identity, flicker and a face count are the crop's own."""
FACTOR = 1.75
"""A 1024 draw against a 768 one: 163 s and 201 s for ep01 T01 and T06 (1.73-1.76x)."""
TAKES = Path("takes") / "r2v"
RENDER = "scripts/episode/takes_r2v.py"
DQ = "scripts/episode/take_dq.py"
CONTENT = "scripts/episode/take_content_check.py"
STEP = "09"


def key(index: int) -> str:
    return f"tiny_face.T{index:02d}"


def read(path: Path, default):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


# ---- the rule ---------------------------------------------------------------------------------

def smallest(person: dict) -> float:
    """The person's smallest tracked face (min_px, from 2026-10-19), else the crop's median."""
    return float(person.get("min_px") or person.get("face_px") or 0.0)


def refused_tiny(person: dict) -> bool:
    """The refine refused this face on a seam or drift wall, and it is 20-40 px at its smallest."""
    why = str(person.get("why") or "")
    return (not person.get("kept") and any(w in why for w in REFUSALS)
            and FLOOR_PX <= smallest(person) < TINY_PX)


def planned(plan: dict, shots: list[int]) -> set[str]:
    """The people the plan puts on these shots: their faces, and who speaks in them (not the narrator)."""
    shots = {int(s) for s in shots}
    faces = {w for s in plan.get("shots") or [] if int(s["index"]) in shots for w in s.get("faces") or []}
    said = {l["speaker"] for l in plan.get("lines") or []
            if int(l.get("shot", -1)) in shots and l.get("kind") != "narration" and l.get("speaker")}
    return faces | said


def on_spark(card: dict) -> bool:
    """The take renders on the Spark graph, the graph the 1024 draw copies (takes_r2v.workflow_for)."""
    from scripts.episode import takes_r2v
    return takes_r2v.workflow_for(card) != takes_r2v.WULI_BASE


def square(plan: dict) -> bool:
    from studio import canvas
    w, h = canvas.size(plan.get("aspect") or canvas.DEFAULT)
    return w == h


def tiny_people(entry: dict, card: dict, plan: dict) -> list[str]:
    """The planned people whose tiny face this take's refine refused; none off the Spark graph."""
    if not on_spark(card):
        return []
    cast = planned(plan, card.get("shots") or [card["index"]])
    return [p["who"] for p in entry.get("people") or [] if refused_tiny(p) and p.get("who") in cast]


def qualifying(doc: dict, cards: list[dict], plan: dict) -> dict[int, list[str]]:
    """take -> the people it earns the rung for, from refine.json, the cards and the plan."""
    out = {}
    for card in cards:
        if who := tiny_people(doc.get(f"T{int(card['index']):02d}") or {}, card, plan):
            out[int(card["index"])] = who
    return out


def owed(home: Path) -> dict[int, list[str]]:
    """The qualifying takes, on the bytes the refusal was read on, not yet drawn, not a still."""
    room, plan = Path(home) / TAKES, read(Path(home) / "plan.json", {})
    if not square(plan):
        return {}
    doc, stills = read(room / "refine.json", {}), take_ladder.live_stills(home)
    found = qualifying(doc, read(room / "prompts.json", []), plan)
    cap = step_caps.rounds("face_refine")         # the refine row's one per take: the rung is its cure
    return {i: who for i, who in found.items() if i not in stills and step_attempts.count(home, key(i)) < cap
            and (room / f"T{i:02d}.mp4").exists() and doc[f"T{i:02d}"].get("take_sha8") == sha8(room / f"T{i:02d}.mp4")}


# ---- the walls --------------------------------------------------------------------------------

def price(takes: int, faces: int) -> float:
    """One cold load, 1.75x a take per take, and the refine of those faces again."""
    return take_ladder.COLD_S + FACTOR * take_ladder.TAKE_S * takes + fr.price(faces, fr.REF_FRAMES)


def refused(ctx, takes: int, faces: int) -> str:
    """Why the rung may not draw (the retakes wall, the clock's reserve), '' when it may."""
    cost, wall = price(takes, faces), step_caps.wall_s(take_ladder.RETAKES)
    if step_attempts.seconds(ctx.home, take_ladder.RETAKES) + cost > wall:
        return f"the retakes wall ({step_caps.mmss(wall)}) has no {cost:.0f} s left"
    if fr.cut(getattr(ctx, "budget", None), STEP, cost):
        return f"the clock's reserve needs the time: {cost:.0f} s priced"
    return ""


# ---- the old take, kept aside and given back ------------------------------------------------------

def snapshot(room: Path, index: int) -> dict:
    """What a failed draw must give back: where the old take goes, its verdicts, its record."""
    stem = room / f"T{index:02d}"
    texts = {s: p.read_text(encoding="utf-8") for s in (".dq.json", ".content.json") if (p := stem.with_suffix(s)).exists()}
    rows = read(room / "shots.json", [])
    return {"fail": episode_home.next_fail(room, index), "texts": texts,
            "row": next((r for r in rows if int(r["index"]) == index), None)}


def restore(room: Path, index: int, snap: dict) -> None:
    """The old take back as T<nn> with its graph (episode_home.swap_in), then its verdicts (written
    after, so the content verdict is no older than the take) and its shots.json row."""
    episode_home.swap_in(room, index, snap["fail"])
    stem = room / f"T{index:02d}"
    for suffix, text in snap["texts"].items():
        stem.with_suffix(suffix).write_text(text, encoding="utf-8")
    if snap["row"] is not None:
        rows = [snap["row"] if int(r["index"]) == index else r for r in read(room / "shots.json", [])]
        episode_home.write_json(room / "shots.json", rows)


# ---- the pass ---------------------------------------------------------------------------------

def say(ctx, line: str) -> None:
    print(line, flush=True)
    ctx.log(line, step_id=STEP, level="WARNING")


def why_of(owing: dict[int, list[str]]) -> str:
    return "tiny_face: " + "; ".join(f"T{i:02d} {', '.join(who)}" for i, who in sorted(owing.items()))


def draw(ctx, owing: dict[int, list[str]], flag: str) -> dict[int, dict]:
    """The one batched draw: the old takes noted, each take's draw spent first, the seconds booked
    to the retakes wall; a render that died gives back every take it left missing."""
    room, indices = Path(ctx.home) / TAKES, sorted(owing)
    saved = {i: snapshot(room, i) for i in indices}
    for i in indices:
        step_attempts.spend(ctx.home, key(i))
    began = time.time()
    try:
        ctx.run_script(RENDER, "--from-refs", "--no-ends", flag, "--tiny-face",
                       *take_ladder.retake_args(indices, why_of(owing)), gpu=True, clock="takes")
    except SystemExit:
        for i in [i for i in indices if not (room / f"T{i:02d}.mp4").exists() and saved[i]["fail"].exists()]:
            restore(room, i, saved[i])
        raise
    finally:
        step_attempts.add_seconds(ctx.home, take_ladder.RETAKES, time.time() - began)
    return saved


def measure(ctx, indices: list[int], checks: tuple[str, ...] = ()) -> None:
    """Every take gate on the draws, never `--attempts` (it would rank the old take back by score)."""
    named = [str(i) for i in indices]
    take_ladder.measured(ctx, DQ, "take_dq", ".dq.json", *named, *checks)
    take_ladder.measured(ctx, CONTENT, "take_content", ".content.json", *named)


def settle(ctx, saved: dict[int, dict], judge) -> list[int]:
    """Each draw the take eye passes is kept; any other gives its old take back (keep_best)."""
    room, kept = Path(ctx.home) / TAKES, []
    for i, snap in sorted(saved.items()):
        verdict = judge(room / f"T{i:02d}.mp4")
        if verdict.passed:
            kept.append(i)
            say(ctx, f"TINY FACE T{i:02d}: the 1024 draw passed every take gate; kept, refined next")
            continue
        restore(room, i, snap)
        kinds = ", ".join(sorted({f.kind for f in verdict.faults}))
        say(ctx, f"TINY FACE T{i:02d}: the 1024 draw failed ({kinds}); the old take stays (keep_best)")
    return kept


def rung(ctx, flag: str, judge, checks: tuple[str, ...] = ()) -> list[int]:
    """The rung's one pass over the takes owed it; the takes whose draw was kept."""
    owing = owed(ctx.home)
    if not owing:
        return []
    if why := refused(ctx, len(owing), sum(len(w) for w in owing.values())):
        say(ctx, f"TINY FACE CUT: {why}; takes {sorted(owing)} keep their refused faces")
        return []
    saved = draw(ctx, owing, flag)
    measure(ctx, sorted(owing), checks)
    return settle(ctx, saved, judge)
